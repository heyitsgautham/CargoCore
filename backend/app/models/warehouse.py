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


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    floor_plan_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    capacity_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hub_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    users = relationship(
        "User",
        back_populates="warehouse",
        foreign_keys="User.warehouse_id",
    )
    inventory_items = relationship("InventoryItem", back_populates="warehouse")
    labourers = relationship("Labourer", back_populates="warehouse")
    orders = relationship("Order", back_populates="warehouse")
    # Docks, stations and zone metrics belong to the hub and go with it.
    loading_docks = relationship("LoadingDock", back_populates="warehouse", cascade="all, delete-orphan")
    packing_stations = relationship("PackingStation", back_populates="warehouse", cascade="all, delete-orphan")
    quality_checks = relationship("QualityCheck", back_populates="warehouse")
    return_gradings = relationship("ReturnGrading", back_populates="warehouse")
    zone_metrics = relationship("WarehouseZoneMetrics", back_populates="warehouse", cascade="all, delete-orphan")


class LoadingDock(Base):
    """Loading dock for truck arrivals and departures."""
    __tablename__ = "loading_docks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    dock_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="FREE")  # FREE, OCCUPIED, MAINTENANCE
    assigned_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("logistics_vehicles.id"), nullable=True)
    assigned_carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    loading_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    warehouse = relationship("Warehouse", back_populates="loading_docks")
    assigned_order = relationship("Order", foreign_keys=[assigned_order_id])
    assigned_vehicle = relationship("LogisticsVehicle", foreign_keys=[assigned_vehicle_id])


class PackingStation(Base):
    """Packing station for order fulfillment."""
    __tablename__ = "packing_stations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    station_number: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="CLOSED")  # ACTIVE, CLOSED, MAINTENANCE
    assigned_labourer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("labourers.id"), nullable=True)
    current_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    items_packed_today: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    warehouse = relationship("Warehouse", back_populates="packing_stations")
    assigned_labourer = relationship("Labourer", foreign_keys=[assigned_labourer_id])
    current_order = relationship("Order", foreign_keys=[current_order_id])


class QualityCheck(Base):
    """Quality check record for packed orders."""
    __tablename__ = "quality_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, unique=True)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    performed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    goods_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    count_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    packaging_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    labor_assigned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    weight_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    label_attached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    order = relationship("Order", foreign_keys=[order_id])
    warehouse = relationship("Warehouse", back_populates="quality_checks")
    performer = relationship("User", foreign_keys=[performed_by])


class ReturnGrading(Base):
    """Return grading record for returned items."""
    __tablename__ = "return_gradings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    rma_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    item_condition: Mapped[str] = mapped_column(String(50), nullable=False)  # Like New, Minor Wear, Damaged, Broken
    condition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    disposition: Mapped[str] = mapped_column(String(30), nullable=False)  # restock, claims, discard, recycle
    is_genuine: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    recommended_outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    inspection_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    damage_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    graded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, completed

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    warehouse = relationship("Warehouse", back_populates="return_gradings")
    order = relationship("Order", foreign_keys=[order_id])
    grader = relationship("User", foreign_keys=[graded_by])


class WarehouseZoneMetrics(Base):
    """Daily metrics for warehouse zones."""
    __tablename__ = "warehouse_zone_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    zone_id: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)

    orders_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    picking_accuracy_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    active_pickers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    capacity_used_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    throughput_items_per_hour: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    warehouse = relationship("Warehouse", back_populates="zone_metrics")
