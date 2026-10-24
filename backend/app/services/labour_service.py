from datetime import date
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.labour import LabourAttendance, Labourer
from app.models.user import User
from app.schemas.labour import (
    AssignLabourResponse,
    AvailabilityItem,
    LabourAttendanceResponse,
    LabourAvailabilityResponse,
    LabourerCreate,
    LabourerListResponse,
    LabourerResponse,
    LabourerUpdate,
)


async def _get_labourer(db: AsyncSession, labourer_id: UUID) -> Labourer:
    result = await db.execute(
        select(Labourer)
        .options(
            selectinload(Labourer.user).selectinload(User.role),
            selectinload(Labourer.assigned_order),
        )
        .where(Labourer.id == labourer_id)
    )
    labourer = result.scalar_one_or_none()
    if not labourer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labourer not found")
    return labourer


async def _ensure_active_warehouse(db: AsyncSession, warehouse_id: UUID):
    from app.models.warehouse import Warehouse

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
            detail="Cannot assign labour to an archived warehouse",
        )
    return warehouse


def _to_labourer_response(labourer: Labourer) -> LabourerResponse:
    # Determine status based on assignment and active state
    if not labourer.is_active:
        status = "OFF_DUTY"
    elif labourer.assigned_order_id:
        # If the linked order is already out for delivery, labourer is on field
        if labourer.assigned_order and labourer.assigned_order.status == "IN_TRANSIT":
            status = "ON_FIELD"
        else:
            status = "ASSIGNED"
    else:
        status = "AVAILABLE"

    user = labourer.user
    # user.role is a Role relationship object — get the name string
    role_name = None
    if user:
        role_obj = user.role
        if role_obj and hasattr(role_obj, 'name'):
            role_name = role_obj.name
        elif isinstance(role_obj, str):
            role_name = role_obj

    return LabourerResponse(
        id=labourer.id,
        user_id=labourer.user_id,
        warehouse_id=labourer.warehouse_id,
        assigned_order_id=labourer.assigned_order_id,
        assigned_order_tracking=labourer.assigned_order.tracking_code if labourer.assigned_order else None,
        assigned_order_substatus=labourer.assigned_order.warehouse_substatus if labourer.assigned_order else None,
        skill_tags=labourer.skill_tags,
        is_active=labourer.is_active,
        name=user.name if user else None,
        full_name=user.name if user else None,
        email=user.email if user else None,
        phone=user.phone if user else None,
        role=role_name or "LABOURER",
        status=status,
        created_at=labourer.created_at,
    )


async def list_labourers(
    db: AsyncSession,
    page: int,
    page_size: int,
    warehouse_id: UUID | None = None,
) -> LabourerListResponse:
    total_query = select(func.count(Labourer.id))
    data_query = (
        select(Labourer)
        .options(
            selectinload(Labourer.user).selectinload(User.role),
            selectinload(Labourer.assigned_order),
        )
        .order_by(Labourer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if warehouse_id:
        total_query = total_query.where(Labourer.warehouse_id == warehouse_id)
        data_query = data_query.where(Labourer.warehouse_id == warehouse_id)

    total = (await db.execute(total_query)).scalar_one()
    rows = (
        await db.execute(data_query)
    ).scalars().all()

    return LabourerListResponse(
        items=[_to_labourer_response(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def create_labourer(db: AsyncSession, data: LabourerCreate) -> LabourerResponse:
    user_id = data.user_id

    # If no user_id provided but name is given, create a new user
    if not user_id and data.name:
        # Generate a unique email if not provided
        email = data.email or f"labourer_{uuid4().hex[:8]}@warehouse.local"

        # Check if email already exists
        normalized_email = email.strip().lower()
        existing_user = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email already exists: {normalized_email}",
            )

        # Look up the LABOURER role_id from the roles table
        from app.models.user import Role
        role_result = await db.execute(select(Role).where(Role.name == "LABOURER"))
        labourer_role = role_result.scalar_one_or_none()
        if not labourer_role:
            # Create the LABOURER role if it doesn't exist
            labourer_role = Role(name="LABOURER")
            db.add(labourer_role)
            await db.flush()

        # Generate unique username from name
        base_username = data.name.lower().replace(" ", "_")
        username = f"{base_username}_{uuid4().hex[:6]}"

        # Create new user with LABOURER role
        new_user = User(
            name=data.name,
            username=username,
            email=normalized_email,
            phone=data.phone,
            role_id=labourer_role.id,
            password_hash="",  # No password - managed user
        )
        db.add(new_user)
        await db.flush()
        user_id = new_user.id
    elif not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either user_id or name is required")

    # Check if labourer profile already exists for this user
    existing = await db.execute(select(Labourer).where(Labourer.user_id == user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Labourer profile already exists")

    # Get a default warehouse if not provided
    warehouse_id = data.warehouse_id
    if warehouse_id:
        await _ensure_active_warehouse(db, warehouse_id)
    else:
        from app.models.warehouse import Warehouse
        result = await db.execute(
            select(Warehouse)
            .where(Warehouse.is_active.is_(True))
            .order_by(Warehouse.created_at.asc())
            .limit(1)
        )
        warehouse = result.scalar_one_or_none()
        if warehouse:
            warehouse_id = warehouse.id
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active warehouse available")

    labourer = Labourer(
        user_id=user_id,
        warehouse_id=warehouse_id,
        skill_tags=data.skill_tags,
        is_active=True,
    )
    db.add(labourer)
    await db.flush()
    labourer = await _get_labourer(db, labourer.id)
    return _to_labourer_response(labourer)


async def delete_labourer(db: AsyncSession, labourer_id: UUID) -> None:
    labourer = await _get_labourer(db, labourer_id)
    user_id = labourer.user_id
    # Delete labourer (cascades attendance_events)
    await db.delete(labourer)
    await db.flush()
    # Only delete the user if it was a system-managed account (empty password)
    try:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user and user.password_hash == "":
            await db.delete(user)
            await db.flush()
    except Exception:
        pass  # User has other FK references, leave the user account intact


async def get_labourer_detail(db: AsyncSession, labourer_id: UUID) -> LabourerResponse:
    labourer = await _get_labourer(db, labourer_id)
    return _to_labourer_response(labourer)


async def update_labourer(
    db: AsyncSession,
    labourer_id: UUID,
    data: LabourerUpdate,
) -> LabourerResponse:
    labourer = await _get_labourer(db, labourer_id)
    if data.warehouse_id is not None:
        await _ensure_active_warehouse(db, data.warehouse_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(labourer, key, value)

    db.add(labourer)
    await db.flush()
    labourer = await _get_labourer(db, labourer.id)
    return _to_labourer_response(labourer)


async def assign_labourer(db: AsyncSession, labourer_id: UUID, order_id: UUID) -> AssignLabourResponse:
    labourer = await _get_labourer(db, labourer_id)
    if labourer.assigned_order_id and labourer.assigned_order_id != order_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Labourer is already assigned to another order",
        )

    labourer.assigned_order_id = order_id
    db.add(labourer)
    await db.flush()

    return AssignLabourResponse(
        message="Labourer assigned successfully",
        labourer_id=labourer.id,
        order_id=order_id,
    )


async def check_in(db: AsyncSession, labourer_id: UUID) -> LabourAttendanceResponse:
    labourer = await _get_labourer(db, labourer_id)
    if not labourer.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Labourer is inactive")

    last_event = (
        await db.execute(
            select(LabourAttendance)
            .where(LabourAttendance.labourer_id == labourer_id)
            .order_by(LabourAttendance.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if last_event and last_event.event_type == "CHECK_IN":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Labourer already checked in")

    event = LabourAttendance(labourer_id=labourer_id, event_type="CHECK_IN")
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return LabourAttendanceResponse.model_validate(event)


async def check_out(db: AsyncSession, labourer_id: UUID) -> LabourAttendanceResponse:
    labourer = await _get_labourer(db, labourer_id)
    if not labourer.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Labourer is inactive")

    last_event = (
        await db.execute(
            select(LabourAttendance)
            .where(LabourAttendance.labourer_id == labourer_id)
            .order_by(LabourAttendance.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not last_event or last_event.event_type != "CHECK_IN":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Labourer must check in before check out",
        )

    event = LabourAttendance(labourer_id=labourer_id, event_type="CHECK_OUT")
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return LabourAttendanceResponse.model_validate(event)


async def availability_today(db: AsyncSession) -> LabourAvailabilityResponse:
    rows = (
        await db.execute(
            select(Labourer).where(
                and_(
                    Labourer.is_active.is_(True),
                    Labourer.assigned_order_id.is_(None),
                )
            )
        )
    ).scalars().all()

    return LabourAvailabilityResponse(
        date=str(date.today()),
        items=[
            AvailabilityItem(
                labourer_id=row.id,
                user_id=row.user_id,
                warehouse_id=row.warehouse_id,
                skill_tags=row.skill_tags,
            )
            for row in rows
        ],
    )
