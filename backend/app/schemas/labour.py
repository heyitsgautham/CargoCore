from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LabourerCreate(BaseModel):
    """Create a new labourer - either with existing user_id or create new with name/phone"""
    user_id: UUID | None = None
    warehouse_id: UUID | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skill_tags: list[str] | None = None
    role: str | None = None
    department: str | None = None


class LabourerUpdate(BaseModel):
    warehouse_id: UUID | None = None
    skill_tags: list[str] | None = None
    is_active: bool | None = None
    assigned_order_id: UUID | None = None


class LabourerResponse(BaseModel):
    id: UUID
    user_id: UUID
    warehouse_id: UUID
    assigned_order_id: UUID | None
    assigned_order_tracking: str | None = None
    assigned_order_substatus: str | None = None
    skill_tags: list[str] | None
    is_active: bool
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    full_name: str | None = None
    status: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LabourerListResponse(BaseModel):
    items: list[LabourerResponse]
    total: int
    page: int
    page_size: int


class LabourAttendanceResponse(BaseModel):
    id: UUID
    labourer_id: UUID
    event_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignLabourResponse(BaseModel):
    message: str
    labourer_id: UUID
    order_id: UUID


class AvailabilityItem(BaseModel):
    labourer_id: UUID
    user_id: UUID
    warehouse_id: UUID
    skill_tags: list[str] | None


class LabourAvailabilityResponse(BaseModel):
    date: str
    items: list[AvailabilityItem]
