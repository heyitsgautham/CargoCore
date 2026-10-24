"""Trip intelligence for dispatchers, with optional Gemini enrichment, plus trip commands and deviation reports."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.logistics import (
    LogisticsAlert,
    LogisticsDriverProfile,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.order import Order
from app.models.user import User
from app.schemas.orders import (
    OrderTripIntelligenceItem,
    TripCommandPushRequest,
    TripDeviationReportRequest,
)
from app.services.orders.common import _get_order, _now, _push_notification
from app.services.orders.routing import _euclidean_km
from app.services.orders.trip_signals import (
    _build_route_signal,
    _clamp,
    _compute_alternate_waypoints,
    _derive_eta_confidence,
    _enrich_with_gemini,
    _eta_label_from_minutes,
    _parse_driver_location,
    _recommended_dispatch_action,
)


def _build_trip_intelligence_item(
    order: Order,
    *,
    driver_name: str | None,
    profile: LogisticsDriverProfile | None,
    vehicle: LogisticsVehicle | None,
    zones: list[LogisticsZone],
    reference_time: datetime | None = None,
) -> dict:
    now = reference_time or _now()
    order_status = str(order.status or "").upper()
    priority = str(getattr(order, "priority", None) or "NORMAL").upper()
    pickup_lat = order.pickup_lat
    pickup_lng = order.pickup_lng
    delivery_lat = order.delivery_lat
    delivery_lng = order.delivery_lng

    live_lat, live_lng = _parse_driver_location(profile.current_location if profile else None)
    origin_lat = live_lat if order_status == "IN_TRANSIT" and live_lat is not None else pickup_lat
    origin_lng = live_lng if order_status == "IN_TRANSIT" and live_lng is not None else pickup_lng

    has_pickup_coords = pickup_lat is not None and pickup_lng is not None
    has_delivery_coords = delivery_lat is not None and delivery_lng is not None
    has_origin_coords = origin_lat is not None and origin_lng is not None

    if has_origin_coords and has_delivery_coords:
        base_distance_km = round(_euclidean_km(origin_lat, origin_lng, delivery_lat, delivery_lng), 1)
    elif has_pickup_coords and has_delivery_coords:
        base_distance_km = round(_euclidean_km(pickup_lat, pickup_lng, delivery_lat, delivery_lng), 1)
    else:
        base_distance_km = 12.0

    base_distance_km = max(base_distance_km, 3.0)
    base_drive_minutes = max(18, round((base_distance_km / 28.0) * 60))
    handling_minutes = 12 if order_status == "ASSIGNED" else 6
    primary_penalty = 0
    signals: list[dict] = []
    no_go_zone_hit = False
    hit_zones: list[LogisticsZone] = []

    hour = now.astimezone(UTC).hour
    peak_window = 8 <= hour <= 10 or 17 <= hour <= 20
    if peak_window:
        primary_penalty += 10
        signals.append(_build_route_signal("traffic", "Peak-hour congestion risk detected on urban corridor.", "medium"))
    elif base_distance_km >= 25:
        primary_penalty += 5
        signals.append(_build_route_signal("distance", "Long single-trip distance increases ETA variability.", "medium"))

    if priority == "URGENT":
        primary_penalty += 10
        signals.append(_build_route_signal("priority", "Urgent order is operating with little dispatch slack.", "high"))
    elif priority == "HIGH":
        primary_penalty += 6
        signals.append(_build_route_signal("priority", "High-priority order should be monitored for ETA drift.", "medium"))

    if profile:
        driver_status = str(profile.status or "").lower()
        if driver_status in {"deviation", "breakdown"}:
            primary_penalty += 18
            signals.append(_build_route_signal("driver_status", f"Driver status is {profile.status}. Dispatch attention recommended.", "high"))
        elif driver_status in {"on break", "on_break"}:
            primary_penalty += 10
            signals.append(_build_route_signal("driver_status", "Driver is near a break window or recently paused.", "medium"))

    if vehicle and vehicle.maintenance_issue:
        primary_penalty += 6
        signals.append(_build_route_signal("vehicle", f"Vehicle note: {vehicle.maintenance_issue}.", "medium"))

    exclusion_margin_km = 1.2
    if has_delivery_coords:
        for zone in zones:
            if zone.lat is None or zone.lng is None or zone.radius_km is None:
                continue
            zone_distance_km = _euclidean_km(zone.lat, zone.lng, delivery_lat, delivery_lng)
            zone_type = str(zone.zone_type or "").lower()
            zone_status = str(zone.status or "").lower()
            within_zone = zone_distance_km <= zone.radius_km
            near_zone = zone_distance_km <= (zone.radius_km + exclusion_margin_km)

            if zone_type == "exclusion" and (within_zone or near_zone):
                no_go_zone_hit = True
                hit_zones.append(zone)
                primary_penalty += 18 if within_zone else 10
                signals.append(
                    _build_route_signal(
                        "zone",
                        f"Restricted zone near destination: {zone.name}. Alternate corridor recommended.",
                        "high" if within_zone else "medium",
                    )
                )
            elif zone_status == "alert" and (within_zone or near_zone):
                primary_penalty += 8
                signals.append(
                    _build_route_signal(
                        "zone_alert",
                        f"Operational alert near destination: {zone.name}. Expect access friction.",
                        "medium",
                    )
                )

    slack_minutes: int | None = None
    if order.scheduled_at:
        scheduled_at = order.scheduled_at
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=UTC)
        projected_primary = now + timedelta(minutes=base_drive_minutes + handling_minutes + primary_penalty)
        slack_minutes = int((scheduled_at - projected_primary).total_seconds() / 60)
        if slack_minutes < 0:
            primary_penalty += 18
            signals.append(_build_route_signal("sla", "Projected ETA is beyond the planned delivery window.", "high"))
        elif slack_minutes < 30:
            primary_penalty += 10
            signals.append(_build_route_signal("sla", "Projected ETA is close to the delivery commitment.", "medium"))

    primary_eta_minutes = base_drive_minutes + handling_minutes + primary_penalty

    alternate_gain = 0
    if peak_window:
        alternate_gain += 8
    if no_go_zone_hit:
        alternate_gain += 14
    if slack_minutes is not None and slack_minutes < 30:
        alternate_gain += 6
    if profile and str(profile.status or "").lower() == "deviation":
        alternate_gain += 8

    if alternate_gain > 0:
        alternate_eta_minutes = max(base_drive_minutes + handling_minutes, primary_eta_minutes - alternate_gain)
        alternate_distance_km = round(base_distance_km * 1.08, 1)
    else:
        alternate_eta_minutes = primary_eta_minutes + 5
        alternate_distance_km = round(base_distance_km * 1.03, 1)

    minutes_saved = max(0, primary_eta_minutes - alternate_eta_minutes)
    delay_probability = int(_clamp(18 + (primary_penalty * 2.2), 12, 97))
    if no_go_zone_hit:
        delay_probability = max(delay_probability, 78)
    if slack_minutes is not None and slack_minutes < 0:
        delay_probability = max(delay_probability, 84)

    if delay_probability >= 82 or (no_go_zone_hit and slack_minutes is not None and slack_minutes < 15):
        risk_level = "CRITICAL"
    elif delay_probability >= 65:
        risk_level = "HIGH"
    elif delay_probability >= 42:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if no_go_zone_hit and risk_level in {"HIGH", "CRITICAL"}:
        route_status = "Blocked"
    elif slack_minutes is not None and slack_minutes < 0:
        route_status = "Delayed"
    elif risk_level in {"MEDIUM", "HIGH", "CRITICAL"}:
        route_status = "Delay Risk"
    else:
        route_status = "On Track"

    recommended_route = "alternate" if minutes_saved >= 5 or no_go_zone_hit else "primary"
    dispatcher_recommendation, driver_message = _recommended_dispatch_action(
        no_go_zone_hit=no_go_zone_hit,
        route_status=route_status,
        risk_level=risk_level,
        order_status=order_status,
        priority=priority,
        minutes_saved=minutes_saved,
    )

    trip_stage = (
        "In-transit"
        if order_status == "IN_TRANSIT"
        else "Pre-dispatch"
        if order_status == "ASSIGNED"
        else "Awaiting Assignment"
    )
    eta_confidence = _derive_eta_confidence(
        has_pickup_coords=has_pickup_coords,
        has_delivery_coords=has_delivery_coords,
        has_live_driver_location=live_lat is not None and live_lng is not None,
        order_status=order_status,
    )

    payload = {
        "order_id": order.id,
        "tracking_code": order.tracking_code or "",
        "order_status": order_status,
        "driver_id": order.assigned_driver_id,
        "driver_name": driver_name,
        "vehicle_id": order.assigned_vehicle_id,
        "vehicle_code": vehicle.code if vehicle else None,
        "pickup_addr": order.pickup_addr or "",
        "delivery_addr": order.delivery_addr or "",
        "pickup_lat": pickup_lat,
        "pickup_lng": pickup_lng,
        "delivery_lat": delivery_lat,
        "delivery_lng": delivery_lng,
        "origin_lat": origin_lat,
        "origin_lng": origin_lng,
        "priority": priority,
        "trip_stage": trip_stage,
        "route_status": route_status,
        "risk_level": risk_level,
        "eta_label": _eta_label_from_minutes(primary_eta_minutes, now),
        "eta_minutes": primary_eta_minutes,
        "delay_probability_pct": delay_probability,
        "eta_confidence": eta_confidence,
        "planned_distance_km": round(base_distance_km, 1),
        "no_go_zone_hit": no_go_zone_hit,
        "signal_count": len(signals),
        "signals": signals,
        "dispatcher_recommendation": dispatcher_recommendation,
        "driver_message": driver_message,
        "primary_route": {
            "route_id": "primary",
            "label": "Primary corridor",
            "eta_minutes": primary_eta_minutes,
            "eta_label": _eta_label_from_minutes(primary_eta_minutes, now),
            "distance_km": round(base_distance_km, 1),
            "delta_minutes": 0,
            "summary": "Default operational plan using the current corridor.",
            "recommended": recommended_route == "primary",
        },
        "alternate_route": {
            "route_id": "alternate",
            "label": "Alternate corridor",
            "eta_minutes": alternate_eta_minutes,
            "eta_label": _eta_label_from_minutes(alternate_eta_minutes, now),
            "distance_km": alternate_distance_km,
            "delta_minutes": alternate_eta_minutes - primary_eta_minutes,
            "summary": (
                f"Recovers about {minutes_saved} minutes by avoiding risk hotspots."
                if minutes_saved > 0
                else "Fallback corridor with lower confidence but similar timing."
            ),
            "recommended": recommended_route == "alternate",
            "waypoints": _compute_alternate_waypoints(
                origin_lat or pickup_lat or 0.0,
                origin_lng or pickup_lng or 0.0,
                delivery_lat or 0.0,
                delivery_lng or 0.0,
                hit_zones,
            ) if has_delivery_coords else [],
        },
        "recommended_route": recommended_route,
        "generated_at": now,
    }
    return OrderTripIntelligenceItem.model_validate(payload).model_dump(mode="python")


async def _build_trip_intelligence_collection(
    db: AsyncSession,
    orders: list[Order],
) -> list[dict]:
    if not orders:
        return []

    driver_ids = {order.assigned_driver_id for order in orders if order.assigned_driver_id}
    vehicle_ids = {order.assigned_vehicle_id for order in orders if order.assigned_vehicle_id}
    warehouse_ids = {order.warehouse_id for order in orders if order.warehouse_id}

    profile_map: dict[UUID, LogisticsDriverProfile] = {}
    user_map: dict[UUID, User] = {}
    vehicle_map: dict[UUID, LogisticsVehicle] = {}
    zone_map: dict[UUID, list[LogisticsZone]] = {}

    if driver_ids:
        profiles = (
            await db.execute(
                select(LogisticsDriverProfile).where(LogisticsDriverProfile.user_id.in_(driver_ids))
            )
        ).scalars().all()
        profile_map = {profile.user_id: profile for profile in profiles}

        users = (
            await db.execute(select(User).where(User.id.in_(driver_ids)))
        ).scalars().all()
        user_map = {user.id: user for user in users}

    if vehicle_ids:
        vehicles = (
            await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.id.in_(vehicle_ids)))
        ).scalars().all()
        vehicle_map = {vehicle.id: vehicle for vehicle in vehicles}

    if warehouse_ids:
        zones = (
            await db.execute(select(LogisticsZone).where(LogisticsZone.warehouse_id.in_(warehouse_ids)))
        ).scalars().all()
        for zone in zones:
            zone_map.setdefault(zone.warehouse_id, []).append(zone)

    import asyncio as _asyncio
    base_items = [
        _build_trip_intelligence_item(
            order,
            driver_name=user_map.get(order.assigned_driver_id).name if order.assigned_driver_id in user_map else None,
            profile=profile_map.get(order.assigned_driver_id),
            vehicle=vehicle_map.get(order.assigned_vehicle_id),
            zones=zone_map.get(order.warehouse_id, []),
        )
        for order in orders
    ]

    items = list(await _asyncio.gather(*[_enrich_with_gemini(item) for item in base_items]))

    severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    items.sort(key=lambda item: (severity_rank.get(item["risk_level"], 9), -item["delay_probability_pct"]))
    return items


async def list_trip_intelligence(db: AsyncSession, statuses: str = "ASSIGNED,IN_TRANSIT") -> list[dict]:
    normalized_statuses = [
        value.strip().upper()
        for value in str(statuses or "").split(",")
        if value.strip()
    ] or ["ASSIGNED", "IN_TRANSIT"]

    orders = (
        await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.status.in_(normalized_statuses))
            .order_by(Order.created_at.desc())
        )
    ).scalars().all()
    return await _build_trip_intelligence_collection(db, orders)


async def get_trip_intelligence(
    db: AsyncSession,
    order_id: UUID,
    caller: User | None = None,
) -> dict:
    order = await _get_order(db, order_id)

    if caller is not None and caller.role.name == "DRIVER" and order.assigned_driver_id != caller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the assigned driver for this order",
        )

    items = await _build_trip_intelligence_collection(db, [order])
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip intelligence unavailable")
    return items[0]


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
