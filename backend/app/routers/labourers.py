from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.schemas.labour import (
    AssignLabourResponse,
    LabourAttendanceResponse,
    LabourAvailabilityResponse,
    LabourerCreate,
    LabourerListResponse,
    LabourerResponse,
    LabourerUpdate,
)
from app.services import labour_service

router = APIRouter(prefix="/api/v1/labourers", tags=["Labourers"])


@router.get("", response_model=LabourerListResponse)
async def list_labourers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return await labour_service.list_labourers(db, page, page_size)


@router.post("", response_model=LabourerResponse, status_code=status.HTTP_201_CREATED)
async def create_labourer(
    data: LabourerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await labour_service.create_labourer(db, data)


@router.get("/{labourer_id}", response_model=LabourerResponse)
async def get_labourer(
    labourer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await labour_service.get_labourer_detail(db, labourer_id)


@router.put("/{labourer_id}", response_model=LabourerResponse)
async def update_labourer(
    labourer_id: UUID,
    data: LabourerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await labour_service.update_labourer(db, labourer_id, data)


@router.post("/{labourer_id}/assign/{order_id}", response_model=AssignLabourResponse)
async def assign_labourer(
    labourer_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await labour_service.assign_labourer(db, labourer_id, order_id)


@router.post("/{labourer_id}/check-in", response_model=LabourAttendanceResponse)
async def check_in(
    labourer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await labour_service.check_in(db, labourer_id)


@router.post("/{labourer_id}/check-out", response_model=LabourAttendanceResponse)
async def check_out(
    labourer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await labour_service.check_out(db, labourer_id)


@router.get("/availability", response_model=LabourAvailabilityResponse)
async def availability(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await labour_service.availability_today(db)
