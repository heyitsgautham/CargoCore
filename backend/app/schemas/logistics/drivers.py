"""Driver app payloads: shifts, telemetry, manifests, earnings and dispatch messages."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.logistics.views import LogisticsVehicleItem


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
