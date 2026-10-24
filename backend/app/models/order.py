import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="NORMAL", index=True)
    warehouse_substatus: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    assigned_driver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    pickup_addr: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'hub' or 'doorstep'
    pickup_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    pickup_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    delivery_addr: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    delivery_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    cargo_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    cargo_volume_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    cargo_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    labor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    base_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    vehicle_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    labor_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    materials_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    packing_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    platform_fee: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    carry_forward_charge_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    carry_forward_charge_paid_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    payment_mode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    paid_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    declared_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    service_otp: Mapped[str | None] = mapped_column(String(10), nullable=True)
    service_otp_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    service_otp_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    service_time_block: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pod_photos: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    pod_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    poc_signature: Mapped[str | None] = mapped_column(Text, nullable=True)  # House-shift customer sign-off
    job_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)   # Driver self-rating 1-5
    job_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)    # Driver feedback note
    customer_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)   # Customer/vendor rating of driver 1-5
    customer_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)    # Customer/vendor feedback note
    packing_return_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Driver packing asset return submission

    # Picking timestamps
    picking_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    picking_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    packing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    packing_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    warehouse = relationship("Warehouse", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    picked_items = relationship("PickedItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (UniqueConstraint("order_id", "sku", name="uq_order_items_order_id_sku"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    box_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_volume: Mapped[float | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("Order", back_populates="items")


class PickedItem(Base):
    """Tracks individual items as they are picked (supports partial picking)."""
    __tablename__ = "picked_items"
    __table_args__ = (UniqueConstraint("order_id", "sku", name="uq_picked_items_order_id_sku"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity_picked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_required: Mapped[int] = mapped_column(Integer, nullable=False)
    picked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)  # aisle/shelf/bin info
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    order = relationship("Order", back_populates="picked_items")
    picker = relationship("User", foreign_keys=[picked_by])


class CustomerQuote(Base):
    __tablename__ = "customer_quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    cargo_type: Mapped[str] = mapped_column(String(100), nullable=False)
    from_location: Mapped[str] = mapped_column(Text, nullable=False)
    to_location: Mapped[str] = mapped_column(Text, nullable=False)
    labor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    packing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class DamageReport(Base):
    __tablename__ = "damage_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    photos: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    flow_type: Mapped[str] = mapped_column(String(30), nullable=False, default="photo_review")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="reported")
    qr_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    support_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_messages: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    customer = relationship("User", foreign_keys=[customer_id])
