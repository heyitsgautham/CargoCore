"""
Finance Service
Live-computes revenue and expense aggregations from the database.
All numbers come from real DB rows — zero when tables are empty.
"""
import random
import string
import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsDailyStats, LogisticsTransaction
from app.models.order import Order
from app.models.payment import OrderPayment
from app.models.user import User

# ── helpers ────────────────────────────────────────────────────────────────
from app.services.finance_common import (
    _today,
)

# The summary lives in finance_summary; routers, the AI chat and tests keep reaching it through here.
from app.services.finance_summary import (
    get_finance_summary as get_finance_summary,
)


def _gen_ref(prefix: str = "PAY") -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"{prefix}-{suffix}"


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
