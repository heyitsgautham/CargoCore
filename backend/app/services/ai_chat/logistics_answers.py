"""Logistics manager snapshot and the shortcut answers built from it."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, RestockRequest
from app.models.logistics import (
    LogisticsAlert,
    LogisticsDailyStats,
    LogisticsDriverProfile,
    LogisticsReturnCase,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import (
    Warehouse,
)
from app.schemas.ai import (
    ChatResponse,
)
from app.services.ai_chat.conversations import _persist_message
from app.services.ai_chat.intents import (
    _is_logistic_manager_chat_context,
    _is_logistics_dashboard_question,
    _is_logistics_driver_question,
    _is_logistics_fleet_question,
    _is_logistics_inventory_question,
    _is_logistics_returns_question,
    _is_logistics_revenue_question,
    _normalize_text,
)
from app.services.ai_chat.support_handoff import _answer_with_grounded_ai
from app.services.finance_service import get_finance_summary


async def _build_logistics_manager_snapshot(ro_db: AsyncSession) -> dict:
    finance_summary = await get_finance_summary(ro_db)

    drivers_result = await ro_db.execute(
        select(LogisticsDriverProfile, User.name, Warehouse.name)
        .join(User, User.id == LogisticsDriverProfile.user_id)
        .outerjoin(Warehouse, Warehouse.id == LogisticsDriverProfile.warehouse_id)
        .order_by(User.name.asc())
    )
    driver_rows = drivers_result.all()

    vehicles_result = await ro_db.execute(
        select(LogisticsVehicle, Warehouse.name, User.name)
        .outerjoin(Warehouse, Warehouse.id == LogisticsVehicle.warehouse_id)
        .outerjoin(User, User.id == LogisticsVehicle.assigned_driver_id)
        .order_by(LogisticsVehicle.code.asc())
    )
    vehicle_rows = vehicles_result.all()

    low_stock_result = await ro_db.execute(
        select(InventoryItem, Warehouse.name)
        .outerjoin(Warehouse, Warehouse.id == InventoryItem.warehouse_id)
        .where(InventoryItem.quantity_on_hand <= InventoryItem.safety_stock)
        .order_by((InventoryItem.safety_stock - InventoryItem.quantity_on_hand).desc(), InventoryItem.name.asc())
        .limit(5)
    )
    low_stock_rows = low_stock_result.all()

    pending_restocks = int(
        (
            await ro_db.execute(
                select(func.count(RestockRequest.id)).where(
                    RestockRequest.status.in_(["PENDING", "OPEN", "REQUESTED"])
                )
            )
        ).scalar_one()
        or 0
    )

    total_inventory_units = int(
        (
            await ro_db.execute(
                select(func.coalesce(func.sum(InventoryItem.quantity_on_hand), 0))
            )
        ).scalar_one()
        or 0
    )

    alerts_result = await ro_db.execute(
        select(LogisticsAlert, Warehouse.name)
        .outerjoin(Warehouse, Warehouse.id == LogisticsAlert.warehouse_id)
        .where(LogisticsAlert.is_active.is_(True))
        .order_by(LogisticsAlert.created_at.desc())
        .limit(5)
    )
    alert_rows = alerts_result.all()

    returns_result = await ro_db.execute(
        select(LogisticsReturnCase, Warehouse.name)
        .outerjoin(Warehouse, Warehouse.id == LogisticsReturnCase.warehouse_id)
        .order_by(LogisticsReturnCase.created_at.desc())
        .limit(5)
    )
    return_rows = returns_result.all()

    stats_result = await ro_db.execute(
        select(LogisticsDailyStats)
        .where(LogisticsDailyStats.warehouse_id.is_(None))
        .order_by(LogisticsDailyStats.stat_date.desc())
        .limit(7)
    )
    stats_rows = list(reversed(stats_result.scalars().all()))

    top_hubs_result = await ro_db.execute(
        select(Warehouse.name, LogisticsDailyStats.revenue, LogisticsDailyStats.orders_count)
        .join(Warehouse, Warehouse.id == LogisticsDailyStats.warehouse_id)
        .order_by(LogisticsDailyStats.stat_date.desc(), LogisticsDailyStats.revenue.desc())
        .limit(3)
    )
    top_hub_rows = top_hubs_result.all()

    pending_orders = int(
        (
            await ro_db.execute(
                select(func.count(Order.id)).where(
                    Order.status.in_(["DRAFT", "CONFIRMED", "ASSIGNED"])
                )
            )
        ).scalar_one()
        or 0
    )
    active_deliveries = int(
        (
            await ro_db.execute(
                select(func.count(Order.id)).where(Order.status == "IN_TRANSIT")
            )
        ).scalar_one()
        or 0
    )
    active_hubs = int(
        (
            await ro_db.execute(
                select(func.count(Warehouse.id)).where(Warehouse.is_active.is_(True))
            )
        ).scalar_one()
        or 0
    )

    driver_status_counts: dict[str, int] = {}
    for profile, _, _ in driver_rows:
        key = (profile.status or "unknown").strip().lower()
        driver_status_counts[key] = driver_status_counts.get(key, 0) + 1

    vehicle_status_counts: dict[str, int] = {}
    for vehicle, _, _ in vehicle_rows:
        key = (vehicle.status or "unknown").strip().lower()
        vehicle_status_counts[key] = vehicle_status_counts.get(key, 0) + 1

    revenue_by_day = finance_summary.get("revenue_by_day") or []
    today_revenue = float(stats_rows[-1].revenue) if stats_rows else float(revenue_by_day[-1].get("revenue", 0.0) if revenue_by_day else 0.0)
    seven_day_revenue = (
        round(sum(float(row.revenue or 0) for row in stats_rows), 2)
        if stats_rows
        else round(sum(float(item.get("revenue", 0.0) or 0.0) for item in revenue_by_day[-7:]), 2)
    )
    daily_average = round(seven_day_revenue / len(stats_rows), 2) if stats_rows else 0.0
    revenue_forecast = round(daily_average * 1.05, 2) if daily_average else 0.0
    active_alerts = len(alert_rows)
    open_returns = sum(1 for item, _ in return_rows if _normalize_text(item.status) not in {"completed", "closed", "approved"})
    total_expenses = float(finance_summary.get("total_expenses", 0.0) or 0.0)
    pending_cod = float(finance_summary.get("pending_cod", 0.0) or 0.0)
    total_payroll_due = float(finance_summary.get("total_payroll_due", 0.0) or 0.0)
    net_profit = float(finance_summary.get("net_profit", 0.0) or 0.0)

    facts = [
        f"Active hubs: {active_hubs}",
        f"Pending orders needing action: {pending_orders}",
        f"Active deliveries in transit: {active_deliveries}",
        f"Tracked drivers: {len(driver_rows)}",
        f"Tracked vehicles: {len(vehicle_rows)}",
        f"Active alerts: {active_alerts}",
        f"Open return or RMA cases in the latest batch: {open_returns}",
        f"Inventory units on hand: {total_inventory_units}",
        f"Pending restock requests: {pending_restocks}",
        f"Network revenue today: INR {today_revenue:,.2f}",
        f"Network 7 day revenue: INR {seven_day_revenue:,.2f}",
        f"Projected next-day revenue from trailing 7 day average: INR {revenue_forecast:,.2f}",
        f"Pending COD exposure: INR {pending_cod:,.2f}",
        f"Outstanding payroll due: INR {total_payroll_due:,.2f}",
        f"Total expenses: INR {total_expenses:,.2f}",
        f"Net profit: INR {net_profit:,.2f}",
    ]

    return {
        "finance_summary": finance_summary,
        "drivers": driver_rows,
        "vehicles": vehicle_rows,
        "low_stock_items": low_stock_rows,
        "pending_restocks": pending_restocks,
        "total_inventory_units": total_inventory_units,
        "alerts": alert_rows,
        "returns": return_rows,
        "stats": stats_rows,
        "top_hubs": top_hub_rows,
        "pending_orders": pending_orders,
        "active_deliveries": active_deliveries,
        "active_hubs": active_hubs,
        "driver_status_counts": driver_status_counts,
        "vehicle_status_counts": vehicle_status_counts,
        "today_revenue": today_revenue,
        "seven_day_revenue": seven_day_revenue,
        "revenue_forecast": revenue_forecast,
        "pending_cod": pending_cod,
        "total_payroll_due": total_payroll_due,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "facts": facts,
    }


def _logistics_dashboard_message(snapshot: dict) -> str:
    lines = [
        f"Network overview: **{snapshot['active_hubs']}** active hubs, **{snapshot['pending_orders']}** pending orders, **{snapshot['active_deliveries']}** deliveries in transit, and **{len(snapshot['alerts'])}** active alerts.",
        f"Live coverage: **{len(snapshot['drivers'])}** tracked drivers and **{len(snapshot['vehicles'])}** tracked vehicles across the network.",
        f"Revenue snapshot: **INR {snapshot['today_revenue']:,.2f}** today and **INR {snapshot['seven_day_revenue']:,.2f}** over the last 7 days.",
    ]
    if snapshot["top_hubs"]:
        lines.append("Top-performing hubs in the latest revenue snapshot:")
        for hub_name, revenue, orders_count in snapshot["top_hubs"][:3]:
            lines.append(f"- {hub_name}: INR {float(revenue or 0):,.2f} revenue from {int(orders_count or 0)} orders")
    if snapshot["alerts"]:
        alert, warehouse_name = snapshot["alerts"][0]
        lines.append(f"Most recent active alert: {alert.title} ({alert.severity}) at {warehouse_name or 'network scope'}")
    return "\n".join(lines)


def _logistics_driver_status_message(snapshot: dict) -> str:
    active = snapshot["driver_status_counts"].get("active", 0)
    idle = snapshot["driver_status_counts"].get("idle", 0)
    off_duty = snapshot["driver_status_counts"].get("off duty", 0) + snapshot["driver_status_counts"].get("offline", 0)
    lines = [
        f"Driver status snapshot: **{len(snapshot['drivers'])}** tracked drivers, **{active}** active, **{idle}** idle, and **{off_duty}** off duty/offline.",
    ]
    if snapshot["drivers"]:
        lines.append("Current driver highlights:")
        for profile, driver_name, warehouse_name in snapshot["drivers"][:5]:
            job = profile.current_job or "No active job"
            location = profile.current_location or (warehouse_name or "Location unavailable")
            lines.append(f"- {driver_name}: {profile.status} at {location} · Job: {job}")
    else:
        lines.append("No driver profiles are available right now.")
    return "\n".join(lines)


def _logistics_fleet_status_message(snapshot: dict) -> str:
    available = snapshot["vehicle_status_counts"].get("available", 0)
    active = snapshot["vehicle_status_counts"].get("active", 0)
    maintenance = snapshot["vehicle_status_counts"].get("maintenance", 0)
    lines = [
        f"Fleet status: **{len(snapshot['vehicles'])}** vehicles tracked, **{available}** available, **{active}** active, and **{maintenance}** in maintenance.",
    ]
    if snapshot["vehicles"]:
        lines.append("Vehicle highlights:")
        for vehicle, warehouse_name, driver_name in snapshot["vehicles"][:5]:
            driver_label = driver_name or "Unassigned"
            lines.append(
                f"- {vehicle.code}: {vehicle.status} · {vehicle.vehicle_type} · Driver: {driver_label} · Hub: {warehouse_name or 'Unassigned'}"
            )
    else:
        lines.append("No fleet vehicles are available right now.")
    return "\n".join(lines)


def _logistics_inventory_message(snapshot: dict) -> str:
    lines = [
        f"Inventory pressure: **{snapshot['total_inventory_units']}** units on hand, **{len(snapshot['low_stock_items'])}** urgent low-stock SKUs, and **{snapshot['pending_restocks']}** pending restock requests.",
    ]
    if snapshot["low_stock_items"]:
        lines.append("Most urgent low-stock items:")
        for item, warehouse_name in snapshot["low_stock_items"][:5]:
            lines.append(
                f"- {item.name} ({item.sku}) at {warehouse_name or 'Unknown hub'}: {item.quantity_on_hand} left vs safety stock {item.safety_stock}"
            )
    else:
        lines.append("No SKUs are currently below safety stock.")
    return "\n".join(lines)


def _logistics_returns_message(snapshot: dict) -> str:
    open_returns = sum(
        1 for item, _ in snapshot["returns"] if _normalize_text(item.status) not in {"completed", "closed", "approved"}
    )
    lines = [
        f"Returns and RMA snapshot: **{open_returns}** open cases in the latest batch and **{len(snapshot['returns'])}** recent cases reviewed.",
    ]
    if snapshot["returns"]:
        lines.append("Latest return cases:")
        for item, warehouse_name in snapshot["returns"][:5]:
            lines.append(
                f"- {item.reference_code}: {item.status} · {item.reason} · Refund INR {float(item.refund_amount or 0):,.2f} · Hub: {warehouse_name or 'Unknown'}"
            )
    else:
        lines.append("No recent return cases are available.")
    return "\n".join(lines)


def _logistics_revenue_message(snapshot: dict) -> str:
    lines = [
        f"Revenue outlook: **INR {snapshot['today_revenue']:,.2f}** booked today and **INR {snapshot['seven_day_revenue']:,.2f}** over the trailing 7 days.",
        f"Next-day forecast from the recent run-rate is **INR {snapshot['revenue_forecast']:,.2f}**.",
        f"Finance position: **INR {snapshot['total_expenses']:,.2f}** total expenses, **INR {snapshot['pending_cod']:,.2f}** pending COD, and **INR {snapshot['total_payroll_due']:,.2f}** payroll due.",
        f"Current net position is **INR {snapshot['net_profit']:,.2f}**.",
    ]
    if snapshot["stats"]:
        lines.append("Recent network revenue trend:")
        for row in snapshot["stats"][-5:]:
            lines.append(
                f"- {row.stat_date}: INR {float(row.revenue or 0):,.2f} revenue · {int(row.orders_count or 0)} orders"
            )
    else:
        lines.append("No network revenue history is available yet.")
    return "\n".join(lines)


async def _try_handle_logistic_manager_shortcuts(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    chat_context: str | None,
) -> ChatResponse | None:
    if not _is_logistic_manager_chat_context(user, chat_context):
        return None

    snapshot = await _build_logistics_manager_snapshot(ro_db)
    msg = (user_message or "").strip().lower()
    base_message = None

    if _is_logistics_driver_question(msg):
        base_message = _logistics_driver_status_message(snapshot)
    elif _is_logistics_fleet_question(msg):
        base_message = _logistics_fleet_status_message(snapshot)
    elif _is_logistics_inventory_question(msg):
        base_message = _logistics_inventory_message(snapshot)
    elif _is_logistics_returns_question(msg):
        base_message = _logistics_returns_message(snapshot)
    elif _is_logistics_revenue_question(msg):
        base_message = _logistics_revenue_message(snapshot)
    elif _is_logistics_dashboard_question(msg):
        base_message = _logistics_dashboard_message(snapshot)

    if not base_message:
        return None

    assistant_message = await _answer_with_grounded_ai(
        user=user,
        user_message=user_message,
        fallback_message=base_message,
        grounding_facts=snapshot["facts"] + [base_message],
    )
    await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
    await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent="db_query",
        sql_generated=None,
    )
