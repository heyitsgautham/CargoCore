from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    order_type: str = Field(..., max_length=20)
    warehouse_id: UUID | None = None
    pickup_addr: str = Field(..., min_length=5)
    delivery_addr: str = Field(..., min_length=5)
    scheduled_at: datetime | None = None


class OrderUpdate(BaseModel):
    warehouse_id: UUID | None = None
    pickup_addr: str | None = Field(default=None, min_length=5)
    delivery_addr: str | None = Field(default=None, min_length=5)
    scheduled_at: datetime | None = None


class OrderAssignRequest(BaseModel):
    driver_id: UUID
    vehicle_id: UUID | None = None


class CancelOrderRequest(BaseModel):
    reason: str = Field(..., min_length=3)


class OrderItemUpsert(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    quantity: int = Field(..., gt=0)
    box_count: int | None = Field(default=None, ge=0)
    estimated_volume: float | None = Field(default=None, ge=0)


class OrderItemResponse(BaseModel):
    id: UUID
    sku: str
    quantity: int
    box_count: int | None
    estimated_volume: float | None

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    tracking_code: str
    order_type: str
    status: str
    customer_id: UUID
    warehouse_id: UUID | None
    assigned_driver_id: UUID | None
    assigned_vehicle_id: UUID | None
    pickup_addr: str
    delivery_addr: str
    scheduled_at: datetime | None
    cancel_reason: str | None
    created_at: datetime
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
