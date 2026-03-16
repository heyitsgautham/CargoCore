from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.schemas.auth import MessageResponse
from app.schemas.warehouse import (
    FloorPlanUpdate,
    WarehouseCreate,
    WarehouseKPIResponse,
    WarehouseListResponse,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.services import warehouse_service

router = APIRouter(prefix="/api/v1/warehouses", tags=["Warehouses"])


@router.get("", response_model=WarehouseListResponse)
async def list_warehouses(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return await warehouse_service.list_warehouses(db, page, page_size)


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await warehouse_service.create_warehouse(db, data)


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await warehouse_service.get_warehouse_detail(db, warehouse_id)


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: UUID,
    data: WarehouseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await warehouse_service.update_warehouse(db, warehouse_id, data)


@router.delete("/{warehouse_id}", response_model=MessageResponse)
async def delete_warehouse(
    warehouse_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    await warehouse_service.delete_warehouse(db, warehouse_id)
    return MessageResponse(message="Warehouse deleted")


@router.put("/{warehouse_id}/floor-plan", response_model=WarehouseResponse)
async def update_floor_plan(
    warehouse_id: UUID,
    data: FloorPlanUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await warehouse_service.update_floor_plan(db, warehouse_id, data)


@router.get("/{warehouse_id}/kpis", response_model=WarehouseKPIResponse)
async def warehouse_kpis(
    warehouse_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await warehouse_service.get_warehouse_kpis(db, warehouse_id)
