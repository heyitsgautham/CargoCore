"""Database lookups and item builders for a driver's vehicle, crew, hours and validations."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.labour import Labourer
from app.models.logistics import (
    LogisticsDriverProfile,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.logistics import (
    DriverCrewMemberItem,
    DriverHosSummary,
    DriverValidationItem,
    LogisticsVehicleItem,
)
from app.services.logistics.formatting import (
    _coerce_utc,
    _driver_code,
    _format_duration_label,
    _is_active_order,
    _is_completed_order,
    _now,
    _order_job_type,
    _title_case_status,
    _to_crew_item,
    _vehicle_metrics,
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
