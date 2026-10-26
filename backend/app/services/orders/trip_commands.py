"""Dispatcher commands to a driver on a trip, and route deviations the driver reports."""

from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsAlert,
)
from app.models.user import User
from app.schemas.orders import (
    TripCommandPushRequest,
    TripDeviationReportRequest,
)
from app.services.orders.common import _get_order, _push_notification
from app.services.orders.trip_intelligence import get_trip_intelligence


async def push_trip_command_update(
    db: AsyncSession,
    order_id: UUID,
    data: TripCommandPushRequest,
    caller: User | None = None,
) -> dict:
    order = await _get_order(db, order_id)
    if not order.assigned_driver_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This order is not assigned to a driver yet",
        )

    intelligence = await get_trip_intelligence(db, order_id, caller=caller)
    selected_route = str(data.selected_route or "recommended").strip().lower()
    if selected_route == "recommended":
        selected_route = intelligence["recommended_route"]
    if selected_route not in {"primary", "alternate"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="selected_route must be primary, alternate, or recommended",
        )

    chosen_route = intelligence["primary_route"] if selected_route == "primary" else intelligence["alternate_route"]
    saved_minutes = max(0, -(chosen_route.get("delta_minutes", 0)))
    dispatcher_note = (data.dispatcher_note or "").strip() or intelligence["driver_message"]

    await _push_notification(
        db,
        title="Route update from dispatch",
        message=dispatcher_note,
        notif_type="info" if selected_route == "primary" else "warning",
        target_user_id=order.assigned_driver_id,
    )

    try:
        from app.routers.ws_fleet import driver_alert_manager
        await driver_alert_manager.send_to_driver(
            str(order.assigned_driver_id),
            {
                "type": "route_update",
                "title": "Route update from dispatch",
                "message": dispatcher_note,
                "order_id": str(order.id),
                "tracking_code": order.tracking_code or "",
                "selected_route": selected_route,
                "saved_minutes": saved_minutes,
                "route_status": intelligence["route_status"],
                "risk_level": intelligence["risk_level"],
                "trip_intelligence": jsonable_encoder(intelligence),
            },
        )
    except Exception:
        pass

    return {
        "success": True,
        "order_id": str(order.id),
        "tracking_code": order.tracking_code or "",
        "selected_route": selected_route,
        "saved_minutes": saved_minutes,
        "message": "Trip command pushed to driver",
    }


async def report_trip_deviation(
    db: AsyncSession,
    order_id: UUID,
    data: TripDeviationReportRequest,
    caller: User,
) -> dict:
    order = await _get_order(db, order_id)
    if order.assigned_driver_id != caller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the assigned driver for this order",
        )

    description = f"{caller.name} reported a route deviation on {order.tracking_code}: {data.reason}"
    if data.details:
        description = f"{description}. {data.details}"
    location = (
        f"{data.latitude}, {data.longitude}"
        if data.latitude is not None and data.longitude is not None
        else order.delivery_addr or order.pickup_addr or "Unknown"
    )

    alert = LogisticsAlert(
        warehouse_id=order.warehouse_id,
        alert_type="route_deviation",
        title=f"Route deviation - {caller.name}",
        description=description,
        severity="high",
        icon="alt_route",
        location=location,
        recommendation="Review Trip Command and push a reroute if the current corridor is no longer viable.",
        impact_json={
            "order_id": str(order.id),
            "tracking_code": order.tracking_code or "",
            "driver_id": str(caller.id),
            "driver_name": caller.name,
            "reason": data.reason,
        },
        is_active=True,
    )
    db.add(alert)
    await db.flush()

    await _push_notification(
        db,
        title="Driver reported route deviation",
        message=f"{caller.name} needs route help on {order.tracking_code}",
        notif_type="warning",
        audience_roles=["DISPATCHER"],
    )

    try:
        from app.routers.ws_fleet import fleet_manager
        await fleet_manager.broadcast(
            {
                "type": "route_deviation",
                "alert_id": str(alert.id),
                "order_id": str(order.id),
                "tracking_code": order.tracking_code or "",
                "driver_id": str(caller.id),
                "driver_name": caller.name,
                "reason": data.reason,
                "location": location,
                "severity": "high",
            }
        )
    except Exception:
        pass

    return {
        "success": True,
        "alert_id": str(alert.id),
        "message": "Route deviation reported to dispatcher",
    }
