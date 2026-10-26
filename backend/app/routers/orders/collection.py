"""The order collection: create an order and list orders."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.orders import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
)
from app.services import orders_service

router = APIRouter()


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
    search: str | None = Query(default=None),
    warehouse_substatus: str | None = Query(default=None, description="Filter by warehouse substatus (AWAITING_INBOUND, AWAITING_PICK, etc.)"),
    order_type: str | None = Query(default=None, description="Filter by order type (VENDOR, INDIVIDUAL, SERVICE_MOVE)"),
    pickup_type: str | None = Query(default=None, description="Filter by pickup type (hub, doorstep)"),
):
    return await orders_service.list_orders(
        db, user, page, page_size, status_filter, search,
        warehouse_substatus=warehouse_substatus, order_type=order_type, pickup_type=pickup_type
    )
