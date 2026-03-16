from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WarehouseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    address: str = Field(..., min_length=5)
    lat: float | None = None
    lng: float | None = None
    manager_id: UUID | None = None
    capacity_limit: int | None = Field(default=None, ge=0)


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    address: str | None = Field(default=None, min_length=5)
    lat: float | None = None
    lng: float | None = None
    manager_id: UUID | None = None
    capacity_limit: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class FloorPlanUpdate(BaseModel):
    floor_plan_json: dict


class WarehouseResponse(BaseModel):
    id: UUID
    name: str
    address: str
    lat: float | None
    lng: float | None
    manager_id: UUID | None
    floor_plan_json: dict | None
    capacity_limit: int | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WarehouseKPIResponse(BaseModel):
    warehouse_id: UUID
    user_count: int
    inventory_sku_count: int
    low_stock_count: int
    labour_count: int
    order_count: int


class WarehouseListResponse(BaseModel):
    items: list[WarehouseResponse]
    total: int
    page: int
    page_size: int
