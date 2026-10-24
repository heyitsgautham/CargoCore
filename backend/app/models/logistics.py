import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LogisticsDriverProfile(Base):
    __tablename__ = "logistics_driver_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Active")
    current_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_job: Mapped[str | None] = mapped_column(String(255), nullable=True)
    efficiency_score: Mapped[int] = mapped_column(Integer, nullable=False, default=85)
    avatar_color: Mapped[str | None] = mapped_column(String(30), nullable=True, default="bg-gray-700")
    chat_history: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class LogisticsVehicle(Base):
    __tablename__ = "logistics_vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(100), nullable=False)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    assigned_driver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    license_plate: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Active")
    fuel_efficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mileage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_service_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    maintenance_issue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class LogisticsTransaction(Base):
    __tablename__ = "logistics_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    transaction_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Completed")
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LogisticsZone(Base):
    __tablename__ = "logistics_zones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    zone_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Polygon")
    radius_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Active")
    color_token: Mapped[str | None] = mapped_column(String(30), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class LogisticsAlert(Base):
    __tablename__ = "logistics_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LogisticsNotification(Base):
    __tablename__ = "logistics_notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="info")
    audience_roles: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LogisticsTask(Base):
    __tablename__ = "logistics_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Priority")
    target_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    repeat_rule: Mapped[str | None] = mapped_column(String(30), nullable=True, default="none")
    silenced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_alert_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LogisticsMeeting(Base):
    __tablename__ = "logistics_meetings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    meeting_type: Mapped[str] = mapped_column(String(30), nullable=False, default="other")
    meeting_link: Mapped[str] = mapped_column(Text, nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    participant_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class LogisticsChatThread(Base):
    __tablename__ = "logistics_chat_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Online")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    messages: Mapped[list["LogisticsChatMessage"]] = relationship(
        "LogisticsChatMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="LogisticsChatMessage.created_at.asc()",
    )


class LogisticsChatMessage(Base):
    __tablename__ = "logistics_chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_chat_threads.id"), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(30), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    thread: Mapped["LogisticsChatThread"] = relationship("LogisticsChatThread", back_populates="messages")


class LogisticsEscalation(Base):
    __tablename__ = "logistics_escalations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="Medium")
    requester_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requester_role: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LogisticsReturnCase(Base):
    __tablename__ = "logistics_return_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    reference_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    flow_type: Mapped[str] = mapped_column(String(30), nullable=False, default="photo_review")
    condition: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending")
    original_price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    refund_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    transport_charge_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    transport_charge_wallet_collected: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    transport_charge_pending_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    transport_charge_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transport_charge_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    transport_charge_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    images: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    wm_is_genuine: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    wm_recommended_outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wm_inspection_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    urgent_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class LogisticsDailyStats(Base):
    __tablename__ = "logistics_daily_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    stat_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    orders_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    deliveries_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deliveries_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sla_compliance: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LogisticsMetric(Base):
    __tablename__ = "logistics_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    value_main: Mapped[float] = mapped_column(Float, nullable=False)
    value_secondary: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LogisticsEquipmentLedger(Base):
    __tablename__ = "logistics_equipment_ledger"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    issued_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    returned_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reference_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LogisticsManifest(Base):
    __tablename__ = "logistics_manifests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    driver_name: Mapped[str] = mapped_column(String(255), nullable=False)
    driver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    vehicle_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hub_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    crew_config: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Draft")
    orders_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_distance: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    stop_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_volume: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    est_duration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fragile_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cod_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    crew_list: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    pushed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
