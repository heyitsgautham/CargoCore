"""Driver accounts managed by the logistics manager."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsDriverProfile,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.schemas.logistics import (
    LogisticsDriverCreate,
    LogisticsDriverItem,
    LogisticsDriverUpdate,
)
from app.services.logistics.formatting import (
    _ensure_active_warehouse,
    _normalize_driver_login_id,
    _validate_driver_pin,
)
from app.services.logistics.lookups import _get_role
from app.utils.hashing import hash_password
from app.utils.username import generate_unique_username, normalize_username


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
