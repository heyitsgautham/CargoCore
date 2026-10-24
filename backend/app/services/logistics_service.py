from __future__ import annotations

import math
import re
from datetime import UTC, datetime, timedelta
from urllib.parse import quote_plus
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.document import LogisticsDocument
from app.models.inventory import InventoryItem, RestockRequest
from app.models.labour import LabourAttendance, Labourer
from app.models.logistics import (
    LogisticsAlert,
    LogisticsChatMessage,
    LogisticsChatThread,
    LogisticsDailyStats,
    LogisticsDriverProfile,
    LogisticsEquipmentLedger,
    LogisticsEscalation,
    LogisticsManifest,
    LogisticsMeeting,
    LogisticsMetric,
    LogisticsNotification,
    LogisticsReturnCase,
    LogisticsTask,
    LogisticsTransaction,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.order import DamageReport, Order
from app.models.user import Role, User
from app.models.warehouse import ReturnGrading, Warehouse
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    DispatchContactItem,
    DriverAuditEventItem,
    DriverCashoutRequest,
    DriverCrewMemberItem,
    DriverDashboardContext,
    DriverDispatchMessageCreate,
    DriverDispatchThreadItem,
    DriverEarnings,
    DriverFuelReceiptCreate,
    DriverHosSummary,
    DriverManifestSummary,
    DriverShiftSummary,
    DriverTelemetryResponse,
    DriverValidationItem,
    DriverVehicleBindRequest,
    LogisticsAiQueryResponse,
    LogisticsAlertItem,
    LogisticsBootstrapResponse,
    LogisticsChatMessageCreate,
    LogisticsChatMessageItem,
    LogisticsChatThreadCreate,
    LogisticsChatThreadItem,
    LogisticsChatThreadUpdate,
    LogisticsDashboardStats,
    LogisticsDocumentCreate,
    LogisticsDocumentItem,
    LogisticsDocumentUpdateStatus,
    LogisticsDriverCreate,
    LogisticsDriverItem,
    LogisticsDriverUpdate,
    LogisticsEquipmentItem,
    LogisticsEscalationItem,
    LogisticsEscalationStatusUpdate,
    LogisticsHubItem,
    LogisticsMaintenanceItem,
    LogisticsManifestCreate,
    LogisticsManifestItem,
    LogisticsMeetingCreate,
    LogisticsMeetingItem,
    LogisticsMeetingParticipantItem,
    LogisticsMeetingUpdate,
    LogisticsNotificationItem,
    LogisticsNotificationUpdate,
    LogisticsReportItem,
    LogisticsReturnCaseItem,
    LogisticsReturnCaseUpdate,
    LogisticsTaskCreate,
    LogisticsTaskItem,
    LogisticsTaskUpdate,
    LogisticsTransactionCreate,
    LogisticsTransactionItem,
    LogisticsUserItem,
    LogisticsVehicleCreate,
    LogisticsVehicleItem,
    LogisticsVehicleUpdate,
    LogisticsZoneCreate,
    LogisticsZoneItem,
    LogisticsZoneUpdate,
)
from app.utils.hashing import hash_password
from app.utils.username import generate_unique_username, normalize_username


def _now() -> datetime:
    return datetime.now(UTC)


async def _ensure_active_warehouse(db: AsyncSession, warehouse_id: UUID | None) -> Warehouse | None:
    if warehouse_id is None:
        return None
    warehouse = (
        await db.execute(
            select(Warehouse).where(
                Warehouse.id == warehouse_id,
                Warehouse.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot assign drivers to an archived warehouse",
        )
    return warehouse


def _fmt_relative(dt: datetime | None) -> str:
    if not dt:
        return "Never"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    delta = _now() - dt.astimezone(UTC)
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "Just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def _status_badge_class(status: str) -> str:
    normalized = status.lower()
    if "shop" in normalized or "overdue" in normalized:
        return "bg-red-500/10 text-red-500"
    if "scheduled" in normalized or "pending" in normalized:
        return "bg-yellow-500/10 text-yellow-500"
    return "bg-green-500/10 text-green-500"


def _title_case_status(value: str | None) -> str:
    if not value:
        return "Unknown"
    return value.replace("_", " ").title()


def _driver_code(user: User) -> str:
    return f"DRV-{str(user.id).split('-')[0][-4:].upper()}"


def _shift_code(user: User, started_at: datetime | None = None) -> str:
    base = started_at or _now()
    return f"SHIFT-{base.strftime('%m%d')}-{_driver_code(user).split('-')[-1]}"


def _coerce_utc(dt: datetime | None) -> datetime | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _format_duration_label(total_minutes: int) -> str:
    total_minutes = max(0, int(total_minutes))
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes:02d}m"


def _format_time_label(dt: datetime | None) -> str | None:
    normalized = _coerce_utc(dt)
    if not normalized:
        return None
    return normalized.strftime("%I:%M %p")


def _format_date_label(dt: datetime | None) -> str:
    normalized = _coerce_utc(dt) or _now()
    return normalized.strftime("%a, %b %d %Y").replace(" 0", " ")


def _avatar_url(name: str | None) -> str:
    safe_name = quote_plus((name or "Crew").strip() or "Crew")
    return f"https://ui-avatars.com/api/?name={safe_name}&background=1CE783&color=0B0F14"

_RESTOCK_ESCALATION_REF_RE = re.compile(r"\[ref:([0-9a-fA-F-]{36})\]")
_DRIVER_PIN_RE = re.compile(r"^\d{4}$")


def _normalize_driver_login_id(value: str | None, fallback_email: str) -> str:
    return (value or "").strip() or fallback_email.split("@")[0]


def _validate_driver_pin(pin: str | None) -> str:
    normalized_pin = (pin or "1234").strip()
    if not _DRIVER_PIN_RE.fullmatch(normalized_pin):
        raise HTTPException(status_code=400, detail="Driver PIN must be exactly 4 digits")
    return normalized_pin


def _to_logistics_escalation_item(escalation: LogisticsEscalation) -> LogisticsEscalationItem:
    return LogisticsEscalationItem(
        id=escalation.id,
        hub_id=escalation.warehouse_id,
        title=escalation.title,
        priority=escalation.priority,
        from_name=escalation.requester_name,
        role=escalation.requester_role,
        time=escalation.created_at.strftime("%I:%M %p"),
        description=escalation.description,
        action_details=escalation.action_details,
        status=escalation.status,
    )


async def _reconcile_restock_escalations(db: AsyncSession) -> None:
    open_escalations = (
        await db.execute(
            select(LogisticsEscalation).where(LogisticsEscalation.status == "OPEN")
        )
    ).scalars().all()

    if not open_escalations:
        return

    request_ids: dict[str, LogisticsEscalation] = {}
    for escalation in open_escalations:
        match = _RESTOCK_ESCALATION_REF_RE.search(escalation.action_details or "")
        if match:
            request_ids[match.group(1)] = escalation

    if not request_ids:
        return

    restock_requests = (
        await db.execute(
            select(RestockRequest).where(RestockRequest.id.in_([UUID(value) for value in request_ids]))
        )
    ).scalars().all()

    changed = False
    for req in restock_requests:
        escalation = request_ids.get(str(req.id))
        if escalation and req.status != "PENDING":
            escalation.status = req.status
            db.add(escalation)
            changed = True

    if changed:
        await db.flush()


def _order_job_type(order: Order) -> str:
    signal = " ".join(
        part for part in [
            order.order_type or "",
            order.cargo_type or "",
            order.vehicle_type or "",
            order.service_time_block or "",
        ]
        if part
    ).lower()

    if any(token in signal for token in ("house", "shift", "move", "moving", "relocation")):
        return "HOUSE_SHIFT"
    if any(token in signal for token in ("pickup", "return", "reverse")):
        return "PARCEL_PICKUP"
    return "PARCEL_DELIVERY"


def _is_terminal_order(order: Order) -> bool:
    return order.status.upper() in {"CANCELLED", "CLOSED"}


def _is_completed_order(order: Order) -> bool:
    return order.status.upper() in {"DELIVERED", "COMPLETED", "CLOSED"}


def _is_active_order(order: Order) -> bool:
    return order.status.upper() in {"ASSIGNED", "IN_TRANSIT", "CONFIRMED"}


def _vehicle_defaults(vehicle_type: str | None) -> tuple[float, int, int]:
    normalized = (vehicle_type or "").lower()
    if "truck" in normalized or "heavy" in normalized or "lorry" in normalized:
        return 3.5, 3, 460
    if "van" in normalized:
        return 1.5, 2, 340
    return 1.0, 2, 280


def _vehicle_metrics(vehicle: LogisticsVehicle) -> dict:
    capacity_tons, seat_capacity, base_range = _vehicle_defaults(vehicle.vehicle_type)
    fuel_level_pct = max(18, min(100, 100 - (vehicle.mileage % 57)))
    range_km = int(base_range * fuel_level_pct / 100)
    telemetry_status = "LIVE" if vehicle.assigned_driver_id else "READY"
    return {
        "fuel_level_pct": fuel_level_pct,
        "range_km": range_km,
        "seat_capacity": seat_capacity,
        "cargo_capacity_tons": capacity_tons,
        "telemetry_status": telemetry_status,
        "telemetry_last_seen": _now() if vehicle.assigned_driver_id else None,
    }


def _parse_profile_coords(profile: LogisticsDriverProfile | None) -> tuple[float | None, float | None]:
    if not profile or not profile.current_location:
        return None, None
    parts = [p.strip() for p in profile.current_location.split(",")]
    if len(parts) != 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return r * c


def _estimate_manifest_distance_km(warehouse: Warehouse | None, orders: list[Order]) -> float:
    coords: list[tuple[float, float]] = []
    if warehouse and warehouse.lat is not None and warehouse.lng is not None:
        coords.append((warehouse.lat, warehouse.lng))
    coords.extend(
        (order.delivery_lat, order.delivery_lng)
        for order in orders
        if order.delivery_lat is not None and order.delivery_lng is not None
    )

    if len(coords) >= 2:
        total = 0.0
        for idx in range(1, len(coords)):
            prev = coords[idx - 1]
            curr = coords[idx]
            total += _haversine_km(prev[0], prev[1], curr[0], curr[1])
        return round(total, 1)

    base = max(len(orders), 1)
    return round(base * 8.5, 1)


def _notification_role_set(notification: LogisticsNotification) -> set[str]:
    raw_value = (notification.audience_roles or "").strip()
    if not raw_value:
        return set()
    return {
        role.strip().upper()
        for role in raw_value.split(",")
        if role.strip()
    }


def _notification_visible_to_user(notification: LogisticsNotification, user: User) -> bool:
    # Per-user notifications (vendor/customer order events) are only visible to that user
    if notification.target_user_id is not None:
        return notification.target_user_id == user.id
    roles = _notification_role_set(notification)
    if not roles or "ALL" in roles:
        return True
    return user.role.name.upper() in roles


# Keep old name as alias for callers that only have role name
def _notification_visible_to_role(notification: LogisticsNotification, role_name: str) -> bool:
    if notification.target_user_id is not None:
        return False  # per-user notifications are not visible by role alone
    roles = _notification_role_set(notification)
    if not roles or "ALL" in roles:
        return True
    return role_name.upper() in roles


def _estimate_duration_minutes(distance_km: float, stop_count: int) -> int:
    drive_minutes = int((distance_km / 28.0) * 60)
    service_minutes = max(stop_count, 1) * 18
    return max(45, drive_minutes + service_minutes)


def _crew_role(labourer: Labourer) -> str:
    if labourer.skill_tags:
        return str(labourer.skill_tags[0]).replace("_", " ").title()
    role_name = getattr(getattr(labourer.user, "role", None), "name", None)
    if role_name and role_name != "LABOURER":
        return role_name.replace("_", " ").title()
    return "Crew"


def _latest_attendance_event(labourer: Labourer) -> LabourAttendance | None:
    if not labourer.attendance_events:
        return None
    return max(
        labourer.attendance_events,
        key=lambda event: _coerce_utc(event.created_at) or datetime.min.replace(tzinfo=UTC),
    )


def _to_crew_item(labourer: Labourer) -> DriverCrewMemberItem:
    last_event = _latest_attendance_event(labourer)
    checked_in = bool(last_event and last_event.event_type == "CHECK_IN")
    return DriverCrewMemberItem(
        labourer_id=labourer.id,
        user_id=labourer.user_id,
        name=labourer.user.name if labourer.user else "Crew Member",
        role=_crew_role(labourer),
        phone=labourer.user.phone if labourer.user else None,
        status="ACTIVE" if checked_in else "ASSIGNED",
        checked_in=checked_in,
        check_in_time=_format_time_label(last_event.created_at) if checked_in else None,
        photo=_avatar_url(labourer.user.name if labourer.user else "Crew"),
    )


def _build_vehicle_item(
    vehicle: LogisticsVehicle,
    *,
    driver_name: str | None,
) -> LogisticsVehicleItem:
    metrics = _vehicle_metrics(vehicle)
    return LogisticsVehicleItem(
        id=vehicle.id,
        hub_id=vehicle.warehouse_id,
        code=vehicle.code,
        type=vehicle.vehicle_type,
        model=vehicle.model,
        year=vehicle.year,
        license_plate=vehicle.license_plate,
        status=vehicle.status,
        driver=driver_name or "Unassigned",
        fuel_efficiency=vehicle.fuel_efficiency,
        mileage=vehicle.mileage,
        next_service=vehicle.next_service_date.strftime("%b %d, %Y") if vehicle.next_service_date else None,
        maintenance_issue=vehicle.maintenance_issue,
        fuel_level_pct=metrics["fuel_level_pct"],
        range_km=metrics["range_km"],
        seat_capacity=metrics["seat_capacity"],
        cargo_capacity_tons=metrics["cargo_capacity_tons"],
        telemetry_status=metrics["telemetry_status"],
        telemetry_last_seen=metrics["telemetry_last_seen"],
    )


async def _get_driver_profile(db: AsyncSession, user: User) -> LogisticsDriverProfile:
    profile = (
        await db.execute(
            select(LogisticsDriverProfile).where(LogisticsDriverProfile.user_id == user.id)
        )
    ).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    return profile


async def _get_driver_warehouse(db: AsyncSession, user: User, profile: LogisticsDriverProfile) -> Warehouse | None:
    warehouse_id = user.warehouse_id or profile.warehouse_id
    if not warehouse_id:
        return None
    return (
        await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    ).scalar_one_or_none()


async def _get_driver_orders(db: AsyncSession, user: User) -> list[Order]:
    start_of_day = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.assigned_driver_id == user.id,
                ~Order.status.in_(["DRAFT", "CANCELLED"]),
            )
            .order_by(Order.scheduled_at.asc().nullslast(), Order.created_at.asc())
        )
    ).scalars().all()

    filtered = []
    for order in rows:
        scheduled = _coerce_utc(order.scheduled_at) or _coerce_utc(order.created_at)
        if (scheduled and scheduled >= start_of_day) or _is_active_order(order) or _is_completed_order(order):
            filtered.append(order)
    return filtered or rows


async def _get_driver_current_vehicle(
    db: AsyncSession,
    user: User,
    orders: list[Order],
) -> LogisticsVehicle | None:
    preferred_vehicle_ids = [order.assigned_vehicle_id for order in orders if order.assigned_vehicle_id]
    if preferred_vehicle_ids:
        vehicles = (
            await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.id.in_(preferred_vehicle_ids)))
        ).scalars().all()
        vehicle_map = {vehicle.id: vehicle for vehicle in vehicles}
        for vehicle_id in preferred_vehicle_ids:
            if vehicle_id in vehicle_map:
                return vehicle_map[vehicle_id]

    return (
        await db.execute(
            select(LogisticsVehicle)
            .where(LogisticsVehicle.assigned_driver_id == user.id)
            .order_by(LogisticsVehicle.created_at.desc())
        )
    ).scalar_one_or_none()


async def _get_driver_crew_members(
    db: AsyncSession,
    orders: list[Order],
) -> list[DriverCrewMemberItem]:
    order_ids = [order.id for order in orders if _order_job_type(order) == "HOUSE_SHIFT"]
    if not order_ids:
        return []

    labourers = (
        await db.execute(
            select(Labourer)
            .options(
                selectinload(Labourer.user).selectinload(User.role),
                selectinload(Labourer.attendance_events),
            )
            .where(Labourer.assigned_order_id.in_(order_ids))
            .order_by(Labourer.created_at.asc())
        )
    ).scalars().all()
    return [_to_crew_item(labourer) for labourer in labourers]


async def _get_order_customers(
    db: AsyncSession,
    orders: list[Order],
) -> dict[UUID, dict]:
    customer_ids = {order.customer_id for order in orders if order.customer_id}
    if not customer_ids:
        return {}

    rows = (
        await db.execute(
            select(User.id, User.name, User.phone).where(User.id.in_(customer_ids))
        )
    ).all()
    return {
        row.id: {
            "name": row.name,
            "phone": row.phone,
        }
        for row in rows
    }


def _build_driver_hos(user: User, profile: LogisticsDriverProfile) -> DriverHosSummary:
    max_minutes = 14 * 60
    shift_started_at = _coerce_utc(user.last_login) if profile.status.lower() != "off-duty" else None
    used_minutes = 0
    if shift_started_at:
        used_minutes = int((_now() - shift_started_at).total_seconds() // 60)
    remaining_minutes = max(0, max_minutes - used_minutes)
    progress_percent = min(100, round((used_minutes / max_minutes) * 100)) if max_minutes else 0
    warning_level = "critical" if remaining_minutes <= 60 else "warning" if remaining_minutes <= 180 else "ok"
    return DriverHosSummary(
        used_minutes=used_minutes,
        remaining_minutes=remaining_minutes,
        max_minutes=max_minutes,
        progress_percent=progress_percent,
        used_label=_format_duration_label(used_minutes),
        remaining_label=_format_duration_label(remaining_minutes),
        max_label=_format_duration_label(max_minutes),
        warning_level=warning_level,
    )


def _build_profile_stats(
    user: User,
    profile: LogisticsDriverProfile,
    orders: list[Order],
    current_vehicle: LogisticsVehicle | None,
) -> dict:
    total_orders = len(orders)
    completed_orders = len([order for order in orders if _is_completed_order(order)])
    on_time_percent = round((completed_orders / total_orders) * 100) if total_orders else 0
    rated_orders = [o for o in orders if o.customer_rating is not None]
    rating = round(sum(o.customer_rating for o in rated_orders) / len(rated_orders), 1) if rated_orders else 0.0
    badge = "Pro Driver" if completed_orders >= 25 else "Field Driver" if completed_orders >= 5 else "Driver"
    tier = "Level 3 - Field Execution" if profile.efficiency_score >= 85 else "Level 2 - Route Ops"
    return {
        "id": str(user.id),
        "driverId": _driver_code(user),
        "name": user.name,
        "role": user.role.name,
        "badge": badge,
        "tier": tier,
        "rating": rating,
        "totalDeliveries": completed_orders,
        "onTimePercent": on_time_percent,
        "fuelEfficiency": current_vehicle.fuel_efficiency if current_vehicle and current_vehicle.fuel_efficiency else "N/A",
        "phone": user.phone or "",
        "email": user.email,
        "status": profile.status,
        "activeOrders": len([order for order in orders if _is_active_order(order)]),
        "completedOrders": completed_orders,
    }


def _build_validations(
    *,
    user: User,
    profile: LogisticsDriverProfile,
    warehouse: Warehouse | None,
    hos: DriverHosSummary,
    current_vehicle: LogisticsVehicle | None,
    available_vehicle_count: int,
    shift_code: str,
) -> list[DriverValidationItem]:
    vehicle_status = (
        f"{current_vehicle.code} · {_title_case_status(current_vehicle.status)}"
        if current_vehicle
        else f"{available_vehicle_count} vehicle(s) available"
    )
    return [
        DriverValidationItem(
            id="credential",
            label="RBAC Credential Verified",
            status=f"{_driver_code(user)} · {_title_case_status(profile.status)}",
            ok=user.is_active and user.role.name == "DRIVER",
            icon="badge",
        ),
        DriverValidationItem(
            id="roster",
            label="Roster Authorized",
            status=f"{shift_code} · {(warehouse.name if warehouse else 'Unassigned Hub')}",
            ok=warehouse is not None,
            icon="assignment",
        ),
        DriverValidationItem(
            id="vehicle",
            label="Vehicle Pool Available",
            status=vehicle_status,
            ok=bool(current_vehicle) or available_vehicle_count > 0,
            icon="local_shipping",
        ),
        DriverValidationItem(
            id="hos",
            label="Hours-of-Service Window",
            status=f"{hos.remaining_label} remaining",
            ok=hos.remaining_minutes > 0,
            icon="schedule",
        ),
    ]


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


async def _get_role(db: AsyncSession, name: str) -> Role:
    role = (await db.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
    if not role:
        raise RuntimeError(f"Required role missing: {name}")
    return role


async def _get_or_create_user(
    db: AsyncSession,
    *,
    role_name: str,
    email: str,
    name: str,
    username: str | None = None,
    warehouse_id: UUID | None = None,
    phone: str | None = None,
) -> User:
    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    role = await _get_role(db, role_name)
    if existing:
        existing.name = name
        if not existing.username:
            existing.username = await generate_unique_username(db, username or email.split("@")[0], exclude_user_id=existing.id)
        existing.role_id = role.id
        existing.warehouse_id = warehouse_id
        existing.phone = phone
        existing.is_active = True
        db.add(existing)
        await db.flush()
        return existing

    user = User(
        name=name,
        username=await generate_unique_username(db, username or email.split("@")[0]),
        email=email,
        phone=phone,
        address="",
        password_hash=hash_password("12345678"),
        role_id=role.id,
        warehouse_id=warehouse_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def _get_vehicle(db: AsyncSession, vehicle_id: UUID) -> LogisticsVehicle:
    vehicle = (await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.id == vehicle_id))).scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


async def _get_zone(db: AsyncSession, zone_id: UUID) -> LogisticsZone:
    zone = (await db.execute(select(LogisticsZone).where(LogisticsZone.id == zone_id))).scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone


async def _get_return_case(db: AsyncSession, case_id: UUID) -> LogisticsReturnCase:
    case = (await db.execute(select(LogisticsReturnCase).where(LogisticsReturnCase.id == case_id))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return case not found")
    return case


async def _get_completed_return_grading(
    db: AsyncSession,
    case: LogisticsReturnCase,
) -> ReturnGrading | None:
    query = (
        select(ReturnGrading)
        .options(selectinload(ReturnGrading.grader))
        .where(ReturnGrading.status == "completed")
        .order_by(ReturnGrading.graded_at.desc(), ReturnGrading.created_at.desc())
    )
    if case.reference_code:
        grading = (
            await db.execute(query.where(ReturnGrading.rma_code == case.reference_code).limit(1))
        ).scalar_one_or_none()
        if grading:
            return grading
    if case.order_id:
        grading = (
            await db.execute(query.where(ReturnGrading.order_id == case.order_id).limit(1))
        ).scalar_one_or_none()
        if grading:
            return grading
    return None


async def _wallet_refund_credited(db: AsyncSession, reference_code: str | None) -> bool:
    if not reference_code:
        return False
    from app.models.wallet import WalletTransaction

    credited = (
        await db.execute(
            select(WalletTransaction.id).where(
                WalletTransaction.reason == "DAMAGE_REFUND",
                WalletTransaction.description.contains(reference_code),
            )
        )
    ).scalar_one_or_none()
    return bool(credited)


async def _build_return_case_item(
    db: AsyncSession,
    case: LogisticsReturnCase,
    completed_grading: ReturnGrading | None = None,
    wallet_credited: bool | None = None,
) -> LogisticsReturnCaseItem:
    grading = completed_grading if completed_grading is not None else await _get_completed_return_grading(db, case)
    credited = wallet_credited if wallet_credited is not None else await _wallet_refund_credited(db, case.reference_code)
    is_physical_flow = getattr(case, "flow_type", None) == "pickup_inspection"
    normalized_status = case.status
    case_images = list(case.images or [])
    if grading and grading.damage_photo_url and grading.damage_photo_url not in case_images:
        case_images.append(grading.damage_photo_url)
    if not is_physical_flow and case.status in {"Inspected", "Physically Inspected"}:
        normalized_status = "Claims Reviewed"
    display_status = normalized_status
    if grading and is_physical_flow and normalized_status in {"Arrived at Warehouse", "At Warehouse", "Inspected", "Physically Inspected"}:
        display_status = "Physically Inspected"

    return LogisticsReturnCaseItem(
        id=case.id,
        hub_id=case.warehouse_id,
        order_id=case.order_id,
        customer=case.customer_name,
        reason=case.reason,
        flow_type=getattr(case, "flow_type", None),
        condition=grading.item_condition if (grading and is_physical_flow) else case.condition,
        status=display_status,
        original_price=case.original_price,
        refund_amount=case.refund_amount,
        images=case_images,
        reference_code=case.reference_code,
        wallet_credited=credited,
        wm_disposition=grading.disposition if (grading and is_physical_flow) else None,
        wm_is_genuine=grading.is_genuine if (grading and is_physical_flow) else getattr(case, "wm_is_genuine", None),
        wm_recommended_outcome=grading.recommended_outcome if (grading and is_physical_flow) else getattr(case, "wm_recommended_outcome", None),
        wm_inspection_remarks=grading.inspection_remarks if (grading and is_physical_flow) else getattr(case, "wm_inspection_remarks", None),
        wm_graded_at=grading.graded_at if (grading and is_physical_flow) else None,
        wm_grader_name=grading.grader.name if (grading and is_physical_flow and grading.grader) else None,
        transport_charge_amount=round(float(case.transport_charge_amount or 0.0), 2),
        transport_charge_wallet_collected=round(float(case.transport_charge_wallet_collected or 0.0), 2),
        transport_charge_pending_amount=round(float(case.transport_charge_pending_amount or 0.0), 2),
        transport_charge_status=case.transport_charge_status,
        transport_charge_applied_at=case.transport_charge_applied_at,
        is_urgent=bool(getattr(case, "is_urgent", False)),
        urgent_reason=getattr(case, "urgent_reason", None),
    )


async def _get_chat_thread(db: AsyncSession, thread_id: UUID) -> LogisticsChatThread:
    thread = (await db.execute(select(LogisticsChatThread).where(LogisticsChatThread.id == thread_id))).scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat thread not found")
    return thread


def _build_thread_item(thread: LogisticsChatThread, messages: list[LogisticsChatMessage]) -> LogisticsChatThreadItem:
    return LogisticsChatThreadItem(
        id=thread.id,
        hub_id=thread.warehouse_id,
        name=thread.name,
        time=_fmt_relative(thread.last_message_at),
        last_message=thread.last_message,
        status=thread.status,
        phone=thread.phone,
        muted=thread.muted,
        messages=[
            LogisticsChatMessageItem(
                id=msg.id,
                text=msg.text,
                sender=msg.sender,
                time=msg.created_at.strftime("%I:%M %p"),
            )
            for msg in sorted(messages, key=lambda m: m.created_at)
        ],
    )


async def list_chat_threads(db: AsyncSession) -> list[LogisticsChatThreadItem]:
    threads = (await db.execute(
        select(LogisticsChatThread).order_by(LogisticsChatThread.last_message_at.desc().nullslast())
    )).scalars().all()
    all_messages = (await db.execute(
        select(LogisticsChatMessage).order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()
    msgs_by_thread: dict[UUID, list[LogisticsChatMessage]] = {}
    for msg in all_messages:
        msgs_by_thread.setdefault(msg.thread_id, []).append(msg)
    return [_build_thread_item(t, msgs_by_thread.get(t.id, [])) for t in threads]


async def get_dispatch_contacts(db: AsyncSession) -> list[DispatchContactItem]:
    """Return all DRIVER + WAREHOUSE_MANAGER users, joined with any existing chat threads."""
    contactable_roles = ["DRIVER", "WAREHOUSE_MANAGER"]
    users = (await db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.name.in_(contactable_roles))
        .where(User.is_active.is_(True))
        .order_by(User.name.asc())
    )).scalars().all()

    threads = (await db.execute(select(LogisticsChatThread))).scalars().all()
    all_messages = (await db.execute(
        select(LogisticsChatMessage).order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()
    msgs_by_thread: dict = {}
    for msg in all_messages:
        msgs_by_thread.setdefault(msg.thread_id, []).append(msg)

    # Index threads by normalised name for matching
    thread_by_name: dict[str, LogisticsChatThread] = {t.name.strip().lower(): t for t in threads}

    # Also load roles for display
    roles_map: dict[UUID, str] = {}
    role_rows = (await db.execute(select(Role))).scalars().all()
    for r in role_rows:
        roles_map[r.id] = r.name

    result: list[DispatchContactItem] = []
    for user in users:
        # Driver threads are named "Driver: {name}" by the driver app — try that first
        thread = (
            thread_by_name.get(f"driver: {user.name.strip().lower()}")
            or thread_by_name.get(user.name.strip().lower())
        )
        thread_messages = []
        if thread:
            thread_messages = [
                LogisticsChatMessageItem(
                    id=m.id, text=m.text, sender=m.sender,
                    time=m.created_at.strftime("%I:%M %p"),
                )
                for m in msgs_by_thread.get(thread.id, [])
            ]
        result.append(DispatchContactItem(
            user_id=user.id,
            name=user.name,
            role=roles_map.get(user.role_id, "DRIVER"),
            phone=user.phone or None,
            email=user.email,
            thread_id=thread.id if thread else None,
            last_message=thread.last_message if thread else None,
            thread_status=thread.status if thread else "Offline",
            messages=thread_messages,
        ))
    return result


async def add_chat_message(
    db: AsyncSession,
    thread_id: UUID,
    data: LogisticsChatMessageCreate,
) -> LogisticsChatThreadItem:
    thread = await _get_chat_thread(db, thread_id)
    msg = LogisticsChatMessage(
        thread_id=thread.id,
        sender=data.sender,
        text=data.text,
        created_at=_now(),
    )
    db.add(msg)
    thread.last_message = data.text
    thread.last_message_at = _now()
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    # Reload messages for this thread
    messages = (await db.execute(
        select(LogisticsChatMessage)
        .where(LogisticsChatMessage.thread_id == thread.id)
        .order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()
    return _build_thread_item(thread, list(messages))


async def create_chat_thread(
    db: AsyncSession,
    data: LogisticsChatThreadCreate,
) -> LogisticsChatThreadItem:
    # Return existing thread if one with this name already exists (prevents duplicates)
    existing = (
        await db.execute(
            select(LogisticsChatThread)
            .where(LogisticsChatThread.name == data.name)
            .order_by(LogisticsChatThread.created_at.asc())
        )
    ).scalars().first()
    if existing:
        messages = (await db.execute(
            select(LogisticsChatMessage)
            .where(LogisticsChatMessage.thread_id == existing.id)
            .order_by(LogisticsChatMessage.created_at.asc())
        )).scalars().all()
        return _build_thread_item(existing, list(messages))

    thread = LogisticsChatThread(
        name=data.name,
        phone=data.phone,
        warehouse_id=data.warehouse_id,
        status="Online",
        muted=False,
        last_message=None,
        last_message_at=None,
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return _build_thread_item(thread, [])


async def delete_chat_thread(db: AsyncSession, thread_id: UUID) -> MessageResponse:
    thread = await _get_chat_thread(db, thread_id)
    await db.delete(thread)
    await db.commit()
    return MessageResponse(message="Chat thread deleted")


async def mute_chat_thread(
    db: AsyncSession,
    thread_id: UUID,
    data: LogisticsChatThreadUpdate,
) -> LogisticsChatThreadItem:
    thread = await _get_chat_thread(db, thread_id)
    thread.muted = data.muted
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    messages = (await db.execute(
        select(LogisticsChatMessage)
        .where(LogisticsChatMessage.thread_id == thread.id)
        .order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()
    return _build_thread_item(thread, list(messages))


async def ensure_logistics_seed_data(db: AsyncSession, manager_user: User) -> None:
    warehouse_count = (await db.execute(select(func.count(Warehouse.id)))).scalar_one()
    if warehouse_count:
        return

    north = Warehouse(name="North-East Hub", address="12 Hudson Logistics Park, New York, NY", lat=40.7128, lng=-74.0060, capacity_limit=1500, is_active=True)
    south = Warehouse(name="South Hub", address="88 Austin Freight Avenue, Austin, TX", lat=30.2672, lng=-97.7431, capacity_limit=2000, is_active=True)
    west = Warehouse(name="West DC-04", address="44 Harbor Cargo Road, Los Angeles, CA", lat=34.0522, lng=-118.2437, capacity_limit=1200, is_active=True)
    db.add_all([north, south, west])
    await db.flush()

    wm_north = await _get_or_create_user(db, role_name="WAREHOUSE_MANAGER", email="ellen.r@cargocore.com", username="ellen_r", name="Ellen Ripley", warehouse_id=north.id, phone="+1 (555) 555-0101")
    wm_south = await _get_or_create_user(db, role_name="WAREHOUSE_MANAGER", email="sarah.c@cargocore.com", username="sarah_c", name="Sarah Connor", warehouse_id=south.id, phone="+1 (555) 123-4567")
    await _get_or_create_user(db, role_name="DISPATCHER", email="john.w@cargocore.com", username="john_w", name="John Wick", warehouse_id=north.id, phone="+1 (555) 987-6543")
    driver_one = await _get_or_create_user(db, role_name="DRIVER", email="david.m@cargocore.com", username="david_m", name="David Miller", warehouse_id=north.id, phone="+1 (555) 123-4567")
    driver_two = await _get_or_create_user(db, role_name="DRIVER", email="sarah.j@cargocore.com", username="sarah_j", name="Sarah Jenkins", warehouse_id=south.id, phone="+1 (555) 987-6543")

    north.manager_id = wm_north.id
    south.manager_id = wm_south.id
    west.manager_id = manager_user.id
    db.add_all([north, south, west])
    await db.flush()

    vendor_role = await _get_role(db, "VENDOR")
    customer = (await db.execute(select(User).where(User.role_id == vendor_role.id))).scalar_one_or_none() or manager_user

    db.add_all([
        LogisticsDriverProfile(user_id=driver_one.id, warehouse_id=north.id, status="breakdown", current_location="Route 4B", current_job="Delivery #9982", efficiency_score=85, avatar_color="bg-gray-700", chat_history=[{"id": 1, "text": "Dispatch, engine light just came on.", "sender": "driver", "time": "09:15 AM"}, {"id": 2, "text": "Copy that David. Sending mobile mechanic.", "sender": "dispatch", "time": "09:16 AM"}]),
        LogisticsDriverProfile(user_id=driver_two.id, warehouse_id=south.id, status="deviation", current_location="Sector 7", current_job="Delivery #9991", efficiency_score=92, avatar_color="bg-gray-700", chat_history=[{"id": 1, "text": "Traffic on Route 9 is blocked.", "sender": "driver", "time": "10:42 AM"}, {"id": 2, "text": "Reroute approved. Follow the AI map.", "sender": "dispatch", "time": "10:43 AM"}]),
    ])

    vehicle_one = LogisticsVehicle(code="TRK-992", vehicle_type="Heavy Truck", warehouse_id=north.id, assigned_driver_id=driver_one.id, model="Volvo FH16", year=2021, license_plate="NY-442-XM", status="In Shop", fuel_efficiency="8.2 MPG", mileage=124500, maintenance_issue="Engine Check Light", next_service_date=_now() + timedelta(days=3))
    vehicle_two = LogisticsVehicle(code="VAN-104", vehicle_type="Delivery Van", warehouse_id=north.id, assigned_driver_id=driver_two.id, model="Ford Transit", year=2022, license_plate="NY-991-AB", status="Scheduled", fuel_efficiency="18.5 MPG", mileage=45200, maintenance_issue="Tire Replacement", next_service_date=_now() + timedelta(days=10))
    vehicle_three = LogisticsVehicle(code="TRK-221", vehicle_type="Heavy Truck", warehouse_id=south.id, model="Peterbilt 579", year=2020, license_plate="TX-118-PQ", status="Active", fuel_efficiency="7.9 MPG", mileage=210000, next_service_date=_now() + timedelta(days=21))
    db.add_all([vehicle_one, vehicle_two, vehicle_three])
    await db.flush()

    orders = [
        Order(tracking_code="QC-LOGI001", order_type="VENDOR", status="IN_TRANSIT", customer_id=customer.id, warehouse_id=north.id, assigned_driver_id=driver_one.id, assigned_vehicle_id=vehicle_one.id, pickup_addr="Amazon FC, Newark, NJ", delivery_addr="Client DC, Boston, MA", cargo_type="Retail Goods", vehicle_type="Truck", labor_count=2, base_amount=12000, vehicle_amount=3000, labor_amount=1200, materials_amount=600, packing_amount=350, platform_fee=500, tax_amount=980, total_amount=18630, payment_mode="Credit", payment_status="paid", scheduled_at=_now() - timedelta(hours=3)),
        Order(tracking_code="QC-LOGI002", order_type="VENDOR", status="ASSIGNED", customer_id=customer.id, warehouse_id=south.id, assigned_driver_id=driver_two.id, assigned_vehicle_id=vehicle_two.id, pickup_addr="Vendor Hub, Austin, TX", delivery_addr="Retail Outlet, Dallas, TX", cargo_type="Electronics", vehicle_type="Van", labor_count=1, base_amount=8000, vehicle_amount=1800, labor_amount=600, materials_amount=220, packing_amount=180, platform_fee=350, tax_amount=700, total_amount=11850, payment_mode="COD", payment_status="pending", scheduled_at=_now() + timedelta(hours=2)),
        Order(tracking_code="QC-LOGI003", order_type="VENDOR", status="DELIVERED", customer_id=customer.id, warehouse_id=west.id, pickup_addr="Port Cargo Gate, LA", delivery_addr="Warehouse Client, San Diego, CA", cargo_type="Furniture", vehicle_type="Truck", labor_count=3, base_amount=14000, vehicle_amount=3400, labor_amount=1600, materials_amount=900, packing_amount=500, platform_fee=650, tax_amount=1220, total_amount=22270, payment_mode="Transfer", payment_status="paid", scheduled_at=_now() - timedelta(days=1)),
    ]
    db.add_all(orders)

    db.add_all([
        InventoryItem(warehouse_id=north.id, sku="INV-001", name="Packing Tape", category="Consumables", unit="Rolls", quantity_on_hand=1540, safety_stock=200, aisle="Zone A"),
        InventoryItem(warehouse_id=south.id, sku="INV-003", name="Cardboard Box (M)", category="Packaging", unit="Pcs", quantity_on_hand=850, safety_stock=1000, aisle="Zone B"),
        InventoryItem(warehouse_id=north.id, sku="INV-009", name="Cargo Straps", category="Cargo", unit="Set", quantity_on_hand=500, safety_stock=100, aisle="Loading Dock"),
        InventoryItem(warehouse_id=south.id, sku="INV-010", name="Utensils (Breakroom)", category="Utensils", unit="Set", quantity_on_hand=200, safety_stock=220, aisle="Breakroom"),
    ])

    db.add_all([
        LogisticsTransaction(warehouse_id=north.id, transaction_code="TX-99212", description="Client Payment - Amazon", transaction_type="Incoming", amount=15400, status="Completed"),
        LogisticsTransaction(warehouse_id=north.id, transaction_code="TX-99213", description="Fuel Expense - Shell", transaction_type="Expense", amount=-2400, status="Completed"),
        LogisticsTransaction(warehouse_id=south.id, transaction_code="TX-99214", description="Driver Payout - Weekly", transaction_type="Payroll", amount=-6500, status="Paid"),
        LogisticsTransaction(warehouse_id=south.id, transaction_code="TX-99215", description="COD Deposit - Zone A", transaction_type="Incoming", amount=1250, status="Pending"),
    ])

    db.add_all([
        LogisticsZone(warehouse_id=north.id, name="Downtown Delivery Zone", zone_type="Polygon", radius_km=12, status="Active", color_token="blue"),
        LogisticsZone(warehouse_id=north.id, name="North-East Hub Perimeter", zone_type="Circle", radius_km=0.5, status="Active", color_token="green"),
        LogisticsZone(warehouse_id=south.id, name="Red Zone - Construction", zone_type="Exclusion", radius_km=2.5, status="Alert", color_token="red"),
        LogisticsZone(warehouse_id=south.id, name="Airport Logistics Corridor", zone_type="Polygon", radius_km=45, status="Active", color_token="indigo"),
    ])

    db.add_all([
        LogisticsAlert(warehouse_id=north.id, alert_type="congestion", title="Hub Congestion Alert", description="North-East Hub is experiencing high dwell times (>45 mins).", severity="high", icon="error", location="North-East Hub", recommendation="Reroute incoming traffic to South Hub temporarily.", impact_json={"affectedDrivers": 12}, is_active=True),
        LogisticsAlert(warehouse_id=south.id, alert_type="delayed", title="Delayed Shipments", description="14 shipments at risk of missing SLA window in Sector 4.", severity="medium", icon="schedule", location="Sector 4", recommendation="Assign priority status to these deliveries.", impact_json={"impact": "Potential SLA breach for 14 clients"}, is_active=True),
    ])

    db.add_all([
        LogisticsNotification(title="New Hub Alert", message="North-East hub congestion > 90%", type="alert"),
        LogisticsNotification(title="Driver Update", message="David Miller reported breakdown", type="warning"),
        LogisticsNotification(title="Shipment Delivered", message="Order QC-LOGI003 delivered", type="success"),
        LogisticsTask(text="Review daily hub performance", status="Priority", target_time=_now() + timedelta(hours=1), repeat_rule="none"),
        LogisticsTask(text="Approve Fleet Maintenance", status="Done", target_time=_now() - timedelta(hours=2), repeat_rule="none"),
    ])

    thread_one = LogisticsChatThread(warehouse_id=north.id, name="Dispatcher Mike", status="Online", phone="+1 (555) 012-3456", muted=False, last_message="Two trucks are down.", last_message_at=_now() - timedelta(minutes=2))
    thread_two = LogisticsChatThread(warehouse_id=south.id, name="Warehouse Team A", status="Offline", phone="+1 (555) 012-7890", muted=False, last_message="Inventory count complete.", last_message_at=_now() - timedelta(hours=1))
    db.add_all([thread_one, thread_two])
    await db.flush()

    db.add_all([
        LogisticsChatMessage(thread_id=thread_one.id, sender="other", text="Hi Boss, we have a situation at Hub 4.", created_at=_now() - timedelta(minutes=6)),
        LogisticsChatMessage(thread_id=thread_one.id, sender="other", text="Two trucks are down.", created_at=_now() - timedelta(minutes=4)),
        LogisticsChatMessage(thread_id=thread_one.id, sender="me", text="Approved. Use the contingency budget.", created_at=_now() - timedelta(minutes=3)),
        LogisticsChatMessage(thread_id=thread_two.id, sender="other", text="Inventory count complete. Report filed.", created_at=_now() - timedelta(hours=1)),
        LogisticsEscalation(warehouse_id=south.id, title="Route Deviation Override Required", priority="High", requester_name="Sarah Connor", requester_role="Dispatcher (South Hub)", description="Driver Alex Morgan is requesting a geofence override due to road construction.", action_details="Approve Geofence Override for V-402", status="OPEN"),
        LogisticsEscalation(warehouse_id=north.id, title="Fuel Limit Exceeded Action Required", priority="Medium", requester_name="System Bot", requester_role="Automated Alert", description="Vehicle V-105 submitted a fuel receipt that exceeds the daily limit.", action_details="Review OCR Receipt vs GPS Log", status="OPEN"),
        LogisticsReturnCase(warehouse_id=north.id, order_id=orders[0].id, reference_code="RMA-9921", customer_name="Alice Cooper", reason="Damaged in transit", condition="Damaged", status="Pending", original_price=150, refund_amount=0, images=["https://placehold.co/600x400/png?text=Damaged+Box+Corner"]),
        LogisticsReturnCase(warehouse_id=south.id, order_id=orders[1].id, reference_code="RMA-9923", customer_name="Charlie Watts", reason="Changed Mind", condition="Unopened", status="Approved", original_price=1250, refund_amount=1250, images=[]),
    ])

    await db.flush()

    # Seed historical daily stats for the past 30 days
    for days_ago in range(30, 0, -1):
        stat_date = (_now() - timedelta(days=days_ago)).date()
        
        # Global stats
        daily_orders = 1000 + int((30 - days_ago) * 8.3) + (hash(str(stat_date)) % 150)
        daily_revenue = 35000 + int((30 - days_ago) * 500) + (hash(str(stat_date)) % 5000)
        
        db.add(LogisticsDailyStats(
            warehouse_id=None,
            stat_date=stat_date,
            orders_count=daily_orders,
            revenue=daily_revenue,
            deliveries_completed=int(daily_orders * 0.98),
            deliveries_failed=int(daily_orders * 0.02),
            sla_compliance=85 + (hash(str(stat_date)) % 15),
        ))
        
        # Per-warehouse stats
        for warehouse in [north, south, west]:
            ratio = 0.33 if warehouse == north else (0.45 if warehouse == south else 0.22)
            hub_orders = int(daily_orders * ratio)
            hub_revenue = daily_revenue * ratio
            
            db.add(LogisticsDailyStats(
                warehouse_id=warehouse.id,
                stat_date=stat_date,
                orders_count=hub_orders,
                revenue=hub_revenue,
                deliveries_completed=int(hub_orders * 0.98),
                deliveries_failed=int(hub_orders * 0.02),
                sla_compliance=82 + (hash(f"{warehouse.id}{stat_date}") % 18),
            ))

    db.add_all([
        LogisticsEquipmentLedger(warehouse_id=north.id, item_type="Crates (Standard)", issued_count=450, returned_count=410, reference_code="ORD-4920", status="Pending Collection"),
        LogisticsEquipmentLedger(warehouse_id=south.id, item_type="Thermal Blankets", issued_count=120, returned_count=120, reference_code="ORD-4921", status="Cleared"),
        LogisticsEquipmentLedger(warehouse_id=west.id, item_type="Pallets (Wood)", issued_count=800, returned_count=750, reference_code="ORD-4925", status="Pending Collection"),
        LogisticsEquipmentLedger(warehouse_id=None, item_type="Refrigerant Packs", issued_count=1800, returned_count=1500, reference_code="NET-SYS", status="Pending Collection"),
    ])

    metrics = []
    for i, (label, val) in enumerate(zip(["Jan", "Feb", "Mar", "Apr", "May", "Jun"], [5.2, 4.8, 4.4, 4.1, 3.9, 4.0])):
        metrics.append(LogisticsMetric(metric_type="vendor_lead_time", label=label, value_main=val))
        metrics.append(LogisticsMetric(metric_type="safety_incidents", label=label, value_main=[2, 3, 1, 2, 1, 0][i]))
    
    for i, (label, eff, ot) in enumerate(zip(["Shift A", "Shift B", "Shift C"], [92, 88, 95], [12, 18, 5])):
        metrics.append(LogisticsMetric(metric_type="shift_efficiency", label=label, value_main=eff, value_secondary=ot))
    
    for i, (label, val) in enumerate(zip(["6am-9am", "9am-12pm", "12pm-3pm", "3pm-6pm", "6pm-9pm"], [15, 45, 25, 60, 20])):
        metrics.append(LogisticsMetric(metric_type="dwell_time", label=label, value_main=val))
    
    db.add_all(metrics)

    # Seed initial Fleet/Driver documents if not present
    existing_docs = (await db.execute(select(func.count(LogisticsDocument.id)))).scalar_one()
    if existing_docs == 0:
        db.add_all([
            # Vehicle Documents (using vehicle UUID as entity_id, not code)
            LogisticsDocument(entity_type="VEHICLE", entity_id=str(vehicle_one.id), hub_id=north.id, doc_type="Insurance Policy", document_url="https://placehold.co/400x500?text=" + vehicle_one.code + "+Insurance", status="Active", expiry_date=_now() + timedelta(days=180)),
            LogisticsDocument(entity_type="VEHICLE", entity_id=str(vehicle_one.id), hub_id=north.id, doc_type="Vehicle Registration", document_url="https://placehold.co/400x500?text=" + vehicle_one.code + "+Registration", status="Active", expiry_date=_now() + timedelta(days=300)),
            LogisticsDocument(entity_type="VEHICLE", entity_id=str(vehicle_two.id), hub_id=north.id, doc_type="Insurance Policy", document_url="https://placehold.co/400x500?text=" + vehicle_two.code + "+Insurance", status="Expiring Soon", expiry_date=_now() + timedelta(days=10)),
            # Driver Documents
            LogisticsDocument(entity_type="DRIVER", entity_id=str(driver_one.id), hub_id=north.id, doc_type="Commercial License (CDL)", document_url="https://placehold.co/400x500?text=" + driver_one.name.replace(" ", "+") + "+CDL", status="Active", expiry_date=_now() + timedelta(days=240)),
            LogisticsDocument(entity_type="DRIVER", entity_id=str(driver_two.id), hub_id=south.id, doc_type="Medical Certificate", document_url="https://placehold.co/400x500?text=" + driver_two.name.replace(" ", "+") + "+Medical", status="Pending Verification", expiry_date=_now() + timedelta(days=120)),
        ])
        await db.flush()

async def build_bootstrap(db: AsyncSession) -> LogisticsBootstrapResponse:
    await _reconcile_restock_escalations(db)
    warehouses = (await db.execute(select(Warehouse).order_by(Warehouse.created_at.asc()))).scalars().all()
    alerts = (await db.execute(select(LogisticsAlert).where(LogisticsAlert.is_active.is_(True)).order_by(LogisticsAlert.created_at.desc()))).scalars().all()
    # Bootstrap is LOGISTIC_MANAGER only — exclude per-user notifications (vendor/customer order events)
    notifications = (await db.execute(
        select(LogisticsNotification)
        .where(LogisticsNotification.target_user_id.is_(None))
        .order_by(LogisticsNotification.created_at.desc())
    )).scalars().all()
    tasks = (await db.execute(select(LogisticsTask).order_by(LogisticsTask.created_at.desc()))).scalars().all()
    driver_profiles = (await db.execute(select(LogisticsDriverProfile).order_by(LogisticsDriverProfile.created_at.asc()))).scalars().all()
    vehicles = (await db.execute(select(LogisticsVehicle).order_by(LogisticsVehicle.created_at.desc()))).scalars().all()
    transactions = (await db.execute(select(LogisticsTransaction).order_by(LogisticsTransaction.transaction_date.desc()))).scalars().all()
    zones = (await db.execute(select(LogisticsZone).order_by(LogisticsZone.created_at.desc()))).scalars().all()
    chat_threads = (await db.execute(select(LogisticsChatThread).order_by(LogisticsChatThread.created_at.desc()))).scalars().all()
    chat_messages = (await db.execute(select(LogisticsChatMessage).order_by(LogisticsChatMessage.created_at.asc()))).scalars().all()
    escalations = (await db.execute(select(LogisticsEscalation).order_by(LogisticsEscalation.created_at.desc()))).scalars().all()
    return_cases = (await db.execute(select(LogisticsReturnCase).order_by(LogisticsReturnCase.created_at.desc()))).scalars().all()
    return_gradings = (
        await db.execute(
            select(ReturnGrading)
            .options(selectinload(ReturnGrading.grader))
            .order_by(ReturnGrading.created_at.desc())
        )
    ).scalars().all()
    _all_users = (await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    _all_orders = (await db.execute(select(Order))).scalars().all()

    # Backfill: auto-create LogisticsReturnCase for any DamageReport not yet linked
    existing_ref_codes = {rc.reference_code for rc in return_cases}
    damage_reports = (await db.execute(select(DamageReport).order_by(DamageReport.created_at.desc()))).scalars().all()
    order_map = {o.id: o for o in _all_orders}
    user_map = {u.id: u for u in _all_users}
    new_cases = []
    for dr in damage_reports:
        if dr.reference_code not in existing_ref_codes:
            order_row = order_map.get(dr.order_id) if dr.order_id else None
            order_total = (order_row.total_amount or 0.0) if order_row else 0.0
            warehouse_id = order_row.warehouse_id if order_row else None
            user_row = user_map.get(dr.customer_id)
            customer_name = (user_row.name or user_row.email or str(dr.customer_id)) if user_row else str(dr.customer_id)
            new_case = LogisticsReturnCase(
                warehouse_id=warehouse_id,
                order_id=dr.order_id,
                reference_code=dr.reference_code,
                customer_name=customer_name,
                reason=(dr.description or "Damage reported")[:255],
                flow_type=getattr(dr, "flow_type", "photo_review") or "photo_review",
                condition="Reported",
                status="Pickup Requested" if (getattr(dr, "flow_type", "photo_review") == "pickup_inspection") else "Reported",
                original_price=order_total,
                refund_amount=0.0,
                images=dr.photos or [],
            )
            db.add(new_case)
            new_cases.append(new_case)

    # Backfill: warehouse/driver-side returns may create ReturnGrading records without
    # a LogisticsReturnCase entry. Surface them in Reverse Logistics so LM can still
    # see "Arrived at Warehouse" / "Physically Inspected" states.
    for grading in return_gradings:
        if not grading.rma_code or grading.rma_code in existing_ref_codes:
            continue

        order_row = order_map.get(grading.order_id) if grading.order_id else None
        user_row = user_map.get(order_row.customer_id) if order_row and order_row.customer_id else None
        customer_name = (
            user_row.name or user_row.email
            if user_row
            else (f"Order {order_row.tracking_code}" if order_row else "Warehouse Return")
        )

        if grading.status == "completed":
            derived_status = "Physically Inspected"
        elif grading.item_condition == "Awaiting Pickup":
            derived_status = "Pickup Scheduled"
        else:
            derived_status = "Arrived at Warehouse"

        new_case = LogisticsReturnCase(
            warehouse_id=grading.warehouse_id or (order_row.warehouse_id if order_row else None),
            order_id=grading.order_id,
            reference_code=grading.rma_code,
            customer_name=customer_name,
            reason=grading.condition_notes or "Warehouse return",
            flow_type="pickup_inspection",
            condition=grading.item_condition or "Pending Inspection",
            status=derived_status,
            original_price=(order_row.total_amount or 0.0) if order_row else 0.0,
            refund_amount=0.0,
            images=[],
        )
        db.add(new_case)
        new_cases.append(new_case)
        existing_ref_codes.add(grading.rma_code)

    if new_cases:
        await db.flush()
        return_cases = list(new_cases) + list(return_cases)

    # Build set of reference codes that already have a DAMAGE_REFUND wallet transaction.
    from app.models.wallet import WalletTransaction
    _credited_ref_codes: set[str] = set()
    _reference_codes = {item.reference_code for item in return_cases if item.reference_code}
    if _reference_codes:
        _dmg_txns = (await db.execute(
            select(WalletTransaction.description).where(WalletTransaction.reason == "DAMAGE_REFUND")
        )).scalars().all()
        for _desc in _dmg_txns:
            description = _desc or ""
            for reference_code in _reference_codes:
                if reference_code in description:
                    _credited_ref_codes.add(reference_code)

    latest_completed_grading_by_rma: dict[str, ReturnGrading] = {}
    latest_completed_grading_by_order_id: dict[UUID, ReturnGrading] = {}
    for grading in return_gradings:
        if grading.status != "completed":
            continue
        if grading.rma_code and grading.rma_code not in latest_completed_grading_by_rma:
            latest_completed_grading_by_rma[grading.rma_code] = grading
        if grading.order_id and grading.order_id not in latest_completed_grading_by_order_id:
            latest_completed_grading_by_order_id[grading.order_id] = grading

    def _wm_completed_grading_for_case(item: LogisticsReturnCase) -> ReturnGrading | None:
        if item.reference_code and item.reference_code in latest_completed_grading_by_rma:
            return latest_completed_grading_by_rma[item.reference_code]
        if item.order_id and item.order_id in latest_completed_grading_by_order_id:
            return latest_completed_grading_by_order_id[item.order_id]
        return None

    def _to_return_case_item(item: LogisticsReturnCase) -> LogisticsReturnCaseItem:
        completed_grading = _wm_completed_grading_for_case(item)
        is_physical_flow = getattr(item, "flow_type", None) == "pickup_inspection"
        normalized_status = item.status
        case_images = list(item.images or [])
        if completed_grading and completed_grading.damage_photo_url and completed_grading.damage_photo_url not in case_images:
            case_images.append(completed_grading.damage_photo_url)
        if not is_physical_flow and item.status in {"Inspected", "Physically Inspected"}:
            normalized_status = "Claims Reviewed"
        display_status = normalized_status
        if completed_grading and is_physical_flow and normalized_status in {"Arrived at Warehouse", "At Warehouse", "Inspected", "Physically Inspected"}:
            display_status = "Physically Inspected"
        return LogisticsReturnCaseItem(
            id=item.id,
            hub_id=item.warehouse_id,
            order_id=item.order_id,
            customer=item.customer_name,
            reason=item.reason,
            flow_type=getattr(item, "flow_type", None),
            condition=completed_grading.item_condition if (completed_grading and is_physical_flow) else item.condition,
            status=display_status,
            original_price=item.original_price,
            refund_amount=item.refund_amount,
            images=case_images,
            reference_code=item.reference_code,
            wallet_credited=item.reference_code in _credited_ref_codes,
            wm_disposition=completed_grading.disposition if (completed_grading and is_physical_flow) else None,
            wm_is_genuine=completed_grading.is_genuine if (completed_grading and is_physical_flow) else getattr(item, "wm_is_genuine", None),
            wm_recommended_outcome=completed_grading.recommended_outcome if (completed_grading and is_physical_flow) else getattr(item, "wm_recommended_outcome", None),
            wm_inspection_remarks=completed_grading.inspection_remarks if (completed_grading and is_physical_flow) else getattr(item, "wm_inspection_remarks", None),
            wm_graded_at=completed_grading.graded_at if (completed_grading and is_physical_flow) else None,
            wm_grader_name=completed_grading.grader.name if (completed_grading and is_physical_flow and completed_grading.grader) else None,
            transport_charge_amount=round(float(item.transport_charge_amount or 0.0), 2),
            transport_charge_wallet_collected=round(float(item.transport_charge_wallet_collected or 0.0), 2),
            transport_charge_pending_amount=round(float(item.transport_charge_pending_amount or 0.0), 2),
            transport_charge_status=item.transport_charge_status,
            transport_charge_applied_at=item.transport_charge_applied_at,
            is_urgent=bool(getattr(item, "is_urgent", False)),
            urgent_reason=getattr(item, "urgent_reason", None),
        )

    inventory_items = (await db.execute(select(InventoryItem).order_by(InventoryItem.created_at.desc()))).scalars().all()
    users = _all_users
    roles = (await db.execute(select(Role))).scalars().all()
    orders = _all_orders
    metrics = (await db.execute(select(LogisticsMetric).order_by(LogisticsMetric.created_at.asc()))).scalars().all()
    equipments = (await db.execute(select(LogisticsEquipmentLedger).order_by(LogisticsEquipmentLedger.created_at.desc()))).scalars().all()
    documents = (await db.execute(select(LogisticsDocument).order_by(LogisticsDocument.created_at.desc()))).scalars().all()

    role_by_id = {role.id: role.name for role in roles}
    user_map = {user.id: user for user in users}
    warehouse_map = {warehouse.id: warehouse for warehouse in warehouses}
    vehicle_map = {vehicle.id: vehicle for vehicle in vehicles}
    vehicle_by_driver = {vehicle.assigned_driver_id: vehicle for vehicle in vehicles if vehicle.assigned_driver_id}
    # For vehicles without a permanent driver assignment, resolve driver from active orders
    active_driver_by_vehicle: dict = {
        o.assigned_vehicle_id: o.assigned_driver_id
        for o in orders
        if o.status in {"ASSIGNED", "IN_TRANSIT"} and o.assigned_vehicle_id and o.assigned_driver_id
    }
    messages_by_thread: dict[UUID, list[LogisticsChatMessage]] = {}
    for message in chat_messages:
        messages_by_thread.setdefault(message.thread_id, []).append(message)

    today = _now().date()
    orders_today = sum(1 for order in orders if order.created_at.date() == today)
    active_deliveries = sum(1 for order in orders if order.status == "IN_TRANSIT")
    processing = sum(1 for order in orders if order.status in {"DRAFT", "CONFIRMED", "ASSIGNED"})
    delivered = sum(1 for order in orders if order.status in {"DELIVERED", "CLOSED"})
    delivery_success = round((delivered / len(orders)) * 100, 1) if orders else 100.0

    # Build 7-day chart arrays live from Orders table (avoids empty LogisticsDailyStats)
    week_start = today - timedelta(days=6)

    # Try LogisticsDailyStats first; fall back to live aggregation
    historical_stats = (
        await db.execute(
            select(LogisticsDailyStats)
            .where(LogisticsDailyStats.warehouse_id.is_(None))
            .where(LogisticsDailyStats.stat_date >= week_start)
            .where(LogisticsDailyStats.stat_date <= today)
            .order_by(LogisticsDailyStats.stat_date.asc())
        )
    ).scalars().all()

    if historical_stats:
        sla_week = [int(stat.sla_compliance) for stat in historical_stats[-7:]]
        revenue_week = [float(stat.revenue) for stat in historical_stats[-7:]]
        orders_week = [stat.orders_count for stat in historical_stats[-7:]]
        while len(sla_week) < 7:
            sla_week.insert(0, 0)
        while len(revenue_week) < 7:
            revenue_week.insert(0, 0)
        while len(orders_week) < 7:
            orders_week.insert(0, 0)
    else:
        # Live aggregation from Orders table for the past 7 days
        from collections import defaultdict
        daily_total: dict = defaultdict(int)
        daily_delivered: dict = defaultdict(int)
        daily_revenue: dict = defaultdict(float)

        for order in orders:
            if not order.created_at:
                continue
            d = order.created_at.date()
            if d < week_start:
                continue
            daily_total[d] += 1
            if order.status in {"DELIVERED", "CLOSED", "COMPLETED"}:
                daily_delivered[d] += 1
            daily_revenue[d] += float(order.total_amount or 0)

        sla_week = []
        revenue_week = []
        orders_week = []
        for offset in range(6, -1, -1):
            d = today - timedelta(days=offset)
            total_d = daily_total[d]
            delivered_d = daily_delivered[d]
            sla_pct = round((delivered_d / total_d) * 100) if total_d > 0 else (
                int(delivery_success)  # use overall rate for days with no orders
            )
            sla_week.append(sla_pct)
            revenue_week.append(round(daily_revenue[d], 2))
            orders_week.append(total_d)

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

    dashboard_stats = LogisticsDashboardStats(
        orders_today=orders_today,
        active_deliveries=active_deliveries,
        processing=processing,
        delivery_success=delivery_success,
        revenue_today=round(revenue_today, 2),
        orders_trend=round((orders_today / max(len(orders), 1)) * 100, 1),
        revenue_trend=revenue_trend,
        sla_week=sla_week[-7:],
        revenue_week=revenue_week[-7:],
        orders_week=orders_week[-7:],
    )

    total_revenue = float(finance_summary.get("total_revenue", 0.0) or 0.0)
    total_expenses = float(finance_summary.get("total_expenses", 0.0) or 0.0)
    total_pending_cod = float(finance_summary.get("pending_cod", 0.0) or 0.0)

    # ── Per-driver order stats computed from real order data ──
    driver_order_counts: dict = {}       # total non-draft orders
    driver_delivered_counts: dict = {}   # delivered orders
    driver_cancelled_counts: dict = {}   # cancelled orders
    driver_rating_sums: dict = {}        # sum of customer_rating values
    driver_rating_counts: dict = {}      # count of orders with customer_rating
    for order in orders:
        if not order.assigned_driver_id:
            continue
        key = str(order.assigned_driver_id)
        if order.status == "DRAFT":
            continue
        driver_order_counts[key] = driver_order_counts.get(key, 0) + 1
        if order.status == "DELIVERED":
            driver_delivered_counts[key] = driver_delivered_counts.get(key, 0) + 1
        if order.status == "CANCELLED":
            driver_cancelled_counts[key] = driver_cancelled_counts.get(key, 0) + 1
        if order.customer_rating is not None:
            driver_rating_sums[key] = driver_rating_sums.get(key, 0) + order.customer_rating
            driver_rating_counts[key] = driver_rating_counts.get(key, 0) + 1

    # EXPENSE_DRIVER rows in LogisticsTransaction sum gives total earned per driver session
    expense_driver_rows = [tx for tx in transactions if tx.transaction_type == "EXPENSE_DRIVER"]
    expense_labour_rows = [tx for tx in transactions if tx.transaction_type == "EXPENSE_LABOUR"]
    total_driver_expense_booked = abs(sum(tx.amount for tx in expense_driver_rows))
    total_labour_expense_booked = abs(sum(tx.amount for tx in expense_labour_rows))

    hubs = []
    for index, warehouse in enumerate(warehouses, start=1):
        hub_users = [user for user in users if user.warehouse_id == warehouse.id]
        hub_orders = [order for order in orders if order.warehouse_id == warehouse.id]
        hub_vehicles = [vehicle for vehicle in vehicles if vehicle.warehouse_id == warehouse.id]
        capacity = int((len(hub_orders) / max(warehouse.capacity_limit or 10, 10)) * 100)
        computed_status = "Optimal" if capacity < 70 else ("High Load" if capacity < 90 else "Congested")
        status = "Archived" if not warehouse.is_active else (warehouse.hub_status if warehouse.hub_status else computed_status)
        efficiency = min(99, max(72, 82 + len(hub_orders) * 3))
        fallback_manager = next(
            (
                user
                for user in hub_users
                if role_by_id.get(user.role_id) == "WAREHOUSE_MANAGER" and user.is_active
            ),
            None,
        )
        manager_name = (
            user_map.get(warehouse.manager_id).name
            if warehouse.manager_id in user_map
            else (fallback_manager.name if fallback_manager else "Unassigned")
        )
        hubs.append(
            LogisticsHubItem(
                id=warehouse.id,
                hub_code=f"HUB-{index:02d}",
                name=warehouse.name,
                location=warehouse.address,
                address=warehouse.address,
                lat=warehouse.lat,
                lng=warehouse.lng,
                manager=manager_name,
                manager_initials="".join(part[0] for part in manager_name.split()[:2]).upper() if manager_name else "UN",
                capacity=capacity,
                efficiency=efficiency,
                staff_active=sum(1 for user in hub_users if user.is_active),
                staff_total=len(hub_users),
                vehicles_active=sum(1 for vehicle in hub_vehicles if vehicle.status == "Active"),
                vehicles_total=len(hub_vehicles),
                process_rate=len(hub_orders) * 120,
                status=status,
                status_color="text-slate-500" if status == "Archived" else ("text-green-500" if status == "Optimal" else ("text-yellow-500" if status == "High Load" else "text-red-500")),
                bg="bg-slate-500" if status == "Archived" else ("bg-green-500" if status == "Optimal" else ("bg-yellow-500" if status == "High Load" else "bg-red-500")),
            )
        )

    # Build per-driver order and alert counts for dynamic scorecard stats
    driver_alert_counts: dict = {}
    for alert in alerts:
        # Alerts that name a driver by name (best-effort)
        for profile in driver_profiles:
            u = user_map.get(profile.user_id)
            if u and u.name and u.name.lower() in (alert.location or "").lower():
                driver_alert_counts[str(u.id)] = driver_alert_counts.get(str(u.id), 0) + 1

    drivers = []
    for profile in driver_profiles:
        user = user_map.get(profile.user_id)
        if not user:
            continue
        assigned_vehicle = vehicle_by_driver.get(user.id)
        uid_str = str(user.id)
        # Rating: avg of customer_rating from delivered orders; 0.0 if none yet
        r_count = driver_rating_counts.get(uid_str, 0)
        driver_rating = round(driver_rating_sums.get(uid_str, 0) / r_count, 1) if r_count else 0.0
        # Efficiency: delivery completion rate from real orders; fall back to stored score
        total_trips = driver_order_counts.get(uid_str, 0)
        delivered_trips = driver_delivered_counts.get(uid_str, 0)
        driver_efficiency = round((delivered_trips / total_trips) * 100) if total_trips else profile.efficiency_score
        # Safety incidents: alert count mentioning this driver
        driver_incidents = driver_alert_counts.get(uid_str, 0)
        # Fuel efficiency: from assigned vehicle or a computed estimate
        if assigned_vehicle and assigned_vehicle.fuel_efficiency:
            fuel_eff = str(assigned_vehicle.fuel_efficiency)
        else:
            mpg = round(6.0 + (driver_efficiency / 100) * 6, 1)
            fuel_eff = f"{mpg} km/l"
        # Average speed: estimate from trips
        avg_spd = f"{min(75, max(35, 40 + total_trips * 2))} km/h"
        drivers.append(
            LogisticsDriverItem(
                id=user.id,
                hub_id=profile.warehouse_id,
                name=user.name,
                status=profile.status,
                location=profile.current_location,
                vehicle=assigned_vehicle.code if assigned_vehicle else None,
                efficiency=driver_efficiency,
                rating=driver_rating,
                safety_incidents=driver_incidents,
                fuel_efficiency_score=fuel_eff,
                avg_speed=avg_spd,
                phone=user.phone,
                current_job=profile.current_job,
                avatar_color=profile.avatar_color,
                chat_history=profile.chat_history or [],
            )
        )

    vehicles_payload = [
        LogisticsVehicleItem(
            id=vehicle.id,
            hub_id=vehicle.warehouse_id,
            code=vehicle.code,
            type=vehicle.vehicle_type,
            model=vehicle.model,
            year=vehicle.year,
            license_plate=vehicle.license_plate,
            status=vehicle.status,
            driver=(
                user_map[vehicle.assigned_driver_id].name if vehicle.assigned_driver_id in user_map
                else user_map[active_driver_by_vehicle[vehicle.id]].name if vehicle.id in active_driver_by_vehicle and active_driver_by_vehicle[vehicle.id] in user_map
                else "Unassigned"
            ),
            fuel_efficiency=vehicle.fuel_efficiency,
            mileage=vehicle.mileage,
            next_service=vehicle.next_service_date.strftime("%b %d, %Y") if vehicle.next_service_date else None,
            maintenance_issue=vehicle.maintenance_issue,
        )
        for vehicle in vehicles
    ]

    ai_suggestion_chips = [
        "Show dashboard overview",
        "Driver status report",
        "Fleet & vehicle status",
        "Check inventory levels",
        "Returns & RMA summary",
        "Revenue forecast",
        "Hub performance",
        "What can you help with?",
    ]
    busiest_hub = max(hubs, key=lambda hub: hub.process_rate, default=None)
    # Generate friendly welcome message
    greeting_options = [
        "Hey! Welcome to your Cargo-Core AI Intelligence hub!",
        "Hello! Ready to optimize your logistics operations today!",
        "Hi there! Your AI assistant is online and ready to help!",
    ]
    import random
    greeting = random.choice(greeting_options)

    if len(alerts) > 0:
        alert_msg = f"I've spotted <b>{len(alerts)} alert(s)</b> that need your attention."
    else:
        alert_msg = "Everything's running smoothly - <b>no alerts</b> to worry about!"

    hub_msg = f"<b>{busiest_hub.name}</b> is your top performer right now" if busiest_hub else "Your network is ready to go"

    ai_messages = [{
        "role": "ai",
        "text": f"{greeting} {hub_msg}. {alert_msg} Ask me anything about your drivers, fleet, orders, or operations!",
        "time": _now().strftime("%I:%M %p"),
        "data": {
            "active_alerts": len(alerts),
            "active_deliveries": active_deliveries,
            "pending_cod": f"${total_pending_cod:,.0f}",
            "top_hub": busiest_hub.name if busiest_hub else "N/A",
        },
    }]

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

    fleet_logs = {
        "Fuel Logs": [
            {
                "id": f"FUEL-{index + 1:03d}",
                "date": tx.transaction_date.strftime("%b %d, %Y"),
                "vehicleId": next((vehicle.code for vehicle in vehicles if vehicle.warehouse_id == tx.warehouse_id), "NA"),
                "hubId": str(tx.warehouse_id) if tx.warehouse_id else "all",
                "station": "Network Fuel Partner",
                "gallons": max(12, round(abs(tx.amount) / 4.25, 1)),
                "cost": abs(tx.amount),
                "alert": abs(tx.amount) > 3000,
                "status": tx.status,
            }
            for index, tx in enumerate([item for item in transactions if item.transaction_type in {"Expense", "Payroll"}][:5])
        ],
        "Service Logs": [
            {
                "id": f"SRV-{index + 1:03d}",
                "date": vehicle.next_service or _now().strftime("%b %d, %Y"),
                "vehicleId": vehicle.code,
                "hubId": str(vehicle.hub_id) if vehicle.hub_id else "all",
                "service": vehicle.maintenance_issue or "Preventive service",
                "provider": "CargoCore Workshop",
                "cost": 180 + index * 60,
                "status": "Scheduled" if vehicle.status != "Active" else "Completed",
            }
            for index, vehicle in enumerate(vehicles_payload[:5])
        ],
        "Maintenance Logs": [
            {
                "id": f"MTN-{index + 1:03d}",
                "date": vehicle.next_service or _now().strftime("%b %d, %Y"),
                "vehicleId": vehicle.code,
                "hubId": str(vehicle.hub_id) if vehicle.hub_id else "all",
                "issue": vehicle.maintenance_issue or "General inspection",
                "mechanic": "Internal Team",
                "cost": 240 + index * 90,
                "status": "Pending" if vehicle.status != "Active" else "Resolved",
            }
            for index, vehicle in enumerate(vehicles_payload[:5])
        ],
        "Cleaning Logs": [
            {
                "id": f"CLN-{index + 1:03d}",
                "date": _fmt_relative(_now() - timedelta(days=index + 1)),
                "vehicleId": vehicle.code,
                "hubId": str(vehicle.hub_id) if vehicle.hub_id else "all",
                "type": "Exterior Wash" if index % 2 == 0 else "Full Detail",
                "provider": "Fleet Care",
                "cost": 40 + index * 20,
                "status": "Completed",
            }
            for index, vehicle in enumerate(vehicles_payload[:5])
        ],
    }

    vehicle_documents = [
        {
            "id": str(doc.id),
            "vehicleId": doc.entity_id,
            "vehicleCode": vehicle_map[UUID(doc.entity_id)].code if doc.entity_id.replace('-', '') in [str(k).replace('-', '') for k in vehicle_map] else "N/A",
            "hubId": str(doc.hub_id) if doc.hub_id else "all",
            "type": doc.doc_type,
            "status": doc.status,
            "expiry": doc.expiry_date.strftime("%b %d, %Y") if doc.expiry_date else "N/A",
            "lastRenewed": doc.created_at.strftime("%b %d, %Y"),
            "url": doc.document_url,
            "notes": doc.notes,
        }
        for doc in documents if doc.entity_type == "VEHICLE"
    ]

    driver_documents = [
        {
            "id": str(doc.id),
            "driver": user_map[UUID(doc.entity_id)].name if doc.entity_id.replace('-', '') in [str(k).replace('-', '') for k in user_map.keys()] else "Unknown",
            "driverId": doc.entity_id,
            "hubId": str(doc.hub_id) if doc.hub_id else "all",
            "type": doc.doc_type,
            "licenseNo": f"DOC-{str(doc.id)[:4].upper()}",
            "status": doc.status,
            "expiry": doc.expiry_date.strftime("%b %d, %Y") if doc.expiry_date else "N/A",
            "joined": doc.created_at.strftime("%b %d, %Y"),
            "url": doc.document_url,
            "notes": doc.notes,
        }
        for doc in documents if doc.entity_type == "DRIVER"
    ]

    report_ai_insights = []
    report_damage_claims = [
        {
            "title": case.reference_code,
            "reporter": case.customer_name,
            "time": _fmt_relative(case.created_at),
            "status": case.status,
            "image": case.images[0] if case.images else "",
            "reason": case.reason,
        }
        for case in return_cases
    ]
    report_security_logs = [
        {
            "time": _fmt_relative(notification.created_at),
            "actor": "system_bot",
            "action": "READ_NOTIFICATION" if notification.is_read else "NEW_NOTIFICATION",
            "target": notification.title,
            "details": notification.message,
            "ip": f"10.0.0.{20 + index}",
        }
        for index, notification in enumerate(notifications[:6], start=1)
    ]
    report_metrics = {
        "payment_reconciliation": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "expected_digital": [max(total_revenue * ratio, 1000) for ratio in (0.10, 0.12, 0.15, 0.13, 0.18)],
            "actual_digital": [max(total_revenue * ratio, 900) for ratio in (0.09, 0.11, 0.145, 0.125, 0.17)],
            "expected_cod": [max(total_pending_cod * ratio, 300) for ratio in (0.20, 0.18, 0.22, 0.17, 0.23)],
            "actual_cod": [max(total_pending_cod * ratio, 250) for ratio in (0.16, 0.15, 0.20, 0.14, 0.21)],
        },
        "fuel_audit": {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "fuel_expense": [total_expenses * ratio for ratio in (0.20, 0.24, 0.19, 0.27)],
            "gps_mileage": [max(sum(vehicle.mileage for vehicle in vehicles) * ratio / 100, 1000) for ratio in (0.18, 0.21, 0.19, 0.22)],
        },
        "workforce": {
            "labels": ["In-Warehouse", "On-Field", "Off-Duty"],
            "values": [
                len([user for user in users if role_by_id.get(user.role_id) in {"WAREHOUSE_MANAGER", "DISPATCHER"}]),
                len([user for user in users if role_by_id.get(user.role_id) == "DRIVER"]),
                max(1, len(users) // 4),
            ],
        },
        "vendor_lead_time": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "values": [
                round(max(1.5, 3.5 - (len(orders) * 0.01)), 1),
                round(max(1.2, 3.2 - (len(orders) * 0.01)), 1),
                round(max(1.8, 3.8 - (len(orders) * 0.01)), 1),
                round(max(1.4, 3.4 - (len(orders) * 0.01)), 1),
                round(max(1.1, 3.1 - (len(orders) * 0.01)), 1),
                round(max(1.0, 2.9 - (len(orders) * 0.01)), 1),
            ],
        },
        "safety_incidents": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "values": [
                max(0, len(alerts) - 2), len(alerts),
                max(0, len(alerts) - 1), len(alerts) + 1,
                max(0, len(alerts) - 1), len(alerts),
            ],
        },
        "shift_efficiency": {
            "labels": ["Shift A", "Shift B", "Shift C"],
            "efficiency": [
                min(97, max(70, int(delivery_success) + 5)),
                min(95, max(65, int(delivery_success))),
                min(92, max(60, int(delivery_success) - 5)),
            ],
            "overtime": [
                max(0, len(orders) // 10),
                max(0, len(orders) // 12),
                max(0, len(orders) // 8),
            ],
        },
        "dwell_time": {
            "labels": ["6am-9am", "9am-12pm", "12pm-3pm", "3pm-6pm", "6pm-9pm"],
            "values": [
                max(15, min(90, processing * 3)),
                max(20, min(120, processing * 4)),
                max(18, min(100, processing * 3 + 5)),
                max(22, min(110, processing * 4 - 5)),
                max(12, min(80, processing * 2)),
            ],
        },
        "rma_vs_orders": {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "orders": [
                # Real per-week order counts for the last 4 weeks
                sum(1 for o in orders if (today - o.created_at.date()).days in range(28, 21)),
                sum(1 for o in orders if (today - o.created_at.date()).days in range(21, 14)),
                sum(1 for o in orders if (today - o.created_at.date()).days in range(14, 7)),
                sum(1 for o in orders if (today - o.created_at.date()).days in range(7, 0)),
            ],
            "rma": [max(1, len(return_cases) - 1), len(return_cases), len(return_cases), len(return_cases) + 1],
        },
        "rma_reasons": {
            "labels": ["Damaged", "Wrong Item", "Late Delivery", "Changed Mind"],
            "values": [
                len([case for case in return_cases if "dam" in case.reason.lower()]),
                len([case for case in return_cases if "wrong" in case.reason.lower()]),
                len([case for case in return_cases if "late" in case.reason.lower()]),
                len([case for case in return_cases if "changed" in case.reason.lower()]),
            ],
        },
        "attendance": {
            "present": len([user for user in users if user.is_active]),
            "late": len(alerts),
            "absent": max(0, len(users) // 5 - 1),
        },
        "pending_dues": total_pending_cod,
    }

    for m in metrics:
        if m.metric_type == "vendor_lead_time":
            report_metrics["vendor_lead_time"]["labels"].append(m.label)
            report_metrics["vendor_lead_time"]["values"].append(m.value_main)
        elif m.metric_type == "safety_incidents":
            report_metrics["safety_incidents"]["labels"].append(m.label)
            report_metrics["safety_incidents"]["values"].append(m.value_main)
        elif m.metric_type == "shift_efficiency":
            report_metrics["shift_efficiency"]["labels"].append(m.label)
            report_metrics["shift_efficiency"]["efficiency"].append(m.value_main)
            report_metrics["shift_efficiency"]["overtime"].append(m.value_secondary or 0)
        elif m.metric_type == "dwell_time":
            report_metrics["dwell_time"]["labels"].append(m.label)
            report_metrics["dwell_time"]["values"].append(m.value_main)

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

    finance_summary = {
        **finance_summary,
        "total_payroll_due": round(sum(item["amount"] for item in finance_staff_records + finance_driver_records if item.get("status") == "Pending"), 2),
    }

    return LogisticsBootstrapResponse(
        dashboard_stats=dashboard_stats,
        hubs=hubs,
        alerts=[LogisticsAlertItem(id=alert.id, type=alert.alert_type, title=alert.title, description=alert.description, severity=alert.severity, icon=alert.icon, timestamp=alert.created_at.strftime("%I:%M %p"), location=alert.location, recommendation=alert.recommendation, impact=alert.impact_json) for alert in alerts],
        drivers=drivers,
        top_drivers=[
            {
                "id": str(driver.id),
                "hubId": driver.hub_id,
                "name": driver.name,
                "rating": driver.rating,
                "trips": driver_order_counts.get(str(driver.id), 0),
                "ontime": (
                    round(driver_delivered_counts.get(str(driver.id), 0) / driver_order_counts.get(str(driver.id), 1) * 100)
                    if driver_order_counts.get(str(driver.id), 0) > 0 else 0
                ),
                "avatar": f"https://i.pravatar.cc/150?u={driver.id}",
            }
            for driver in sorted(drivers, key=lambda item: driver_order_counts.get(str(item.id), 0), reverse=True)[:5]
        ],
        vehicles=vehicles_payload,
        maintenance=[LogisticsMaintenanceItem(id=vehicle.id, hub_id=vehicle.warehouse_id, issue=vehicle.maintenance_issue or "Scheduled Maintenance", status=vehicle.status, status_class=_status_badge_class(vehicle.status)) for vehicle in vehicles if vehicle.status != "Active"],
        transactions=[
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
        ],
        reports=[LogisticsReportItem(id=f"report-{index}", hub_id=hub.id, title=f"{hub.name} Performance Report", date=_fmt_relative(_now() - timedelta(days=index)), icon="analytics", color=color) for index, (hub, color) in enumerate(zip(hubs, ["blue", "green", "orange"]), start=1)],
        users=[LogisticsUserItem(id=user.id, hub_id=user.warehouse_id, name=user.name, email=user.email, role=role_by_id.get(user.role_id, ""), status="Active" if user.is_active else "Inactive", last_login=user.last_login.isoformat() if user.last_login else "", username=user.username, pending_payout=(
                    next((item["amount"] for item in finance_staff_records if item["userId"] == str(user.id) and item.get("status") == "Pending"), 0.0)
                    or next((item["amount"] for item in finance_driver_records if item["userId"] == str(user.id) and item.get("status") == "Pending"), 0.0)
                ), mobile=user.phone, mobile_verified=bool(user.phone), email_verified=True, avatar=f"https://i.pravatar.cc/150?u={user.id}", approval_status=user.approval_status, approval_note=user.approval_note, approval_reviewed_at=user.approval_reviewed_at, company_name=user.company_name, tax_id=user.tax_id, contact_person=user.contact_person, business_email=user.business_email, business_phone=user.business_phone, submitted_at=user.created_at) for user in users if role_by_id.get(user.role_id) != "INDIVIDUAL"],
        returns=[_to_return_case_item(item) for item in return_cases],
        zones=[LogisticsZoneItem(id=zone.id, hub_id=zone.warehouse_id, name=zone.name, type=zone.zone_type, radius=zone.radius_km, status=zone.status, color=zone.color_token, lat=zone.lat, lng=zone.lng) for zone in zones],
        chats=[LogisticsChatThreadItem(id=thread.id, hub_id=thread.warehouse_id, name=thread.name, time=_fmt_relative(thread.last_message_at), last_message=thread.last_message, status=thread.status, phone=thread.phone, muted=thread.muted, messages=[LogisticsChatMessageItem(id=message.id, text=message.text, sender=message.sender, time=message.created_at.strftime("%I:%M %p")) for message in messages_by_thread.get(thread.id, [])]) for thread in chat_threads],
        escalations=[_to_logistics_escalation_item(esc) for esc in escalations],
        inventory=[{"id": str(item.id), "name": item.name, "category": item.category or "General", "quantity": item.quantity_on_hand, "unit": item.unit, "threshold": item.safety_stock, "location": item.aisle or (warehouse_map.get(item.warehouse_id).name if warehouse_map.get(item.warehouse_id) else "Unknown"), "status": "Low Stock" if item.quantity_on_hand <= item.safety_stock else "Good", "hubId": item.warehouse_id, "sku": item.sku} for item in inventory_items],
        notifications=[LogisticsNotificationItem(id=item.id, title=item.title, message=item.message, time=_fmt_relative(item.created_at), created_at=item.created_at, read=item.is_read, type=item.type) for item in notifications],
        tasks=[LogisticsTaskItem(id=item.id, text=item.text, status=item.status, target_time=item.target_time, repeat=item.repeat_rule, created_at=item.created_at, last_alert_time=item.last_alert_time, silenced=item.silenced) for item in tasks],
        ai_suggestion_chips=ai_suggestion_chips,
        ai_messages=ai_messages,
        finance_summary=finance_summary,
        finance_cod_records=finance_cod_records,
        finance_staff_records=finance_staff_records,
        finance_driver_records=finance_driver_records,
        fleet_logs=fleet_logs,
        vehicle_documents=vehicle_documents,
        driver_documents=driver_documents,
        report_ai_insights=report_ai_insights,
        report_damage_claims=report_damage_claims,
        report_security_logs=report_security_logs,
        report_metrics=report_metrics,
        equipment_ledger=[LogisticsEquipmentItem(id=eq.id, hub_id=eq.warehouse_id, item_type=eq.item_type, issued_count=eq.issued_count, returned_count=eq.returned_count, reference_code=eq.reference_code, status=eq.status) for eq in equipments]
    )


async def update_escalation_status(
    db: AsyncSession,
    escalation_id: UUID,
    data: LogisticsEscalationStatusUpdate,
) -> LogisticsEscalationItem:
    escalation = (
        await db.execute(select(LogisticsEscalation).where(LogisticsEscalation.id == escalation_id))
    ).scalar_one_or_none()
    if escalation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")

    escalation.status = (data.status or "").strip().upper()
    db.add(escalation)
    await db.flush()
    await db.refresh(escalation)
    return _to_logistics_escalation_item(escalation)


async def answer_ai_query(db: AsyncSession, query: str) -> LogisticsAiQueryResponse:
    """
    AI-powered query handler for Logistic Manager.
    Provides comprehensive insights across all operational areas.
    """
    bootstrap = await build_bootstrap(db)
    lower_query = query.lower()

    # Greetings
    if any(keyword in lower_query for keyword in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy")):
        stats = bootstrap.dashboard_stats
        greetings = ["Hey there!", "Hello!", "Hi!", "Howdy!"]
        import random
        greeting = random.choice(greetings)
        return LogisticsAiQueryResponse(
            text=f"{greeting} Great to see you! I'm your Cargo-Core AI assistant. Right now you have <b>{stats.orders_today} orders</b> today and <b>{stats.active_deliveries}</b> active deliveries. What would you like to know about?",
            data={
                "orders_today": stats.orders_today,
                "active_deliveries": stats.active_deliveries,
                "open_alerts": len(bootstrap.alerts),
                "tip": "Try asking: 'How are my drivers doing?' or 'Show fleet status'",
            },
        )

    # Dashboard / Overview queries
    if any(keyword in lower_query for keyword in ("dashboard", "overview", "summary", "status", "today", "how are we doing", "what's happening")):
        stats = bootstrap.dashboard_stats
        greeting = "Great question! " if stats.delivery_success >= 90 else "Here's the scoop! "
        mood = "Things are looking solid today!" if stats.delivery_success >= 90 else "We've got some work to do, but nothing we can't handle!"
        return LogisticsAiQueryResponse(
            text=f"{greeting}You've got <b>{stats.orders_today} orders</b> rolling today with a <b>{stats.delivery_success}%</b> success rate. {stats.active_deliveries} deliveries are currently on the road. {mood}",
            data={
                "orders_today": stats.orders_today,
                "active_deliveries": stats.active_deliveries,
                "processing": stats.processing,
                "delivery_success": f"{stats.delivery_success}%",
                "revenue_today": f"${stats.revenue_today:,.0f}",
                "active_alerts": len(bootstrap.alerts),
            },
        )

    # Risk / Bottleneck queries
    if any(keyword in lower_query for keyword in ("risk", "bottleneck", "delay", "alert", "problem", "issue", "warning")):
        top_alert = bootstrap.alerts[0] if bootstrap.alerts else None
        if top_alert:
            text = f"Heads up! I spotted something worth watching: <b>{top_alert.title}</b>. Don't worry though, I've got a recommendation ready for you below!"
        else:
            text = "Awesome news! I've scanned everything and there are <b>no major issues</b> right now. Your operations are running smoothly!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "active_alerts": len(bootstrap.alerts),
                "highest_risk": top_alert.title if top_alert else "None - All Clear!",
                "affected_hub": top_alert.location if top_alert else "Network-wide stable",
                "recommendation": top_alert.recommendation if top_alert else "Keep up the great work!",
            },
        )

    # Driver queries
    if any(keyword in lower_query for keyword in ("driver", "drivers", "delivery personnel", "delivery staff")):
        active_drivers = [d for d in bootstrap.drivers if d.status == "active"]
        idle_drivers = [d for d in bootstrap.drivers if d.status == "idle"]
        issues = [d for d in bootstrap.drivers if d.status in ("breakdown", "deviation")]
        total = len(bootstrap.drivers)
        if total == 0:
            text = "Hmm, looks like we don't have any drivers registered yet. Want me to help you set some up?"
        elif len(issues) == 0:
            text = f"Your driver team is looking great! <b>{len(active_drivers)}</b> drivers are active and crushing it out there, with <b>{len(idle_drivers)}</b> ready for their next assignment."
        else:
            text = f"Quick driver update: <b>{len(active_drivers)}</b> are active, <b>{len(idle_drivers)}</b> are standing by, and <b>{len(issues)}</b> need some attention. Let's take care of those!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_drivers": total,
                "active": len(active_drivers),
                "idle": len(idle_drivers),
                "breakdown_deviation": len(issues),
                "avg_efficiency": f"{sum(d.efficiency_score for d in bootstrap.drivers) / max(total, 1):.0f}%" if bootstrap.drivers else "N/A",
            },
        )

    # Vehicle / Fleet queries
    if any(keyword in lower_query for keyword in ("vehicle", "vehicles", "fleet", "truck", "van", "maintenance")):
        active_vehicles = [v for v in bootstrap.vehicles if v.status == "Active"]
        in_shop = [v for v in bootstrap.vehicles if v.status == "In Shop"]
        scheduled = [v for v in bootstrap.vehicles if v.status == "Scheduled"]
        total = len(bootstrap.vehicles)
        if total == 0:
            text = "No vehicles in the system yet! Ready to add your first one?"
        elif len(in_shop) == 0 and len(scheduled) == 0:
            text = f"Your fleet is in top shape! All <b>{len(active_vehicles)} vehicles</b> are active and ready to roll. Nice work keeping them maintained!"
        else:
            text = f"Fleet check complete! <b>{len(active_vehicles)}</b> vehicles are road-ready, <b>{len(in_shop)}</b> are getting some TLC in the shop, and <b>{len(scheduled)}</b> have upcoming service."
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_vehicles": total,
                "active": len(active_vehicles),
                "in_maintenance": len(in_shop),
                "scheduled_service": len(scheduled),
                "vehicle_types": list(set(v.vehicle_type for v in bootstrap.vehicles)) if bootstrap.vehicles else [],
            },
        )

    # Order / Delivery queries
    if any(keyword in lower_query for keyword in ("order", "orders", "delivery", "deliveries", "shipment", "shipping")):
        stats = bootstrap.dashboard_stats
        mood = "Fantastic pace!" if stats.delivery_success >= 95 else ("Solid numbers!" if stats.delivery_success >= 85 else "Let's push for more!")
        return LogisticsAiQueryResponse(
            text=f"Here's your delivery pulse: <b>{stats.orders_today} orders</b> today with <b>{stats.active_deliveries}</b> packages en route. Success rate sitting at <b>{stats.delivery_success}%</b>. {mood}",
            data={
                "orders_today": stats.orders_today,
                "in_transit": stats.active_deliveries,
                "processing": stats.processing,
                "success_rate": f"{stats.delivery_success}%",
                "orders_trend": f"{'+' if stats.orders_trend > 0 else ''}{stats.orders_trend}%",
            },
        )

    # Returns / RMA queries
    if any(keyword in lower_query for keyword in ("return", "returns", "rma", "refund", "damaged")):
        pending_returns = [r for r in bootstrap.returns if r.status.lower() == "pending"]
        approved_returns = [r for r in bootstrap.returns if r.status.lower() == "approved"]
        total_refunds = sum(r.refund_amount for r in bootstrap.returns if r.refund_amount)
        if len(bootstrap.returns) == 0:
            text = "No returns to worry about right now! That's a good sign - customers are happy!"
        elif len(pending_returns) == 0:
            text = f"Returns are all caught up! <b>{len(approved_returns)}</b> cases have been processed. Great job staying on top of things!"
        else:
            text = f"RMA update: You've got <b>{len(pending_returns)}</b> returns waiting for your review out of <b>{len(bootstrap.returns)}</b> total. Let's get those taken care of!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_returns": len(bootstrap.returns),
                "pending_review": len(pending_returns),
                "approved": len(approved_returns),
                "total_refunds": f"${total_refunds:,.0f}",
            },
        )

    # Revenue / Finance queries
    if any(keyword in lower_query for keyword in ("revenue", "forecast", "financial", "finance", "money", "cash", "payment", "cod", "payroll")):
        revenue = bootstrap.finance_summary.get('total_revenue', 0)
        expenses = bootstrap.finance_summary.get('total_expenses', 0)
        net = revenue - expenses
        mood = "Looking profitable!" if net > 0 else "Let's work on improving those margins!"
        return LogisticsAiQueryResponse(
            text=f"Here's your financial snapshot! Revenue at <b>₹{revenue:,.0f}</b> with expenses of <b>₹{expenses:,.0f}</b>. Net position: <b>₹{net:,.0f}</b>. {mood}",
            data={
                "total_revenue": f"₹{revenue:,.0f}",
                "total_expenses": f"₹{expenses:,.0f}",
                "pending_cod": f"₹{bootstrap.finance_summary.get('pending_cod', 0):,.0f}",
                "payroll_due": f"₹{bootstrap.finance_summary.get('total_payroll_due', 0):,.0f}",
                "net_position": f"₹{net:,.0f}",
            },
        )

    # Hub / Warehouse queries
    if any(keyword in lower_query for keyword in ("hub", "hubs", "warehouse", "warehouses", "underperform", "efficiency")):
        if bootstrap.hubs:
            best_hub = max(bootstrap.hubs, key=lambda h: h.efficiency)
            worst_hub = min(bootstrap.hubs, key=lambda h: h.efficiency)
            return LogisticsAiQueryResponse(
                text=f"Hub performance check! Your star performer is <b>{best_hub.name}</b> crushing it at <b>{best_hub.efficiency}%</b> efficiency! <b>{worst_hub.name}</b> could use some love - sitting at {worst_hub.efficiency}%. Want me to dig deeper?",
                data={
                    "total_hubs": len(bootstrap.hubs),
                    "best_hub": best_hub.name,
                    "best_efficiency": f"{best_hub.efficiency}%",
                    "needs_attention": worst_hub.name,
                    "lowest_efficiency": f"{worst_hub.efficiency}%",
                },
            )
        return LogisticsAiQueryResponse(
            text="No hubs set up yet! Let's get your first warehouse configured to start tracking performance.",
            data={"total_hubs": 0},
        )

    # Inventory / Stock queries
    if any(keyword in lower_query for keyword in ("stock", "inventory", "supplies", "materials", "packing")):
        low_items = [item for item in bootstrap.inventory if "Low" in item.get("status", "")]
        total = len(bootstrap.inventory)
        if total == 0:
            text = "No inventory items tracked yet. Ready to add some supplies to monitor?"
        elif len(low_items) == 0:
            text = f"Inventory looking healthy! All <b>{total} items</b> are well-stocked. No reorders needed right now!"
        else:
            text = f"Heads up! <b>{len(low_items)} items</b> are running low and need restocking soon. I've listed the top ones below so you can take action!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_items": total,
                "low_stock_count": len(low_items),
                "low_stock_items": [item["name"] for item in low_items[:5]] if low_items else ["All stocked up!"],
                "status": "Action Required" if low_items else "All Good!",
            },
        )

    # Staff / Team queries
    if any(keyword in lower_query for keyword in ("staff", "team", "employee", "user", "workforce", "labor", "labourer")):
        users_by_role = {}
        for user in bootstrap.users:
            role = user.get("role", "Unknown")
            users_by_role[role] = users_by_role.get(role, 0) + 1
        total = len(bootstrap.users)
        active = len([u for u in bootstrap.users if u.get("is_active", True)])
        if total == 0:
            text = "No team members registered yet. Time to build your dream team!"
        else:
            text = f"Team check! You've got <b>{total} awesome people</b> on board, with <b>{active}</b> currently active. Here's the breakdown by role:"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_staff": total,
                "by_role": users_by_role if users_by_role else {"No roles": 0},
                "active": active,
            },
        )

    # Task queries
    if any(keyword in lower_query for keyword in ("task", "tasks", "todo", "pending", "action")):
        priority_tasks = [t for t in bootstrap.tasks if t.status == "Priority"]
        done_tasks = [t for t in bootstrap.tasks if t.status == "Done"]
        total = len(bootstrap.tasks)
        if total == 0:
            text = "No tasks on your plate right now! Enjoy the breather, or add something new to stay productive."
        elif len(priority_tasks) == 0:
            text = f"You're on top of things! <b>{len(done_tasks)}</b> tasks completed. No urgent items waiting!"
        else:
            text = f"Quick task update: <b>{len(priority_tasks)} priority items</b> need your attention. I've listed the top ones below - let's knock them out!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_tasks": total,
                "priority": len(priority_tasks),
                "completed": len(done_tasks),
                "priority_items": [t.text for t in priority_tasks[:3]] if priority_tasks else ["All caught up!"],
            },
        )

    # Escalation queries
    if any(keyword in lower_query for keyword in ("escalation", "escalations", "urgent", "critical", "approval")):
        open_escalations = [e for e in bootstrap.escalations if e.status == "OPEN"]
        high_priority = [e for e in open_escalations if e.priority == "High"]
        if len(open_escalations) == 0:
            text = "All clear on escalations! No pending approvals or urgent matters. Your team is handling things well!"
        elif len(high_priority) > 0:
            text = f"Attention needed! <b>{len(high_priority)} high-priority</b> escalations require your review. Let's get these resolved!"
        else:
            text = f"You have <b>{len(open_escalations)} open escalations</b> to review. None are critical, but let's not keep them waiting too long!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_open": len(open_escalations),
                "high_priority": len(high_priority),
                "titles": [e.title for e in open_escalations[:3]] if open_escalations else ["No escalations pending"],
            },
        )

    # Zone queries
    if any(keyword in lower_query for keyword in ("zone", "zones", "area", "coverage", "geofence")):
        active_zones = [z for z in bootstrap.zones if z.status == "Active"]
        alert_zones = [z for z in bootstrap.zones if z.status == "Alert"]
        total = len(bootstrap.zones)
        if total == 0:
            text = "No delivery zones configured yet. Set some up to better organize your coverage areas!"
        elif len(alert_zones) > 0:
            text = f"Zone check: <b>{len(alert_zones)} zones</b> are in alert status - might need some attention. {len(active_zones)} zones running smoothly!"
        else:
            text = f"All <b>{len(active_zones)} delivery zones</b> are active and running perfectly! Great coverage management!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_zones": total,
                "active": len(active_zones),
                "alert_status": len(alert_zones),
                "zone_types": list(set(z.zone_type for z in bootstrap.zones)) if bootstrap.zones else ["None configured"],
            },
        )

    # Notification queries
    if any(keyword in lower_query for keyword in ("notification", "notifications", "message", "unread")):
        unread = [n for n in bootstrap.notifications if not n.read]
        total = len(bootstrap.notifications)
        if total == 0:
            text = "Your notification inbox is empty! All caught up!"
        elif len(unread) == 0:
            text = f"You've read all <b>{total}</b> notifications! Nothing new waiting for you."
        else:
            text = f"You have <b>{len(unread)} unread</b> notifications out of {total} total. Here are the most recent ones:"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "unread": len(unread),
                "total": total,
                "recent": [n.title for n in bootstrap.notifications[:3]] if bootstrap.notifications else ["No notifications"],
            },
        )

    # Performance / SLA queries
    if any(keyword in lower_query for keyword in ("performance", "sla", "kpi", "metric", "trend")):
        stats = bootstrap.dashboard_stats
        avg_sla = sum(stats.sla_week) / len(stats.sla_week) if stats.sla_week else 0
        mood = "Outstanding work!" if avg_sla >= 95 else ("Solid performance!" if avg_sla >= 85 else "Room for improvement - let's strategize!")
        return LogisticsAiQueryResponse(
            text=f"Performance report: <b>{stats.delivery_success}%</b> delivery success with <b>{avg_sla:.1f}%</b> average SLA compliance this week. {mood}",
            data={
                "delivery_success": f"{stats.delivery_success}%",
                "avg_sla_week": f"{avg_sla:.1f}%",
                "sla_trend": stats.sla_week[-3:] if len(stats.sla_week) >= 3 else stats.sla_week,
                "orders_trend": f"{stats.orders_trend}%",
                "revenue_trend": f"{stats.revenue_trend}%",
            },
        )

    # Help / What can you do queries
    if any(keyword in lower_query for keyword in ("help", "what can you", "capabilities", "features", "how to")):
        return LogisticsAiQueryResponse(
            text="Hey there! I'm your Logistics AI assistant, and I'm here to make your life easier! Just ask me about <b>orders</b>, <b>drivers</b>, <b>vehicles</b>, <b>inventory</b>, <b>finances</b>, <b>returns</b>, or anything else logistics-related. I've got real-time insights ready for you!",
            data={
                "available_topics": [
                    "Dashboard & Overview",
                    "Drivers & Delivery Staff",
                    "Vehicles & Fleet",
                    "Orders & Deliveries",
                    "Returns & RMA",
                    "Finance & Revenue",
                    "Hubs & Warehouses",
                    "Inventory & Stock",
                    "Staff & Workforce",
                    "Tasks & To-dos",
                    "Escalations",
                    "Delivery Zones",
                    "Performance & SLA",
                ],
            },
        )

    # Default response with system overview
    return LogisticsAiQueryResponse(
        text="Hey! I didn't quite catch that, but no worries! Try asking me about <b>dashboard status</b>, <b>driver updates</b>, <b>fleet health</b>, <b>order tracking</b>, <b>inventory levels</b>, or <b>financial overview</b>. I'm here to help you stay on top of your logistics operations!",
        data={
            "active_hubs": len(bootstrap.hubs),
            "active_drivers": len(bootstrap.drivers),
            "total_vehicles": len(bootstrap.vehicles),
            "orders_today": bootstrap.dashboard_stats.orders_today,
            "open_returns": len([r for r in bootstrap.returns if r.status.lower() == "pending"]),
            "open_alerts": len(bootstrap.alerts),
        },
    )


async def list_vehicles(
    db: AsyncSession,
    warehouse_id: UUID | None = None,
    driver_id: UUID | None = None,
    driver_scoped: bool = False,
) -> list[LogisticsVehicleItem]:
    query = select(LogisticsVehicle).order_by(LogisticsVehicle.created_at.desc())
    if warehouse_id is not None:
        query = query.where(LogisticsVehicle.warehouse_id == warehouse_id)
    if driver_scoped and driver_id is not None:
        if warehouse_id is not None:
            query = query.where(
                or_(
                    LogisticsVehicle.assigned_driver_id == driver_id,
                    and_(
                        LogisticsVehicle.warehouse_id == warehouse_id,
                        or_(
                            LogisticsVehicle.assigned_driver_id.is_(None),
                            LogisticsVehicle.assigned_driver_id == driver_id,
                        ),
                    ),
                )
            )
        else:
            query = query.where(LogisticsVehicle.assigned_driver_id == driver_id)
    vehicles = (await db.execute(query)).scalars().all()
    # Collect all user IDs: from permanent assignments + from active orders
    active_orders = (await db.execute(
        select(Order).where(
            Order.status.in_(["ASSIGNED", "IN_TRANSIT"]),
            Order.assigned_vehicle_id.isnot(None),
            Order.assigned_driver_id.isnot(None),
        )
    )).scalars().all()
    active_driver_by_vehicle: dict = {
        o.assigned_vehicle_id: o.assigned_driver_id for o in active_orders
    }
    permanent_user_ids = [v.assigned_driver_id for v in vehicles if v.assigned_driver_id]
    active_user_ids = list(active_driver_by_vehicle.values())
    all_user_ids = list({uid for uid in permanent_user_ids + active_user_ids if uid})
    users = (await db.execute(select(User).where(User.id.in_(all_user_ids)))).scalars().all() if all_user_ids else []
    user_map = {u.id: u for u in users}
    items: list[LogisticsVehicleItem] = []
    for vehicle in vehicles:
        if vehicle.assigned_driver_id in user_map:
            driver_name = user_map[vehicle.assigned_driver_id].name
        elif vehicle.id in active_driver_by_vehicle and active_driver_by_vehicle[vehicle.id] in user_map:
            driver_name = user_map[active_driver_by_vehicle[vehicle.id]].name
        else:
            driver_name = "Unassigned"
        items.append(_build_vehicle_item(vehicle, driver_name=driver_name))
    return items


async def create_vehicle(db: AsyncSession, data: LogisticsVehicleCreate) -> LogisticsVehicleItem:
    vehicle = LogisticsVehicle(**data.model_dump())
    db.add(vehicle)
    await db.flush()
    bootstrap = await build_bootstrap(db)
    return next(item for item in bootstrap.vehicles if item.id == vehicle.id)


async def update_vehicle(db: AsyncSession, vehicle_id: UUID, data: LogisticsVehicleUpdate) -> LogisticsVehicleItem:
    vehicle = await _get_vehicle(db, vehicle_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, key, value)
    db.add(vehicle)
    await db.flush()
    bootstrap = await build_bootstrap(db)
    return next(item for item in bootstrap.vehicles if item.id == vehicle.id)


async def create_transaction(db: AsyncSession, data: LogisticsTransactionCreate) -> LogisticsTransactionItem:
    import uuid as _uuid
    tx = LogisticsTransaction(
        warehouse_id=data.warehouse_id,
        transaction_code=f"TX-{str(_uuid.uuid4()).replace('-', '').upper()[:12]}",
        description=data.description,
        transaction_type=data.transaction_type,
        amount=data.amount,
        status=data.status,
        metadata_json=data.metadata_json,
    )
    db.add(tx)
    await db.flush()
    return LogisticsTransactionItem(
        id=tx.id,
        hub_id=tx.warehouse_id,
        transaction_code=tx.transaction_code,
        date=tx.transaction_date.strftime("%b %d, %Y"),
        desc=tx.description,
        type=tx.transaction_type,
        amount=tx.amount,
        status=tx.status,
        metadata_json=dict(tx.metadata_json or {}),
        related_order=None,
    )


async def update_return_case(db: AsyncSession, case_id: UUID, data: LogisticsReturnCaseUpdate) -> LogisticsReturnCaseItem:
    case = await _get_return_case(db, case_id)
    case.status = data.status
    if data.refund_amount is not None:
        case.refund_amount = data.refund_amount
    if data.condition is not None:
        case.condition = data.condition
    db.add(case)

    # Sync DamageReport status so customer sees the outcome
    completed_grading = await _get_completed_return_grading(db, case)
    should_apply_transport_charge = (
        data.status == "Rejected"
        and (
            data.apply_transport_charge
            or (
                getattr(case, "flow_type", None) == "pickup_inspection"
                and completed_grading is not None
                and (
                    completed_grading.is_genuine is False
                    or (completed_grading.recommended_outcome or "").strip().lower() == "reject claim"
                )
            )
        )
    )

    if should_apply_transport_charge:
        from app.models.order import Order as OriginalOrder
        from app.services.return_charge_service import (
            apply_rejected_claim_transport_charge,
        )

        customer_id = None
        if case.order_id:
            original_order = (await db.execute(
                select(OriginalOrder).where(OriginalOrder.id == case.order_id)
            )).scalar_one_or_none()
            customer_id = getattr(original_order, "customer_id", None)
        if customer_id:
            await apply_rejected_claim_transport_charge(
                db,
                case=case,
                customer_id=customer_id,
            )

    if case.reference_code:
        damage_report = (await db.execute(
            select(DamageReport).where(DamageReport.reference_code == case.reference_code)
        )).scalar_one_or_none()
        if damage_report:
            if data.status == "Approved":
                damage_report.status = "resolved"
                # Credit customer wallet and debit finance revenue
                if case.refund_amount and case.refund_amount > 0:
                    from app.services.wallet_service import credit_return_refund
                    await credit_return_refund(
                        db,
                        customer_id=damage_report.customer_id,
                        order_id=case.order_id,
                        refund_amount=case.refund_amount,
                        reference_code=case.reference_code,
                            warehouse_id=case.warehouse_id,
                    )
            elif data.status == "Rejected":
                damage_report.status = "rejected"
            elif data.status == "Pending":
                damage_report.status = "inspected"
            db.add(damage_report)

    await db.flush()
    credited = await _wallet_refund_credited(db, case.reference_code)
    return await _build_return_case_item(
        db,
        case,
        completed_grading=completed_grading,
        wallet_credited=credited,
    )


async def issue_return_refund(db: AsyncSession, case_id: UUID) -> dict:
    case = await _get_return_case(db, case_id)
    if case.status not in {"Approved", "Partially Approved", "Refunded"}:
        raise HTTPException(status_code=400, detail="Return case is not approved for wallet refund")
    if not case.refund_amount or case.refund_amount <= 0:
        raise HTTPException(status_code=400, detail="No refund amount set on this return case")

    damage_report = None
    if case.reference_code:
        damage_report = (await db.execute(
            select(DamageReport).where(DamageReport.reference_code == case.reference_code)
        )).scalar_one_or_none()

    if not damage_report:
        raise HTTPException(status_code=400, detail="No linked customer damage report found — cannot determine wallet recipient")

    from app.services.wallet_service import credit_return_refund
    credited = await credit_return_refund(
        db,
        customer_id=damage_report.customer_id,
        order_id=case.order_id,
        refund_amount=case.refund_amount,
        reference_code=case.reference_code,
        warehouse_id=case.warehouse_id,
    )
    case.status = "Refunded"
    db.add(case)
    damage_report.status = "resolved"
    db.add(damage_report)
    await db.flush()
    return {
        "credited": credited,
        "amount": case.refund_amount,
        "reference_code": case.reference_code,
        "message": "Refund credited to customer wallet" if credited else "Refund was already issued",
    }


async def schedule_return_pickup(db: AsyncSession, case_id: UUID) -> LogisticsReturnCaseItem:
    """Schedule a driver pickup for an approved return case.

    Creates a PARCEL_PICKUP order so the dispatcher can assign a driver to
    collect the item from the customer and bring it back to the warehouse.
    The order's delivery_notes stores the case reference_code so the chain
    can be followed all the way through to the WM grading step.
    """
    case = await _get_return_case(db, case_id)
    if case.status not in ("Approved", "Pickup Approved", "Pickup Scheduled"):
        raise HTTPException(status_code=400, detail=f"Cannot schedule pickup: return case status is '{case.status}'")

    # Fetch original order and warehouse
    original_order = (await db.execute(select(Order).where(Order.id == case.order_id))).scalar_one_or_none() if case.order_id else None
    warehouse = (await db.execute(select(Warehouse).where(Warehouse.id == case.warehouse_id))).scalar_one_or_none() if case.warehouse_id else None

    # Create PARCEL_PICKUP order only when we have all required data.
    # If missing, skip the order (dispatcher can create it manually) but still
    # pre-create the ReturnGrading so WM sees the incoming item.
    if original_order and warehouse:
        short_ref = case.reference_code.replace("RMA-", "").replace("DMG-", "")[:8] if case.reference_code else case_id.hex[:8].upper()
        pickup_tracking = f"RTN-{short_ref}"

        existing_pickup = (await db.execute(select(Order).where(Order.tracking_code == pickup_tracking))).scalar_one_or_none()
        if existing_pickup:
            pickup_tracking = f"RTN-{short_ref}-{_now().strftime('%H%M')}"

        # Check again after timestamp suffix
        if not (await db.execute(select(Order).where(Order.tracking_code == pickup_tracking))).scalar_one_or_none():
            pickup_order = Order(
                tracking_code=pickup_tracking,
                order_type="PARCEL_PICKUP",
                status="CONFIRMED",
                customer_id=original_order.customer_id,
                warehouse_id=case.warehouse_id,
                pickup_addr=original_order.delivery_addr,
                delivery_addr=warehouse.address,
                delivery_lat=warehouse.lat,
                delivery_lng=warehouse.lng,
                cargo_type="Return Parcel",
                total_amount=0.0,
                payment_mode="INTERNAL",
                payment_status="paid",
                delivery_notes=case.reference_code,
            )
            db.add(pickup_order)

    # Pre-create a pending ReturnGrading so the Warehouse Manager sees the
    # incoming item in their queue immediately — before the driver even arrives.
    # The WM will see it as "Awaiting Pickup" until the driver drops it off.
    rma_code = case.reference_code or f"RMA-{pickup_tracking}"
    existing_grading = (await db.execute(
        select(ReturnGrading).where(ReturnGrading.rma_code == rma_code)
    )).scalar_one_or_none()
    if not existing_grading:
        grading = ReturnGrading(
            warehouse_id=case.warehouse_id,
            order_id=case.order_id,
            rma_code=rma_code,
            item_condition="Awaiting Pickup",
            condition_notes="Approved by Logistic Manager. Driver pickup scheduled.",
            disposition="pending",
            status="pending",
        )
        db.add(grading)

    case.flow_type = "pickup_inspection"
    case.status = "Pickup Scheduled"
    db.add(case)

    await db.flush()
    return await _build_return_case_item(db, case, wallet_credited=False)


async def create_zone(db: AsyncSession, data: LogisticsZoneCreate) -> LogisticsZoneItem:
    zone = LogisticsZone(**data.model_dump())
    db.add(zone)
    await db.flush()
    return LogisticsZoneItem(id=zone.id, hub_id=zone.warehouse_id, name=zone.name, type=zone.zone_type, radius=zone.radius_km, status=zone.status, color=zone.color_token, lat=zone.lat, lng=zone.lng)


async def list_zones(db: AsyncSession) -> list[LogisticsZoneItem]:
    zones = (
        await db.execute(select(LogisticsZone).order_by(LogisticsZone.created_at.desc()))
    ).scalars().all()
    return [
        LogisticsZoneItem(
            id=zone.id,
            hub_id=zone.warehouse_id,
            name=zone.name,
            type=zone.zone_type,
            radius=zone.radius_km,
            status=zone.status,
            color=zone.color_token,
            lat=zone.lat,
            lng=zone.lng,
        )
        for zone in zones
    ]


async def update_zone(db: AsyncSession, zone_id: UUID, data: LogisticsZoneUpdate) -> LogisticsZoneItem:
    zone = await _get_zone(db, zone_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(zone, key, value)
    db.add(zone)
    await db.flush()
    return LogisticsZoneItem(id=zone.id, hub_id=zone.warehouse_id, name=zone.name, type=zone.zone_type, radius=zone.radius_km, status=zone.status, color=zone.color_token, lat=zone.lat, lng=zone.lng)


async def delete_zone(db: AsyncSession, zone_id: UUID) -> MessageResponse:
    zone = await _get_zone(db, zone_id)
    await db.delete(zone)
    await db.flush()
    return MessageResponse(message="Zone deleted")


async def add_chat_message(db: AsyncSession, thread_id: UUID, data: LogisticsChatMessageCreate) -> LogisticsChatThreadItem:
    thread = await _get_chat_thread(db, thread_id)
    message = LogisticsChatMessage(thread_id=thread.id, sender=data.sender, text=data.text)
    db.add(message)
    thread.last_message = data.text
    thread.last_message_at = _now()
    db.add(thread)
    await db.flush()
    bootstrap = await build_bootstrap(db)
    return next(item for item in bootstrap.chats if item.id == thread.id)


_SUPPORTED_MEETING_TYPES = {"gmeet", "zoom", "jitsi", "other"}
_TIME_LABEL_RE = re.compile(r"^\d{2}:\d{2}$")


def _normalize_meeting_type(value: str | None) -> str:
    normalized = (value or "other").strip().lower()
    return normalized if normalized in _SUPPORTED_MEETING_TYPES else "other"


def _normalize_meeting_link(value: str | None) -> str:
    trimmed = (value or "").strip()
    if not trimmed:
        return ""
    if re.match(r"^https?://", trimmed, re.IGNORECASE):
        return trimmed
    if re.match(r"^(meet\.google\.com|meet\.jit\.si|[\w-]+\.zoom\.(us|com)|zoom\.us|zoom\.com)", trimmed, re.IGNORECASE):
        return f"https://{trimmed}"
    return trimmed


async def _create_daily_room(topic: str) -> str:
    settings = get_settings()
    if not settings.daily_api_key:
        raise HTTPException(status_code=500, detail="Daily.co API key not configured")

    slug = re.sub(r"[^a-z0-9-]", "", topic.lower().replace(" ", "-"))[:30].strip("-")
    import secrets
    room_name = f"logistics-{slug}-{secrets.token_hex(3)}"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://api.daily.co/v1/rooms",
            headers={"Authorization": f"Bearer {settings.daily_api_key}"},
            json={"name": room_name, "privacy": "public", "properties": {"enable_prejoin_ui": False}},
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="Failed to create Daily.co room")

    return resp.json()["url"]


def _validate_meeting_time_range(start_time: str, end_time: str) -> None:
    if not _TIME_LABEL_RE.match(start_time) or not _TIME_LABEL_RE.match(end_time):
        raise HTTPException(status_code=400, detail="Meeting time must use HH:MM format")
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="Meeting end time must be after start time")


async def _normalize_meeting_participants(
    db: AsyncSession,
    participant_ids: list[UUID] | None,
    creator_id: UUID,
) -> list[str]:
    candidate_ids: list[UUID] = []
    seen: set[str] = set()

    for raw_id in [*(participant_ids or []), creator_id]:
        normalized = str(raw_id)
        if normalized in seen:
            continue
        seen.add(normalized)
        candidate_ids.append(raw_id)

    if not candidate_ids:
        return [str(creator_id)]

    existing_ids = (
        await db.execute(select(User.id).where(User.id.in_(candidate_ids)))
    ).scalars().all()
    existing_lookup = {str(item) for item in existing_ids}

    normalized_ids = [str(item) for item in candidate_ids if str(item) in existing_lookup]
    if str(creator_id) not in normalized_ids:
        normalized_ids.append(str(creator_id))
    return normalized_ids


def _meeting_to_item(meeting: LogisticsMeeting) -> LogisticsMeetingItem:
    participants: list[UUID] = []
    for participant_id in meeting.participant_ids or []:
        try:
            participants.append(UUID(str(participant_id)))
        except (TypeError, ValueError):
            continue

    return LogisticsMeetingItem(
        id=meeting.id,
        topic=meeting.topic,
        description=meeting.description or "",
        meeting_type=_normalize_meeting_type(meeting.meeting_type),
        link=meeting.meeting_link,
        date=meeting.meeting_date,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        participants=participants,
        created_by_id=meeting.created_by_id,
        warehouse_id=meeting.warehouse_id,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


async def _get_meeting_for_user(db: AsyncSession, meeting_id: UUID, current_user: User) -> LogisticsMeeting:
    meeting = (
        await db.execute(
            select(LogisticsMeeting).where(
                LogisticsMeeting.id == meeting_id,
                or_(
                    LogisticsMeeting.created_by_id == current_user.id,
                    LogisticsMeeting.participant_ids.contains([str(current_user.id)]),
                ),
            )
        )
    ).scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


def _ensure_meeting_owner(meeting: LogisticsMeeting, current_user: User) -> None:
    if meeting.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the meeting creator can modify this meeting")


async def list_meetings(db: AsyncSession, current_user: User) -> list[LogisticsMeetingItem]:
    meetings = (
        await db.execute(
            select(LogisticsMeeting)
            .where(
                or_(
                    LogisticsMeeting.created_by_id == current_user.id,
                    LogisticsMeeting.participant_ids.contains([str(current_user.id)]),
                )
            )
            .order_by(LogisticsMeeting.meeting_date.asc(), LogisticsMeeting.start_time.asc(), LogisticsMeeting.created_at.asc())
        )
    ).scalars().all()
    return [_meeting_to_item(meeting) for meeting in meetings]


async def list_meeting_participants(db: AsyncSession, current_user: User) -> list[LogisticsMeetingParticipantItem]:
    query = (
        select(User)
        .options(selectinload(User.role))
        .where(User.is_active == True)
    )

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "LOGISTIC_MANAGER":
        query = query.where(User.role.has(Role.name.in_(["LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER"])))
    elif role_name in {"WAREHOUSE_MANAGER", "DISPATCHER"}:
        scoped_warehouse_id = current_user.warehouse_id
        query = query.where(
            or_(
                User.role.has(Role.name == "LOGISTIC_MANAGER"),
                and_(
                    User.warehouse_id == scoped_warehouse_id,
                    User.role.has(Role.name.in_(["WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER"])),
                ),
            )
        )

    users = (await db.execute(query.order_by(User.name.asc()))).scalars().all()

    return [
        LogisticsMeetingParticipantItem(
            id=user.id,
            name=user.name,
            role=user.role.name.replace("_", " ").title() if user.role else "User",
            hub_id=user.warehouse_id,
        )
        for user in users
    ]


async def create_meeting(db: AsyncSession, data: LogisticsMeetingCreate, current_user: User) -> LogisticsMeetingItem:
    _validate_meeting_time_range(data.start_time, data.end_time)
    participant_ids = await _normalize_meeting_participants(db, data.participants, current_user.id)

    meeting = LogisticsMeeting(
        topic=data.topic.strip(),
        description=data.description.strip() if data.description else "",
        meeting_type=_normalize_meeting_type(data.meeting_type),
        meeting_link=_normalize_meeting_link(data.link),
        meeting_date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        participant_ids=participant_ids,
        created_by_id=current_user.id,
        warehouse_id=current_user.warehouse_id,
    )
    db.add(meeting)
    await db.flush()
    await db.refresh(meeting)
    return _meeting_to_item(meeting)


async def update_meeting(
    db: AsyncSession,
    meeting_id: UUID,
    data: LogisticsMeetingUpdate,
    current_user: User,
) -> LogisticsMeetingItem:
    meeting = await _get_meeting_for_user(db, meeting_id, current_user)
    _ensure_meeting_owner(meeting, current_user)

    updates = data.model_dump(exclude_unset=True)
    next_start = updates.get("start_time", meeting.start_time)
    next_end = updates.get("end_time", meeting.end_time)
    _validate_meeting_time_range(next_start, next_end)

    if "topic" in updates and updates["topic"] is not None:
        meeting.topic = updates["topic"].strip()
    if "description" in updates and updates["description"] is not None:
        meeting.description = updates["description"].strip()
    if "meeting_type" in updates and updates["meeting_type"] is not None:
        meeting.meeting_type = _normalize_meeting_type(updates["meeting_type"])
    if "link" in updates and updates["link"] is not None:
        meeting.meeting_link = _normalize_meeting_link(updates["link"])
    if "date" in updates and updates["date"] is not None:
        meeting.meeting_date = updates["date"]
    if "start_time" in updates and updates["start_time"] is not None:
        meeting.start_time = updates["start_time"]
    if "end_time" in updates and updates["end_time"] is not None:
        meeting.end_time = updates["end_time"]
    if "participants" in updates:
        meeting.participant_ids = await _normalize_meeting_participants(db, updates["participants"], current_user.id)

    db.add(meeting)
    await db.flush()
    await db.refresh(meeting)
    return _meeting_to_item(meeting)


async def delete_meeting(db: AsyncSession, meeting_id: UUID, current_user: User) -> MessageResponse:
    meeting = await _get_meeting_for_user(db, meeting_id, current_user)
    _ensure_meeting_owner(meeting, current_user)
    await db.delete(meeting)
    await db.flush()
    return MessageResponse(message="Meeting deleted")


def _task_to_item(task: LogisticsTask) -> LogisticsTaskItem:
    return LogisticsTaskItem(
        id=task.id,
        text=task.text,
        status=task.status,
        target_time=task.target_time,
        repeat=task.repeat_rule,
        created_at=task.created_at,
        last_alert_time=task.last_alert_time,
        silenced=task.silenced,
    )


async def list_tasks(db: AsyncSession) -> list[LogisticsTaskItem]:
    tasks = (await db.execute(select(LogisticsTask).order_by(LogisticsTask.created_at.desc()))).scalars().all()
    return [_task_to_item(t) for t in tasks]


async def create_task(db: AsyncSession, data: LogisticsTaskCreate) -> LogisticsTaskItem:
    task = LogisticsTask(
        text=data.text,
        status=data.status,
        target_time=data.target_time,
        repeat_rule=data.repeat or "none",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_to_item(task)


async def delete_task(db: AsyncSession, task_id: UUID) -> MessageResponse:
    task = (await db.execute(select(LogisticsTask).where(LogisticsTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
    return MessageResponse(message="Task deleted")


async def update_task(db: AsyncSession, task_id: UUID, data: LogisticsTaskUpdate) -> LogisticsTaskItem:
    task = (await db.execute(select(LogisticsTask).where(LogisticsTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updates = data.model_dump(exclude_unset=True)
    if "repeat" in updates:
        task.repeat_rule = updates.pop("repeat")
    for key, value in updates.items():
        setattr(task, key, value)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_to_item(task)


async def get_notifications(db: AsyncSession, current_user: User) -> list[LogisticsNotificationItem]:
    notifications = (await db.execute(select(LogisticsNotification).order_by(LogisticsNotification.created_at.desc()))).scalars().all()
    notifications = [item for item in notifications if _notification_visible_to_user(item, current_user)]
    return [LogisticsNotificationItem(id=item.id, title=item.title, message=item.message, time=_fmt_relative(item.created_at), created_at=item.created_at, read=item.is_read, type=item.type) for item in notifications]


async def update_notification(db: AsyncSession, notification_id: UUID, data: LogisticsNotificationUpdate, current_user: User) -> LogisticsNotificationItem:
    notification = (await db.execute(select(LogisticsNotification).where(LogisticsNotification.id == notification_id))).scalar_one_or_none()
    if not notification or not _notification_visible_to_user(notification, current_user):
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = data.read
    db.add(notification)
    await db.flush()
    return LogisticsNotificationItem(id=notification.id, title=notification.title, message=notification.message, time=_fmt_relative(notification.created_at), created_at=notification.created_at, read=notification.is_read, type=notification.type)


async def mark_all_notifications_read(db: AsyncSession, current_user: User) -> MessageResponse:
    notifications = (await db.execute(select(LogisticsNotification))).scalars().all()
    for notification in notifications:
        if not _notification_visible_to_user(notification, current_user):
            continue
        notification.is_read = True
        db.add(notification)
    await db.flush()
    return MessageResponse(message="Notifications marked as read")


async def clear_notifications(db: AsyncSession, current_user: User) -> MessageResponse:
    notifications = (await db.execute(select(LogisticsNotification))).scalars().all()
    for notification in notifications:
        if not _notification_visible_to_user(notification, current_user):
            continue
        await db.delete(notification)
    await db.flush()
    return MessageResponse(message="Notifications cleared")


async def create_driver_crisis_alert(db: AsyncSession, user, payload: dict) -> LogisticsAlert:
    """Create a crisis alert from a driver - for SOS, accidents, breakdowns etc."""
    alert_type = payload.get("type", "sos")
    
    # Get driver name
    driver_name = user.name or user.email.split("@")[0]
    
    # Build alert title based on type
    type_labels = {
        "sos": "🚨 SOS Alert",
        "accident": "🚗 Accident Report", 
        "breakdown": "🔧 Vehicle Breakdown",
        "security": "🔐 Security Threat",
        "medical": "🏥 Medical Emergency"
    }
    title = f"{type_labels.get(alert_type, '🚨 Emergency')} — {driver_name}"
    
    # Build description
    location = payload.get("location", "Location unknown")
    description = payload.get("description", f"Driver {driver_name} triggered {alert_type} alert")
    if payload.get("latitude") and payload.get("longitude"):
        location = f"{payload['latitude']}, {payload['longitude']}"
        description += f" at coordinates {location}"
    
    # Severity based on type
    severity_map = {"sos": "critical", "accident": "critical", "medical": "critical", "security": "high", "breakdown": "high"}
    severity = severity_map.get(alert_type, "high")
    
    # Icon based on type
    icon_map = {"sos": "emergency", "accident": "car_crash", "breakdown": "build", "security": "security", "medical": "local_hospital"}
    icon = icon_map.get(alert_type, "warning")
    
    alert = LogisticsAlert(
        alert_type=alert_type,
        title=title,
        description=description,
        severity=severity,
        icon=icon,
        location=location,
        recommendation=f"Contact driver {driver_name} immediately. Dispatch emergency response if needed.",
        impact_json={"driver_id": str(user.id), "driver_name": driver_name, "alert_type": alert_type},
        is_active=True,
    )
    db.add(alert)
    await db.flush()
    
    # Broadcast crisis alert to dispatcher dashboard via WebSocket
    try:
        from app.routers.ws_fleet import fleet_manager
        await fleet_manager.broadcast({
            "type": "crisis_alert",
            "alert_id": str(alert.id),
            "alert_type": alert_type,
            "title": title,
            "description": description,
            "severity": severity,
            "icon": icon,
            "location": location,
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "driver_id": str(user.id),
            "driver_name": driver_name,
            "timestamp": datetime.now(UTC).isoformat(),
        })
    except Exception:
        pass  # WebSocket broadcast is best-effort
    
    return alert


async def create_alert(db: AsyncSession, payload: dict) -> LogisticsAlertItem:
    alert = LogisticsAlert(
        warehouse_id=payload.get("warehouse_id"),
        alert_type=payload.get("type", "manual"),
        title=payload["title"],
        description=payload["description"],
        severity=payload.get("severity", "medium"),
        icon=payload.get("icon"),
        location=payload.get("location"),
        recommendation=payload.get("recommendation"),
        impact_json=payload.get("impact"),
        is_active=True,
    )
    db.add(alert)
    await db.flush()
    return LogisticsAlertItem(id=alert.id, type=alert.alert_type, title=alert.title, description=alert.description, severity=alert.severity, icon=alert.icon, timestamp=alert.created_at.strftime("%I:%M %p"), location=alert.location, recommendation=alert.recommendation, impact=alert.impact_json)


async def resolve_alert(db: AsyncSession, alert_id: UUID) -> MessageResponse:
    alert = (await db.execute(select(LogisticsAlert).where(LogisticsAlert.id == alert_id))).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = False
    db.add(alert)
    await db.flush()
    return MessageResponse(message="Alert resolved")


async def list_alerts(db: AsyncSession) -> list[LogisticsAlertItem]:
    result = await db.execute(
        select(LogisticsAlert)
        .where(LogisticsAlert.is_active == True)
        .order_by(LogisticsAlert.created_at.desc())
        .limit(50)
    )
    alerts = result.scalars().all()
    return [
        LogisticsAlertItem(
            id=a.id,
            type=a.alert_type,
            title=a.title,
            description=a.description,
            severity=a.severity,
            icon=a.icon,
            timestamp=a.created_at.strftime("%I:%M %p"),
            location=a.location,
            recommendation=a.recommendation,
            impact=a.impact_json,
        )
        for a in alerts
    ]


def _manifest_to_item(m: LogisticsManifest) -> LogisticsManifestItem:
    from app.schemas.logistics import ManifestCrewMember
    crew = [ManifestCrewMember(**c) for c in (m.crew_list or [])]
    return LogisticsManifestItem(
        id=m.id,
        route_id=m.route_id,
        driver_name=m.driver_name,
        driver_id=m.driver_id,
        vehicle_code=m.vehicle_code,
        hub_name=m.hub_name,
        crew_config=m.crew_config,
        status=m.status,
        orders_count=m.orders_count,
        total_weight=m.total_weight,
        total_distance=m.total_distance,
        stop_count=m.stop_count,
        total_volume=m.total_volume,
        est_duration=m.est_duration,
        fragile_count=m.fragile_count,
        cod_count=m.cod_count,
        crew_list=crew,
        pushed=m.pushed,
        pushed_at=m.pushed_at,
        created_at=m.created_at,
    )


async def list_manifests(db: AsyncSession) -> list[LogisticsManifestItem]:
    result = await db.execute(
        select(LogisticsManifest).order_by(LogisticsManifest.created_at.desc()).limit(100)
    )
    return [_manifest_to_item(m) for m in result.scalars().all()]


async def create_manifest(db: AsyncSession, data: LogisticsManifestCreate, created_by_id: UUID | None = None) -> LogisticsManifestItem:
    crew_list = [c.model_dump() for c in data.crew_list] if data.crew_list else []
    manifest = LogisticsManifest(
        route_id=data.route_id,
        driver_name=data.driver_name,
        driver_id=data.driver_id,
        vehicle_code=data.vehicle_code,
        hub_name=data.hub_name,
        crew_config=data.crew_config,
        status="Draft",
        orders_count=data.orders_count,
        total_weight=data.total_weight,
        total_distance=data.total_distance,
        stop_count=data.stop_count,
        total_volume=data.total_volume,
        est_duration=data.est_duration,
        fragile_count=data.fragile_count,
        cod_count=data.cod_count,
        crew_list=crew_list,
        pushed=False,
        created_by_id=created_by_id,
    )
    db.add(manifest)
    await db.flush()
    return _manifest_to_item(manifest)


async def push_manifest(db: AsyncSession, manifest_id: UUID) -> LogisticsManifestItem:
    manifest = (await db.execute(select(LogisticsManifest).where(LogisticsManifest.id == manifest_id))).scalar_one_or_none()
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    manifest.pushed = True
    manifest.pushed_at = _now()
    manifest.status = "Dispatched"
    db.add(manifest)
    await db.flush()
    return _manifest_to_item(manifest)


async def create_document(db: AsyncSession, data: LogisticsDocumentCreate) -> LogisticsDocumentItem:
    doc = LogisticsDocument(
        entity_type=data.entity_type.upper(),
        entity_id=data.entity_id,
        hub_id=data.hub_id,
        doc_type=data.doc_type,
        document_url=data.document_url,
        expiry_date=data.expiry_date,
        status="Pending Verification"
    )
    db.add(doc)
    await db.flush()
    return doc


async def update_document_status(db: AsyncSession, doc_id: UUID, data: LogisticsDocumentUpdateStatus) -> LogisticsDocumentItem:
    doc = (await db.execute(select(LogisticsDocument).where(LogisticsDocument.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = data.status
    if data.notes is not None:
        doc.notes = data.notes

    db.add(doc)
    await db.flush()
    return doc


def _build_driver_item(profile: LogisticsDriverProfile, user: User, vehicle_code: str | None) -> LogisticsDriverItem:
    return LogisticsDriverItem(
        id=user.id,
        hub_id=profile.warehouse_id,
        name=user.name,
        status=profile.status,
        location=profile.current_location,
        vehicle=vehicle_code,
        efficiency=profile.efficiency_score,
        phone=user.phone,
        current_job=profile.current_job,
        avatar_color=profile.avatar_color,
        chat_history=profile.chat_history or [],
    )


async def list_drivers(db: AsyncSession, warehouse_id: UUID | None = None) -> list[LogisticsDriverItem]:
    from sqlalchemy import or_
    query = select(LogisticsDriverProfile).order_by(LogisticsDriverProfile.created_at.asc())
    if warehouse_id is not None:
        # Include drivers assigned to this hub AND global drivers (warehouse_id = null)
        query = query.where(or_(LogisticsDriverProfile.warehouse_id == warehouse_id, LogisticsDriverProfile.warehouse_id.is_(None)))
    profiles = (await db.execute(query)).scalars().all()
    user_ids = [p.user_id for p in profiles]
    if not user_ids:
        return []
    users = (await db.execute(select(User).where(User.id.in_(user_ids), User.is_active.is_(True)))).scalars().all()
    user_map = {u.id: u for u in users}
    # 1) Vehicle assigned directly on the vehicle record
    vehicles = (await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.assigned_driver_id.in_(user_ids)))).scalars().all()
    vehicle_by_driver = {v.assigned_driver_id: v.code for v in vehicles}
    # 2) Vehicle linked via active order (ASSIGNED / IN_TRANSIT) — takes precedence over static assignment
    active_orders = (await db.execute(
        select(Order).where(
            Order.assigned_driver_id.in_(user_ids),
            Order.status.in_(["ASSIGNED", "IN_TRANSIT"]),
            Order.assigned_vehicle_id.isnot(None),
        )
    )).scalars().all()
    if active_orders:
        order_vehicle_ids = list({o.assigned_vehicle_id for o in active_orders})
        order_vehicles = (await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.id.in_(order_vehicle_ids)))).scalars().all()
        order_vehicle_map = {v.id: v.code for v in order_vehicles}
        for o in active_orders:
            if o.assigned_driver_id and o.assigned_vehicle_id in order_vehicle_map:
                vehicle_by_driver[o.assigned_driver_id] = order_vehicle_map[o.assigned_vehicle_id]
    result = []
    for profile in profiles:
        user = user_map.get(profile.user_id)
        if not user:
            continue
        result.append(_build_driver_item(profile, user, vehicle_by_driver.get(user.id)))
    return result


async def create_driver(db: AsyncSession, data: LogisticsDriverCreate) -> LogisticsDriverItem:
    await _ensure_active_warehouse(db, data.warehouse_id)
    existing = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    driver_id = _normalize_driver_login_id(data.driver_id, data.email)
    driver_pin = _validate_driver_pin(data.pin)
    if existing:
        # If the user already exists as a DRIVER (created via User Management),
        # just create the missing logistics profile instead of failing.
        driver_role = await _get_role(db, "DRIVER")
        if existing.role_id != driver_role.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists with a different role")
        normalized_driver_id = normalize_username(driver_id)
        conflicting_user = (
            await db.execute(select(User).where(User.username == normalized_driver_id, User.id != existing.id))
        ).scalar_one_or_none()
        if conflicting_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Driver ID already in use")
        existing.username = normalized_driver_id
        existing.password_hash = hash_password(driver_pin)
        existing.phone = data.phone or existing.phone
        existing.warehouse_id = data.warehouse_id
        existing.is_active = True
        db.add(existing)
        existing_profile = (await db.execute(select(LogisticsDriverProfile).where(LogisticsDriverProfile.user_id == existing.id))).scalar_one_or_none()
        if existing_profile:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A driver profile for this email already exists")
        profile = LogisticsDriverProfile(
            user_id=existing.id,
            warehouse_id=data.warehouse_id,
            status=data.status,
            current_location=data.current_location,
            efficiency_score=85,
            avatar_color="bg-blue-600",
        )
        db.add(profile)
        await db.flush()
        return _build_driver_item(profile, existing, None)

    role = await _get_role(db, "DRIVER")
    username = await generate_unique_username(db, driver_id)
    user = User(
        name=data.name,
        username=username,
        email=data.email,
        phone=data.phone,
        address="",
        password_hash=hash_password(driver_pin),
        role_id=role.id,
        warehouse_id=data.warehouse_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = LogisticsDriverProfile(
        user_id=user.id,
        warehouse_id=data.warehouse_id,
        status=data.status,
        current_location=data.current_location,
        efficiency_score=85,
        avatar_color="bg-blue-600",
    )
    db.add(profile)
    await db.flush()
    return _build_driver_item(profile, user, None)


async def update_driver(db: AsyncSession, driver_id: UUID, data: LogisticsDriverUpdate) -> LogisticsDriverItem:
    profile = (await db.execute(select(LogisticsDriverProfile).where(LogisticsDriverProfile.user_id == driver_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    user = (await db.execute(select(User).where(User.id == driver_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Driver user not found")
    if data.status is not None:
        profile.status = data.status
    if data.current_location is not None:
        profile.current_location = data.current_location
    if data.current_job is not None:
        profile.current_job = data.current_job
    if data.warehouse_id is not None:
        await _ensure_active_warehouse(db, data.warehouse_id)
        profile.warehouse_id = data.warehouse_id
        user.warehouse_id = data.warehouse_id
    if data.efficiency_score is not None:
        profile.efficiency_score = data.efficiency_score
    db.add(profile)
    db.add(user)
    await db.flush()
    vehicles = (await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.assigned_driver_id == driver_id))).scalars().all()
    vehicle_code = vehicles[0].code if vehicles else None
    return _build_driver_item(profile, user, vehicle_code)


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


# ── Driver Dispatch Chat ───────────────────────────────────────────────────────

_DISPATCHER_SENDERS = {"dispatcher", "dispatch", "system", "me"}
_MANAGER_SENDERS = {"manager", "logistics manager", "system", "me"}


async def _find_driver_thread(db: AsyncSession, user: User):
    """Find the driver's dispatch thread, checking both naming conventions."""
    for name in (f"Driver: {user.name}", user.name):
        thread = (
            await db.execute(
                select(LogisticsChatThread)
                .options(selectinload(LogisticsChatThread.messages))
                .where(LogisticsChatThread.name == name)
                .order_by(LogisticsChatThread.created_at.asc())
            )
        ).scalars().first()
        if thread:
            return thread
    return None


async def _find_driver_manager_thread(db: AsyncSession, user: User):
    """Find the driver's Logistics Manager thread, keeping it separate from dispatch."""
    for name in (f"LM Driver: {user.name}", f"Manager: {user.name}"):
        thread = (
            await db.execute(
                select(LogisticsChatThread)
                .options(selectinload(LogisticsChatThread.messages))
                .where(LogisticsChatThread.name == name)
                .order_by(LogisticsChatThread.created_at.asc())
            )
        ).scalars().first()
        if thread:
            return thread
    return None


async def get_driver_dispatch_thread(
    db: AsyncSession,
    user: User,
) -> DriverDispatchThreadItem:
    thread = await _find_driver_thread(db, user)

    if not thread:
        thread = LogisticsChatThread(
            name=f"Driver: {user.name}",
            status="Online",
            warehouse_id=user.warehouse_id,
        )
        db.add(thread)
        await db.flush()
        welcome = LogisticsChatMessage(
            thread_id=thread.id,
            sender="Dispatcher",
            text=f"Dispatch channel ready for {user.name}. How can I help?",
        )
        db.add(welcome)
        await db.flush()
        thread = (
            await db.execute(
                select(LogisticsChatThread)
                .options(selectinload(LogisticsChatThread.messages))
                .where(LogisticsChatThread.id == thread.id)
            )
        ).scalars().first()
        await db.commit()

    messages = [
        {
            "id": str(msg.id),
            "text": msg.text,
            "fromDriver": msg.sender.lower() not in _DISPATCHER_SENDERS,
            "time": msg.created_at.strftime("%H:%M"),
        }
        for msg in thread.messages
    ]
    return DriverDispatchThreadItem(thread_id=str(thread.id), messages=messages)


async def add_driver_dispatch_message(
    db: AsyncSession,
    user: User,
    data: DriverDispatchMessageCreate,
) -> DriverDispatchThreadItem:
    thread = await _find_driver_thread(db, user)

    if not thread:
        thread = LogisticsChatThread(
            name=f"Driver: {user.name}",
            status="Online",
            warehouse_id=user.warehouse_id,
        )
        db.add(thread)
        await db.flush()

    # Truncate sender to fit the String(30) DB column
    sender_name = (user.name or "Driver")[:30]
    msg = LogisticsChatMessage(
        thread_id=thread.id,
        sender=sender_name,
        text=data.text,
    )
    thread.last_message = data.text
    thread.last_message_at = _now()
    db.add(msg)
    db.add(thread)
    await db.commit()

    # Fetch messages directly to avoid SQLAlchemy identity-map cache returning stale data
    all_messages = (await db.execute(
        select(LogisticsChatMessage)
        .where(LogisticsChatMessage.thread_id == thread.id)
        .order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()

    messages = [
        {
            "id": str(m.id),
            "text": m.text,
            "fromDriver": m.sender.lower() not in _DISPATCHER_SENDERS,
            "time": m.created_at.strftime("%H:%M"),
        }
        for m in all_messages
    ]
    return DriverDispatchThreadItem(thread_id=str(thread.id), messages=messages)


async def get_driver_manager_thread(
    db: AsyncSession,
    user: User,
) -> DriverDispatchThreadItem:
    thread = await _find_driver_manager_thread(db, user)

    if not thread:
        thread = LogisticsChatThread(
            name=f"LM Driver: {user.name}",
            status="Online",
            warehouse_id=user.warehouse_id,
        )
        db.add(thread)
        await db.flush()
        welcome = LogisticsChatMessage(
            thread_id=thread.id,
            sender="Logistics Manager",
            text=f"Manager channel ready for {user.name}. Reach out if you need operational support.",
        )
        db.add(welcome)
        await db.flush()
        thread = (
            await db.execute(
                select(LogisticsChatThread)
                .options(selectinload(LogisticsChatThread.messages))
                .where(LogisticsChatThread.id == thread.id)
            )
        ).scalars().first()
        await db.commit()

    messages = [
        {
            "id": str(msg.id),
            "text": msg.text,
            "fromDriver": msg.sender.lower() not in _MANAGER_SENDERS,
            "time": msg.created_at.strftime("%H:%M"),
        }
        for msg in thread.messages
    ]
    return DriverDispatchThreadItem(thread_id=str(thread.id), messages=messages)


async def add_driver_manager_message(
    db: AsyncSession,
    user: User,
    data: DriverDispatchMessageCreate,
) -> DriverDispatchThreadItem:
    thread = await _find_driver_manager_thread(db, user)

    if not thread:
        thread = LogisticsChatThread(
            name=f"LM Driver: {user.name}",
            status="Online",
            warehouse_id=user.warehouse_id,
        )
        db.add(thread)
        await db.flush()

    sender_name = (user.name or "Driver")[:30]
    msg = LogisticsChatMessage(
        thread_id=thread.id,
        sender=sender_name,
        text=data.text,
    )
    thread.last_message = data.text
    thread.last_message_at = _now()
    db.add(msg)
    db.add(thread)
    await db.commit()

    all_messages = (await db.execute(
        select(LogisticsChatMessage)
        .where(LogisticsChatMessage.thread_id == thread.id)
        .order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()

    messages = [
        {
            "id": str(m.id),
            "text": m.text,
            "fromDriver": m.sender.lower() not in _MANAGER_SENDERS,
            "time": m.created_at.strftime("%H:%M"),
        }
        for m in all_messages
    ]
    return DriverDispatchThreadItem(thread_id=str(thread.id), messages=messages)


# ── Driver Audit Log ───────────────────────────────────────────────────────────

async def get_driver_audit_log(
    db: AsyncSession,
    user: User,
) -> list[DriverAuditEventItem]:
    profile = await _get_driver_profile(db, user)
    vehicles = (
        await db.execute(
            select(LogisticsVehicle).where(LogisticsVehicle.assigned_driver_id == user.id)
        )
    ).scalars().all()
    orders = await _get_driver_orders(db, user)

    events: list[DriverAuditEventItem] = []
    event_id = 1

    def _fmt(dt: datetime | None) -> str:
        if not dt:
            return "—"
        local = _coerce_utc(dt)
        return local.strftime("%H:%M")

    shift_started = _coerce_utc(user.last_login) if profile.status.lower() != "off-duty" else None
    if shift_started:
        events.append(DriverAuditEventItem(
            id=str(event_id),
            icon="login",
            color="text-primary",
            action=f"Shift Started — {user.name}",
            detail=f"RBAC: DRIVER · Shift code {_shift_code(user, shift_started)}",
            time=_fmt(shift_started),
        ))
        event_id += 1

    for v in vehicles:
        events.append(DriverAuditEventItem(
            id=str(event_id),
            icon="directions_car",
            color="text-accent-blue",
            action="Vehicle Bound",
            detail=f"{v.code} · {v.license_plate or 'No plate'}",
            time=_fmt(v.updated_at),
        ))
        event_id += 1

    for order in orders:
        if _is_completed_order(order):
            events.append(DriverAuditEventItem(
                id=str(event_id),
                icon="verified",
                color="text-primary",
                action=f"Delivery Completed — {order.tracking_code}",
                detail=f"Order {order.tracking_code} · POD recorded",
                time=_fmt(order.updated_at),
            ))
            event_id += 1
        elif _is_active_order(order):
            events.append(DriverAuditEventItem(
                id=str(event_id),
                icon="place",
                color="text-accent-purple",
                action=f"Stop Active — {order.tracking_code}",
                detail=f"Order in progress · {order.status}",
                time=_fmt(order.updated_at),
            ))
            event_id += 1

    events.sort(key=lambda e: e.time)
    return events


# ── Driver Cashout ─────────────────────────────────────────────────────────────

async def request_driver_cashout(
    db: AsyncSession,
    user: User,
    data: DriverCashoutRequest,
) -> MessageResponse:
    profile = await _get_driver_profile(db, user)
    warehouse_id = user.warehouse_id or profile.warehouse_id

    tx_code = f"CASHOUT-{str(user.id)[:8].upper()}-{int(_now().timestamp())}"
    tx = LogisticsTransaction(
        warehouse_id=warehouse_id,
        transaction_code=tx_code,
        description=f"Driver cashout — {user.name}",
        transaction_type="DRIVER_CASHOUT",
        amount=-abs(data.amount),
        status="Pending",
        metadata_json={
            "driver_id": str(user.id),
            "driver_name": user.name,
            "requested_at": _now().isoformat(),
        },
    )
    db.add(tx)
    await db.commit()
    return MessageResponse(message=f"Cashout of ₹{data.amount:.0f} requested successfully")
