from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, InventoryMovement
from app.models.order import Order
from app.models.order import OrderItem
from app.models.user import User
from app.schemas.inventory import (
    InventoryCreate,
    InventoryListResponse,
    InventoryMovementCreate,
    InventoryMovementResponse,
    InventoryResponse,
    InventoryUpdate,
    PickingListItem,
    PickingListResponse,
)

MOVEMENT_TYPES = {"INBOUND", "OUTBOUND", "ADJUSTMENT"}


async def _get_item(db: AsyncSession, item_id: UUID) -> InventoryItem:
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    return item


async def list_items(
    db: AsyncSession,
    page: int,
    page_size: int,
    warehouse_id: UUID | None,
) -> InventoryListResponse:
    filters = []
    if warehouse_id:
        filters.append(InventoryItem.warehouse_id == warehouse_id)

    total_query = select(func.count(InventoryItem.id))
    data_query = (
        select(InventoryItem)
        .order_by(InventoryItem.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if filters:
        total_query = total_query.where(*filters)
        data_query = data_query.where(*filters)

    total = (await db.execute(total_query)).scalar_one()
    rows = (await db.execute(data_query)).scalars().all()

    return InventoryListResponse(
        items=[InventoryResponse.model_validate(item) for item in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def create_item(db: AsyncSession, data: InventoryCreate) -> InventoryResponse:
    item = InventoryItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return InventoryResponse.model_validate(item)


async def get_item_detail(db: AsyncSession, item_id: UUID) -> InventoryResponse:
    item = await _get_item(db, item_id)
    return InventoryResponse.model_validate(item)


async def update_item(db: AsyncSession, item_id: UUID, data: InventoryUpdate) -> InventoryResponse:
    item = await _get_item(db, item_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return InventoryResponse.model_validate(item)


async def delete_item(db: AsyncSession, item_id: UUID) -> None:
    item = await _get_item(db, item_id)
    await db.delete(item)
    await db.flush()


async def create_movement(
    db: AsyncSession,
    data: InventoryMovementCreate,
    user: User,
) -> InventoryMovementResponse:
    movement_type = data.movement_type.upper()
    if movement_type not in MOVEMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid movement_type")

    item = await _get_item(db, data.item_id)

    if movement_type == "OUTBOUND" and item.quantity_on_hand < data.quantity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient stock")

    if movement_type == "OUTBOUND":
        item.quantity_on_hand -= data.quantity
    else:
        item.quantity_on_hand += data.quantity

    movement = InventoryMovement(
        item_id=item.id,
        movement_type=movement_type,
        quantity=data.quantity,
        reference_order_id=data.reference_order_id,
        performed_by=user.id,
    )

    db.add(item)
    db.add(movement)
    await db.flush()
    await db.refresh(movement)
    return InventoryMovementResponse.model_validate(movement)


async def list_movements(
    db: AsyncSession,
    page: int,
    page_size: int,
    item_id: UUID | None,
) -> list[InventoryMovementResponse]:
    query = select(InventoryMovement).order_by(InventoryMovement.created_at.desc())
    if item_id:
        query = query.where(InventoryMovement.item_id == item_id)

    rows = (
        await db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()

    return [InventoryMovementResponse.model_validate(row) for row in rows]


async def low_stock_items(db: AsyncSession, warehouse_id: UUID | None) -> list[InventoryResponse]:
    query = select(InventoryItem).where(InventoryItem.quantity_on_hand <= InventoryItem.safety_stock)
    if warehouse_id:
        query = query.where(InventoryItem.warehouse_id == warehouse_id)

    rows = (await db.execute(query.order_by(InventoryItem.quantity_on_hand.asc()))).scalars().all()
    return [InventoryResponse.model_validate(row) for row in rows]


async def generate_pick_list(db: AsyncSession, order_id: UUID) -> PickingListResponse:
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not order.warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order must be assigned to a warehouse before generating pick list",
        )

    order_items = (await db.execute(select(OrderItem).where(OrderItem.order_id == order_id))).scalars().all()
    if not order_items:
        return PickingListResponse(order_id=order_id, items=[])

    result_items: list[PickingListItem] = []
    for order_item in order_items:
        inventory_result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == order.warehouse_id,
                InventoryItem.sku == order_item.sku,
            )
        )
        inventory_item = inventory_result.scalar_one_or_none()
        available = inventory_item.quantity_on_hand if inventory_item else 0
        result_items.append(
            PickingListItem(
                sku=order_item.sku,
                required_quantity=order_item.quantity,
                available_quantity=available,
            )
        )

    return PickingListResponse(order_id=order_id, items=result_items)
