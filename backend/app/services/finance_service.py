"""
Finance Service
Live-computes revenue and expense aggregations from the database.
All numbers come from real DB rows — zero when tables are empty.
"""
import random
import string
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsDailyStats, LogisticsTransaction
from app.models.order import Order
from app.models.payment import OrderPayment
from app.models.user import User

# ── helpers ────────────────────────────────────────────────────────────────

def _today() -> date:
    return datetime.now(UTC).date()


def _gen_ref(prefix: str = "PAY") -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"{prefix}-{suffix}"


def _coerce_uuid(value) -> UUID | None:
    if value is None or value == "":
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def resolve_transaction_warehouse_id(
    tx: LogisticsTransaction,
    order_warehouse_by_id: dict[UUID, UUID | None],
    order_warehouse_by_tracking: dict[str, UUID | None],
    user_warehouse_by_id: dict[UUID, UUID | None],
) -> UUID | None:
    if tx.warehouse_id:
        return tx.warehouse_id

    metadata = tx.metadata_json or {}

    order_id = _coerce_uuid(metadata.get("order_id"))
    if order_id in order_warehouse_by_id:
        return order_warehouse_by_id[order_id]

    tracking_code = metadata.get("tracking_code")
    if tracking_code and tracking_code in order_warehouse_by_tracking:
        return order_warehouse_by_tracking[tracking_code]

    user_id = _coerce_uuid(metadata.get("user_id") or metadata.get("collected_by"))
    if user_id in user_warehouse_by_id:
        return user_warehouse_by_id[user_id]

    return None


def _legacy_order_revenue_amount(order: Order, recorded_payment_total: float) -> float:
    if recorded_payment_total > 0:
        return 0.0
    if order.payment_status != "paid":
        return 0.0
    if order.status in {"CANCELLED", "DRAFT"}:
        return 0.0
    return float(order.paid_amount or order.total_amount or 0.0)


async def _upsert_daily_stats(
    db: AsyncSession,
    delta_revenue: float = 0.0,
    warehouse_id: UUID | None = None,
) -> None:
    """Add delta_revenue to today's LogisticsDailyStats row (upsert)."""
    today = _today()
    query = select(LogisticsDailyStats).where(LogisticsDailyStats.stat_date == today)
    if warehouse_id is None:
        query = query.where(LogisticsDailyStats.warehouse_id.is_(None))
    else:
        query = query.where(LogisticsDailyStats.warehouse_id == warehouse_id)

    row = (await db.execute(query)).scalar_one_or_none()
    if row is None:
        row = LogisticsDailyStats(
            warehouse_id=warehouse_id,
            stat_date=today,
            orders_count=0,
            revenue=0.0,
            deliveries_completed=0,
            deliveries_failed=0,
            sla_compliance=95.0,
        )
        db.add(row)
    row.revenue = (row.revenue or 0.0) + delta_revenue
    db.add(row)


# ── core payment recorder ──────────────────────────────────────────────────

async def record_order_payment(
    db: AsyncSession,
    order_id: UUID,
    amount: float,
    payment_mode: str,           # ONLINE | COD | PARTIAL
    payment_method: str | None,  # "UPI | GPay", "Card ending 4242", etc.
    payment_ref: str | None,     # Razorpay pay_XXXX or None (auto-generated)
    collected_by_user: User | None = None,
    notes: str | None = None,
) -> OrderPayment:
    """
    Record a payment event:
      1. Creates OrderPayment row
      2. Updates Order.paid_amount + payment_status
      3. Creates LogisticsTransaction (type=REVENUE_ONLINE/COD)
      4. Updates LogisticsDailyStats.revenue
    """
    from app.models.order import Order

    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if order is None:
        from fastapi import HTTPException
        from fastapi import status as http_status
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Order not found")

    ref = payment_ref or _gen_ref("PAY")

    # 1. OrderPayment row
    pmt = OrderPayment(
        order_id=order_id,
        payment_ref=ref,
        payment_mode=payment_mode.upper(),
        payment_method=payment_method,
        amount=amount,
        status="completed",
        collected_by=collected_by_user.id if collected_by_user else None,
        notes=notes,
    )
    db.add(pmt)

    # 2. Update Order
    order.paid_amount = (order.paid_amount or 0.0) + amount
    if order.paid_amount >= order.total_amount:
        order.payment_status = "paid"
    elif order.paid_amount > 0:
        order.payment_status = "partial"
    db.add(order)

    from app.services.return_charge_service import (
        settle_transport_charges_from_order_payment,
    )
    await settle_transport_charges_from_order_payment(
        db,
        order=order,
        payment_amount=amount,
        collection_source=payment_mode.upper(),
    )

    # 3. LogisticsTransaction
    tx_type = "REVENUE_COD" if payment_mode.upper() == "COD" else "REVENUE_ONLINE"
    tx = LogisticsTransaction(
        warehouse_id=order.warehouse_id,
        transaction_code=ref,
        description=f"Order {order.tracking_code} - {payment_method or payment_mode}",
        transaction_type=tx_type,
        amount=amount,
        status="Completed",
        metadata_json={
            "order_id": str(order_id),
            "tracking_code": order.tracking_code,
            "payment_mode": payment_mode,
            "payment_method": payment_method,
            "collected_by": str(collected_by_user.id) if collected_by_user else None,
        },
    )
    db.add(tx)

    # 4. Daily stats
    await _upsert_daily_stats(db, delta_revenue=amount)
    if order.warehouse_id:
        await _upsert_daily_stats(db, delta_revenue=amount, warehouse_id=order.warehouse_id)

    await db.flush()
    return pmt


# ── expense recorder ────────────────────────────────────────────────────────

LABOUR_RATE_PER_HEAD = 800.0      # ₹/laborer
DRIVER_SHIFT_RATE = 1200.0        # ₹ flat per shift
FUEL_RATE_PER_KM = {
    "mini": 8, "tempo": 10, "lcv": 14, "hcv": 20,
}
WAREHOUSE_FEE_RATIO = 0.05        # 5% of total as warehouse handling fee


async def record_expense(
    db: AsyncSession,
    expense_type: str,   # EXPENSE_LABOUR | EXPENSE_DRIVER | EXPENSE_FUEL | EXPENSE_WAREHOUSE | EXPENSE_PROCUREMENT
    amount: float,
    description: str,
    warehouse_id: UUID | None = None,
    order_id: UUID | None = None,
    tracking_code: str | None = None,
    extra_metadata: dict | None = None,
) -> None:
    """Write a LogisticsTransaction expense row (does NOT touch daily stats revenue)."""
    if amount <= 0:
        return
    ref = _gen_ref("EXP")
    meta = {
        "order_id": str(order_id) if order_id else None,
        "tracking_code": tracking_code,
    }
    if extra_metadata:
        meta.update(extra_metadata)
    tx = LogisticsTransaction(
        warehouse_id=warehouse_id,
        transaction_code=ref,
        description=description,
        transaction_type=expense_type,
        amount=-abs(amount),   # expenses are negative
        status="Completed",
        metadata_json=meta,
    )
    db.add(tx)


async def create_capital_investment(
    db: AsyncSession,
    amount: float,
    description: str,
    funding_source: str,
    warehouse_id: UUID | None = None,
    investment_date: str | None = None,
) -> dict:
    """Record an offline capital injection (cash, bank transfer, owner equity, etc.)."""
    ref = _gen_ref("CAP")
    tx = LogisticsTransaction(
        transaction_code=ref,
        warehouse_id=warehouse_id,
        description=description,
        transaction_type="CAPITAL_INVESTMENT",
        amount=abs(amount),   # positive — money coming in
        status="Completed",
        metadata_json={
            "funding_source": funding_source,
            "investment_date": investment_date,
        },
    )
    db.add(tx)
    await db.flush()
    return {
        "id": str(tx.id),
        "transaction_code": tx.transaction_code,
        "description": tx.description,
        "transaction_type": tx.transaction_type,
        "amount": tx.amount,
        "funding_source": funding_source,
        "status": tx.status,
    }


# ── aggregation (for the /finance/summary endpoint) ─────────────────────────

async def get_finance_summary(db: AsyncSession, warehouse_id: UUID | None = None) -> dict:
    order_query = select(Order)
    if warehouse_id:
        order_query = order_query.where(Order.warehouse_id == warehouse_id)
    orders = (await db.execute(order_query)).scalars().all()

    payment_query = (
        select(OrderPayment)
        .join(Order, Order.id == OrderPayment.order_id)
        .where(
            OrderPayment.status == "completed",
            # Exclude REFUND reversals; WALLET payments are now covered via
            # REVENUE_WALLET LogisticsTransaction rows created by wallet_service.
            OrderPayment.payment_mode.notin_(["WALLET", "REFUND"]),
        )
    )
    if warehouse_id:
        payment_query = payment_query.where(Order.warehouse_id == warehouse_id)
    payments = (await db.execute(payment_query)).scalars().all()

    user_query = select(User)
    if warehouse_id:
        user_query = user_query.where(User.warehouse_id == warehouse_id)
    users = (await db.execute(user_query)).scalars().all()

    transaction_query = select(LogisticsTransaction)
    if warehouse_id:
        transaction_query = transaction_query.where(
            or_(
                LogisticsTransaction.warehouse_id == warehouse_id,
                LogisticsTransaction.warehouse_id.is_(None),
            )
        )
    transactions = (await db.execute(transaction_query)).scalars().all()

    order_warehouse_by_id = {order.id: order.warehouse_id for order in orders}
    order_warehouse_by_tracking = {
        order.tracking_code: order.warehouse_id
        for order in orders
        if order.tracking_code
    }
    user_warehouse_by_id = {user.id: user.warehouse_id for user in users}

    scoped_transactions = [
        tx for tx in transactions
        if warehouse_id is None
        or resolve_transaction_warehouse_id(
            tx,
            order_warehouse_by_id=order_warehouse_by_id,
            order_warehouse_by_tracking=order_warehouse_by_tracking,
            user_warehouse_by_id=user_warehouse_by_id,
        ) == warehouse_id
    ]

    payment_totals_by_order: dict[UUID, float] = defaultdict(float)
    revenue_by_mode_acc: dict[str, float] = defaultdict(float)
    revenue_by_day_acc: dict[date, float] = defaultdict(float)
    refunds_by_day_acc: dict[date, float] = defaultdict(float)
    normalized_revenue = 0.0

    for payment in payments:
        payment_totals_by_order[payment.order_id] += float(payment.amount or 0.0)
        normalized_revenue += float(payment.amount or 0.0)
        revenue_by_mode_acc[payment.payment_mode or "UNKNOWN"] += float(payment.amount or 0.0)
        if payment.created_at:
            revenue_by_day_acc[payment.created_at.date()] += float(payment.amount or 0.0)

    legacy_revenue = 0.0
    for order in orders:
        legacy_amount = _legacy_order_revenue_amount(order, payment_totals_by_order[order.id])
        if legacy_amount <= 0:
            continue
        legacy_revenue += legacy_amount
        revenue_by_mode_acc[order.payment_mode or "UNKNOWN"] += legacy_amount
        if order.created_at:
            revenue_by_day_acc[order.created_at.date()] += legacy_amount

    total_refunds_issued = 0.0
    return_charge_revenue = 0.0
    wallet_revenue = 0.0
    for tx in scoped_transactions:
        tx_amount = float(tx.amount or 0.0)
        if tx.transaction_type == "REVENUE_REFUND":
            refund_amount = abs(tx_amount)
            total_refunds_issued += refund_amount
            if tx.transaction_date:
                refunds_by_day_acc[tx.transaction_date.date()] += refund_amount
            continue
        if tx.transaction_type == "REVENUE_RETURN_CHARGE" and tx_amount > 0:
            return_charge_revenue += tx_amount
            revenue_by_mode_acc["RETURN_CHARGE"] += tx_amount
            if tx.transaction_date:
                revenue_by_day_acc[tx.transaction_date.date()] += tx_amount
        # ── Wallet-paid bookings recorded as REVENUE_WALLET transactions ──
        if tx.transaction_type == "REVENUE_WALLET" and tx_amount > 0:
            wallet_revenue += tx_amount
            revenue_by_mode_acc["WALLET"] += tx_amount
            if tx.transaction_date:
                revenue_by_day_acc[tx.transaction_date.date()] += tx_amount

    gross_revenue = max(0.0, normalized_revenue + legacy_revenue + return_charge_revenue + wallet_revenue - total_refunds_issued)

    expense_breakdown_acc: dict[str, float] = defaultdict(float)
    total_expenses = 0.0
    total_payroll_due = 0.0
    procurement_expenses = 0.0
    capital_invested = 0.0
    # Bonus/staff payouts drawn from revenue (EXPENSE_BONUS, Expense, PAYROLL_RUN, etc.)
    revenue_debit_expenses = 0.0

    # Types that should be paid FROM revenue (not from external capital)
    REVENUE_DEBIT_TYPES = {
        "EXPENSE_BONUS", "PAYROLL_RUN", "EXPENSE_DRIVER", "EXPENSE_LABOUR",
        "Expense", "Payroll"
    }

    for tx in scoped_transactions:
        amount = float(tx.amount or 0.0)
        tx_type = tx.transaction_type or "UNKNOWN"
        if amount < 0 and tx_type != "REVENUE_REFUND":
            abs_amount = abs(amount)
            total_expenses += abs_amount
            expense_breakdown_acc[tx_type] += abs_amount
            if tx_type in {"EXPENSE_DRIVER", "EXPENSE_LABOUR"}:
                total_payroll_due += abs_amount
            if tx_type == "EXPENSE_PROCUREMENT":
                procurement_expenses += abs_amount
            # Track which expenses debit from revenue vs capital
            if tx_type in REVENUE_DEBIT_TYPES:
                revenue_debit_expenses += abs_amount
        elif tx_type == "CAPITAL_INVESTMENT" and amount > 0:
            capital_invested += amount

    # ─── Revenue vs Expenses vs Capital ───────────────────────────────────────
    # total_revenue = what customers ACTUALLY PAID (gross).  This is what the
    # "Revenue (MTD)" stat card should always display — it must NEVER be zeroed
    # out by expenses, because expenses are a separate outflow.
    # The capital overflow logic is for internal accounting only:
    #   If gross_revenue < expenses, the shortfall is drawn from capital_invested.
    total_revenue = gross_revenue   # ← always show real customer payments

    # Capital accounting: how much capital remains after covering the expense
    # shortfall that revenue could not cover.
    expense_shortfall = max(0.0, total_expenses - gross_revenue)
    effective_capital = max(0.0, capital_invested - expense_shortfall)

    # Net profit uses actual revenue minus actual expenses (may be negative)
    net_profit_value = gross_revenue - total_expenses

    # Alert: fire when revenue alone cannot cover expenses and capital is also
    # running low (i.e. operations are being funded entirely from capital reserve).
    capital_flow_empty = gross_revenue <= 0.0

    pending_cod = float(sum(
        order.total_amount or 0.0
        for order in orders
        if (order.payment_mode or "").strip().upper() == "COD"
        and order.payment_status == "pending"
    ))

    thirty_ago = _today() - timedelta(days=29)
    revenue_by_day = [
        {
            "date": str(day),
            "revenue": round(revenue_by_day_acc.get(day, 0.0) - refunds_by_day_acc.get(day, 0.0), 2),
        }
        for day in (
            thirty_ago + timedelta(days=offset)
            for offset in range(30)
        )
    ]

    total_orders = len(orders)
    delivered_orders = sum(1 for order in orders if order.status == "DELIVERED")
    expense_breakdown = {
        key: round(value, 2)
        for key, value in expense_breakdown_acc.items()
    }
    revenue_by_mode = {
        key: round(value, 2)
        for key, value in revenue_by_mode_acc.items()
    }

    return {
        "total_revenue": round(total_revenue, 2),          # gross customer payments
        "total_expenses": round(total_expenses, 2),
        "net_profit": round(net_profit_value, 2),
        "pending_cod": round(pending_cod, 2),
        "total_payroll_due": round(total_payroll_due, 2),
        "procurement_expenses": round(procurement_expenses, 2),
        "capital_invested": round(effective_capital, 2),    # remaining capital after covering shortfall
        "gross_capital_invested": round(capital_invested, 2),
        "capital_flow_empty": capital_flow_empty,           # true only when zero customer revenue
        "revenue_debit_expenses": round(revenue_debit_expenses, 2),
        "total_refunds_issued": round(total_refunds_issued, 2),
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "revenue_by_day": revenue_by_day,
        "expense_breakdown": expense_breakdown,
        "revenue_by_mode": revenue_by_mode,
    }


async def run_payroll(db: AsyncSession, user_payouts: list[dict]) -> dict:
    """
    Persist payroll payments as PAYROLL_RUN transactions — one per user.
    Each transaction stores user_id + payroll_period in metadata_json so the
    bootstrap can query them to mark records as 'Paid' after the run.

    user_payouts: list of {user_id, amount, record_type, name}
    """
    period = datetime.now(UTC).strftime("%Y-%m")
    created = 0
    total_paid = 0.0
    user_ids = [uuid.UUID(str(payout["user_id"])) for payout in user_payouts if payout.get("user_id")]
    users_by_id = {}
    if user_ids:
        users_by_id = {
            user.id: user
            for user in (
                await db.execute(select(User).where(User.id.in_(user_ids)))
            ).scalars().all()
        }

    for payout in user_payouts:
        amount = float(payout.get("amount", 0))
        if amount <= 0:
            continue
        user_id = uuid.UUID(str(payout["user_id"]))
        user = users_by_id.get(user_id)
        tx = LogisticsTransaction(
            warehouse_id=user.warehouse_id if user else None,
            transaction_code=_gen_ref("PAY"),
            description=f"Payroll - {payout.get('name', 'Staff')} ({period})",
            transaction_type="PAYROLL_RUN",
            amount=-abs(amount),
            status="Completed",
            metadata_json={
                "user_id": str(user_id),
                "payroll_period": period,
                "record_type": payout.get("record_type", "staff"),
                "name": payout.get("name", ""),
            },
        )
        db.add(tx)
        created += 1
        total_paid += amount

    await db.flush()
    return {"count": created, "total": round(total_paid, 2)}
