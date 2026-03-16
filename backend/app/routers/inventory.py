from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.inventory import (
    InventoryCreate,
    InventoryListResponse,
    InventoryMovementCreate,
    InventoryMovementResponse,
    InventoryResponse,
    InventoryUpdate,
    PickingListResponse,
)
from app.services import inventory_service

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


@router.get("", response_model=InventoryListResponse)
async def list_inventory(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    warehouse_id: UUID | None = Query(default=None),
):
    return await inventory_service.list_items(db, page, page_size, warehouse_id)


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    data: InventoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await inventory_service.create_item(db, data)


@router.get("/{item_id}", response_model=InventoryResponse)
async def get_inventory_item(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await inventory_service.get_item_detail(db, item_id)


@router.put("/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(
    item_id: UUID,
    data: InventoryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await inventory_service.update_item(db, item_id, data)


@router.delete("/{item_id}", response_model=MessageResponse)
async def delete_inventory_item(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    await inventory_service.delete_item(db, item_id)
    return MessageResponse(message="Inventory item deleted")


@router.post("/movements", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_movement(
    data: InventoryMovementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await inventory_service.create_movement(db, data, user)


@router.get("/movements", response_model=list[InventoryMovementResponse])
async def list_inventory_movements(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    item_id: UUID | None = Query(default=None),
):
    return await inventory_service.list_movements(db, page, page_size, item_id)


@router.get("/low-stock", response_model=list[InventoryResponse])
async def low_stock(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
    warehouse_id: UUID | None = Query(default=None),
):
    return await inventory_service.low_stock_items(db, warehouse_id)


@router.post("/pick-list/{order_id}", response_model=PickingListResponse)
async def pick_list(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await inventory_service.generate_pick_list(db, order_id)
