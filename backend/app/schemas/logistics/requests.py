"""Request bodies for creating and updating logistics records, plus documents and the AI query."""

from datetime import date as date_type
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LogisticsVehicleCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    vehicle_type: str = Field(..., min_length=2, max_length=100)
    warehouse_id: UUID | None = None
    assigned_driver_id: UUID | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=1990, le=2100)
    license_plate: str | None = None
    status: str = "Active"
    fuel_efficiency: str | None = None
    mileage: int = Field(default=0, ge=0)
    next_service_date: datetime | None = None
    maintenance_issue: str | None = None


class LogisticsVehicleUpdate(BaseModel):
    warehouse_id: UUID | None = None
    assigned_driver_id: UUID | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=1990, le=2100)
    license_plate: str | None = None
    status: str | None = None
    fuel_efficiency: str | None = None
    mileage: int | None = Field(default=None, ge=0)
    next_service_date: datetime | None = None
    maintenance_issue: str | None = None


class LogisticsDriverCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    phone: str | None = None
    warehouse_id: UUID | None = None
    status: str = "Active"
    current_location: str | None = None
    driver_id: str | None = Field(default=None, min_length=3, max_length=64)
    pin: str | None = Field(default=None, min_length=4, max_length=4)


class LogisticsDriverUpdate(BaseModel):
    status: str | None = None
    current_location: str | None = None
    current_job: str | None = None
    warehouse_id: UUID | None = None
    efficiency_score: int | None = None


class LogisticsTransactionCreate(BaseModel):
    warehouse_id: UUID | None = None
    description: str = Field(..., min_length=2, max_length=255)
    transaction_type: str = Field(..., min_length=2, max_length=50)
    amount: float
    status: str = "Completed"
    metadata_json: dict | None = None


class CapitalInvestmentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=2, max_length=255)
    funding_source: str = Field(default="OFFLINE_CAPITAL", max_length=30)
    warehouse_id: UUID | None = None
    investment_date: str | None = None


class LogisticsReturnCaseUpdate(BaseModel):
    status: str = Field(..., min_length=2, max_length=30)
    refund_amount: float | None = None
    condition: str | None = None
    notes: str | None = None
    apply_transport_charge: bool = False


class LogisticsZoneCreate(BaseModel):
    warehouse_id: UUID
    name: str = Field(..., min_length=2, max_length=255)
    zone_type: str = Field(..., min_length=2, max_length=50)
    radius_km: float | None = None
    status: str = "Active"
    color_token: str | None = None
    lat: float | None = None
    lng: float | None = None


class LogisticsZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    zone_type: str | None = Field(default=None, min_length=2, max_length=50)
    radius_km: float | None = None
    status: str | None = None
    color_token: str | None = None
    lat: float | None = None
    lng: float | None = None


class LogisticsChatMessageCreate(BaseModel):
    text: str = Field(..., min_length=1)
    sender: str = Field(default="me", min_length=2, max_length=30)


class LogisticsChatThreadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = None
    warehouse_id: UUID | None = None


class LogisticsChatThreadUpdate(BaseModel):
    muted: bool


class LogisticsTaskUpdate(BaseModel):
    text: str | None = None
    status: str | None = None
    silenced: bool | None = None
    target_time: datetime | None = None
    repeat: str | None = None
    last_alert_time: datetime | None = None


class LogisticsTaskCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    status: str = Field(default="To Do")
    target_time: datetime | None = None
    repeat: str | None = None


class LogisticsMeetingCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    meeting_type: str = Field(default="other", max_length=30)
    link: str = Field(default="", max_length=2000)
    date: date_type
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    participants: list[UUID] = Field(default_factory=list)


class LogisticsMeetingUpdate(BaseModel):
    topic: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    meeting_type: str | None = Field(default=None, max_length=30)
    link: str | None = Field(default=None, min_length=5, max_length=2000)
    date: date_type | None = None
    start_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    end_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    participants: list[UUID] | None = None


class LogisticsNotificationUpdate(BaseModel):
    read: bool


class LogisticsDocumentItem(BaseModel):
    id: UUID
    entity_type: str
    entity_id: str
    hub_id: UUID | None = None
    doc_type: str
    document_url: str | None = None
    status: str
    expiry_date: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LogisticsDocumentCreate(BaseModel):
    entity_type: str = Field(..., min_length=2, max_length=50)
    entity_id: str = Field(..., min_length=2, max_length=50)
    hub_id: UUID | None = None
    doc_type: str = Field(..., min_length=2, max_length=100)
    document_url: str | None = None
    expiry_date: datetime | None = None


class LogisticsDocumentUpdateStatus(BaseModel):
    status: str = Field(..., min_length=2, max_length=50)
    notes: str | None = None


class LogisticsAiQueryRequest(BaseModel):
    query: str = Field(..., min_length=2)


class LogisticsAiQueryResponse(BaseModel):
    text: str
    data: dict | None = None
