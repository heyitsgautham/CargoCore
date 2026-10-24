"""Zone metrics and warehouse performance metrics."""

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.labour import Labourer
from app.models.order import Order
from app.models.warehouse import (
    WarehouseZoneMetrics,
)
from app.schemas.warehouse_operations import (
    PerformanceMetrics,
    PerformanceResponse,
    ZoneMetricsCreate,
    ZoneMetricsListResponse,
    ZoneMetricsResponse,
)
from app.services.warehouse_ops.common import TERMINAL_ORDER_STATUSES, _get_warehouse

# ======================
# Zone Metrics Operations
# ======================

async def get_zone_metrics(
    db: AsyncSession,
    warehouse_id: UUID,
    zone_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ZoneMetricsListResponse:
    """Get metrics for a specific zone."""
    await _get_warehouse(db, warehouse_id)

    query = select(WarehouseZoneMetrics).where(
        WarehouseZoneMetrics.warehouse_id == warehouse_id,
        WarehouseZoneMetrics.zone_id == zone_id,
    )

    if date_from:
        query = query.where(WarehouseZoneMetrics.metric_date >= date_from)
    if date_to:
        query = query.where(WarehouseZoneMetrics.metric_date <= date_to)

    query = query.order_by(WarehouseZoneMetrics.metric_date.desc())

    result = await db.execute(query)
    metrics = result.scalars().all()

    items = [
        ZoneMetricsResponse(
            id=m.id,
            warehouse_id=m.warehouse_id,
            zone_id=m.zone_id,
            metric_date=m.metric_date,
            orders_processed=m.orders_processed,
            picking_accuracy_pct=m.picking_accuracy_pct,
            active_pickers=m.active_pickers,
            capacity_used_pct=m.capacity_used_pct,
            throughput_items_per_hour=m.throughput_items_per_hour,
            created_at=m.created_at,
        )
        for m in metrics
    ]

    return ZoneMetricsListResponse(items=items, total=len(items))


async def record_zone_metrics(
    db: AsyncSession,
    warehouse_id: UUID,
    data: ZoneMetricsCreate,
) -> ZoneMetricsResponse:
    """Record metrics for a zone (upsert for today)."""
    await _get_warehouse(db, warehouse_id)
    today = date.today()

    # Check for existing record
    result = await db.execute(
        select(WarehouseZoneMetrics).where(
            WarehouseZoneMetrics.warehouse_id == warehouse_id,
            WarehouseZoneMetrics.zone_id == data.zone_id,
            WarehouseZoneMetrics.metric_date == today,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.orders_processed = data.orders_processed
        existing.picking_accuracy_pct = data.picking_accuracy_pct
        existing.active_pickers = data.active_pickers
        existing.capacity_used_pct = data.capacity_used_pct
        existing.throughput_items_per_hour = data.throughput_items_per_hour
        metrics = existing
    else:
        # Create new
        metrics = WarehouseZoneMetrics(
            warehouse_id=warehouse_id,
            zone_id=data.zone_id,
            metric_date=today,
            orders_processed=data.orders_processed,
            picking_accuracy_pct=data.picking_accuracy_pct,
            active_pickers=data.active_pickers,
            capacity_used_pct=data.capacity_used_pct,
            throughput_items_per_hour=data.throughput_items_per_hour,
        )
        db.add(metrics)

    await db.commit()
    await db.refresh(metrics)

    return ZoneMetricsResponse(
        id=metrics.id,
        warehouse_id=metrics.warehouse_id,
        zone_id=metrics.zone_id,
        metric_date=metrics.metric_date,
        orders_processed=metrics.orders_processed,
        picking_accuracy_pct=metrics.picking_accuracy_pct,
        active_pickers=metrics.active_pickers,
        capacity_used_pct=metrics.capacity_used_pct,
        throughput_items_per_hour=metrics.throughput_items_per_hour,
        created_at=metrics.created_at,
    )


# ======================
# Performance Metrics
# ======================

async def get_performance_metrics(
    db: AsyncSession,
    warehouse_id: UUID,
    time_range: str = "today",
) -> PerformanceResponse:
    """Get performance metrics for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    # Define date range
    now = datetime.now(UTC)
    if time_range == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == "week":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date.replace(day=start_date.day - start_date.weekday())
    elif time_range == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get orders created in the selected time period (for KPI totals and completion rate).
    result = await db.execute(
        select(Order).where(
            Order.warehouse_id == warehouse_id,
            Order.created_at >= start_date,
        )
    )
    period_orders = result.scalars().all()

    # Get ALL active (in-progress) orders for the pipeline breakdown regardless of creation date.
    # Orders can be created one day and processed over following days, so restricting by
    # created_at causes pipeline stages to show 0 for carryover orders.
    active_pipeline_statuses = [
        "AWAITING_PICK", "PICKING", "PICKED",
        "PACKING", "PACKED", "QC_PASSED",
        "READY_FOR_DISPATCH", "ON_DOCK", "ON_HOLD",
        "AWAITING_INBOUND",
    ]
    result = await db.execute(
        select(Order).where(
            Order.warehouse_id == warehouse_id,
            Order.warehouse_substatus.in_(active_pipeline_statuses),
            Order.status.notin_(TERMINAL_ORDER_STATUSES),
        )
    )
    active_orders = result.scalars().all()

    # Get labourers
    result = await db.execute(
        select(Labourer).where(Labourer.warehouse_id == warehouse_id)
    )
    labourers = result.scalars().all()

    # KPI totals: based on orders created in the period
    total_orders = len(period_orders)
    dispatched = sum(1 for o in period_orders if o.warehouse_substatus == "DISPATCHED")
    completion_rate = (dispatched / total_orders * 100) if total_orders > 0 else 0

    # Pipeline breakdown: current snapshot from active (in-progress) orders regardless of creation date
    status_breakdown: dict[str, int] = {}
    for order in active_orders:
        substatus = order.warehouse_substatus or "NONE"
        status_breakdown[substatus] = status_breakdown.get(substatus, 0) + 1
    # Fold dispatched-in-period into the breakdown for chart completeness
    status_breakdown["DISPATCHED"] = dispatched

    labor_breakdown = {"active": 0, "idle": 0, "off": 0}
    for labourer in labourers:
        if labourer.is_active:
            if labourer.assigned_order_id:
                labor_breakdown["active"] += 1
            else:
                labor_breakdown["idle"] += 1
        else:
            labor_breakdown["off"] += 1

    metrics = PerformanceMetrics(
        completion_rate=round(completion_rate, 1),
        on_hold_count=status_breakdown.get("ON_HOLD", 0),
        picking_active=status_breakdown.get("PICKING", 0),
        packing_active=status_breakdown.get("PACKING", 0),
        ready_for_dispatch=status_breakdown.get("READY_FOR_DISPATCH", 0) + status_breakdown.get("QC_PASSED", 0),
        dispatched_today=dispatched,
        total_orders=total_orders,
        status_breakdown=status_breakdown,
        labor_breakdown=labor_breakdown,
    )

    return PerformanceResponse(
        warehouse_id=warehouse_id,
        time_range=time_range,
        metrics=metrics,
    )
