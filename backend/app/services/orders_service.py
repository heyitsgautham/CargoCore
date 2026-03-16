import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
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

ORDER_TYPES = {"INDIVIDUAL", "VENDOR"}
ORDER_STATUSES = {
    "DRAFT",
    "CONFIRMED",
    "ASSIGNED",
    "IN_TRANSIT",
    "DELIVERED",
    "CLOSED",
    "CANCELLED",
}
ALLOWED_TRANSITIONS = {
    "DRAFT": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"ASSIGNED", "CANCELLED"},
    "ASSIGNED": {"IN_TRANSIT", "CANCELLED"},
    "IN_TRANSIT": {"DELIVERED", "CANCELLED"},
    "DELIVERED": {"CLOSED"},
    "CLOSED": set(),
    "CANCELLED": set(),
}


async def _get_order(db: AsyncSession, order_id: UUID) -> Order:
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def _tracking_code() -> str:
    return f"QC-{uuid.uuid4().hex[:10].upper()}"


def _validate_transition(current_status: str, next_status: str) -> None:
    if next_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid transition from {current_status} to {next_status}",
        )


def _to_order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        tracking_code=order.tracking_code,
        order_type=order.order_type,
        status=order.status,
        customer_id=order.customer_id,
        warehouse_id=order.warehouse_id,
        assigned_driver_id=order.assigned_driver_id,
        assigned_vehicle_id=order.assigned_vehicle_id,
        pickup_addr=order.pickup_addr,
        delivery_addr=order.delivery_addr,
        scheduled_at=order.scheduled_at,
        cancel_reason=order.cancel_reason,
        created_at=order.created_at,
        items=[OrderItemResponse.model_validate(item) for item in order.items],
    )


async def create_order(db: AsyncSession, data: OrderCreate, user: User) -> OrderResponse:
    order_type = data.order_type.upper()
    if order_type not in ORDER_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid order_type")

    order = Order(
        tracking_code=_tracking_code(),
        order_type=order_type,
        status="DRAFT",
        customer_id=user.id,
        warehouse_id=data.warehouse_id,
        pickup_addr=data.pickup_addr,
        delivery_addr=data.delivery_addr,
        scheduled_at=data.scheduled_at,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])
    return _to_order_response(order)


async def list_orders(
    db: AsyncSession,
    user: User,
    page: int,
    page_size: int,
    status_filter: str | None = None,
) -> OrderListResponse:
    filters = []
    user_role = user.role.name

    if user_role in {"INDIVIDUAL", "VENDOR"}:
        filters.append(Order.customer_id == user.id)
    elif user_role in {"WAREHOUSE_MANAGER", "LABOURER"} and user.warehouse_id:
        filters.append(Order.warehouse_id == user.warehouse_id)

    if status_filter:
        upper_status = status_filter.upper()
        if upper_status in ORDER_STATUSES:
            filters.append(Order.status == upper_status)

    total_query = select(func.count(Order.id))
    data_query = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if filters:
        total_query = total_query.where(*filters)
        data_query = data_query.where(*filters)

    total = (await db.execute(total_query)).scalar_one()
    rows = (await db.execute(data_query)).scalars().all()

    return OrderListResponse(
        items=[_to_order_response(order) for order in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_order_detail(db: AsyncSession, order_id: UUID, user: User) -> OrderResponse:
    order = await _get_order(db, order_id)
    if user.role.name in {"INDIVIDUAL", "VENDOR"} and order.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return _to_order_response(order)


async def update_order(db: AsyncSession, order_id: UUID, user: User, data: OrderUpdate) -> OrderResponse:
    order = await _get_order(db, order_id)
    if order.status not in {"DRAFT", "CONFIRMED"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order cannot be edited in current status",
        )

    if user.role.name in {"INDIVIDUAL", "VENDOR"} and order.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(order, key, value)
    db.add(order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])
    return _to_order_response(order)


async def confirm_order(db: AsyncSession, order_id: UUID) -> OrderResponse:
    order = await _get_order(db, order_id)
    _validate_transition(order.status, "CONFIRMED")
    order.status = "CONFIRMED"
    db.add(order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])
    return _to_order_response(order)


async def assign_order(db: AsyncSession, order_id: UUID, data: OrderAssignRequest) -> OrderResponse:
    order = await _get_order(db, order_id)
    _validate_transition(order.status, "ASSIGNED")
    order.assigned_driver_id = data.driver_id
    order.assigned_vehicle_id = data.vehicle_id
    order.status = "ASSIGNED"
    db.add(order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])
    return _to_order_response(order)


async def cancel_order(db: AsyncSession, order_id: UUID, data: CancelOrderRequest) -> OrderResponse:
    order = await _get_order(db, order_id)
    _validate_transition(order.status, "CANCELLED")
    order.status = "CANCELLED"
    order.cancel_reason = data.reason
    db.add(order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])
    return _to_order_response(order)


async def track_order(db: AsyncSession, tracking_code: str) -> dict:
    result = await db.execute(select(Order).where(Order.tracking_code == tracking_code))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracking code not found")

    return {
        "tracking_code": order.tracking_code,
        "status": order.status,
        "pickup_addr": order.pickup_addr,
        "delivery_addr": order.delivery_addr,
        "scheduled_at": order.scheduled_at,
    }


async def get_order_items(db: AsyncSession, order_id: UUID) -> list[OrderItemResponse]:
    order = await _get_order(db, order_id)
    return [OrderItemResponse.model_validate(item) for item in order.items]


async def upsert_order_items(
    db: AsyncSession,
    order_id: UUID,
    items: list[OrderItemUpsert],
) -> list[OrderItemResponse]:
    order = await _get_order(db, order_id)

    existing_by_sku = {item.sku: item for item in order.items}
    for item_data in items:
        existing = existing_by_sku.get(item_data.sku)
        if existing:
            existing.quantity = item_data.quantity
            existing.box_count = item_data.box_count
            existing.estimated_volume = item_data.estimated_volume
            db.add(existing)
            continue

        db.add(
            OrderItem(
                order_id=order.id,
                sku=item_data.sku,
                quantity=item_data.quantity,
                box_count=item_data.box_count,
                estimated_volume=item_data.estimated_volume,
            )
        )

    await db.flush()
    refreshed = await _get_order(db, order_id)
    return [OrderItemResponse.model_validate(item) for item in refreshed.items]
