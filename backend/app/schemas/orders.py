from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    order_type: str = Field(..., max_length=20)
    warehouse_id: UUID | None = None
    pickup_addr: str = Field(..., min_length=5)
    pickup_type: str | None = Field(default=None, max_length=20, description="'hub' or 'doorstep' for vendor orders")
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    delivery_addr: str = Field(..., min_length=5)
    cargo_weight_kg: float | None = Field(default=None, ge=0)
    cargo_volume_m3: float | None = Field(default=None, ge=0)
    cargo_type: str | None = None
    vehicle_type: str | None = None
    labor_count: int = Field(default=0, ge=0)
    base_amount: float = Field(default=0, ge=0)
    vehicle_amount: float = Field(default=0, ge=0)
    labor_amount: float = Field(default=0, ge=0)
    materials_amount: float = Field(default=0, ge=0)
    packing_amount: float = Field(default=0, ge=0)
    platform_fee: float = Field(default=0, ge=0)
    tax_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(default=0, ge=0)
    payment_mode: str | None = None
    payment_status: str = "pending"
    initial_payment_amount: float = Field(default=0, ge=0)
    initial_payment_ref: str | None = None
    initial_payment_mode: str | None = None
    initial_payment_method: str | None = None
    declared_value: float = Field(default=0, ge=0)
    service_otp: str | None = None
    service_time_block: str | None = None
    delivery_notes: str | None = None
    scheduled_at: datetime | None = None
    priority: str = "NORMAL"
    delivery_lat: float | None = None
    delivery_lng: float | None = None


class OrderUpdate(BaseModel):
    warehouse_id: UUID | None = None
    pickup_addr: str | None = Field(default=None, min_length=5)
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    delivery_addr: str | None = Field(default=None, min_length=5)
    cargo_weight_kg: float | None = Field(default=None, ge=0)
    cargo_volume_m3: float | None = Field(default=None, ge=0)
    cargo_type: str | None = None
    vehicle_type: str | None = None
    labor_count: int | None = Field(default=None, ge=0)
    base_amount: float | None = Field(default=None, ge=0)
    vehicle_amount: float | None = Field(default=None, ge=0)
    labor_amount: float | None = Field(default=None, ge=0)
    materials_amount: float | None = Field(default=None, ge=0)
    packing_amount: float | None = Field(default=None, ge=0)
    platform_fee: float | None = Field(default=None, ge=0)
    tax_amount: float | None = Field(default=None, ge=0)
    total_amount: float | None = Field(default=None, ge=0)
    payment_mode: str | None = None
    payment_status: str | None = None
    service_otp: str | None = None
    service_time_block: str | None = None
    delivery_notes: str | None = None
    scheduled_at: datetime | None = None
    delivery_lat: float | None = None
    delivery_lng: float | None = None


class OrderAssignRequest(BaseModel):
    driver_id: UUID
    vehicle_id: UUID | None = None


class CancelOrderRequest(BaseModel):
    reason: str = Field(..., min_length=3)


class OrderEscalateRequest(BaseModel):
    reason: str = Field(..., min_length=3)


class OrderItemUpsert(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    quantity: int = Field(..., gt=0)
    box_count: int | None = Field(default=None, ge=0)
    estimated_volume: float | None = Field(default=None, ge=0)


class OrderItemResponse(BaseModel):
    id: UUID
    sku: str
    name: str | None = None
    quantity: int
    box_count: int | None
    estimated_volume: float | None

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    tracking_code: str
    order_type: str
    status: str
    warehouse_substatus: str | None = None
    picking_started_at: datetime | None = None
    picking_completed_at: datetime | None = None
    packing_started_at: datetime | None = None
    packing_completed_at: datetime | None = None
    customer_id: UUID
    warehouse_id: UUID | None
    assigned_driver_id: UUID | None
    assigned_vehicle_id: UUID | None
    assigned_driver_name: str | None = None
    assigned_vehicle_code: str | None = None
    pickup_addr: str
    pickup_type: str | None = None
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    delivery_addr: str
    cargo_weight_kg: float | None = None
    cargo_volume_m3: float | None = None
    cargo_type: str | None
    vehicle_type: str | None
    labor_count: int
    base_amount: float
    vehicle_amount: float
    labor_amount: float
    materials_amount: float
    packing_amount: float
    platform_fee: float
    tax_amount: float
    total_amount: float
    carry_forward_charge_amount: float = 0
    carry_forward_charge_paid_amount: float = 0
    payment_mode: str | None
    payment_status: str
    paid_amount: float = 0
    declared_value: float = 0
    service_otp: str | None
    service_otp_sent_at: datetime | None = None
    service_otp_verified_at: datetime | None = None
    service_time_block: str | None
    scheduled_at: datetime | None
    arrived_at: datetime | None = None
    cancel_reason: str | None
    cancellation_fee: float = 0
    wallet_refund_amount: float = 0
    delivered_at: datetime | None = None
    delivery_notes: str | None = None
    pod_photos: list[str] = []
    pod_signature: str | None = None
    poc_signature: str | None = None
    job_rating: int | None = None
    job_feedback: str | None = None
    customer_rating: int | None = None
    customer_feedback: str | None = None
    packing_return_data: dict | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    escalated: bool = False
    escalation_id: UUID | None = None
    escalation_status: str | None = None
    created_at: datetime
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class OrderAssignmentPreview(BaseModel):
    warehouse_id: UUID
    warehouse_name: str
    warehouse_address: str
    assignment_type: str  # selected | auto
    message: str


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int


# ── Clustering Schemas ────────────────────────────────────────────────────────

class ClusterOrderItem(BaseModel):
    id: UUID
    tracking_code: str
    delivery_addr: str
    pickup_addr: str
    cargo_type: str | None = None
    vehicle_type: str | None = None
    total_amount: float = 0
    scheduled_at: datetime | None = None
    delivery_lat: float | None = None
    delivery_lng: float | None = None

    model_config = {"from_attributes": True}


class OrderCluster(BaseModel):
    cluster_id: int
    centroid_lat: float
    centroid_lng: float
    orders: list[ClusterOrderItem]
    total_distance_km: float
    efficiency_pct: float
    total_weight: float
    time_window: str
    order_count: int


class ClusterResponse(BaseModel):
    clusters: list[OrderCluster]
    unbatched: list[ClusterOrderItem]
    total_orders: int
    estimated_miles_saved_pct: float
    avg_efficiency_pct: float


# ── AI Dispatch Schemas ────────────────────────────────────────────────────────

class DriverSuggestionItem(BaseModel):
    order_id: str
    order_tracking_code: str
    pickup_addr: str
    delivery_addr: str
    priority: str
    suggested_driver_id: str
    suggested_driver_name: str
    distance_km: float | None
    confidence: int
    reason: str
    ai_powered: bool = True


class DriverSuggestionResponse(BaseModel):
    suggestions: list[DriverSuggestionItem]
    total: int


class ReturnTripSuggestionItem(BaseModel):
    driver_id: str
    driver_name: str
    pending_order_id: str
    pending_tracking_code: str
    pickup_addr: str
    delivery_addr: str
    distance_km: float
    priority: str
    delivered_minutes_ago: int
    last_delivery_addr: str
    reason: str
    ai_powered: bool = True


class ReturnTripResponse(BaseModel):
    suggestions: list[ReturnTripSuggestionItem]
    total: int


class BatchAssignment(BaseModel):
    order_id: UUID
    driver_id: UUID
    vehicle_id: UUID | None = None


class BatchConfirmRequest(BaseModel):
    assignments: list[BatchAssignment]


class DeliveryOtpSendResponse(BaseModel):
    message: str
    email: str
    sent_at: datetime
    debug_otp: str | None = None


class TripRouteSignal(BaseModel):
    key: str
    label: str
    severity: str


class TripRouteWaypoint(BaseModel):
    lat: float
    lng: float


class TripRouteOption(BaseModel):
    route_id: str
    label: str
    eta_minutes: int
    eta_label: str
    distance_km: float
    delta_minutes: int = 0
    summary: str
    recommended: bool = False
    waypoints: list[TripRouteWaypoint] = Field(default_factory=list)


class OrderTripIntelligenceItem(BaseModel):
    order_id: UUID
    tracking_code: str
    order_status: str
    driver_id: UUID | None = None
    driver_name: str | None = None
    vehicle_id: UUID | None = None
    vehicle_code: str | None = None
    pickup_addr: str
    delivery_addr: str
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    delivery_lat: float | None = None
    delivery_lng: float | None = None
    origin_lat: float | None = None
    origin_lng: float | None = None
    priority: str = "NORMAL"
    trip_stage: str
    route_status: str
    risk_level: str
    eta_label: str
    eta_minutes: int
    delay_probability_pct: int
    eta_confidence: str
    planned_distance_km: float
    no_go_zone_hit: bool = False
    signal_count: int = 0
    signals: list[TripRouteSignal] = Field(default_factory=list)
    dispatcher_recommendation: str
    driver_message: str
    primary_route: TripRouteOption
    alternate_route: TripRouteOption
    recommended_route: str
    generated_at: datetime


class TripCommandPushRequest(BaseModel):
    selected_route: str = Field(default="recommended", min_length=3, max_length=20)
    dispatcher_note: str | None = Field(default=None, max_length=280)


class TripDeviationReportRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=160)
    details: str | None = Field(default=None, max_length=280)
    latitude: float | None = None
    longitude: float | None = None


# ── Request bodies for single-order actions ─────────────────────────────────


class DeliveryOtpSendRequest(BaseModel):
    force_resend: bool = False


class PODRequest(BaseModel):
    otp_code: str | None = None
    image_data: str | None = None
    images_data: list[str] = []
    signature_data: str | None = None
    customer_name: str | None = None
    notes: str | None = None


class PayOrderRequest(BaseModel):
    payment_ref: str | None = None
    payment_mode: str = "ONLINE"     # ONLINE | COD | PARTIAL
    payment_method: str | None = None
    amount: float | None = None      # defaults to order.total_amount
    notes: str | None = None


class HouseShiftSignoffRequest(BaseModel):
    signature_data: str
    customer_name: str | None = None
    notes: str | None = None


class JobRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = None


class CustomerRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = None


class PackingReturnItem(BaseModel):
    name: str
    sku: str | None = None
    count: int = 0


class PackingReturnRequest(BaseModel):
    items: list[PackingReturnItem]
    notes: str | None = None
    submitted_at: str | None = None
    skipped: bool = False


class AssetLogItem(BaseModel):
    name: str
    sku: str | None = None
    sent_out: int = 0
    returned: int = 0


class AssetLogRequest(BaseModel):
    items: list[AssetLogItem]
    notes: str | None = None
