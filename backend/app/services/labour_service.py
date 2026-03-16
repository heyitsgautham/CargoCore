from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.labour import LabourAttendance, Labourer
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
    result = await db.execute(select(Labourer).where(Labourer.id == labourer_id))
    labourer = result.scalar_one_or_none()
    if not labourer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labourer not found")
    return labourer


async def list_labourers(db: AsyncSession, page: int, page_size: int) -> LabourerListResponse:
    total = (await db.execute(select(func.count(Labourer.id)))).scalar_one()
    rows = (
        await db.execute(
            select(Labourer)
            .order_by(Labourer.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return LabourerListResponse(
        items=[LabourerResponse.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def create_labourer(db: AsyncSession, data: LabourerCreate) -> LabourerResponse:
    existing = await db.execute(select(Labourer).where(Labourer.user_id == data.user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Labourer profile already exists")

    labourer = Labourer(**data.model_dump(), is_active=True)
    db.add(labourer)
    await db.flush()
    await db.refresh(labourer)
    return LabourerResponse.model_validate(labourer)


async def get_labourer_detail(db: AsyncSession, labourer_id: UUID) -> LabourerResponse:
    labourer = await _get_labourer(db, labourer_id)
    return LabourerResponse.model_validate(labourer)


async def update_labourer(
    db: AsyncSession,
    labourer_id: UUID,
    data: LabourerUpdate,
) -> LabourerResponse:
    labourer = await _get_labourer(db, labourer_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(labourer, key, value)

    db.add(labourer)
    await db.flush()
    await db.refresh(labourer)
    return LabourerResponse.model_validate(labourer)


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
