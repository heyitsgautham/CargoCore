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


class DriverValidationItem(BaseModel):
    id: str
    label: str
    status: str
    ok: bool
    icon: str


class DriverShiftSummary(BaseModel):
    shift_code: str
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    warehouse_name: str | None = None
    active_order_count: int = 0
    last_vehicle_code: str | None = None
    profile_stats: dict = Field(default_factory=dict)
    validations: list[DriverValidationItem] = Field(default_factory=list)


class DriverHosSummary(BaseModel):
    used_minutes: int
    remaining_minutes: int
    max_minutes: int = 14 * 60
    progress_percent: int
    used_label: str
    remaining_label: str
    max_label: str
    warning_level: str = "ok"


class DriverCrewMemberItem(BaseModel):
    labourer_id: UUID
    user_id: UUID
    name: str
    role: str
    phone: str | None = None
    status: str
    checked_in: bool = False
    check_in_time: str | None = None
    photo: str | None = None


class DriverTelemetryResponse(BaseModel):
    gps_live: bool
    latitude: float | None = None
    longitude: float | None = None
    speed_kmh: int = 0
    distance_covered_km: float = 0
    fuel_level_pct: int | None = None
    range_km: int | None = None
    odometer_km: int | None = None
    capacity_tons: float | None = None
    seat_capacity: int | None = None
    vehicle_id: UUID | None = None
    vehicle_code: str | None = None
    telemetry_status: str | None = None
    last_updated: datetime | None = None


# ── Dispatcher Manifest schemas ───────────────────────────────────────────────

class ManifestCrewMember(BaseModel):
    name: str
    role: str


class LogisticsManifestCreate(BaseModel):
    route_id: str
    driver_name: str
    driver_id: UUID | None = None
    vehicle_code: str | None = None
    hub_name: str | None = None
    crew_config: str | None = None
    orders_count: int = 0
    total_weight: float = 0
    total_distance: float = 0
    stop_count: int = 0
    total_volume: float = 0
    est_duration: str | None = None
    fragile_count: int = 0
    cod_count: int = 0
    crew_list: list[ManifestCrewMember] | None = None


class LogisticsManifestItem(BaseModel):
    id: UUID
    route_id: str
    driver_name: str
    driver_id: UUID | None = None
    vehicle_code: str | None = None
    hub_name: str | None = None
    crew_config: str | None = None
    status: str
    orders_count: int
    total_weight: float
    total_distance: float
    stop_count: int
    total_volume: float
    est_duration: str | None = None
    fragile_count: int
    cod_count: int
    crew_list: list[ManifestCrewMember] | None = None
    pushed: bool
    pushed_at: datetime | None = None
    created_at: datetime


class LogisticsManifestPushRequest(BaseModel):
    pass  # future fields if needed


class LogisticsManifestStatusUpdate(BaseModel):
    status: str


class DriverManifestSummary(BaseModel):
    route_id: str | None = None
    date: str
    total_stops: int
    completed_stops: int
    total_distance_km: float
    estimated_duration_minutes: int
    estimated_end_time: str
    zone: str | None = None
    parcel_count: int = 0
    crew_count: int = 0
    cod_collected: float = 0
    current_location_label: str | None = None


class DriverEarnings(BaseModel):
    today_base: float = 0
    today_deliveries: float = 0
    today_move: float = 0
    today_tips: float = 0
    week_base: float = 0
    week_deliveries: float = 0
    week_move: float = 0
    week_tips: float = 0
    month_base: float = 0
    month_deliveries: float = 0
    month_move: float = 0
    month_tips: float = 0
    shift_score: int = 0
    safety_score: int = 0


class DriverAuditEventItem(BaseModel):
    id: str
    icon: str
    color: str
    action: str
    detail: str
    time: str


class DriverFuelReceiptCreate(BaseModel):
    amount: float
    liters: float
    station: str
    photo_base64: str | None = None


class DriverDispatchMessageCreate(BaseModel):
    text: str


class DriverDispatchThreadItem(BaseModel):
    thread_id: str
    messages: list[dict] = Field(default_factory=list)


class DriverCashoutRequest(BaseModel):
    amount: float


class DriverDashboardContext(BaseModel):
    profile: dict = Field(default_factory=dict)
    shift: DriverShiftSummary
    hos: DriverHosSummary
    telemetry: DriverTelemetryResponse
    manifest: DriverManifestSummary
    crew: list[DriverCrewMemberItem] = Field(default_factory=list)
    current_vehicle: LogisticsVehicleItem | None = None
    current_job: dict | None = None
    earnings: DriverEarnings = Field(default_factory=DriverEarnings)


class DriverVehicleBindRequest(BaseModel):
    vehicle_id: UUID | None = None
    vehicle_code: str | None = None
