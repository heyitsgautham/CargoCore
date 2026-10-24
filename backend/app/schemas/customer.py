from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.auth import UserProfile


class CustomerDashboardStats(BaseModel):
    total_orders: int
    active_orders: int
    pending_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_spent: float = 0


class CustomerDashboardOrder(BaseModel):
    id: UUID
    tracking_code: str
    order_type: str
    status: str
    ui_status: str
    pickup_addr: str
    delivery_addr: str
    scheduled_at: datetime | None
    created_at: datetime
    vehicle_type: str
    total_amount: float = 0


class CustomerDashboardMonthlyPoint(BaseModel):
    month: str
    count: int


class CustomerDashboardCostSummary(BaseModel):
    base: float = 0
    vehicle: float = 0
    labor: float = 0
    materials: float = 0
    packing: float = 0
    platform_fee: float = 0
    taxes: float = 0
    total: float = 0


class CustomerDashboardDriver(BaseModel):
    name: str | None = None
    phone: str | None = None
    rating: float | None = None


class CustomerDashboardActiveMove(BaseModel):
    id: UUID
    tracking_code: str
    status: str
    ui_status: str
    pickup_addr: str
    delivery_addr: str
    scheduled_at: datetime | None
    created_at: datetime
    vehicle_type: str
    cargo_type: str
    progress: int
    eta_label: str
    service_otp: str
    service_time_block: str
    labor_count: int
    driver: CustomerDashboardDriver | None = None
    cost: CustomerDashboardCostSummary


class CustomerDashboardResponse(BaseModel):
    profile: UserProfile
    stats: CustomerDashboardStats
    active_move: CustomerDashboardActiveMove | None = None
    active_moves: list[CustomerDashboardActiveMove]
    recent_orders: list[CustomerDashboardOrder]
    monthly_activity: list[CustomerDashboardMonthlyPoint]


class CustomerTrackingOrder(BaseModel):
    id: UUID
    tracking_code: str
    status: str
    ui_status: str
    warehouse_id: UUID | None = None
    warehouse_name: str | None = None
    warehouse_address: str | None = None
    warehouse_lat: float | None = None
    warehouse_lng: float | None = None
    warehouse_substatus: str | None = None
    pickup_addr: str
    delivery_addr: str
    scheduled_at: datetime | None
    created_at: datetime
    progress: int
    eta_label: str
    picking_started_at: datetime | None = None
    picking_completed_at: datetime | None = None
    packing_started_at: datetime | None = None
    packing_completed_at: datetime | None = None
    qc_passed_at: datetime | None = None
    dispatched_at: datetime | None = None
    transport_log: list[dict]


class CustomerTrackingResponse(BaseModel):
    orders: list[CustomerTrackingOrder]


class CustomerPaymentRecord(BaseModel):
    id: str
    order_id: UUID
    tracking_code: str
    amount: float
    mode: str
    status: str
    created_at: datetime


class CustomerPaymentsSummary(BaseModel):
    total_paid: float
    pending_amount: float
    records: list[CustomerPaymentRecord]


class CustomerProfileResponse(BaseModel):
    profile: UserProfile
    alt_phone: str | None = None
    date_of_birth: str | None = None
    address: str | None = None
    language: str = "en"
    currency: str = "INR"
    default_payment: str = "Full Payment"
    notification_prefs: dict[str, bool] = {}
    privacy_prefs: dict[str, bool] = {}


class CustomerQuote(BaseModel):
    id: str
    cargo_type: str
    from_location: str
    to_location: str
    labor_count: int
    packing: bool
    total: float
    date: str
    status: str


class CustomerQuotesResponse(BaseModel):
    quotes: list[CustomerQuote]


class CustomerDamageReportCreate(BaseModel):
    order_id: str
    description: str
    photos: list[str] = []
    resolution_type: str = "photo_review"


class CustomerDamageReport(BaseModel):
    id: str
    order_id: str
    description: str
    photos: list[str]
    flow_type: str | None = None
    status: str
    qr_code: str
    created_at: str
    refund_amount: float | None = None
    condition: str | None = None


class CustomerDamageReportsResponse(BaseModel):
    reports: list[CustomerDamageReport]


class DamageReviewQueueItem(BaseModel):
    id: str
    order_id: str
    customer: str
    description: str
    images: list[str] = []
    flow_type: str | None = None
    status: str


class DamageReviewUpdate(BaseModel):
    damage_severity: str | None = None
    is_genuine: bool | None = None
    recommended_settlement: str | None = None
    remarks: str | None = None
    new_status: str = "Claims Reviewed"


class CustomerSettings(BaseModel):
    language: str = "en"
    currency: str = "INR"
    default_payment: str = "Full Payment"
    notification_prefs: dict[str, bool] = {}
    privacy_prefs: dict[str, bool] = {}


class CustomerSettingsResponse(BaseModel):
    settings: CustomerSettings
