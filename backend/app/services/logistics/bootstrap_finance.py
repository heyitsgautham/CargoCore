"""Finance figures for the logistics bootstrap: revenue, COD, payroll and the transaction ledger."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsTransaction,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.schemas.logistics import (
    LogisticsTransactionItem,
)
from app.services.logistics.formatting import (
    _fmt_relative,
    _now,
    _title_case_status,
)


async def finance_snapshot(db: AsyncSession, today: date) -> tuple[dict, float, list[float], float]:
    """Finance summary plus today's revenue, the 7-day revenue series and the day-on-day trend in percent."""
    from app.services import finance_service as _finance_service

    finance_summary = await _finance_service.get_finance_summary(db)
    revenue_by_date = {
        str(item.get("date")): float(item.get("revenue") or 0.0)
        for item in finance_summary.get("revenue_by_day", [])
    }
    revenue_today = revenue_by_date.get(str(today), 0.0)
    revenue_week = [
        round(revenue_by_date.get(str(today - timedelta(days=offset)), 0.0), 2)
        for offset in range(6, -1, -1)
    ]
    yesterday_revenue = revenue_by_date.get(str(today - timedelta(days=1)), 0.0)
    if yesterday_revenue:
        revenue_trend = round(((revenue_today - yesterday_revenue) / abs(yesterday_revenue)) * 100, 1)
    elif revenue_today:
        revenue_trend = 100.0
    else:
        revenue_trend = 0.0
    return finance_summary, revenue_today, revenue_week, revenue_trend


def cod_records(user_map: dict[UUID, User], orders: Sequence[Order]) -> list[dict]:
    """Up to three pending and three paid cash-on-delivery orders for the finance page."""
    def _cod_hub_id(order: Order) -> str | None:
        """Resolve hubId for a COD order — fall back to driver's warehouse if order is legacy-unlinked."""
        if order.warehouse_id:
            return str(order.warehouse_id)
        # Legacy orders: infer from the assigned driver's warehouse
        driver = user_map.get(order.assigned_driver_id) if order.assigned_driver_id else None
        if driver and driver.warehouse_id:
            return str(driver.warehouse_id)
        # Last resort: pick first warehouse whose staff includes the customer or creator
        return None

    pending_cod_orders = [
        order
        for order in orders
        if (order.payment_mode or "").upper() == "COD" and order.payment_status == "pending"
    ][:3]

    finance_cod_records = [
        {
            "id": f"COD-{order.tracking_code}",
            "date": order.scheduled_at.strftime("%b %d, %Y") if order.scheduled_at else _fmt_relative(order.created_at),
            "desc": order.tracking_code,
            "name": user_map.get(order.assigned_driver_id).name if order.assigned_driver_id in user_map else "Unassigned Driver",
            "amount": float(order.total_amount),
            "status": "Completed" if order.payment_status == "paid" else "Pending",
            "type": "COD",
            "hubId": _cod_hub_id(order),
        }
        for order in pending_cod_orders + [order for order in orders if order.payment_mode == "COD" and order.payment_status == "paid"][:3]
    ]
    return finance_cod_records


async def payroll_records(
    db: AsyncSession,
    users: Sequence[User],
    role_by_id: dict[UUID, str],
    orders: Sequence[Order],
    driver_order_counts: dict[str, int],
) -> tuple[list[dict], list[dict]]:
    """Staff and driver payroll rows, marked Paid when a payroll run this month covered the user."""
    # ── Payroll records driven by real DB expense transactions ──────────────
    # EXPENSE_DRIVER rows represent shift fees booked per assignment.
    # We count how many such rows exist (each assignment => 1 EXPENSE_DRIVER tx)
    # and multiply by DRIVER_SHIFT_RATE.  If no rows yet => amount = 0.
    DRIVER_SHIFT_RATE = 1200.0   # must match finance_service.py
    STAFF_SESSION_RATE = 1600.0  # per active shift/session for WH managers / dispatchers

    # Query which users already had their payroll paid this month
    _current_month_start = _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=UTC)
    _payroll_paid_result = await db.execute(
        select(LogisticsTransaction.metadata_json)
        .where(
            LogisticsTransaction.transaction_type == "PAYROLL_RUN",
            LogisticsTransaction.transaction_date >= _current_month_start,
        )
    )
    paid_user_ids: set[str] = {
        row[0]["user_id"]
        for row in _payroll_paid_result.all()
        if row[0] and "user_id" in row[0]
    }

    finance_staff_records = []
    finance_driver_records = []

    for user in users:
        role_name = role_by_id.get(user.role_id, "")
        if role_name in {"INDIVIDUAL", "LOGISTIC_MANAGER"}:
            continue

        uid_str = str(user.id)
        uid_prefix = uid_str[:8].upper()
        hub_id = str(user.warehouse_id) if user.warehouse_id else None
        avatar = f"https://i.pravatar.cc/150?u={user.id}"

        if role_name in {"WAREHOUSE_MANAGER", "DISPATCHER"}:
            # Staff earned: number of active work-days at their hub.
            # For legacy data, orders may not have warehouse_id set — also count orders
            # assigned to drivers who belong to the same warehouse.
            hub_driver_ids = {
                u.id for u in users
                if u.warehouse_id == user.warehouse_id and role_by_id.get(u.role_id) == "DRIVER"
            }
            hub_orders = [
                o for o in orders
                if (
                    (o.warehouse_id and o.warehouse_id == user.warehouse_id)
                    or (not o.warehouse_id and o.assigned_driver_id and o.assigned_driver_id in hub_driver_ids)
                )
            ]
            days_active = len({
                o.created_at.date()
                for o in hub_orders
                if user.is_active and o.status not in {"DRAFT", "CANCELLED"}
            })
            payout = round(days_active * STAFF_SESSION_RATE, 2)
            if payout > 0:
                finance_staff_records.append({
                    "id": f"PAY-{uid_prefix}",
                    "userId": uid_str,
                    "date": _now().strftime("%b %d, %Y"),
                    "name": user.name,
                    "role": _title_case_status(role_name),
                    "amount": payout,
                    "status": "Paid" if uid_str in paid_user_ids else "Pending",
                    "avatar": avatar,
                    "hubId": hub_id,
                })
        elif role_name == "DRIVER":
            # Driver earned: number of EXPENSE_DRIVER transactions that reference orders
            # assigned to this driver (count driver_order_counts[uid_str] shifts)
            shifts = driver_order_counts.get(uid_str, 0)
            payout = round(shifts * DRIVER_SHIFT_RATE, 2)
            if payout > 0:
                finance_driver_records.append({
                    "id": f"WAGE-{uid_prefix}",
                    "userId": uid_str,
                    "date": _now().strftime("%b %d, %Y"),
                    "name": user.name,
                    "role": "Driver",
                    "amount": payout,
                    "status": "Paid" if uid_str in paid_user_ids else "Pending",
                    "avatar": avatar,
                    "hubId": hub_id,
                })
    return finance_staff_records, finance_driver_records


def build_transaction_items(
    transactions: list[LogisticsTransaction],
    orders: list[Order],
    user_map: dict[UUID, User],
    vehicle_map: dict[UUID, LogisticsVehicle],
) -> list[LogisticsTransactionItem]:
    """Ledger rows with their hub and, where one can be found, the order they belong to."""
    # Build order lookups for legacy transaction resolution and slip generation
    order_map_by_str_id: dict[str, Order] = {str(o.id): o for o in orders}
    order_map_by_tracking: dict[str, Order] = {
        str(o.tracking_code).upper(): o
        for o in orders
        if o.tracking_code
    }

    def _extract_tracking_code(value: str | None) -> str | None:
        if not value:
            return None
        match = re.search(r"\b([A-Z]{2,5}-[A-Z0-9]{4,})\b", str(value).upper())
        return match.group(1) if match else None

    def _related_order_for_transaction(tx: LogisticsTransaction) -> dict | None:
        meta = dict(tx.metadata_json or {})
        order = None

        order_id = meta.get("order_id")
        if order_id:
            order = order_map_by_str_id.get(str(order_id))

        tracking_code = meta.get("tracking_code") or _extract_tracking_code(tx.description)
        if order is None and tracking_code:
            order = order_map_by_tracking.get(str(tracking_code).upper())

        if order is None:
            return None

        customer = user_map.get(order.customer_id)
        driver = user_map.get(order.assigned_driver_id) if order.assigned_driver_id else None
        vehicle = vehicle_map.get(order.assigned_vehicle_id) if order.assigned_vehicle_id else None

        return {
            "id": str(order.id),
            "tracking_code": order.tracking_code,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "scheduled_at": order.scheduled_at.isoformat() if order.scheduled_at else None,
            "service_time_block": order.service_time_block,
            "pickup_addr": order.pickup_addr,
            "delivery_addr": order.delivery_addr,
            "total_amount": float(order.total_amount or 0.0),
            "paid_amount": float(order.paid_amount or 0.0),
            "payment_mode": order.payment_mode,
            "payment_status": order.payment_status,
            "labor_count": order.labor_count,
            "vehicle_type": order.vehicle_type,
            "customer_name": customer.name if customer else None,
            "customer_phone": customer.phone if customer else None,
            "customer_email": customer.email if customer else None,
            "assigned_driver_name": driver.name if driver else None,
            "assigned_vehicle_code": vehicle.code if vehicle else None,
        }

    def _tx_hub_id(tx: LogisticsTransaction) -> UUID | None:
        """Return the resolved warehouse_id for a transaction, inferring from metadata if null."""
        if tx.warehouse_id:
            return tx.warehouse_id
        meta = tx.metadata_json or {}
        # Try order_id first
        oid_str = meta.get("order_id")
        if oid_str:
            order = order_map_by_str_id.get(str(oid_str))
            if order and order.warehouse_id:
                return order.warehouse_id
            # Even if the order has no warehouse_id, try via its assigned driver
            if order and order.assigned_driver_id:
                driver = user_map.get(order.assigned_driver_id)
                if driver and driver.warehouse_id:
                    return driver.warehouse_id
        # Try collected_by / user_id in metadata
        for key in ("collected_by", "user_id"):
            uid_str = meta.get(key)
            if uid_str:
                try:
                    uid = UUID(str(uid_str))
                except (ValueError, TypeError):
                    continue
                u = user_map.get(uid)
                if u and u.warehouse_id:
                    return u.warehouse_id
        return None

    return [
        LogisticsTransactionItem(
            id=tx.id,
            hub_id=_tx_hub_id(tx),
            transaction_code=tx.transaction_code,
            date=tx.transaction_date.strftime("%b %d, %Y"),
            desc=tx.description,
            type=tx.transaction_type,
            amount=tx.amount,
            status=tx.status,
            metadata_json=dict(tx.metadata_json or {}),
            related_order=_related_order_for_transaction(tx),
        )
        for tx in transactions
    ]
