"""Read models the logistics manager dashboard and its bootstrap payload return."""

from datetime import date as date_type
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LogisticsDashboardStats(BaseModel):
    orders_today: int
    active_deliveries: int
    processing: int
    delivery_success: float
    revenue_today: float
    orders_trend: float
    revenue_trend: float
    sla_week: list[int]
    revenue_week: list[float]
    orders_week: list[int]


class LogisticsHubItem(BaseModel):
    id: UUID
    hub_code: str
    name: str
    location: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    manager: str
    manager_initials: str
    capacity: int
    efficiency: int
    staff_active: int
    staff_total: int
    vehicles_active: int
    vehicles_total: int
    process_rate: int
    status: str
    status_color: str
    bg: str


class LogisticsDriverItem(BaseModel):
    id: UUID
    hub_id: UUID | None
    name: str
    status: str
    location: str | None
    vehicle: str | None
    efficiency: int
    rating: float = 4.8
    safety_incidents: int = 0
    fuel_efficiency_score: str = "8.2 mpg"
    avg_speed: str = "55 mph"
    phone: str | None
    current_job: str | None
    avatar_color: str | None
    chat_history: list[dict] = Field(default_factory=list)


class LogisticsVehicleItem(BaseModel):
    id: UUID
    hub_id: UUID | None
    code: str
    type: str
    model: str | None
    year: int | None
    license_plate: str | None
    status: str
    driver: str
    fuel_efficiency: str | None
    mileage: int
    next_service: str | None
    maintenance_issue: str | None = None
    fuel_level_pct: int | None = None
    range_km: int | None = None
    seat_capacity: int | None = None
    cargo_capacity_tons: float | None = None
    telemetry_status: str | None = None
    telemetry_last_seen: datetime | None = None


class LogisticsMaintenanceItem(BaseModel):
    id: UUID
    hub_id: UUID | None
    issue: str
    status: str
    status_class: str


class LogisticsTransactionItem(BaseModel):
    id: UUID
    hub_id: UUID | None
    transaction_code: str | None = None
    date: str
    desc: str
    type: str
    amount: float
    status: str
    metadata_json: dict = Field(default_factory=dict)
    related_order: dict | None = None


class LogisticsUserItem(BaseModel):
    id: UUID
    hub_id: UUID | str | None
    name: str
    email: str
    role: str
    status: str
    last_login: str
    username: str
    pending_payout: float = 0
    mobile: str | None = None
    mobile_verified: bool = False
    email_verified: bool = True
    avatar: str | None = None
    approval_status: str = "APPROVED"
    approval_note: str | None = None
    approval_reviewed_at: datetime | None = None
    company_name: str | None = None
    tax_id: str | None = None
    contact_person: str | None = None
    business_email: str | None = None
    business_phone: str | None = None
    submitted_at: datetime | None = None


class LogisticsReturnCaseItem(BaseModel):
    id: UUID
    hub_id: UUID | None
    order_id: UUID | None
    customer: str
    reason: str
    flow_type: str | None = None
    condition: str
    status: str
    original_price: float
    refund_amount: float
    images: list[str] = Field(default_factory=list)
    reference_code: str
    wallet_credited: bool = False
    wm_disposition: str | None = None
    wm_is_genuine: bool | None = None
    wm_recommended_outcome: str | None = None
    wm_inspection_remarks: str | None = None
    wm_graded_at: datetime | None = None
    wm_grader_name: str | None = None
    transport_charge_amount: float = 0
    transport_charge_wallet_collected: float = 0
    transport_charge_pending_amount: float = 0
    transport_charge_status: str | None = None
    transport_charge_applied_at: datetime | None = None
    is_urgent: bool = False
    urgent_reason: str | None = None


class LogisticsZoneItem(BaseModel):
    id: UUID
    hub_id: UUID
    name: str
    type: str
    radius: float | None
    status: str
    color: str | None = None
    lat: float | None = None
    lng: float | None = None


class LogisticsChatMessageItem(BaseModel):
    id: UUID
    text: str
    sender: str
    time: str


class DispatchContactItem(BaseModel):
    user_id: UUID
    name: str
    role: str
    phone: str | None = None
    email: str | None = None
    thread_id: UUID | None = None
    last_message: str | None = None
    thread_status: str = "Offline"
    messages: list["LogisticsChatMessageItem"] = Field(default_factory=list)


class LogisticsChatThreadItem(BaseModel):
    id: UUID
    hub_id: UUID | None
    name: str
    time: str
    last_message: str | None
    status: str
    phone: str | None
    muted: bool = False
    messages: list[LogisticsChatMessageItem] = Field(default_factory=list)


class LogisticsEscalationItem(BaseModel):
    id: UUID
    hub_id: UUID | None
    title: str
    priority: str
    from_name: str
    role: str
    time: str
    description: str
    action_details: str | None
    status: str


class LogisticsEscalationStatusUpdate(BaseModel):
    status: str = Field(..., min_length=2, max_length=30)


class LogisticsAlertItem(BaseModel):
    id: UUID
    type: str
    title: str
    description: str
    severity: str
    icon: str | None
    timestamp: str
    location: str | None = None
    recommendation: str | None = None
    impact: dict | None = None


class LogisticsNotificationItem(BaseModel):
    id: UUID
    title: str
    message: str
    time: str
    created_at: datetime
    read: bool
    type: str


class LogisticsTaskItem(BaseModel):
    id: UUID
    text: str
    status: str
    target_time: datetime | None = None
    repeat: str | None = None
    created_at: datetime
    last_alert_time: datetime | None = None
    silenced: bool = False
    remaining: str = ""


class LogisticsMeetingItem(BaseModel):
    id: UUID
    topic: str
    description: str = ""
    meeting_type: str
    link: str
    date: date_type
    start_time: str
    end_time: str
    participants: list[UUID] = Field(default_factory=list)
    created_by_id: UUID
    warehouse_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class LogisticsMeetingParticipantItem(BaseModel):
    id: UUID
    name: str
    role: str
    hub_id: UUID | None = None


class LogisticsEquipmentItem(BaseModel):
    id: UUID
    hub_id: UUID | None
    item_type: str
    issued_count: int
    returned_count: int
    reference_code: str | None = None
    status: str


class LogisticsReportItem(BaseModel):
    id: str
    hub_id: UUID | str | None
    title: str
    date: str
    icon: str
    color: str


class LogisticsBootstrapResponse(BaseModel):
    dashboard_stats: LogisticsDashboardStats
    hubs: list[LogisticsHubItem]
    alerts: list[LogisticsAlertItem]
    drivers: list[LogisticsDriverItem]
    top_drivers: list[dict]
    vehicles: list[LogisticsVehicleItem]
    maintenance: list[LogisticsMaintenanceItem]
    transactions: list[LogisticsTransactionItem]
    reports: list[LogisticsReportItem]
    users: list[LogisticsUserItem]
    returns: list[LogisticsReturnCaseItem]
    zones: list[LogisticsZoneItem]
    chats: list[LogisticsChatThreadItem]
    escalations: list[LogisticsEscalationItem]
    inventory: list[dict]
    notifications: list[LogisticsNotificationItem]
    tasks: list[LogisticsTaskItem]
    ai_suggestion_chips: list[str] = Field(default_factory=list)
    ai_messages: list[dict] = Field(default_factory=list)
    finance_summary: dict = Field(default_factory=dict)
    finance_cod_records: list[dict] = Field(default_factory=list)
    finance_staff_records: list[dict] = Field(default_factory=list)
    finance_driver_records: list[dict] = Field(default_factory=list)
    fleet_logs: dict = Field(default_factory=dict)
    vehicle_documents: list[dict] = Field(default_factory=list)
    driver_documents: list[dict] = Field(default_factory=list)
    report_ai_insights: list[str] = Field(default_factory=list)
    report_damage_claims: list[dict] = Field(default_factory=list)
    report_security_logs: list[dict] = Field(default_factory=list)
    report_metrics: dict = Field(default_factory=dict)
    equipment_ledger: list[LogisticsEquipmentItem] = Field(default_factory=list)
