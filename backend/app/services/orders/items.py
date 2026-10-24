"""Order tracking and order line items."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem
from app.models.order import Order, OrderItem
from app.schemas.orders import (
    OrderItemResponse,
    OrderItemUpsert,
)
from app.services.orders.common import _get_order


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
    if not order.items:
        return []

    # Resolve inventory item names for all SKUs in this order
    name_map: dict[str, str] = {}
    if order.warehouse_id:
        skus = [item.sku for item in order.items]
        inv_rows = (await db.execute(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == order.warehouse_id,
                InventoryItem.sku.in_(skus),
            )
        )).scalars().all()
        name_map = {inv.sku: inv.name for inv in inv_rows}

    results = []
    for item in order.items:
        r = OrderItemResponse.model_validate(item)
        r.name = name_map.get(item.sku)
        results.append(r)
    return results


async def _canonical_order_item_sku(db: AsyncSession, order: Order, sku: str) -> str:
    """Normalize legacy packing material IDs like PKG-<inventory UUID> to real inventory SKUs."""
    raw = (sku or "").strip()
    candidate = raw.removeprefix("PKG-")

    try:
        item_id = UUID(candidate)
    except (TypeError, ValueError):
        return raw

    filters = [InventoryItem.id == item_id]
    if order.warehouse_id:
        filters.append(InventoryItem.warehouse_id == order.warehouse_id)

    inventory_item = (await db.execute(select(InventoryItem).where(*filters))).scalar_one_or_none()
    return inventory_item.sku if inventory_item and inventory_item.sku else raw


async def upsert_order_items(
    db: AsyncSession,
    order_id: UUID,
    items: list[OrderItemUpsert],
) -> list[OrderItemResponse]:
    order = await _get_order(db, order_id)

    existing_by_sku = {item.sku: item for item in order.items}
    for item_data in items:
        sku = await _canonical_order_item_sku(db, order, item_data.sku)
        existing = existing_by_sku.get(sku)
        if existing:
            existing.quantity = item_data.quantity
            existing.box_count = item_data.box_count
            existing.estimated_volume = item_data.estimated_volume
            db.add(existing)
            continue

        new_item = OrderItem(
            order_id=order.id,
            sku=sku,
            quantity=item_data.quantity,
            box_count=item_data.box_count,
            estimated_volume=item_data.estimated_volume,
        )
        db.add(new_item)
        existing_by_sku[sku] = new_item

    await db.flush()
    refreshed = await _get_order(db, order_id)
    return [OrderItemResponse.model_validate(item) for item in refreshed.items]
