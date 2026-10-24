"""Driver app actions: shift, vehicle binding, crew check-in, location, broadcasts and fuel receipts."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.labour import LabourAttendance, Labourer
from app.models.logistics import (
    LogisticsAlert,
    LogisticsNotification,
    LogisticsTransaction,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.order import Order
from app.models.user import Role, User
from app.models.warehouse import Warehouse
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    DriverCrewMemberItem,
    DriverDashboardContext,
    DriverFuelReceiptCreate,
    DriverHosSummary,
    DriverShiftSummary,
    DriverTelemetryResponse,
    DriverVehicleBindRequest,
    LogisticsVehicleItem,
)
from app.services.logistics.driver_context import (
    _build_vehicle_item,
    _get_driver_orders,
    _get_driver_profile,
)
from app.services.logistics.driver_jobs import _build_driver_dashboard_bundle
from app.services.logistics.formatting import (
    _latest_attendance_event,
    _now,
    _order_job_type,
    _shift_code,
    _to_crew_item,
)


async def get_driver_dashboard(db: AsyncSession, user: User) -> DriverDashboardContext:
    bundle = await _build_driver_dashboard_bundle(db, user)
    return DriverDashboardContext(**bundle)


async def get_driver_shift(db: AsyncSession, user: User) -> DriverShiftSummary:
    bundle = await _build_driver_dashboard_bundle(db, user)
    return bundle["shift"]


async def get_driver_hos(db: AsyncSession, user: User) -> DriverHosSummary:
    bundle = await _build_driver_dashboard_bundle(db, user)
    return bundle["hos"]


async def get_driver_crew(db: AsyncSession, user: User) -> list[DriverCrewMemberItem]:
    bundle = await _build_driver_dashboard_bundle(db, user)
    return bundle["crew"]


async def get_driver_telemetry(db: AsyncSession, user: User) -> DriverTelemetryResponse:
    bundle = await _build_driver_dashboard_bundle(db, user)
    return bundle["telemetry"]


async def bind_driver_vehicle(
    db: AsyncSession,
    user: User,
    data: DriverVehicleBindRequest,
) -> LogisticsVehicleItem:
    if not data.vehicle_id and not data.vehicle_code:
        raise HTTPException(status_code=400, detail="Provide vehicle_id or vehicle_code")

    vehicle_query = select(LogisticsVehicle)
    if data.vehicle_id:
        vehicle_query = vehicle_query.where(LogisticsVehicle.id == data.vehicle_id)
    else:
        vehicle_query = vehicle_query.where(LogisticsVehicle.code == data.vehicle_code)
    vehicle = (await db.execute(vehicle_query)).scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    profile = await _get_driver_profile(db, user)
    warehouse_id = user.warehouse_id or profile.warehouse_id
    if warehouse_id and vehicle.warehouse_id and vehicle.warehouse_id != warehouse_id:
        raise HTTPException(status_code=403, detail="Vehicle is outside your assigned hub")

    vehicle.assigned_driver_id = user.id
    db.add(vehicle)

    active_orders = (
        await db.execute(
            select(Order).where(
                Order.assigned_driver_id == user.id,
                ~Order.status.in_(["DELIVERED", "COMPLETED", "CANCELLED", "CLOSED"]),
            )
        )
    ).scalars().all()
    for order in active_orders:
        order.assigned_vehicle_id = vehicle.id
        db.add(order)

    profile.current_job = active_orders[0].tracking_code if active_orders else profile.current_job
    db.add(profile)
    await db.flush()
    return _build_vehicle_item(vehicle, driver_name=user.name)


async def check_in_driver_crew_member(
    db: AsyncSession,
    user: User,
    labourer_id: UUID,
) -> DriverCrewMemberItem:
    driver_orders = await _get_driver_orders(db, user)
    house_shift_order_ids = {order.id for order in driver_orders if _order_job_type(order) == "HOUSE_SHIFT"}
    if not house_shift_order_ids:
        raise HTTPException(status_code=404, detail="No house-shift crew assigned")

    labourer = (
        await db.execute(
            select(Labourer)
            .options(
                selectinload(Labourer.user).selectinload(User.role),
                selectinload(Labourer.attendance_events),
            )
            .where(
                Labourer.id == labourer_id,
                Labourer.assigned_order_id.in_(house_shift_order_ids),
            )
        )
    ).scalar_one_or_none()
    if not labourer:
        raise HTTPException(status_code=404, detail="Crew member not found")
    if not labourer.is_active:
        raise HTTPException(status_code=409, detail="Crew member is inactive")

    last_event = _latest_attendance_event(labourer)
    if last_event and last_event.event_type == "CHECK_IN":
        return _to_crew_item(labourer)

    event = LabourAttendance(labourer_id=labourer.id, event_type="CHECK_IN")
    db.add(event)
    await db.flush()
    labourer = (
        await db.execute(
            select(Labourer)
            .options(
                selectinload(Labourer.user).selectinload(User.role),
                selectinload(Labourer.attendance_events),
            )
            .where(Labourer.id == labourer.id)
        )
    ).scalar_one()
    return _to_crew_item(labourer)


async def start_shift(db: AsyncSession, user: User) -> dict:
    profile = await _get_driver_profile(db, user)
    user.last_login = _now()
    profile.status = "Active"
    active_orders = await _get_driver_orders(db, user)
    if active_orders:
        profile.current_job = active_orders[0].tracking_code
    db.add(profile)
    db.add(user)
    await db.flush()
    return {
        "status": "success",
        "message": "Shift started",
        "shift_code": _shift_code(user, user.last_login),
        "started_at": user.last_login.isoformat(),
    }


async def end_shift(db: AsyncSession, user: User) -> dict:
    profile = await _get_driver_profile(db, user)
    profile.status = "Off-Duty"
    profile.current_job = None

    # Snap driver's last known location back to their warehouse so the dispatcher
    # map doesn't show them frozen at a delivery address after logout.
    warehouse_id = user.warehouse_id or profile.warehouse_id
    if warehouse_id:
        warehouse = (await db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )).scalar_one_or_none()
        if warehouse and warehouse.lat is not None and warehouse.lng is not None:
            profile.current_location = f"{warehouse.lat},{warehouse.lng}"

    db.add(profile)
    await db.flush()
    return {"status": "success", "message": "Shift ended", "ended_at": _now().isoformat()}


async def return_vehicle(
    db: AsyncSession,
    user: User,
    odometer_km: int | None,
    fuel_level_pct: int | None,
    notes: str | None,
) -> dict:
    """Driver returns their assigned vehicle. Updates mileage, unassigns driver, marks vehicle Available."""
    vehicle = (
        await db.execute(
            select(LogisticsVehicle).where(LogisticsVehicle.assigned_driver_id == user.id)
        )
    ).scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="No vehicle currently assigned to you")

    vehicle_code = vehicle.code
    if odometer_km is not None and odometer_km > vehicle.mileage:
        vehicle.mileage = odometer_km
    if notes:
        vehicle.maintenance_issue = notes
    vehicle.assigned_driver_id = None
    vehicle.status = "Active"
    db.add(vehicle)

    profile = await _get_driver_profile(db, user)
    profile.current_job = None
    db.add(profile)

    await db.flush()
    return {
        "status": "success",
        "message": f"Vehicle {vehicle_code} returned successfully",
        "vehicle_code": vehicle_code,
        "returned_at": _now().isoformat(),
        "odometer_km": vehicle.mileage,
        "fuel_level_pct": fuel_level_pct,
    }


async def update_driver_location(db: AsyncSession, user: User, latitude: float, longitude: float) -> dict:
    profile = await _get_driver_profile(db, user)
    profile.current_location = f"{latitude},{longitude}"
    db.add(profile)
    await db.flush()

    # Resolve assigned vehicle for the broadcast payload
    vehicle = (
        await db.execute(
            select(LogisticsVehicle).where(LogisticsVehicle.assigned_driver_id == user.id)
        )
    ).scalar_one_or_none()

    # Broadcast location to all connected dashboard WebSocket clients (fire-and-forget)
    import asyncio

    from app.routers.ws_fleet import fleet_manager
    asyncio.ensure_future(
        fleet_manager.broadcast({
            "type": "location_update",
            "driver_id": str(user.id),
            "driver_name": user.name,
            "latitude": latitude,
            "longitude": longitude,
            "status": profile.status,
            "vehicle_code": vehicle.code if vehicle else None,
            "vehicle_id": str(vehicle.id) if vehicle else None,
            "last_updated": _now().isoformat(),
        })
    )

    # ── Geofence breach detection ────────────────────────────────────────────
    active_zones = (await db.execute(
        select(LogisticsZone).where(LogisticsZone.status == "Active")
    )).scalars().all()

    for zone in active_zones:
        if zone.lat is None or zone.lng is None or zone.radius_km is None:
            continue
        # Haversine distance in km
        R = 6371.0
        dlat = math.radians(latitude - zone.lat)
        dlng = math.radians(longitude - zone.lng)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(zone.lat))
             * math.cos(math.radians(latitude))
             * math.sin(dlng / 2) ** 2)
        distance_km = R * 2 * math.asin(math.sqrt(min(1.0, a)))

        if distance_km > zone.radius_km:
            # Avoid duplicate active breach alerts for the same driver
            driver_tag = f"driver:{user.id}"
            existing_breach = (await db.execute(
                select(LogisticsAlert).where(
                    LogisticsAlert.alert_type == "geofence_breach",
                    LogisticsAlert.is_active.is_(True),
                    LogisticsAlert.location.contains(driver_tag),
                )
            )).scalar_one_or_none()

            if not existing_breach:
                breach_alert = LogisticsAlert(
                    warehouse_id=zone.warehouse_id,
                    alert_type="geofence_breach",
                    title=f"Geofence Breach — {user.name}",
                    description=(
                        f"Driver {user.name} is {distance_km:.1f} km outside "
                        f"zone '{zone.name}'. Last known position: {latitude:.4f}, {longitude:.4f}."
                    ),
                    severity="high",
                    icon="warning",
                    location=f"{latitude},{longitude}|driver:{user.id}|zone:{zone.id}",
                    recommendation="Contact the driver immediately or review the route deviation.",
                    impact_json={
                        "driver_id": str(user.id),
                        "zone_id": str(zone.id),
                        "zone_name": zone.name,
                        "distance_km": round(distance_km, 2),
                    },
                    is_active=True,
                )
                db.add(breach_alert)
                asyncio.ensure_future(
                    fleet_manager.broadcast({
                        "type": "geofence_breach",
                        "driver_id": str(user.id),
                        "driver_name": user.name,
                        "zone_id": str(zone.id),
                        "zone_name": zone.name,
                        "distance_km": round(distance_km, 2),
                        "latitude": latitude,
                        "longitude": longitude,
                        "timestamp": _now().isoformat(),
                    })
                )
        else:
            # Driver is back inside the zone — auto-resolve any active breach alert
            driver_tag = f"driver:{user.id}|zone:{zone.id}"
            resolved = (await db.execute(
                select(LogisticsAlert).where(
                    LogisticsAlert.alert_type == "geofence_breach",
                    LogisticsAlert.is_active.is_(True),
                    LogisticsAlert.location.contains(driver_tag),
                )
            )).scalar_one_or_none()
            if resolved:
                resolved.is_active = False
                db.add(resolved)

    return {
        "status": "success",
        "latitude": latitude,
        "longitude": longitude,
        "updated_at": _now().isoformat(),
    }


async def send_broadcast(db: AsyncSession, payload: dict) -> MessageResponse:
    """
    Create LogisticsNotification records for the selected audience.
    audience: 'all' | 'warehouses' | 'drivers'
    type: 'info' | 'warning' | 'emergency'
    message: str
    """
    audience = str(payload.get("audience", "all")).lower()
    alert_type = str(payload.get("type", "info")).lower()
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is required")

    # Map type → notification type label
    type_label_map = {
        "info": "info",
        "warning": "warning",
        "emergency": "alert",
    }
    notif_type = type_label_map.get(alert_type, "info")

    # Map audience → role names
    audience_role_map = {
        "all": ["WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER"],
        "warehouses": ["WAREHOUSE_MANAGER"],
        "drivers": ["DRIVER"],
    }
    target_roles = audience_role_map.get(audience, ["WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER"])

    # Derive title from type
    title_map = {
        "info": "System Broadcast",
        "warning": "⚠️ System Warning",
        "emergency": "🚨 Emergency Alert",
    }
    title = title_map.get(alert_type, "System Broadcast")

    # Fetch target roles
    role_rows = (await db.execute(select(Role).where(Role.name.in_(target_roles)))).scalars().all()
    role_ids = {role.id for role in role_rows}

    # Fetch target users
    target_users = (
        await db.execute(select(User).where(User.role_id.in_(role_ids), User.is_active.is_(True)))
    ).scalars().all()

    # Create one shared notification visible to all target roles
    db.add(LogisticsNotification(
        title=title,
        message=message,
        type=notif_type,
        audience_roles=",".join(target_roles),
        is_read=False,
    ))

    # Create a confirmation notification visible in the LM's own feed
    db.add(LogisticsNotification(
        title=f"[Broadcast Sent] {title}",
        message=f"Sent to {len(target_users)} recipient(s): {message}",
        type=notif_type,
        audience_roles="LOGISTIC_MANAGER",
        is_read=False,
    ))

    await db.commit()
    
    # Broadcast to drivers via WebSocket (real-time push)
    if "DRIVER" in target_roles:
        try:
            from app.routers.ws_fleet import driver_alert_manager
            await driver_alert_manager.broadcast({
                "type": "broadcast_alert",
                "severity": alert_type,  # info, warning, emergency
                "title": title,
                "message": message,
                "timestamp": datetime.now(UTC).isoformat(),
            })
        except Exception:
            pass  # WebSocket broadcast is best-effort
    
    return MessageResponse(message=f"Broadcast sent to {len(target_users)} recipient(s)")


# ── Driver Fuel Receipt ────────────────────────────────────────────────────────

async def submit_fuel_receipt(
    db: AsyncSession,
    user: User,
    data: DriverFuelReceiptCreate,
) -> MessageResponse:
    profile = await _get_driver_profile(db, user)
    warehouse_id = user.warehouse_id or profile.warehouse_id

    tx_code = f"FUEL-{str(user.id)[:8].upper()}-{int(_now().timestamp())}"
    tx = LogisticsTransaction(
        warehouse_id=warehouse_id,
        transaction_code=tx_code,
        description=f"Fuel receipt — {data.station or 'Unknown station'} — {data.liters}L",
        transaction_type="FUEL_EXPENSE",
        amount=-abs(data.amount),
        status="Completed",
        metadata_json={
            "driver_id": str(user.id),
            "driver_name": user.name,
            "station": data.station,
            "liters": data.liters,
            "amount": data.amount,
            "has_photo": bool(data.photo_base64),
        },
    )
    db.add(tx)
    await db.commit()
    return MessageResponse(message="Fuel receipt submitted successfully")
