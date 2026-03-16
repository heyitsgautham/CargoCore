from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InventoryCreate(BaseModel):
    warehouse_id: UUID
    sku: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    unit: str = Field(default="pcs", min_length=1, max_length=30)
    quantity_on_hand: int = Field(default=0, ge=0)
    safety_stock: int = Field(default=0, ge=0)
    aisle: str | None = Field(default=None, max_length=30)
    shelf: str | None = Field(default=None, max_length=30)
    bin: str | None = Field(default=None, max_length=30)


class InventoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    unit: str | None = Field(default=None, min_length=1, max_length=30)
    safety_stock: int | None = Field(default=None, ge=0)
    aisle: str | None = Field(default=None, max_length=30)
    shelf: str | None = Field(default=None, max_length=30)
    bin: str | None = Field(default=None, max_length=30)


class InventoryMovementCreate(BaseModel):
    item_id: UUID
    movement_type: str = Field(..., max_length=20)
    quantity: int = Field(..., gt=0)
    reference_order_id: UUID | None = None


class InventoryResponse(BaseModel):
    id: UUID
    warehouse_id: UUID
    sku: str
    name: str
    category: str | None
    unit: str
    quantity_on_hand: int
    safety_stock: int
    aisle: str | None
    shelf: str | None
    bin: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InventoryMovementResponse(BaseModel):
    id: UUID
    item_id: UUID
    movement_type: str
    quantity: int
    reference_order_id: UUID | None
    performed_by: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InventoryListResponse(BaseModel):
    items: list[InventoryResponse]
    total: int
    page: int
    page_size: int


class PickingListItem(BaseModel):
    sku: str
    required_quantity: int
    available_quantity: int


class PickingListResponse(BaseModel):
    order_id: UUID
    items: list[PickingListItem]
