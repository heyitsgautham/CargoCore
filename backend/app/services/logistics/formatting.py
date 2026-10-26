"""Formatting, classification and geometry helpers shared by the logistics services."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import quote_plus
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import RestockRequest
from app.models.labour import LabourAttendance, Labourer
from app.models.logistics import (
    LogisticsDriverProfile,
    LogisticsEscalation,
    LogisticsNotification,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.logistics import (
    DriverCrewMemberItem,
    LogisticsEscalationItem,
)


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
