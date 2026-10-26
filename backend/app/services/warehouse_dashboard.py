"""The warehouse manager dashboard: one payload with capacity, orders, staff, docks, alerts and activity."""

from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, InventoryMovement
from app.models.labour import Labourer
from app.models.order import DamageReport, Order, OrderItem
from app.models.user import User
from app.schemas.warehouse import (
    ChartData,
    ChartDataset,
    CriticalSkuItem,
    PickingQueueItem,
    RecentReturnItem,
    WarehouseDashboardResponse,
)
from app.services.warehouse_service import _get_warehouse


async def get_warehouse_dashboard(db: AsyncSession, warehouse_id: UUID) -> WarehouseDashboardResponse:
    """Get comprehensive dashboard data for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    # Calculate total inventory value (using average cost estimation)
    inventory_items = (
        await db.execute(
            select(InventoryItem).where(InventoryItem.warehouse_id == warehouse_id)
        )
    ).scalars().all()

    # Estimate value at ₹100 per unit average (simplified)
    total_inventory_value = sum(item.quantity_on_hand for item in inventory_items) * 100.0

    # Get inventory value from a week ago for comparison
    week_ago = datetime.now(UTC) - timedelta(days=7)
    inventory_movements_week = (
        await db.execute(
            select(InventoryMovement)
            .join(InventoryItem, InventoryMovement.item_id == InventoryItem.id)
            .where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryMovement.created_at >= week_ago
            )
        )
    ).scalars().all()

    # Calculate change percentage (simplified calculation)
    net_movement = sum(
        m.quantity if (m.movement_type or '').upper() in ['INBOUND', 'RETURN', 'RESTOCK', 'ADJUSTMENT'] else -m.quantity
        for m in inventory_movements_week
    )
    value_change = (net_movement * 100.0) / (total_inventory_value or 1)
    inventory_value_change_percent = round(value_change, 1)

    # Get orders data
    all_orders = (
        await db.execute(
            select(Order).where(Order.warehouse_id == warehouse_id)
        )
    ).scalars().all()

    # Pending orders (PENDING, PICKING, PACKING status)
    pending_statuses = ['PENDING', 'PICKING', 'PACKING', 'CONFIRMED']
    pending_orders = [o for o in all_orders if o.status in pending_statuses]

    # Ready for dispatch
    ready_for_dispatch = len([o for o in all_orders if o.status in ['PACKED', 'READY']])

    # Labor stats
    all_laborers = (
        await db.execute(
            select(Labourer).where(Labourer.warehouse_id == warehouse_id)
        )
    ).scalars().all()

    total_labor = len(all_laborers)
    active_labor = len([laborer for laborer in all_laborers if laborer.is_active])

    # Critical SKUs (low stock)
    critical_items = (
        await db.execute(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.quantity_on_hand <= InventoryItem.safety_stock
            )
        )
    ).scalars().all()

    critical_skus = [
        CriticalSkuItem(
            id=item.sku,
            name=item.name,
            current=item.quantity_on_hand,
            min=item.safety_stock,
            sku=item.sku
        )
        for item in critical_items
    ]

    # Picking queue (orders with PICKING or PENDING status with assigned laborers)
    picking_queue_orders = (
        await db.execute(
            select(Order, func.count(OrderItem.id).label('item_count'))
            .join(OrderItem, Order.id == OrderItem.order_id, isouter=True)
            .where(
                Order.warehouse_id == warehouse_id,
                Order.status.in_(['PENDING', 'PICKING', 'PACKING', 'CONFIRMED'])
            )
            .group_by(Order.id)
            .order_by(Order.created_at.desc())
            .limit(20)
        )
    ).all()

    picking_queue = []
    for order, item_count in picking_queue_orders:
        # Get assigned user if any
        assigned_name = None
        assigned_initials = ""
        if order.assigned_driver_id:
            assigned_user = (
                await db.execute(select(User).where(User.id == order.assigned_driver_id))
            ).scalar_one_or_none()
            if assigned_user:
                assigned_name = assigned_user.name
                assigned_initials = "".join([word[0].upper() for word in assigned_name.split()[:2]])

        # Determine progress and priority
        progress = 0
        if order.status == 'PICKING':
            progress = 50
        elif order.status == 'PACKING':
            progress = 75
        elif order.status == 'PACKED':
            progress = 100

        priority = 'High' if order.order_type == 'EXPRESS' else 'Normal'

        # Determine zone from inventory items
        zone = 'A-01'  # Default
        if item_count > 0:
            first_item = (
                await db.execute(
                    select(OrderItem).where(OrderItem.order_id == order.id).limit(1)
                )
            ).scalar_one_or_none()
            if first_item:
                inv_item = (
                    await db.execute(
                        select(InventoryItem).where(
                            InventoryItem.warehouse_id == warehouse_id,
                            InventoryItem.sku == first_item.sku
                        )
                    )
                ).scalar_one_or_none()
                if inv_item and inv_item.aisle:
                    zone = inv_item.aisle

        picking_queue.append(
            PickingQueueItem(
                id=order.tracking_code,
                order_id=str(order.id),
                items=item_count or 0,
                zone=zone,
                priority=priority,
                assigned=assigned_name,
                assignedInitials=assigned_initials,
                progress=progress,
                status=order.status.title().replace('_', ' '),
                tracking_code=order.tracking_code
            )
        )

    # Recent returns (from damage reports)
    recent_damage_reports = (
        await db.execute(
            select(DamageReport)
            .where(DamageReport.created_at >= datetime.now(UTC) - timedelta(days=1))
            .order_by(desc(DamageReport.created_at))
            .limit(5)
        )
    ).scalars().all()

    recent_returns = [
        RecentReturnItem(
            id=report.reference_code,
            description=report.description[:50] + '...' if len(report.description) > 50 else report.description,
            action='Scrap' if report.status == 'rejected' else 'Restock',
            created_at=report.created_at
        )
        for report in recent_damage_reports
    ]

    # Chart data - Throughput (hourly orders for today in IST, dynamic window up to current hour)
    IST = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(IST)
    today_ist = now_ist.date()
    today_start_ist = datetime.combine(today_ist, datetime.min.time(), tzinfo=IST)

    start_hour = 6  # 6 AM IST
    end_hour = max(now_ist.hour, 13)  # extend to at least 13:00 IST

    hour_labels = [f"{h:02d}:00" for h in range(start_hour, end_hour + 1)]
    hourly_picks = []

    for hour in range(start_hour, end_hour + 1):
        hour_start = today_start_ist + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)

        # Count orders placed in this hour for this warehouse
        order_count = (
            await db.execute(
                select(func.count(Order.id))
                .where(
                    Order.warehouse_id == warehouse_id,
                    Order.created_at >= hour_start,
                    Order.created_at < hour_end
                )
            )
        ).scalar_one()

        # Also count outbound inventory movements (actual picks by staff)
        pick_count = (
            await db.execute(
                select(func.coalesce(func.count(InventoryMovement.id), 0))
                .join(InventoryItem, InventoryMovement.item_id == InventoryItem.id)
                .where(
                    InventoryItem.warehouse_id == warehouse_id,
                    func.upper(InventoryMovement.movement_type).in_(['OUTBOUND', 'PICK', 'ISSUE']),
                    InventoryMovement.created_at >= hour_start,
                    InventoryMovement.created_at < hour_end
                )
            )
        ).scalar_one()

        hourly_picks.append(int(order_count or 0) + int(pick_count or 0))

    throughput_chart = ChartData(
        labels=hour_labels,
        datasets=[ChartDataset(
            label='Items Picked',
            data=hourly_picks,
            borderColor='#14b8a6',
            backgroundColor='rgba(20, 184, 166, 0.1)',
            borderWidth=2,
            tension=0.4,
            fill=True
        )]
    )

    # Orders vs Returns (last 7 days)
    daily_orders = []
    daily_returns = []
    day_labels = []

    for i in range(7):
        day = today_ist - timedelta(days=6 - i)
        day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=UTC)
        day_end = day_start + timedelta(days=1)

        day_labels.append(day.strftime('%a'))

        order_count = (
            await db.execute(
                select(func.count(Order.id))
                .where(
                    Order.warehouse_id == warehouse_id,
                    Order.created_at >= day_start,
                    Order.created_at < day_end
                )
            )
        ).scalar_one()

        return_count = (
            await db.execute(
                select(func.count(DamageReport.id))
                .where(
                    DamageReport.created_at >= day_start,
                    DamageReport.created_at < day_end
                )
            )
        ).scalar_one()

        daily_orders.append(order_count)
        daily_returns.append(return_count)

    orders_returns_chart = ChartData(
        labels=day_labels,
        datasets=[
            ChartDataset(
                label='Outbound Orders',
                data=daily_orders,
                backgroundColor='#3b82f6',
                borderRadius=4
            ),
            ChartDataset(
                label='Inbound Returns',
                data=daily_returns,
                backgroundColor='#fb7185',
                borderRadius=4
            )
        ]
    )

    # Stock composition (by category)
    category_counts = (
        await db.execute(
            select(
                InventoryItem.category,
                func.sum(InventoryItem.quantity_on_hand).label('total_qty')
            )
            .where(InventoryItem.warehouse_id == warehouse_id)
            .group_by(InventoryItem.category)
        )
    ).all()

    total_inventory = sum(row.total_qty for row in category_counts) or 1

    # Default categories if none exist
    if not category_counts:
        stock_packaging_chart = ChartData(
            labels=['No Data'],
            datasets=[ChartDataset(
                label='Inventory',
                data=[100],
                backgroundColor=['#10b981'],
                borderWidth=1,
                borderColor='#1f2937',
                hoverOffset=4
            )]
        )
    else:
        stock_packaging_chart = ChartData(
            labels=[row.category or 'Uncategorized' for row in category_counts],
            datasets=[ChartDataset(
                label='Inventory',
                data=[round((row.total_qty / total_inventory) * 100, 1) for row in category_counts],
                backgroundColor=['#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#3b82f6', '#ec4899'],
                borderWidth=1,
                borderColor='#1f2937',
                hoverOffset=4
            )]
        )

    # Active staff distribution (warehouse workers vs drivers)
    active_staff_chart = ChartData(
        labels=['Warehouse Floor Staff', 'Active Delivery Drivers'],
        datasets=[ChartDataset(
            label='Active Staff',
            data=[active_labor, 0],  # TODO: Add driver count when driver model is available
            backgroundColor=['#eab308', '#0ea5e9'],
            borderWidth=0,
            hoverOffset=6
        )]
    )

    # Labor distribution by task
    assigned_laborers = len([laborer for laborer in all_laborers if laborer.assigned_order_id])
    idle_laborers = active_labor - assigned_laborers

    # Simplified distribution
    picking_labor = int(assigned_laborers * 0.5)
    packing_labor = int(assigned_laborers * 0.3)
    receiving_labor = int(assigned_laborers * 0.2)

    labor_distribution_chart = ChartData(
        labels=['Picking (Zone A)', 'Packing', 'Receiving', 'Idle'],
        datasets=[ChartDataset(
            label='Labor',
            data=[picking_labor, packing_labor, receiving_labor, idle_laborers],
            backgroundColor=['#14b8a6', '#3b82f6', '#a855f7', '#eab308'],
            borderWidth=0,
            hoverOffset=6
        )]
    )

    # Calculate average pick time (simplified - based on recent completed orders)
    completed_orders_today = (
        await db.execute(
            select(Order)
            .where(
                Order.warehouse_id == warehouse_id,
                Order.status.in_(['PACKED', 'READY', 'DISPATCHED']),
                Order.updated_at >= today_start_ist
            )
        )
    ).scalars().all()

    # Simplified avg: assume 10-15 minutes per order
    avg_pick_time = 12 if len(completed_orders_today) > 0 else 10

    # Next truck estimate (simplified)
    next_truck_minutes = 15  # TODO: Connect to actual dispatch schedule

    # Efficiency insight (analyze recent activity)
    efficiency_insight = "All zones operating at normal efficiency."
    if active_labor < total_labor * 0.5:
        efficiency_insight = f"Labor utilization at {round((active_labor/total_labor)*100)}%. Consider scheduling more staff."
    elif len(critical_skus) > 5:
        efficiency_insight = f"{len(critical_skus)} SKUs below safety stock. Restock orders recommended."

    return WarehouseDashboardResponse(
        total_inventory_value=round(total_inventory_value, 2),
        inventory_value_change_percent=inventory_value_change_percent,
        pending_orders_count=len(pending_orders),
        avg_pick_time_minutes=avg_pick_time,
        ready_for_dispatch=ready_for_dispatch,
        next_truck_minutes=next_truck_minutes,
        active_labor=active_labor,
        total_labor=total_labor,
        critical_skus=critical_skus,
        picking_queue=picking_queue,
        recent_returns=recent_returns,
        throughput_chart=throughput_chart,
        orders_returns_chart=orders_returns_chart,
        stock_packaging_chart=stock_packaging_chart,
        active_staff_chart=active_staff_chart,
        labor_distribution_chart=labor_distribution_chart,
        efficiency_insight=efficiency_insight
    )
