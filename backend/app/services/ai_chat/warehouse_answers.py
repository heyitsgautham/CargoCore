"""Warehouse manager snapshot and the shortcut answers built from it."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, RestockRequest
from app.models.labour import Labourer
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import (
    LoadingDock,
    PackingStation,
    ReturnGrading,
    Warehouse,
    WarehouseZoneMetrics,
)
from app.schemas.ai import (
    ChatResponse,
)
from app.services.ai_chat.conversations import _persist_message
from app.services.ai_chat.intents import (
    _is_warehouse_capacity_question,
    _is_warehouse_chat_context,
    _is_warehouse_dock_question,
    _is_warehouse_inventory_question,
    _is_warehouse_overview_question,
    _is_warehouse_pending_question,
    _is_warehouse_returns_question,
    _is_warehouse_staff_question,
    _is_warehouse_workload_question,
    _normalize_text,
)
from app.services.ai_chat.support_handoff import _answer_with_grounded_ai


async def _build_warehouse_snapshot(ro_db: AsyncSession, user: User) -> dict | None:
    warehouse_id = getattr(user, "warehouse_id", None)
    if not warehouse_id:
        return None

    warehouse = (
        await ro_db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    ).scalar_one_or_none()
    if not warehouse:
        return None

    status_rows = (
        await ro_db.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.warehouse_id == warehouse_id)
            .group_by(Order.status)
        )
    ).all()
    status_counts = {
        (status or "UNKNOWN").upper(): int(count or 0)
        for status, count in status_rows
    }

    substatus_rows = (
        await ro_db.execute(
            select(Order.warehouse_substatus, func.count(Order.id))
            .where(Order.warehouse_id == warehouse_id)
            .group_by(Order.warehouse_substatus)
        )
    ).all()
    substatus_counts = {
        (substatus or "NONE").upper(): int(count or 0)
        for substatus, count in substatus_rows
    }

    active_orders = sum(
        count
        for status, count in status_counts.items()
        if status not in {"DELIVERED", "CANCELLED", "CLOSED"}
    )
    pending_orders = (
        await ro_db.execute(
            select(func.count(Order.id))
            .where(
                Order.warehouse_id == warehouse_id,
                or_(
                    func.upper(Order.warehouse_substatus).in_(
                        ["AWAITING_INBOUND", "AWAITING_PICK", "PICKING", "PICKED", "PACKING", "QC_PASSED"]
                    ),
                    (
                        Order.warehouse_substatus.is_(None)
                        & func.upper(Order.status).in_(["CONFIRMED", "ASSIGNED"])
                    ),
                ),
            )
        )
    ).scalar_one()
    picking_orders = sum(
        substatus_counts.get(key, 0)
        for key in ["PICKING", "PICKED", "PACKING"]
    )
    ready_for_dispatch = sum(
        substatus_counts.get(key, 0)
        for key in ["PACKED", "QC_PASSED", "ON_DOCK", "DISPATCHED"]
    )
    in_transit_orders = status_counts.get("IN_TRANSIT", 0)
    delivered_orders = status_counts.get("DELIVERED", 0) + status_counts.get("CLOSED", 0)

    recent_orders = (
        await ro_db.execute(
            select(Order)
            .where(Order.warehouse_id == warehouse_id)
            .order_by(Order.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    labour_pairs = (
        await ro_db.execute(
            select(Labourer, Order, User.name)
            .outerjoin(User, Labourer.user_id == User.id)
            .outerjoin(Order, Labourer.assigned_order_id == Order.id)
            .where(Labourer.warehouse_id == warehouse_id)
            .order_by(Labourer.created_at.desc())
        )
    ).all()

    available_staff = 0
    assigned_staff = 0
    on_field_staff = 0
    off_duty_staff = 0
    available_names: list[str] = []
    on_field_names: list[str] = []
    for labourer, order, labour_name in labour_pairs:
        if not labourer.is_active:
            off_duty_staff += 1
            continue
        if order and _normalize_text(order.status) == "in_transit":
            on_field_staff += 1
            if labour_name and len(on_field_names) < 3:
                on_field_names.append(labour_name)
            continue
        if labourer.assigned_order_id:
            assigned_staff += 1
            continue
        available_staff += 1
        if labour_name and len(available_names) < 3:
            available_names.append(labour_name)

    total_staff = len(labour_pairs)

    dock_rows = (
        await ro_db.execute(
            select(LoadingDock, Order.tracking_code)
            .outerjoin(Order, LoadingDock.assigned_order_id == Order.id)
            .where(LoadingDock.warehouse_id == warehouse_id)
            .order_by(LoadingDock.dock_number.asc())
        )
    ).all()
    docks = [dock for dock, _ in dock_rows]
    free_docks = sum(1 for dock in docks if _normalize_text(dock.status) == "free")
    occupied_docks = sum(1 for dock in docks if _normalize_text(dock.status) == "occupied")
    maintenance_docks = sum(1 for dock in docks if _normalize_text(dock.status) == "maintenance")
    occupied_dock_labels = [
        f"Dock {dock.dock_number}{f' ({tracking_code})' if tracking_code else ''}"
        for dock, tracking_code in dock_rows
        if _normalize_text(dock.status) == "occupied"
    ][:3]

    packing_stations = (
        await ro_db.execute(
            select(PackingStation).where(PackingStation.warehouse_id == warehouse_id)
        )
    ).scalars().all()
    active_stations = sum(1 for station in packing_stations if _normalize_text(station.status) == "active")
    maintenance_stations = sum(
        1 for station in packing_stations if _normalize_text(station.status) == "maintenance"
    )

    low_stock_items = (
        await ro_db.execute(
            select(InventoryItem)
            .where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.quantity_on_hand <= InventoryItem.safety_stock,
            )
            .order_by(InventoryItem.quantity_on_hand.asc(), InventoryItem.name.asc())
            .limit(5)
        )
    ).scalars().all()
    total_inventory_units = (
        await ro_db.execute(
            select(func.coalesce(func.sum(InventoryItem.quantity_on_hand), 0))
            .where(InventoryItem.warehouse_id == warehouse_id)
        )
    ).scalar_one()
    pending_restocks = (
        await ro_db.execute(
            select(func.count(RestockRequest.id))
            .where(
                RestockRequest.warehouse_id == warehouse_id,
                func.upper(RestockRequest.status) == "PENDING",
            )
        )
    ).scalar_one()

    latest_metric_date = (
        await ro_db.execute(
            select(func.max(WarehouseZoneMetrics.metric_date))
            .where(WarehouseZoneMetrics.warehouse_id == warehouse_id)
        )
    ).scalar_one()
    zone_metrics = []
    if latest_metric_date:
        zone_metrics = (
            await ro_db.execute(
                select(WarehouseZoneMetrics)
                .where(
                    WarehouseZoneMetrics.warehouse_id == warehouse_id,
                    WarehouseZoneMetrics.metric_date == latest_metric_date,
                )
                .order_by(WarehouseZoneMetrics.zone_id.asc())
            )
        ).scalars().all()

    aisle_rows = (
        await ro_db.execute(
            select(
                InventoryItem.aisle,
                func.count(InventoryItem.id).label("sku_count"),
                func.coalesce(func.sum(InventoryItem.quantity_on_hand), 0).label("total_qty"),
            )
            .where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.aisle.is_not(None),
            )
            .group_by(InventoryItem.aisle)
        )
    ).all()

    free_space_label = "No aisle utilization data yet"
    busy_space_label = "No busy zone detected"
    if zone_metrics:
        freest_zone = min(zone_metrics, key=lambda row: row.capacity_used_pct or 0.0)
        busiest_zone = max(zone_metrics, key=lambda row: row.capacity_used_pct or 0.0)
        free_space_label = (
            f"Zone {freest_zone.zone_id} at {round(float(freest_zone.capacity_used_pct or 0.0), 1)}% utilized"
        )
        busy_space_label = (
            f"Zone {busiest_zone.zone_id} at {round(float(busiest_zone.capacity_used_pct or 0.0), 1)}% utilized"
        )
    elif aisle_rows:
        freest_aisle = min(aisle_rows, key=lambda row: int(row.total_qty or 0))
        busiest_aisle = max(aisle_rows, key=lambda row: int(row.total_qty or 0))
        free_space_label = f"Aisle {freest_aisle.aisle} with {int(freest_aisle.total_qty or 0)} units stored"
        busy_space_label = f"Aisle {busiest_aisle.aisle} with {int(busiest_aisle.total_qty or 0)} units stored"

    recent_returns = (
        await ro_db.execute(
            select(ReturnGrading)
            .where(ReturnGrading.warehouse_id == warehouse_id)
            .order_by(ReturnGrading.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    pending_returns = sum(1 for row in recent_returns if _normalize_text(row.status) != "completed")
    completed_returns = sum(1 for row in recent_returns if _normalize_text(row.status) == "completed")

    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    orders_last_week = (
        await ro_db.execute(
            select(func.count(Order.id))
            .where(
                Order.warehouse_id == warehouse_id,
                Order.created_at >= seven_days_ago,
            )
        )
    ).scalar_one()
    avg_daily_orders = round(float(orders_last_week or 0) / 7.0, 1)
    projected_orders = int(round(max(avg_daily_orders, float(active_orders or 0)) * 1.15))
    suggested_staff = max(1, int((max(projected_orders, pending_orders, 1) + 3) // 4))

    facts = [
        f"Warehouse name: {warehouse.name}",
        f"Warehouse capacity limit: {warehouse.capacity_limit or 0}",
        f"Active warehouse orders: {active_orders}",
        f"Orders awaiting warehouse action: {pending_orders}",
        f"Orders in picking or packing: {picking_orders}",
        f"Orders ready for dispatch: {ready_for_dispatch}",
        f"Orders already in transit from this warehouse: {in_transit_orders}",
        f"Available staff: {available_staff} out of {total_staff}",
        f"Assigned floor staff: {assigned_staff}",
        f"On-field staff: {on_field_staff}",
        f"Loading docks free: {free_docks} out of {len(docks)}",
        f"Packing stations active: {active_stations} out of {len(packing_stations)}",
        f"Low-stock SKUs: {len(low_stock_items)}",
        f"Pending restock requests: {int(pending_restocks or 0)}",
        f"Most free storage area: {free_space_label}",
        f"Most loaded storage area: {busy_space_label}",
        f"Pending return gradings in the latest batch: {pending_returns}",
        f"Completed return gradings in the latest batch: {completed_returns}",
        f"Average incoming orders per day over the last 7 days: {avg_daily_orders}",
        f"Projected tomorrow workload: {projected_orders}",
        f"Suggested active floor staff for tomorrow: {suggested_staff}",
    ]

    return {
        "warehouse": warehouse,
        "active_orders": active_orders,
        "pending_orders": pending_orders,
        "picking_orders": picking_orders,
        "ready_for_dispatch": ready_for_dispatch,
        "in_transit_orders": in_transit_orders,
        "delivered_orders": delivered_orders,
        "recent_orders": recent_orders,
        "available_staff": available_staff,
        "assigned_staff": assigned_staff,
        "on_field_staff": on_field_staff,
        "off_duty_staff": off_duty_staff,
        "total_staff": total_staff,
        "available_names": available_names,
        "on_field_names": on_field_names,
        "free_docks": free_docks,
        "occupied_docks": occupied_docks,
        "maintenance_docks": maintenance_docks,
        "total_docks": len(docks),
        "occupied_dock_labels": occupied_dock_labels,
        "active_stations": active_stations,
        "maintenance_stations": maintenance_stations,
        "total_stations": len(packing_stations),
        "low_stock_items": low_stock_items,
        "total_inventory_units": int(total_inventory_units or 0),
        "pending_restocks": int(pending_restocks or 0),
        "free_space_label": free_space_label,
        "busy_space_label": busy_space_label,
        "recent_returns": recent_returns,
        "pending_returns": pending_returns,
        "completed_returns": completed_returns,
        "avg_daily_orders": avg_daily_orders,
        "projected_orders": projected_orders,
        "suggested_staff": suggested_staff,
        "facts": facts,
    }


def _warehouse_overview_message(snapshot: dict) -> str:
    warehouse = snapshot["warehouse"]
    return (
        f"Warehouse **{warehouse.name}** snapshot:\n"
        f"- Active orders: **{snapshot['active_orders']}**\n"
        f"- Awaiting warehouse action: **{snapshot['pending_orders']}**\n"
        f"- Picking / packing now: **{snapshot['picking_orders']}**\n"
        f"- Ready for dispatch: **{snapshot['ready_for_dispatch']}**\n"
        f"- Staff available: **{snapshot['available_staff']}/{snapshot['total_staff']}**\n"
        f"- Free docks: **{snapshot['free_docks']}/{snapshot['total_docks']}**"
    )


def _warehouse_capacity_message(snapshot: dict) -> str:
    return (
        f"Best free space right now: **{snapshot['free_space_label']}**.\n"
        f"Most loaded area: **{snapshot['busy_space_label']}**.\n"
        f"Free docks: **{snapshot['free_docks']}/{snapshot['total_docks']}**. "
        f"Active orders on the warehouse floor: **{snapshot['active_orders']}**."
    )


def _warehouse_staff_message(snapshot: dict) -> str:
    available_line = ", ".join(snapshot["available_names"]) if snapshot["available_names"] else "No unassigned staff listed"
    on_field_line = ", ".join(snapshot["on_field_names"]) if snapshot["on_field_names"] else "No staff currently on field"
    return (
        f"Staff status right now:\n"
        f"- Available: **{snapshot['available_staff']}**\n"
        f"- Assigned on floor: **{snapshot['assigned_staff']}**\n"
        f"- On field: **{snapshot['on_field_staff']}**\n"
        f"- Off duty: **{snapshot['off_duty_staff']}**\n"
        f"- Available names: {available_line}\n"
        f"- On-field names: {on_field_line}"
    )


def _warehouse_workload_message(snapshot: dict) -> str:
    return (
        f"Tomorrow's workload forecast:\n"
        f"- 7-day average inbound volume: **{snapshot['avg_daily_orders']}** orders/day\n"
        f"- Current active pipeline: **{snapshot['active_orders']}** orders\n"
        f"- Projected tomorrow load: **{snapshot['projected_orders']}** orders\n"
        f"- Suggested active floor staff: **{snapshot['suggested_staff']}**\n"
        f"- Available now: **{snapshot['available_staff']}**"
    )


def _warehouse_pending_orders_message(snapshot: dict) -> str:
    lines = [
        f"Orders needing warehouse attention: **{snapshot['pending_orders']}**.",
        f"Picking / packing in progress: **{snapshot['picking_orders']}**. Ready for dispatch: **{snapshot['ready_for_dispatch']}**.",
    ]
    if snapshot["recent_orders"]:
        lines.append("Recent warehouse orders:")
        for order in snapshot["recent_orders"][:5]:
            lines.append(
                f"- {order.tracking_code}: {order.status} | Stage: {order.warehouse_substatus or 'N/A'}"
            )
    return "\n".join(lines)


def _warehouse_returns_message(snapshot: dict) -> str:
    lines = [
        f"Returns / damage snapshot: **{snapshot['pending_returns']}** pending gradings and **{snapshot['completed_returns']}** completed in the latest batch.",
    ]
    if snapshot["recent_returns"]:
        lines.append("Latest graded returns:")
        for grading in snapshot["recent_returns"][:5]:
            lines.append(
                f"- {grading.rma_code}: {grading.item_condition} -> {grading.disposition} | Status: {grading.status}"
            )
    else:
        lines.append("No recent return gradings found for this warehouse.")
    return "\n".join(lines)


def _warehouse_dock_message(snapshot: dict) -> str:
    lines = [
        f"Loading dock status: **{snapshot['free_docks']}** free, **{snapshot['occupied_docks']}** occupied, **{snapshot['maintenance_docks']}** under maintenance.",
    ]
    if snapshot["occupied_dock_labels"]:
        lines.append("Occupied docks:")
        lines.extend(f"- {label}" for label in snapshot["occupied_dock_labels"])
    else:
        lines.append("All tracked docks are currently free.")
    return "\n".join(lines)


def _warehouse_inventory_message(snapshot: dict) -> str:
    lines = [
        f"Inventory health: **{snapshot['total_inventory_units']}** units on hand, **{len(snapshot['low_stock_items'])}** low-stock SKUs, **{snapshot['pending_restocks']}** pending restock requests.",
    ]
    if snapshot["low_stock_items"]:
        lines.append("Most urgent low-stock items:")
        for item in snapshot["low_stock_items"]:
            lines.append(
                f"- {item.name} ({item.sku}): {item.quantity_on_hand} left vs safety stock {item.safety_stock}"
            )
    else:
        lines.append("No SKUs are currently below safety stock.")
    return "\n".join(lines)


async def _try_handle_warehouse_shortcuts(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    chat_context: str | None,
    snapshot: dict | None = None,
) -> ChatResponse | None:
    if not _is_warehouse_chat_context(user, chat_context):
        return None

    snapshot = snapshot or await _build_warehouse_snapshot(ro_db, user)
    if not snapshot:
        return None

    msg = (user_message or "").strip().lower()
    base_message = None
    intent = "general"

    if _is_warehouse_workload_question(msg):
        base_message = _warehouse_workload_message(snapshot)
    elif _is_warehouse_staff_question(msg):
        base_message = _warehouse_staff_message(snapshot)
    elif _is_warehouse_capacity_question(msg):
        base_message = _warehouse_capacity_message(snapshot)
    elif _is_warehouse_pending_question(msg):
        base_message = _warehouse_pending_orders_message(snapshot)
        intent = "db_query"
    elif _is_warehouse_returns_question(msg):
        base_message = _warehouse_returns_message(snapshot)
        intent = "db_query"
    elif _is_warehouse_dock_question(msg):
        base_message = _warehouse_dock_message(snapshot)
    elif _is_warehouse_inventory_question(msg):
        base_message = _warehouse_inventory_message(snapshot)
        intent = "db_query"
    elif _is_warehouse_overview_question(msg):
        base_message = _warehouse_overview_message(snapshot)

    if not base_message:
        return None

    assistant_message = await _answer_with_grounded_ai(
        user=user,
        user_message=user_message,
        fallback_message=base_message,
        grounding_facts=snapshot["facts"] + [base_message],
    )
    await _persist_message(db, session_id, user.id, "user", user_message, intent)
    await _persist_message(db, session_id, user.id, "assistant", assistant_message, intent)
    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent=intent,
        sql_generated=None,
    )
