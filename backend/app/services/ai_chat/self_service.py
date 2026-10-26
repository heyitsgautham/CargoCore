"""Answers for customers and vendors: orders, wallet, recurring runs, support, spend and refunds."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsReturnCase,
)
from app.models.order import DamageReport, Order
from app.models.user import User
from app.models.vendor import VendorRecurringRule, VendorSupportTicket
from app.models.wallet import WalletTransaction
from app.services.ai_chat.intents import (
    _extract_tracking_code,
    _format_money,
    _normalize_text,
)
from app.services.wallet_service import get_wallet_balance

IST = ZoneInfo("Asia/Kolkata")


def _format_schedule(scheduled_at: datetime | None) -> str:
    """A schedule as customers read it, for example 26 Oct 2026, 12:08 AM IST."""
    if scheduled_at is None:
        return "Not scheduled yet"
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=UTC)
    return scheduled_at.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")


async def _list_current_self_service_orders(
    ro_db: AsyncSession,
    user: User,
    role: str,
) -> str:
    noun_plural = "shipments" if role == "VENDOR" else "orders"
    rows = (
        await ro_db.execute(
            select(Order)
            .where(
                Order.customer_id == user.id,
                func.upper(Order.status).notin_(["DELIVERED", "CANCELLED"]),
            )
            .order_by(Order.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    if not rows:
        return f"You do not have any active {noun_plural} right now."

    header = f"Here are your current {noun_plural}:"
    lines = [header]
    for order in rows:
        schedule = _format_schedule(order.scheduled_at)
        stage = order.warehouse_substatus or "N/A"
        lines.append(
            f"- {order.tracking_code}: {order.status} | Stage: {stage} | Scheduled: {schedule}"
        )
    return "\n".join(lines)


async def _list_self_service_orders_by_status(
    ro_db: AsyncSession,
    user: User,
    role: str,
    status_label: str,
    statuses: set[str],
) -> str:
    noun_plural = "shipments" if role == "VENDOR" else "orders"
    rows = (
        await ro_db.execute(
            select(Order)
            .where(
                Order.customer_id == user.id,
                func.upper(Order.status).in_(sorted(statuses)),
            )
            .order_by(Order.created_at.desc())
            .limit(10)
        )
    ).scalars().all()

    if not rows:
        return f"You do not have any {status_label} {noun_plural} right now."

    lines = [f"Here are your {status_label} {noun_plural}:"]
    for order in rows:
        schedule = _format_schedule(order.scheduled_at)
        stage = order.warehouse_substatus or "N/A"
        lines.append(
            f"- {order.tracking_code}: {order.status} | Stage: {stage} | Scheduled: {schedule}"
        )
    return "\n".join(lines)


async def _lookup_self_service_order(
    ro_db: AsyncSession,
    user: User,
    user_message: str,
) -> tuple[Order | None, str | None]:
    tracking_code = _extract_tracking_code(user_message)

    stmt = select(Order).where(Order.customer_id == user.id)
    if tracking_code:
        stmt = stmt.where(func.upper(Order.tracking_code) == tracking_code).limit(1)
    else:
        stmt = stmt.order_by(Order.created_at.desc()).limit(1)

    order = (await ro_db.execute(stmt)).scalar_one_or_none()
    return order, tracking_code


def _format_self_service_order_message(
    order: Order,
    role: str,
    tracking_code: str | None = None,
) -> str:
    noun = "shipment" if role == "VENDOR" else "order"
    heading = (
        f"Your {noun}: **{order.tracking_code}**"
        if tracking_code
        else f"Your latest {noun}: **{order.tracking_code}**"
    )
    eta = _format_schedule(order.scheduled_at)
    pickup_addr = order.pickup_addr or "N/A"
    delivery_addr = order.delivery_addr or "N/A"
    substatus = order.warehouse_substatus or "N/A"
    return (
        f"{heading}\n"
        f"- Status: {order.status}\n"
        f"- Warehouse stage: {substatus}\n"
        f"- Scheduled: {eta}\n"
        f"- Route: {pickup_addr} -> {delivery_addr}"
    )


async def _vendor_wallet_message(ro_db: AsyncSession, user: User) -> str:
    balance = round(await get_wallet_balance(ro_db, user.id), 2)
    rows = (
        await ro_db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.user_id == user.id)
            .order_by(WalletTransaction.created_at.desc())
            .limit(3)
        )
    ).scalars().all()
    lines = [f"Your wallet balance right now is **{_format_money(balance)}**."]
    if rows:
        lines.append("Recent wallet activity:")
        for tx in rows:
            lines.append(
                f"- {tx.transaction_kind}: {_format_money(float(tx.amount or 0.0))} for {tx.reason} on {tx.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
    else:
        lines.append("No wallet transactions found yet.")
    return "\n".join(lines)


async def _vendor_recurring_orders_message(ro_db: AsyncSession, user: User) -> str:
    rules = (
        await ro_db.execute(
            select(VendorRecurringRule)
            .where(VendorRecurringRule.vendor_id == user.id)
            .order_by(VendorRecurringRule.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    if not rules:
        return (
            "You do not have any recurring shipment schedules yet. "
            "Create one from the Recurring Orders section to automate repeat shipments."
        )

    lines = ["Here are your recurring shipment schedules:"]
    for rule in rules:
        status = "Active" if rule.active else "Paused"
        lines.append(
            f"- {rule.name}: {rule.frequency} | Next run: {rule.next_run} | Route: {rule.route} | {status}"
        )
    return "\n".join(lines)


async def _vendor_support_message(ro_db: AsyncSession, user: User) -> str:
    tickets = (
        await ro_db.execute(
            select(VendorSupportTicket)
            .where(VendorSupportTicket.vendor_id == user.id)
            .order_by(VendorSupportTicket.created_at.desc())
            .limit(3)
        )
    ).scalars().all()

    open_count = (
        await ro_db.execute(
            select(func.count())
            .select_from(VendorSupportTicket)
            .where(
                VendorSupportTicket.vendor_id == user.id,
                func.upper(VendorSupportTicket.status) != "RESOLVED",
            )
        )
    ).scalar_one()

    lines = [
        f"You currently have {int(open_count or 0)} open support ticket(s).",
    ]
    if tickets:
        latest = tickets[0]
        lines.append(
            f"Latest ticket: {latest.subject} | Status: {latest.status} | Priority: {latest.priority}"
        )
    else:
        lines.append("No support tickets have been raised yet.")
    lines.append("If you need further help, you can raise a new ticket from the Support Tickets tab.")
    return "\n".join(lines)


async def _vendor_analytics_message(ro_db: AsyncSession, user: User) -> str:
    orders = (
        await ro_db.execute(
            select(Order)
            .where(Order.customer_id == user.id)
            .order_by(Order.created_at.desc())
        )
    ).scalars().all()

    total = len(orders)
    delivered = sum(1 for order in orders if _normalize_text(order.status) == "delivered")
    cancelled = sum(1 for order in orders if _normalize_text(order.status) == "cancelled")
    active = sum(1 for order in orders if _normalize_text(order.status) not in {"delivered", "cancelled"})
    successful = max(total - cancelled, 0)
    success_rate = round((successful / total) * 100, 1) if total else 0.0
    avg_order_value = round(sum(float(order.total_amount or 0.0) for order in orders) / total, 2) if total else 0.0
    current_month = datetime.now(UTC).strftime("%Y-%m")
    monthly_spend = round(
        sum(float(order.total_amount or 0.0) for order in orders if order.created_at.strftime("%Y-%m") == current_month),
        2,
    )

    return (
        "The Analytics section shows your shipment trends and business performance, "
        "including monthly spend, active vs delivered shipments, success rate, and average order value.\n"
        f"Right now: total shipments **{total}**, active **{active}**, delivered **{delivered}**, "
        f"success rate **{success_rate}%**, average order value **{_format_money(avg_order_value)}**, "
        f"this month spend **{_format_money(monthly_spend)}**."
    )


async def _self_service_spend_message(ro_db: AsyncSession, user: User, role: str) -> str:
    orders = (
        await ro_db.execute(
            select(Order)
            .where(Order.customer_id == user.id)
            .order_by(Order.created_at.desc())
        )
    ).scalars().all()

    completed_orders = [
        order for order in orders
        if _normalize_text(order.payment_status) == "paid" or _normalize_text(order.status) == "delivered"
    ]
    total_spent = round(sum(float(order.total_amount or 0.0) for order in completed_orders), 2)
    current_month = datetime.now(UTC).strftime("%Y-%m")
    month_spent = round(
        sum(
            float(order.total_amount or 0.0)
            for order in completed_orders
            if order.created_at.strftime("%Y-%m") == current_month
        ),
        2,
    )
    noun_plural = "shipments" if role == "VENDOR" else "orders"

    if not completed_orders:
        return (
            f"You have not completed any paid {noun_plural} yet, so your total spend so far is "
            f"**{_format_money(0.0)}**."
        )

    latest = completed_orders[0]
    return (
        f"Your total spend so far is **{_format_money(total_spent)}** across **{len(completed_orders)}** completed {noun_plural}.\n"
        f"This month: **{_format_money(month_spent)}**.\n"
        f"Latest completed {'shipment' if role == 'VENDOR' else 'order'}: **{latest.tracking_code}** for **{_format_money(float(latest.total_amount or 0.0))}**."
    )


async def _self_service_refund_message(
    ro_db: AsyncSession,
    user: User,
    role: str,
    user_message: str,
) -> str:
    msg = _normalize_text(user_message)
    refund_rows = (
        await ro_db.execute(
            select(WalletTransaction, Order.tracking_code)
            .outerjoin(Order, Order.id == WalletTransaction.order_id)
            .where(
                WalletTransaction.user_id == user.id,
                WalletTransaction.reason.in_(["CANCELLATION_REFUND", "DAMAGE_REFUND"]),
            )
            .order_by(WalletTransaction.created_at.desc())
            .limit(10)
        )
    ).all()

    if role == "INDIVIDUAL" and ("damage" in msg or "claim" in msg):
        damage_rows = (
            await ro_db.execute(
                select(DamageReport.reference_code, LogisticsReturnCase.refund_amount, LogisticsReturnCase.status, Order.tracking_code)
                .select_from(DamageReport)
                .outerjoin(LogisticsReturnCase, LogisticsReturnCase.reference_code == DamageReport.reference_code)
                .outerjoin(Order, Order.id == DamageReport.order_id)
                .where(DamageReport.customer_id == user.id)
                .order_by(DamageReport.created_at.desc())
                .limit(10)
            )
        ).all()
        approved_damage = [row for row in damage_rows if float(row.refund_amount or 0.0) > 0]
        if not approved_damage:
            return (
                "You do not have any approved damage-report refunds yet. "
                "If a claim is approved, the refund will appear in your wallet history."
            )

        total_damage_refund = round(sum(float(row.refund_amount or 0.0) for row in approved_damage), 2)
        lines = [f"Your approved damage-report refunds total **{_format_money(total_damage_refund)}**."]
        for row in approved_damage[:5]:
            tracking_code = row.tracking_code or "No linked order"
            lines.append(
                f"- {tracking_code}: {_format_money(float(row.refund_amount or 0.0))} | Claim status: {row.status or 'N/A'}"
            )
        return "\n".join(lines)

    if not refund_rows:
        return "You do not have any wallet refunds recorded yet."

    total_refunds = round(sum(float(tx.amount or 0.0) for tx, _ in refund_rows), 2)
    lines = [f"Your total recorded refunds are **{_format_money(total_refunds)}**."]
    for tx, tracking_code in refund_rows[:5]:
        ref_label = tracking_code or "Wallet adjustment"
        lines.append(
            f"- {ref_label}: {_format_money(float(tx.amount or 0.0))} | {tx.reason} | {tx.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
    return "\n".join(lines)
