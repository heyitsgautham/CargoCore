from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.orders import (
    CancelOrderRequest,
    OrderAssignRequest,
    OrderCreate,
    OrderItemResponse,
    OrderItemUpsert,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)
from app.services import orders_service

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await orders_service.create_order(db, data, user)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None),
):
    return await orders_service.list_orders(db, user, page, page_size, status_filter)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await orders_service.get_order_detail(db, order_id, user)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    data: OrderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await orders_service.update_order(db, order_id, user, data)


@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await orders_service.confirm_order(db, order_id)


@router.post("/{order_id}/assign", response_model=OrderResponse)
async def assign_order(
    order_id: UUID,
    data: OrderAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await orders_service.assign_order(db, order_id, data)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    data: CancelOrderRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(get_current_user)],
):
    return await orders_service.cancel_order(db, order_id, data)


@router.get("/track/{tracking_code}")
async def track_order(tracking_code: str, db: Annotated[AsyncSession, Depends(get_db)]):
    return await orders_service.track_order(db, tracking_code)


@router.get("/{order_id}/items", response_model=list[OrderItemResponse])
async def get_order_items(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(get_current_user)],
):
    return await orders_service.get_order_items(db, order_id)


@router.post("/{order_id}/items", response_model=list[OrderItemResponse])
async def upsert_items(
    order_id: UUID,
    items: list[OrderItemUpsert],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(get_current_user)],
):
    return await orders_service.upsert_order_items(db, order_id, items)
