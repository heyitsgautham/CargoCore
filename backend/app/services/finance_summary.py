"""The finance summary behind /finance/summary: revenue, expenses, payouts and trends."""

from collections import defaultdict
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsTransaction
from app.models.order import Order
from app.models.payment import OrderPayment
from app.models.user import User

# ── helpers ────────────────────────────────────────────────────────────────
from app.services.finance_common import (
    _legacy_order_revenue_amount,
    _today,
    resolve_transaction_warehouse_id,
)


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
