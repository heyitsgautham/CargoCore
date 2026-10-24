"""Builds the driver app dashboard: manifest summary and delivery, pickup and house-shift jobs."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsDriverProfile,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.logistics import (
    DriverCrewMemberItem,
    DriverEarnings,
    DriverHosSummary,
    DriverManifestSummary,
    DriverShiftSummary,
    DriverTelemetryResponse,
)
from app.services.logistics.driver_context import (
    _build_driver_hos,
    _build_profile_stats,
    _build_validations,
    _build_vehicle_item,
    _get_driver_crew_members,
    _get_driver_current_vehicle,
    _get_driver_orders,
    _get_driver_profile,
    _get_driver_warehouse,
    _get_order_customers,
)
from app.services.logistics.formatting import (
    _coerce_utc,
    _driver_code,
    _estimate_duration_minutes,
    _estimate_manifest_distance_km,
    _format_date_label,
    _format_time_label,
    _is_active_order,
    _is_completed_order,
    _now,
    _order_job_type,
    _parse_profile_coords,
    _shift_code,
    _vehicle_metrics,
)
from app.services.logistics.operations import list_vehicles


def _build_manifest_summary(
    *,
    warehouse: Warehouse | None,
    orders: list[Order],
    crew: list[DriverCrewMemberItem],
    profile: LogisticsDriverProfile,
    hos: DriverHosSummary,
) -> DriverManifestSummary:
    if not orders:
        return DriverManifestSummary(
            route_id=None,
            date=_format_date_label(_now()),
            total_stops=0,
            completed_stops=0,
            total_distance_km=0,
            estimated_duration_minutes=0,
            estimated_end_time=_format_time_label(_now()) or "--:--",
            zone=warehouse.name if warehouse else None,
            parcel_count=0,
            crew_count=len(crew),
            current_location_label=warehouse.name if warehouse else profile.current_location,
        )

    total_stops = len(orders)
    completed_stops = len([order for order in orders if _is_completed_order(order)])
    total_distance_km = _estimate_manifest_distance_km(warehouse, orders)
    estimated_duration_minutes = _estimate_duration_minutes(total_distance_km, total_stops)
    estimated_end_dt = _now() + timedelta(minutes=max(estimated_duration_minutes - hos.used_minutes, 0))
    parcel_count = sum(sum(item.quantity for item in order.items) for order in orders)
    route_id = f"RT-{_now().strftime('%m%d')}-{str(orders[0].id).split('-')[0][-4:].upper()}"
    current_location = profile.current_location
    lat, lng = _parse_profile_coords(profile)
    location_label = f"{lat:.4f}, {lng:.4f}" if lat is not None and lng is not None else current_location or (warehouse.name if warehouse else None)
    cod_collected = sum(
        o.paid_amount
        for o in orders
        if _is_completed_order(o) and getattr(o, "payment_method", None) == "COD" and o.paid_amount
    )

    return DriverManifestSummary(
        route_id=route_id,
        date=_format_date_label(_coerce_utc(orders[0].scheduled_at) or _now()),
        total_stops=total_stops,
        completed_stops=completed_stops,
        total_distance_km=total_distance_km,
        estimated_duration_minutes=estimated_duration_minutes,
        estimated_end_time=_format_time_label(estimated_end_dt) or "--:--",
        zone=warehouse.name if warehouse else None,
        parcel_count=parcel_count,
        crew_count=len(crew),
        cod_collected=cod_collected,
        current_location_label=location_label,
    )


def _build_delivery_or_pickup_job(
    *,
    user: User,
    orders: list[Order],
    manifest: DriverManifestSummary,
    vehicle: LogisticsVehicle | None,
    job_type: str,
    customer_lookup: dict[UUID, dict],
) -> dict | None:
    if not orders:
        return None

    state_map = {
        "ASSIGNED": "ASSIGNED",
        "CONFIRMED": "ASSIGNED",
        "IN_TRANSIT": "IN_TRANSIT" if job_type == "PARCEL_DELIVERY" else "RETURN_TRANSIT",
        "DELIVERED": "COMPLETED",
        "COMPLETED": "COMPLETED",
        "CLOSED": "COMPLETED",
    }
    current_stop_index = 0
    stops = []
    for index, order in enumerate(orders):
        customer = customer_lookup.get(order.customer_id, {})
        stop_payload = {
            "id": str(order.id),
            "sequence": index + 1,
            "stopNumber": index + 1,
            "type": "pickup" if job_type == "PARCEL_PICKUP" else "parcel",
            "stopType": "pickup" if job_type == "PARCEL_PICKUP" else "delivery",
            "customerName": customer.get("name") or f"Order {order.tracking_code}",
            "customerPhone": customer.get("phone") or "",
            "address": order.pickup_addr if job_type == "PARCEL_PICKUP" else order.delivery_addr,
            "location": {"lat": order.delivery_lat, "lng": order.delivery_lng},
            "packages": [
                {
                    "id": str(item.id),
                    "barcode": item.sku,
                    "weight": f"{item.quantity} unit",
                    "description": item.sku,
                    "dims": None,
                }
                for item in order.items
            ] if job_type == "PARCEL_DELIVERY" else [],
            "expectedItems": sum(item.quantity for item in order.items),
            "itemsScanned": [],
            "specialInstructions": order.service_time_block or "Follow dispatch instructions.",
            "timeWindow": {
                "start": (_format_time_label(order.scheduled_at) or "--:--"),
                "end": (_format_time_label((_coerce_utc(order.scheduled_at) or _now()) + timedelta(minutes=45)) or "--:--"),
            } if order.scheduled_at else {
                "start": "--:--",
                "end": "--:--",
            },
            "cod": (order.payment_mode or "").upper() == "COD",
            "codAmount": max(order.total_amount - order.paid_amount, 0),
            "status": "completed" if _is_completed_order(order) else "pending",
            "arrivedAt": None,
            "completedAt": order.updated_at.isoformat() if _is_completed_order(order) else None,
            "pod": None,
        }
        if not _is_completed_order(order) and current_stop_index == 0:
            current_stop_index = index
        stops.append(stop_payload)

    active_order = next((order for order in orders if not _is_completed_order(order)), orders[-1])
    primary = orders[0]
    return {
        "jobId": primary.tracking_code,
        "jobType": job_type,
        "currentState": state_map.get(active_order.status.upper(), "ASSIGNED"),
        "manifestId": manifest.route_id,
        "vehicleId": vehicle.code if vehicle else None,
        "driverId": _driver_code(user),
        "assignedAt": (_coerce_utc(primary.scheduled_at) or _coerce_utc(primary.created_at) or _now()).isoformat(),
        "estimatedDuration": manifest.estimated_duration_minutes,
        "routeDistance": manifest.total_distance_km,
        "currentStopIndex": current_stop_index,
        "trackingCode": primary.tracking_code,
        "pickupAddr": primary.pickup_addr,
        "deliveryAddr": primary.delivery_addr,
        "stops": stops,
        "warehouseLocation": {
            "name": manifest.zone or "Warehouse",
            "address": manifest.zone or "Warehouse",
            "location": {"lat": None, "lng": None},
        },
    }


def _build_house_shift_job(
    *,
    user: User,
    order: Order,
    vehicle: LogisticsVehicle | None,
    manifest: DriverManifestSummary,
    crew: list[DriverCrewMemberItem],
    customer_lookup: dict[UUID, dict],
) -> dict:
    customer = customer_lookup.get(order.customer_id, {})
    inventory = [
        {
            "id": str(item.id),
            "category": "Inventory",
            "item": item.sku,
            "qty": item.quantity,
            "loaded": False,
            "unloaded": False,
            "packed": False,
        }
        for item in order.items
    ]
    checklist = [
        {"id": "packing-1", "phase": "packing", "task": "Crew attendance confirmed", "required": True, "completed": all(member.checked_in for member in crew) if crew else False},
        {"id": "packing-2", "phase": "packing", "task": "Customer inventory verified", "required": True, "completed": False},
        {"id": "loading-1", "phase": "loading", "task": "Heavy items secured in vehicle", "required": True, "completed": False},
        {"id": "unloading-1", "phase": "unloading", "task": "Destination placement confirmed", "required": True, "completed": False},
        {"id": "final-1", "phase": "final", "task": "Customer walkthrough completed", "required": True, "completed": False},
    ]
    return {
        "id": str(order.id),
        "jobId": order.tracking_code,
        "jobType": "HOUSE_SHIFT",
        "currentState": "ASSIGNED",
        "manifestId": manifest.route_id or order.tracking_code,
        "vehicleId": vehicle.code if vehicle else None,
        "driverId": _driver_code(user),
        "assignedAt": (_coerce_utc(order.scheduled_at) or _coerce_utc(order.created_at) or _now()).isoformat(),
        "estimatedDuration": manifest.estimated_duration_minutes,
        "routeDistance": manifest.total_distance_km,
        "currentStopIndex": 0,
        "crewRequired": order.labor_count,
        "crewAssigned": [
            {
                "id": str(member.labourer_id),
                "labourerId": str(member.labourer_id),
                "name": member.name,
                "role": member.role,
                "photo": member.photo,
                "checkedIn": member.checked_in,
                "checkInTime": member.check_in_time,
            }
            for member in crew
        ],
        "sourceLocation": {
            "name": "Source Address",
            "customerName": customer.get("name") or "Pickup Location",
            "customerPhone": customer.get("phone") or "",
            "address": order.pickup_addr,
            "location": {"lat": None, "lng": None},
            "floors": None,
            "elevator": None,
            "parkingAvailable": None,
        },
        "destinationLocation": {
            "name": "Destination Address",
            "customerName": customer.get("name") or "Drop Location",
            "customerPhone": customer.get("phone") or "",
            "address": order.delivery_addr,
            "location": {"lat": order.delivery_lat, "lng": order.delivery_lng},
            "floors": None,
            "elevator": None,
            "parkingAvailable": None,
        },
        "inventory": inventory,
        "equipment": [],
        "checklist": checklist,
        "beforePhotos": [],
        "afterPhotos": [],
        "totalCost": order.total_amount,
        "advancePaid": order.paid_amount,
        "balanceDue": max(order.total_amount - order.paid_amount, 0),
        "stops": [
            {
                "id": str(order.id),
                "sequence": 1,
                "status": "completed" if _is_completed_order(order) else "pending",
                "customerName": "Destination",
                "address": order.delivery_addr,
                "packages": [],
            }
        ],
    }


async def _build_driver_dashboard_bundle(
    db: AsyncSession,
    user: User,
) -> dict:
    profile = await _get_driver_profile(db, user)
    warehouse = await _get_driver_warehouse(db, user, profile)
    orders = await _get_driver_orders(db, user)
    current_vehicle = await _get_driver_current_vehicle(db, user, orders)
    visible_vehicles = await list_vehicles(
        db,
        warehouse_id=warehouse.id if warehouse else None,
        driver_id=user.id,
        driver_scoped=True,
    )
    crew = await _get_driver_crew_members(db, orders)
    customer_lookup = await _get_order_customers(db, orders)
    hos = _build_driver_hos(user, profile)
    manifest = _build_manifest_summary(
        warehouse=warehouse,
        orders=orders,
        crew=crew,
        profile=profile,
        hos=hos,
    )
    profile_stats = _build_profile_stats(user, profile, orders, current_vehicle)
    shift_code = _shift_code(user, _coerce_utc(user.last_login))
    validations = _build_validations(
        user=user,
        profile=profile,
        warehouse=warehouse,
        hos=hos,
        current_vehicle=current_vehicle,
        available_vehicle_count=len(visible_vehicles),
        shift_code=shift_code,
    )
    shift = DriverShiftSummary(
        shift_code=shift_code,
        status=profile.status,
        started_at=_coerce_utc(user.last_login) if profile.status.lower() != "off-duty" else None,
        ended_at=None,
        warehouse_name=warehouse.name if warehouse else None,
        active_order_count=len([order for order in orders if _is_active_order(order)]),
        last_vehicle_code=current_vehicle.code if current_vehicle else None,
        profile_stats=profile_stats,
        validations=validations,
    )
    lat, lng = _parse_profile_coords(profile)
    telemetry = DriverTelemetryResponse(
        gps_live=lat is not None and lng is not None,
        latitude=lat,
        longitude=lng,
        speed_kmh=0 if lat is None or lng is None else 28 + (profile.efficiency_score % 12),
        distance_covered_km=round(
            manifest.total_distance_km * (manifest.completed_stops / manifest.total_stops),
            1,
        ) if manifest.total_stops else 0,
        fuel_level_pct=_vehicle_metrics(current_vehicle)["fuel_level_pct"] if current_vehicle else None,
        range_km=_vehicle_metrics(current_vehicle)["range_km"] if current_vehicle else None,
        odometer_km=current_vehicle.mileage if current_vehicle else None,
        capacity_tons=_vehicle_metrics(current_vehicle)["cargo_capacity_tons"] if current_vehicle else None,
        seat_capacity=_vehicle_metrics(current_vehicle)["seat_capacity"] if current_vehicle else None,
        vehicle_id=current_vehicle.id if current_vehicle else None,
        vehicle_code=current_vehicle.code if current_vehicle else None,
        telemetry_status=_vehicle_metrics(current_vehicle)["telemetry_status"] if current_vehicle else None,
        last_updated=_now() if current_vehicle else None,
    )

    active_orders = [order for order in orders if _is_active_order(order)]
    house_shift_orders = [order for order in active_orders if _order_job_type(order) == "HOUSE_SHIFT"]
    pickup_orders = [order for order in active_orders if _order_job_type(order) == "PARCEL_PICKUP"]
    delivery_orders = [
        order
        for order in active_orders
        if _order_job_type(order) == "PARCEL_DELIVERY"
    ]

    current_job = None
    if house_shift_orders:
        current_job = _build_house_shift_job(
            user=user,
            order=house_shift_orders[0],
            vehicle=current_vehicle,
            manifest=manifest,
            crew=crew,
            customer_lookup=customer_lookup,
        )
    elif pickup_orders:
        current_job = _build_delivery_or_pickup_job(
            user=user,
            orders=pickup_orders,
            manifest=manifest,
            vehicle=current_vehicle,
            job_type="PARCEL_PICKUP",
            customer_lookup=customer_lookup,
        )
    elif delivery_orders:
        current_job = _build_delivery_or_pickup_job(
            user=user,
            orders=delivery_orders,
            manifest=manifest,
            vehicle=current_vehicle,
            job_type="PARCEL_DELIVERY",
            customer_lookup=customer_lookup,
        )

    current_vehicle_item = None
    if current_vehicle:
        current_vehicle_item = _build_vehicle_item(
            current_vehicle,
            driver_name=user.name,
        )

    earnings = _build_driver_earnings(profile, orders)
    return {
        "profile": profile_stats,
        "shift": shift,
        "hos": hos,
        "telemetry": telemetry,
        "manifest": manifest,
        "crew": crew,
        "current_vehicle": current_vehicle_item,
        "current_job": current_job,
        "earnings": earnings,
    }


# ── Driver Earnings ────────────────────────────────────────────────────────────

def _build_driver_earnings(
    profile: LogisticsDriverProfile,
    orders: list[Order],
) -> DriverEarnings:
    from datetime import timedelta
    now = _now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    base_per_shift = 500.0
    bonus_per_delivery = 50.0
    move_premium = 200.0

    def _order_date(order: Order) -> datetime:
        if order.updated_at:
            return _coerce_utc(order.updated_at)
        return _coerce_utc(order.created_at)

    def _compute_for_period(start: datetime) -> tuple[float, float, float]:
        period_orders = [o for o in orders if _is_completed_order(o) and _order_date(o) >= start]
        deliveries = len([o for o in period_orders if _order_job_type(o) == "PARCEL_DELIVERY"])
        moves = len([o for o in period_orders if _order_job_type(o) == "HOUSE_SHIFT"])
        pickups = len([o for o in period_orders if _order_job_type(o) == "PARCEL_PICKUP"])
        base = base_per_shift if period_orders else 0.0
        delivery_bonus = (deliveries + pickups) * bonus_per_delivery
        move_pay = moves * move_premium
        return base, delivery_bonus, move_pay

    t_base, t_del, t_move = _compute_for_period(today_start)
    w_base, w_del, w_move = _compute_for_period(week_start)
    m_base, m_del, m_move = _compute_for_period(month_start)

    score = min(100, 70 + profile.efficiency_score // 10)
    return DriverEarnings(
        today_base=t_base,
        today_deliveries=t_del,
        today_move=t_move,
        today_tips=0.0,
        week_base=w_base,
        week_deliveries=w_del,
        week_move=w_move,
        week_tips=0.0,
        month_base=m_base,
        month_deliveries=m_del,
        month_move=m_move,
        month_tips=0.0,
        shift_score=score,
        safety_score=score,
    )
