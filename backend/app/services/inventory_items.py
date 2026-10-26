"""Load one inventory item, shared by the inventory and restock request services."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem


async def get_inventory_item(db: AsyncSession, item_id: UUID) -> InventoryItem:
    """Return the item with this id, or answer 404 when there is none."""
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    return item
