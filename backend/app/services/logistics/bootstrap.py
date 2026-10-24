"""Builds the single bootstrap payload behind the logistics manager dashboard."""

from __future__ import annotations

import re
from datetime import UTC, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import LogisticsDocument
from app.models.inventory import InventoryItem
from app.models.logistics import (
    LogisticsAlert,
    LogisticsChatMessage,
    LogisticsChatThread,
    LogisticsDailyStats,
    LogisticsDriverProfile,
    LogisticsEquipmentLedger,
    LogisticsEscalation,
    LogisticsMetric,
    LogisticsNotification,
    LogisticsReturnCase,
    LogisticsTask,
    LogisticsTransaction,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.order import DamageReport, Order
from app.models.user import Role, User
from app.models.warehouse import ReturnGrading, Warehouse
from app.schemas.logistics import (
    LogisticsAlertItem,
    LogisticsBootstrapResponse,
    LogisticsChatMessageItem,
    LogisticsChatThreadItem,
    LogisticsDashboardStats,
    LogisticsDriverItem,
    LogisticsEquipmentItem,
    LogisticsEscalationItem,
    LogisticsEscalationStatusUpdate,
    LogisticsHubItem,
    LogisticsMaintenanceItem,
    LogisticsNotificationItem,
    LogisticsReportItem,
    LogisticsReturnCaseItem,
    LogisticsTaskItem,
    LogisticsTransactionItem,
    LogisticsUserItem,
    LogisticsVehicleItem,
    LogisticsZoneItem,
)
from app.services.logistics.formatting import (
    _fmt_relative,
    _now,
    _reconcile_restock_escalations,
    _status_badge_class,
    _title_case_status,
    _to_logistics_escalation_item,
)


async def build_bootstrap(db: AsyncSession) -> LogisticsBootstrapResponse:
    await _reconcile_restock_escalations(db)
    warehouses = (await db.execute(select(Warehouse).order_by(Warehouse.created_at.asc()))).scalars().all()
    alerts = (await db.execute(select(LogisticsAlert).where(LogisticsAlert.is_active.is_(True)).order_by(LogisticsAlert.created_at.desc()))).scalars().all()
    # Bootstrap is LOGISTIC_MANAGER only — exclude per-user notifications (vendor/customer order events)
    notifications = (await db.execute(
        select(LogisticsNotification)
        .where(LogisticsNotification.target_user_id.is_(None))
        .order_by(LogisticsNotification.created_at.desc())
    )).scalars().all()
    tasks = (await db.execute(select(LogisticsTask).order_by(LogisticsTask.created_at.desc()))).scalars().all()
    driver_profiles = (await db.execute(select(LogisticsDriverProfile).order_by(LogisticsDriverProfile.created_at.asc()))).scalars().all()
    vehicles = (await db.execute(select(LogisticsVehicle).order_by(LogisticsVehicle.created_at.desc()))).scalars().all()
    transactions = (await db.execute(select(LogisticsTransaction).order_by(LogisticsTransaction.transaction_date.desc()))).scalars().all()
    zones = (await db.execute(select(LogisticsZone).order_by(LogisticsZone.created_at.desc()))).scalars().all()
    chat_threads = (await db.execute(select(LogisticsChatThread).order_by(LogisticsChatThread.created_at.desc()))).scalars().all()
    chat_messages = (await db.execute(select(LogisticsChatMessage).order_by(LogisticsChatMessage.created_at.asc()))).scalars().all()
    escalations = (await db.execute(select(LogisticsEscalation).order_by(LogisticsEscalation.created_at.desc()))).scalars().all()
    return_cases = (await db.execute(select(LogisticsReturnCase).order_by(LogisticsReturnCase.created_at.desc()))).scalars().all()
    return_gradings = (
        await db.execute(
            select(ReturnGrading)
            .options(selectinload(ReturnGrading.grader))
            .order_by(ReturnGrading.created_at.desc())
        )
    ).scalars().all()
    _all_users = (await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    _all_orders = (await db.execute(select(Order))).scalars().all()

    # Backfill: auto-create LogisticsReturnCase for any DamageReport not yet linked
    existing_ref_codes = {rc.reference_code for rc in return_cases}
    damage_reports = (await db.execute(select(DamageReport).order_by(DamageReport.created_at.desc()))).scalars().all()
    order_map = {o.id: o for o in _all_orders}
    user_map = {u.id: u for u in _all_users}
    new_cases = []
    for dr in damage_reports:
        if dr.reference_code not in existing_ref_codes:
            order_row = order_map.get(dr.order_id) if dr.order_id else None
            order_total = (order_row.total_amount or 0.0) if order_row else 0.0
            warehouse_id = order_row.warehouse_id if order_row else None
            user_row = user_map.get(dr.customer_id)
            customer_name = (user_row.name or user_row.email or str(dr.customer_id)) if user_row else str(dr.customer_id)
            new_case = LogisticsReturnCase(
                warehouse_id=warehouse_id,
                order_id=dr.order_id,
                reference_code=dr.reference_code,
                customer_name=customer_name,
                reason=(dr.description or "Damage reported")[:255],
                flow_type=getattr(dr, "flow_type", "photo_review") or "photo_review",
                condition="Reported",
                status="Pickup Requested" if (getattr(dr, "flow_type", "photo_review") == "pickup_inspection") else "Reported",
                original_price=order_total,
                refund_amount=0.0,
                images=dr.photos or [],
            )
            db.add(new_case)
            new_cases.append(new_case)

    # Backfill: warehouse/driver-side returns may create ReturnGrading records without
    # a LogisticsReturnCase entry. Surface them in Reverse Logistics so LM can still
    # see "Arrived at Warehouse" / "Physically Inspected" states.
    for grading in return_gradings:
        if not grading.rma_code or grading.rma_code in existing_ref_codes:
            continue

        order_row = order_map.get(grading.order_id) if grading.order_id else None
        user_row = user_map.get(order_row.customer_id) if order_row and order_row.customer_id else None
        customer_name = (
            user_row.name or user_row.email
            if user_row
            else (f"Order {order_row.tracking_code}" if order_row else "Warehouse Return")
        )

        if grading.status == "completed":
            derived_status = "Physically Inspected"
        elif grading.item_condition == "Awaiting Pickup":
            derived_status = "Pickup Scheduled"
        else:
            derived_status = "Arrived at Warehouse"

        new_case = LogisticsReturnCase(
            warehouse_id=grading.warehouse_id or (order_row.warehouse_id if order_row else None),
            order_id=grading.order_id,
            reference_code=grading.rma_code,
            customer_name=customer_name,
            reason=grading.condition_notes or "Warehouse return",
            flow_type="pickup_inspection",
            condition=grading.item_condition or "Pending Inspection",
            status=derived_status,
            original_price=(order_row.total_amount or 0.0) if order_row else 0.0,
            refund_amount=0.0,
            images=[],
        )
        db.add(new_case)
        new_cases.append(new_case)
        existing_ref_codes.add(grading.rma_code)

    if new_cases:
        await db.flush()
        return_cases = list(new_cases) + list(return_cases)

    # Build set of reference codes that already have a DAMAGE_REFUND wallet transaction.
    from app.models.wallet import WalletTransaction
    _credited_ref_codes: set[str] = set()
    _reference_codes = {item.reference_code for item in return_cases if item.reference_code}
    if _reference_codes:
        _dmg_txns = (await db.execute(
            select(WalletTransaction.description).where(WalletTransaction.reason == "DAMAGE_REFUND")
        )).scalars().all()
        for _desc in _dmg_txns:
            description = _desc or ""
            for reference_code in _reference_codes:
                if reference_code in description:
                    _credited_ref_codes.add(reference_code)

    latest_completed_grading_by_rma: dict[str, ReturnGrading] = {}
    latest_completed_grading_by_order_id: dict[UUID, ReturnGrading] = {}
    for grading in return_gradings:
        if grading.status != "completed":
            continue
        if grading.rma_code and grading.rma_code not in latest_completed_grading_by_rma:
            latest_completed_grading_by_rma[grading.rma_code] = grading
        if grading.order_id and grading.order_id not in latest_completed_grading_by_order_id:
            latest_completed_grading_by_order_id[grading.order_id] = grading

    def _wm_completed_grading_for_case(item: LogisticsReturnCase) -> ReturnGrading | None:
        if item.reference_code and item.reference_code in latest_completed_grading_by_rma:
            return latest_completed_grading_by_rma[item.reference_code]
        if item.order_id and item.order_id in latest_completed_grading_by_order_id:
            return latest_completed_grading_by_order_id[item.order_id]
        return None

    def _to_return_case_item(item: LogisticsReturnCase) -> LogisticsReturnCaseItem:
        completed_grading = _wm_completed_grading_for_case(item)
        is_physical_flow = getattr(item, "flow_type", None) == "pickup_inspection"
        normalized_status = item.status
        case_images = list(item.images or [])
        if completed_grading and completed_grading.damage_photo_url and completed_grading.damage_photo_url not in case_images:
            case_images.append(completed_grading.damage_photo_url)
        if not is_physical_flow and item.status in {"Inspected", "Physically Inspected"}:
            normalized_status = "Claims Reviewed"
        display_status = normalized_status
        if completed_grading and is_physical_flow and normalized_status in {"Arrived at Warehouse", "At Warehouse", "Inspected", "Physically Inspected"}:
            display_status = "Physically Inspected"
        return LogisticsReturnCaseItem(
            id=item.id,
            hub_id=item.warehouse_id,
            order_id=item.order_id,
            customer=item.customer_name,
            reason=item.reason,
            flow_type=getattr(item, "flow_type", None),
            condition=completed_grading.item_condition if (completed_grading and is_physical_flow) else item.condition,
            status=display_status,
            original_price=item.original_price,
            refund_amount=item.refund_amount,
            images=case_images,
            reference_code=item.reference_code,
            wallet_credited=item.reference_code in _credited_ref_codes,
            wm_disposition=completed_grading.disposition if (completed_grading and is_physical_flow) else None,
            wm_is_genuine=completed_grading.is_genuine if (completed_grading and is_physical_flow) else getattr(item, "wm_is_genuine", None),
            wm_recommended_outcome=completed_grading.recommended_outcome if (completed_grading and is_physical_flow) else getattr(item, "wm_recommended_outcome", None),
            wm_inspection_remarks=completed_grading.inspection_remarks if (completed_grading and is_physical_flow) else getattr(item, "wm_inspection_remarks", None),
            wm_graded_at=completed_grading.graded_at if (completed_grading and is_physical_flow) else None,
            wm_grader_name=completed_grading.grader.name if (completed_grading and is_physical_flow and completed_grading.grader) else None,
            transport_charge_amount=round(float(item.transport_charge_amount or 0.0), 2),
            transport_charge_wallet_collected=round(float(item.transport_charge_wallet_collected or 0.0), 2),
            transport_charge_pending_amount=round(float(item.transport_charge_pending_amount or 0.0), 2),
            transport_charge_status=item.transport_charge_status,
            transport_charge_applied_at=item.transport_charge_applied_at,
            is_urgent=bool(getattr(item, "is_urgent", False)),
            urgent_reason=getattr(item, "urgent_reason", None),
        )

    inventory_items = (await db.execute(select(InventoryItem).order_by(InventoryItem.created_at.desc()))).scalars().all()
    users = _all_users
    roles = (await db.execute(select(Role))).scalars().all()
    orders = _all_orders
    metrics = (await db.execute(select(LogisticsMetric).order_by(LogisticsMetric.created_at.asc()))).scalars().all()
    equipments = (await db.execute(select(LogisticsEquipmentLedger).order_by(LogisticsEquipmentLedger.created_at.desc()))).scalars().all()
    documents = (await db.execute(select(LogisticsDocument).order_by(LogisticsDocument.created_at.desc()))).scalars().all()

    role_by_id = {role.id: role.name for role in roles}
    user_map = {user.id: user for user in users}
    warehouse_map = {warehouse.id: warehouse for warehouse in warehouses}
    vehicle_map = {vehicle.id: vehicle for vehicle in vehicles}
    vehicle_by_driver = {vehicle.assigned_driver_id: vehicle for vehicle in vehicles if vehicle.assigned_driver_id}
    # For vehicles without a permanent driver assignment, resolve driver from active orders
    active_driver_by_vehicle: dict = {
        o.assigned_vehicle_id: o.assigned_driver_id
        for o in orders
        if o.status in {"ASSIGNED", "IN_TRANSIT"} and o.assigned_vehicle_id and o.assigned_driver_id
    }
    messages_by_thread: dict[UUID, list[LogisticsChatMessage]] = {}
    for message in chat_messages:
        messages_by_thread.setdefault(message.thread_id, []).append(message)

    today = _now().date()
    orders_today = sum(1 for order in orders if order.created_at.date() == today)
    active_deliveries = sum(1 for order in orders if order.status == "IN_TRANSIT")
    processing = sum(1 for order in orders if order.status in {"DRAFT", "CONFIRMED", "ASSIGNED"})
    delivered = sum(1 for order in orders if order.status in {"DELIVERED", "CLOSED"})
    delivery_success = round((delivered / len(orders)) * 100, 1) if orders else 100.0

    # Build 7-day chart arrays live from Orders table (avoids empty LogisticsDailyStats)
    week_start = today - timedelta(days=6)

    # Try LogisticsDailyStats first; fall back to live aggregation
    historical_stats = (
        await db.execute(
            select(LogisticsDailyStats)
            .where(LogisticsDailyStats.warehouse_id.is_(None))
            .where(LogisticsDailyStats.stat_date >= week_start)
            .where(LogisticsDailyStats.stat_date <= today)
            .order_by(LogisticsDailyStats.stat_date.asc())
        )
    ).scalars().all()

    if historical_stats:
        sla_week = [int(stat.sla_compliance) for stat in historical_stats[-7:]]
        revenue_week = [float(stat.revenue) for stat in historical_stats[-7:]]
        orders_week = [stat.orders_count for stat in historical_stats[-7:]]
        while len(sla_week) < 7:
            sla_week.insert(0, 0)
        while len(revenue_week) < 7:
            revenue_week.insert(0, 0)
        while len(orders_week) < 7:
            orders_week.insert(0, 0)
    else:
        # Live aggregation from Orders table for the past 7 days
        from collections import defaultdict
        daily_total: dict = defaultdict(int)
        daily_delivered: dict = defaultdict(int)
        daily_revenue: dict = defaultdict(float)

        for order in orders:
            if not order.created_at:
                continue
            d = order.created_at.date()
            if d < week_start:
                continue
            daily_total[d] += 1
            if order.status in {"DELIVERED", "CLOSED", "COMPLETED"}:
                daily_delivered[d] += 1
            daily_revenue[d] += float(order.total_amount or 0)

        sla_week = []
        revenue_week = []
        orders_week = []
        for offset in range(6, -1, -1):
            d = today - timedelta(days=offset)
            total_d = daily_total[d]
            delivered_d = daily_delivered[d]
            sla_pct = round((delivered_d / total_d) * 100) if total_d > 0 else (
                int(delivery_success)  # use overall rate for days with no orders
            )
            sla_week.append(sla_pct)
            revenue_week.append(round(daily_revenue[d], 2))
            orders_week.append(total_d)

    from app.services import finance_service as _finance_service

    finance_summary = await _finance_service.get_finance_summary(db)
    revenue_by_date = {
        str(item.get("date")): float(item.get("revenue") or 0.0)
        for item in finance_summary.get("revenue_by_day", [])
    }
    revenue_today = revenue_by_date.get(str(today), 0.0)
    revenue_week = [
        round(revenue_by_date.get(str(today - timedelta(days=offset)), 0.0), 2)
        for offset in range(6, -1, -1)
    ]
    yesterday_revenue = revenue_by_date.get(str(today - timedelta(days=1)), 0.0)
    if yesterday_revenue:
        revenue_trend = round(((revenue_today - yesterday_revenue) / abs(yesterday_revenue)) * 100, 1)
    elif revenue_today:
        revenue_trend = 100.0
    else:
        revenue_trend = 0.0

    dashboard_stats = LogisticsDashboardStats(
        orders_today=orders_today,
        active_deliveries=active_deliveries,
        processing=processing,
        delivery_success=delivery_success,
        revenue_today=round(revenue_today, 2),
        orders_trend=round((orders_today / max(len(orders), 1)) * 100, 1),
        revenue_trend=revenue_trend,
        sla_week=sla_week[-7:],
        revenue_week=revenue_week[-7:],
        orders_week=orders_week[-7:],
    )

    total_revenue = float(finance_summary.get("total_revenue", 0.0) or 0.0)
    total_expenses = float(finance_summary.get("total_expenses", 0.0) or 0.0)
    total_pending_cod = float(finance_summary.get("pending_cod", 0.0) or 0.0)

    # ── Per-driver order stats computed from real order data ──
    driver_order_counts: dict = {}       # total non-draft orders
    driver_delivered_counts: dict = {}   # delivered orders
    driver_cancelled_counts: dict = {}   # cancelled orders
    driver_rating_sums: dict = {}        # sum of customer_rating values
    driver_rating_counts: dict = {}      # count of orders with customer_rating
    for order in orders:
        if not order.assigned_driver_id:
            continue
        key = str(order.assigned_driver_id)
        if order.status == "DRAFT":
            continue
        driver_order_counts[key] = driver_order_counts.get(key, 0) + 1
        if order.status == "DELIVERED":
            driver_delivered_counts[key] = driver_delivered_counts.get(key, 0) + 1
        if order.status == "CANCELLED":
            driver_cancelled_counts[key] = driver_cancelled_counts.get(key, 0) + 1
        if order.customer_rating is not None:
            driver_rating_sums[key] = driver_rating_sums.get(key, 0) + order.customer_rating
            driver_rating_counts[key] = driver_rating_counts.get(key, 0) + 1

    # EXPENSE_DRIVER rows in LogisticsTransaction sum gives total earned per driver session

    hubs = []
    for index, warehouse in enumerate(warehouses, start=1):
        hub_users = [user for user in users if user.warehouse_id == warehouse.id]
        hub_orders = [order for order in orders if order.warehouse_id == warehouse.id]
        hub_vehicles = [vehicle for vehicle in vehicles if vehicle.warehouse_id == warehouse.id]
        capacity = int((len(hub_orders) / max(warehouse.capacity_limit or 10, 10)) * 100)
        computed_status = "Optimal" if capacity < 70 else ("High Load" if capacity < 90 else "Congested")
        status = "Archived" if not warehouse.is_active else (warehouse.hub_status if warehouse.hub_status else computed_status)
        efficiency = min(99, max(72, 82 + len(hub_orders) * 3))
        fallback_manager = next(
            (
                user
                for user in hub_users
                if role_by_id.get(user.role_id) == "WAREHOUSE_MANAGER" and user.is_active
            ),
            None,
        )
        manager_name = (
            user_map.get(warehouse.manager_id).name
            if warehouse.manager_id in user_map
            else (fallback_manager.name if fallback_manager else "Unassigned")
        )
        hubs.append(
            LogisticsHubItem(
                id=warehouse.id,
                hub_code=f"HUB-{index:02d}",
                name=warehouse.name,
                location=warehouse.address,
                address=warehouse.address,
                lat=warehouse.lat,
                lng=warehouse.lng,
                manager=manager_name,
                manager_initials="".join(part[0] for part in manager_name.split()[:2]).upper() if manager_name else "UN",
                capacity=capacity,
                efficiency=efficiency,
                staff_active=sum(1 for user in hub_users if user.is_active),
                staff_total=len(hub_users),
                vehicles_active=sum(1 for vehicle in hub_vehicles if vehicle.status == "Active"),
                vehicles_total=len(hub_vehicles),
                process_rate=len(hub_orders) * 120,
                status=status,
                status_color="text-slate-500" if status == "Archived" else ("text-green-500" if status == "Optimal" else ("text-yellow-500" if status == "High Load" else "text-red-500")),
                bg="bg-slate-500" if status == "Archived" else ("bg-green-500" if status == "Optimal" else ("bg-yellow-500" if status == "High Load" else "bg-red-500")),
            )
        )

    # Build per-driver order and alert counts for dynamic scorecard stats
    driver_alert_counts: dict = {}
    for alert in alerts:
        # Alerts that name a driver by name (best-effort)
        for profile in driver_profiles:
            u = user_map.get(profile.user_id)
            if u and u.name and u.name.lower() in (alert.location or "").lower():
                driver_alert_counts[str(u.id)] = driver_alert_counts.get(str(u.id), 0) + 1

    drivers = []
    for profile in driver_profiles:
        user = user_map.get(profile.user_id)
        if not user:
            continue
        assigned_vehicle = vehicle_by_driver.get(user.id)
        uid_str = str(user.id)
        # Rating: avg of customer_rating from delivered orders; 0.0 if none yet
        r_count = driver_rating_counts.get(uid_str, 0)
        driver_rating = round(driver_rating_sums.get(uid_str, 0) / r_count, 1) if r_count else 0.0
        # Efficiency: delivery completion rate from real orders; fall back to stored score
        total_trips = driver_order_counts.get(uid_str, 0)
        delivered_trips = driver_delivered_counts.get(uid_str, 0)
        driver_efficiency = round((delivered_trips / total_trips) * 100) if total_trips else profile.efficiency_score
        # Safety incidents: alert count mentioning this driver
        driver_incidents = driver_alert_counts.get(uid_str, 0)
        # Fuel efficiency: from assigned vehicle or a computed estimate
        if assigned_vehicle and assigned_vehicle.fuel_efficiency:
            fuel_eff = str(assigned_vehicle.fuel_efficiency)
        else:
            mpg = round(6.0 + (driver_efficiency / 100) * 6, 1)
            fuel_eff = f"{mpg} km/l"
        # Average speed: estimate from trips
        avg_spd = f"{min(75, max(35, 40 + total_trips * 2))} km/h"
        drivers.append(
            LogisticsDriverItem(
                id=user.id,
                hub_id=profile.warehouse_id,
                name=user.name,
                status=profile.status,
                location=profile.current_location,
                vehicle=assigned_vehicle.code if assigned_vehicle else None,
                efficiency=driver_efficiency,
                rating=driver_rating,
                safety_incidents=driver_incidents,
                fuel_efficiency_score=fuel_eff,
                avg_speed=avg_spd,
                phone=user.phone,
                current_job=profile.current_job,
                avatar_color=profile.avatar_color,
                chat_history=profile.chat_history or [],
            )
        )

    vehicles_payload = [
        LogisticsVehicleItem(
            id=vehicle.id,
            hub_id=vehicle.warehouse_id,
            code=vehicle.code,
            type=vehicle.vehicle_type,
            model=vehicle.model,
            year=vehicle.year,
            license_plate=vehicle.license_plate,
            status=vehicle.status,
            driver=(
                user_map[vehicle.assigned_driver_id].name if vehicle.assigned_driver_id in user_map
                else user_map[active_driver_by_vehicle[vehicle.id]].name if vehicle.id in active_driver_by_vehicle and active_driver_by_vehicle[vehicle.id] in user_map
                else "Unassigned"
            ),
            fuel_efficiency=vehicle.fuel_efficiency,
            mileage=vehicle.mileage,
            next_service=vehicle.next_service_date.strftime("%b %d, %Y") if vehicle.next_service_date else None,
            maintenance_issue=vehicle.maintenance_issue,
        )
        for vehicle in vehicles
    ]

    ai_suggestion_chips = [
        "Show dashboard overview",
        "Driver status report",
        "Fleet & vehicle status",
        "Check inventory levels",
        "Returns & RMA summary",
        "Revenue forecast",
        "Hub performance",
        "What can you help with?",
    ]
    busiest_hub = max(hubs, key=lambda hub: hub.process_rate, default=None)
    # Generate friendly welcome message
    greeting_options = [
        "Hey! Welcome to your Cargo-Core AI Intelligence hub!",
        "Hello! Ready to optimize your logistics operations today!",
        "Hi there! Your AI assistant is online and ready to help!",
    ]
    import random
    greeting = random.choice(greeting_options)

    if len(alerts) > 0:
        alert_msg = f"I've spotted <b>{len(alerts)} alert(s)</b> that need your attention."
    else:
        alert_msg = "Everything's running smoothly - <b>no alerts</b> to worry about!"

    hub_msg = f"<b>{busiest_hub.name}</b> is your top performer right now" if busiest_hub else "Your network is ready to go"

    ai_messages = [{
        "role": "ai",
        "text": f"{greeting} {hub_msg}. {alert_msg} Ask me anything about your drivers, fleet, orders, or operations!",
        "time": _now().strftime("%I:%M %p"),
        "data": {
            "active_alerts": len(alerts),
            "active_deliveries": active_deliveries,
            "pending_cod": f"${total_pending_cod:,.0f}",
            "top_hub": busiest_hub.name if busiest_hub else "N/A",
        },
    }]

    def _cod_hub_id(order: Order) -> str | None:
        """Resolve hubId for a COD order — fall back to driver's warehouse if order is legacy-unlinked."""
        if order.warehouse_id:
            return str(order.warehouse_id)
        # Legacy orders: infer from the assigned driver's warehouse
        driver = user_map.get(order.assigned_driver_id) if order.assigned_driver_id else None
        if driver and driver.warehouse_id:
            return str(driver.warehouse_id)
        # Last resort: pick first warehouse whose staff includes the customer or creator
        return None

    pending_cod_orders = [
        order
        for order in orders
        if (order.payment_mode or "").upper() == "COD" and order.payment_status == "pending"
    ][:3]

    finance_cod_records = [
        {
            "id": f"COD-{order.tracking_code}",
            "date": order.scheduled_at.strftime("%b %d, %Y") if order.scheduled_at else _fmt_relative(order.created_at),
            "desc": order.tracking_code,
            "name": user_map.get(order.assigned_driver_id).name if order.assigned_driver_id in user_map else "Unassigned Driver",
            "amount": float(order.total_amount),
            "status": "Completed" if order.payment_status == "paid" else "Pending",
            "type": "COD",
            "hubId": _cod_hub_id(order),
        }
        for order in pending_cod_orders + [order for order in orders if order.payment_mode == "COD" and order.payment_status == "paid"][:3]
    ]

    # ── Payroll records driven by real DB expense transactions ──────────────
    # EXPENSE_DRIVER rows represent shift fees booked per assignment.
    # We count how many such rows exist (each assignment => 1 EXPENSE_DRIVER tx)
    # and multiply by DRIVER_SHIFT_RATE.  If no rows yet => amount = 0.
    DRIVER_SHIFT_RATE = 1200.0   # must match finance_service.py
    STAFF_SESSION_RATE = 1600.0  # per active shift/session for WH managers / dispatchers

    # Query which users already had their payroll paid this month
    _current_month_start = _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=UTC)
    _payroll_paid_result = await db.execute(
        select(LogisticsTransaction.metadata_json)
        .where(
            LogisticsTransaction.transaction_type == "PAYROLL_RUN",
            LogisticsTransaction.transaction_date >= _current_month_start,
        )
    )
    paid_user_ids: set[str] = {
        row[0]["user_id"]
        for row in _payroll_paid_result.all()
        if row[0] and "user_id" in row[0]
    }

    finance_staff_records = []
    finance_driver_records = []

    for user in users:
        role_name = role_by_id.get(user.role_id, "")
        if role_name in {"INDIVIDUAL", "LOGISTIC_MANAGER"}:
            continue

        uid_str = str(user.id)
        uid_prefix = uid_str[:8].upper()
        hub_id = str(user.warehouse_id) if user.warehouse_id else None
        avatar = f"https://i.pravatar.cc/150?u={user.id}"

        if role_name in {"WAREHOUSE_MANAGER", "DISPATCHER"}:
            # Staff earned: number of active work-days at their hub.
            # For legacy data, orders may not have warehouse_id set — also count orders
            # assigned to drivers who belong to the same warehouse.
            hub_driver_ids = {
                u.id for u in users
                if u.warehouse_id == user.warehouse_id and role_by_id.get(u.role_id) == "DRIVER"
            }
            hub_orders = [
                o for o in orders
                if (
                    (o.warehouse_id and o.warehouse_id == user.warehouse_id)
                    or (not o.warehouse_id and o.assigned_driver_id and o.assigned_driver_id in hub_driver_ids)
                )
            ]
            days_active = len({
                o.created_at.date()
                for o in hub_orders
                if user.is_active and o.status not in {"DRAFT", "CANCELLED"}
            })
            payout = round(days_active * STAFF_SESSION_RATE, 2)
            if payout > 0:
                finance_staff_records.append({
                    "id": f"PAY-{uid_prefix}",
                    "userId": uid_str,
                    "date": _now().strftime("%b %d, %Y"),
                    "name": user.name,
                    "role": _title_case_status(role_name),
                    "amount": payout,
                    "status": "Paid" if uid_str in paid_user_ids else "Pending",
                    "avatar": avatar,
                    "hubId": hub_id,
                })
        elif role_name == "DRIVER":
            # Driver earned: number of EXPENSE_DRIVER transactions that reference orders
            # assigned to this driver (count driver_order_counts[uid_str] shifts)
            shifts = driver_order_counts.get(uid_str, 0)
            payout = round(shifts * DRIVER_SHIFT_RATE, 2)
            if payout > 0:
                finance_driver_records.append({
                    "id": f"WAGE-{uid_prefix}",
                    "userId": uid_str,
                    "date": _now().strftime("%b %d, %Y"),
                    "name": user.name,
                    "role": "Driver",
                    "amount": payout,
                    "status": "Paid" if uid_str in paid_user_ids else "Pending",
                    "avatar": avatar,
                    "hubId": hub_id,
                })

    fleet_logs = {
        "Fuel Logs": [
            {
                "id": f"FUEL-{index + 1:03d}",
                "date": tx.transaction_date.strftime("%b %d, %Y"),
                "vehicleId": next((vehicle.code for vehicle in vehicles if vehicle.warehouse_id == tx.warehouse_id), "NA"),
                "hubId": str(tx.warehouse_id) if tx.warehouse_id else "all",
                "station": "Network Fuel Partner",
                "gallons": max(12, round(abs(tx.amount) / 4.25, 1)),
                "cost": abs(tx.amount),
                "alert": abs(tx.amount) > 3000,
                "status": tx.status,
            }
            for index, tx in enumerate([item for item in transactions if item.transaction_type in {"Expense", "Payroll"}][:5])
        ],
        "Service Logs": [
            {
                "id": f"SRV-{index + 1:03d}",
                "date": vehicle.next_service or _now().strftime("%b %d, %Y"),
                "vehicleId": vehicle.code,
                "hubId": str(vehicle.hub_id) if vehicle.hub_id else "all",
                "service": vehicle.maintenance_issue or "Preventive service",
                "provider": "CargoCore Workshop",
                "cost": 180 + index * 60,
                "status": "Scheduled" if vehicle.status != "Active" else "Completed",
            }
            for index, vehicle in enumerate(vehicles_payload[:5])
        ],
        "Maintenance Logs": [
            {
                "id": f"MTN-{index + 1:03d}",
                "date": vehicle.next_service or _now().strftime("%b %d, %Y"),
                "vehicleId": vehicle.code,
                "hubId": str(vehicle.hub_id) if vehicle.hub_id else "all",
                "issue": vehicle.maintenance_issue or "General inspection",
                "mechanic": "Internal Team",
                "cost": 240 + index * 90,
                "status": "Pending" if vehicle.status != "Active" else "Resolved",
            }
            for index, vehicle in enumerate(vehicles_payload[:5])
        ],
        "Cleaning Logs": [
            {
                "id": f"CLN-{index + 1:03d}",
                "date": _fmt_relative(_now() - timedelta(days=index + 1)),
                "vehicleId": vehicle.code,
                "hubId": str(vehicle.hub_id) if vehicle.hub_id else "all",
                "type": "Exterior Wash" if index % 2 == 0 else "Full Detail",
                "provider": "Fleet Care",
                "cost": 40 + index * 20,
                "status": "Completed",
            }
            for index, vehicle in enumerate(vehicles_payload[:5])
        ],
    }

    vehicle_documents = [
        {
            "id": str(doc.id),
            "vehicleId": doc.entity_id,
            "vehicleCode": vehicle_map[UUID(doc.entity_id)].code if doc.entity_id.replace('-', '') in [str(k).replace('-', '') for k in vehicle_map] else "N/A",
            "hubId": str(doc.hub_id) if doc.hub_id else "all",
            "type": doc.doc_type,
            "status": doc.status,
            "expiry": doc.expiry_date.strftime("%b %d, %Y") if doc.expiry_date else "N/A",
            "lastRenewed": doc.created_at.strftime("%b %d, %Y"),
            "url": doc.document_url,
            "notes": doc.notes,
        }
        for doc in documents if doc.entity_type == "VEHICLE"
    ]

    driver_documents = [
        {
            "id": str(doc.id),
            "driver": user_map[UUID(doc.entity_id)].name if doc.entity_id.replace('-', '') in [str(k).replace('-', '') for k in user_map] else "Unknown",
            "driverId": doc.entity_id,
            "hubId": str(doc.hub_id) if doc.hub_id else "all",
            "type": doc.doc_type,
            "licenseNo": f"DOC-{str(doc.id)[:4].upper()}",
            "status": doc.status,
            "expiry": doc.expiry_date.strftime("%b %d, %Y") if doc.expiry_date else "N/A",
            "joined": doc.created_at.strftime("%b %d, %Y"),
            "url": doc.document_url,
            "notes": doc.notes,
        }
        for doc in documents if doc.entity_type == "DRIVER"
    ]

    report_ai_insights = []
    report_damage_claims = [
        {
            "title": case.reference_code,
            "reporter": case.customer_name,
            "time": _fmt_relative(case.created_at),
            "status": case.status,
            "image": case.images[0] if case.images else "",
            "reason": case.reason,
        }
        for case in return_cases
    ]
    report_security_logs = [
        {
            "time": _fmt_relative(notification.created_at),
            "actor": "system_bot",
            "action": "READ_NOTIFICATION" if notification.is_read else "NEW_NOTIFICATION",
            "target": notification.title,
            "details": notification.message,
            "ip": f"10.0.0.{20 + index}",
        }
        for index, notification in enumerate(notifications[:6], start=1)
    ]
    report_metrics = {
        "payment_reconciliation": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "expected_digital": [max(total_revenue * ratio, 1000) for ratio in (0.10, 0.12, 0.15, 0.13, 0.18)],
            "actual_digital": [max(total_revenue * ratio, 900) for ratio in (0.09, 0.11, 0.145, 0.125, 0.17)],
            "expected_cod": [max(total_pending_cod * ratio, 300) for ratio in (0.20, 0.18, 0.22, 0.17, 0.23)],
            "actual_cod": [max(total_pending_cod * ratio, 250) for ratio in (0.16, 0.15, 0.20, 0.14, 0.21)],
        },
        "fuel_audit": {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "fuel_expense": [total_expenses * ratio for ratio in (0.20, 0.24, 0.19, 0.27)],
            "gps_mileage": [max(sum(vehicle.mileage for vehicle in vehicles) * ratio / 100, 1000) for ratio in (0.18, 0.21, 0.19, 0.22)],
        },
        "workforce": {
            "labels": ["In-Warehouse", "On-Field", "Off-Duty"],
            "values": [
                len([user for user in users if role_by_id.get(user.role_id) in {"WAREHOUSE_MANAGER", "DISPATCHER"}]),
                len([user for user in users if role_by_id.get(user.role_id) == "DRIVER"]),
                max(1, len(users) // 4),
            ],
        },
        "vendor_lead_time": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "values": [
                round(max(1.5, 3.5 - (len(orders) * 0.01)), 1),
                round(max(1.2, 3.2 - (len(orders) * 0.01)), 1),
                round(max(1.8, 3.8 - (len(orders) * 0.01)), 1),
                round(max(1.4, 3.4 - (len(orders) * 0.01)), 1),
                round(max(1.1, 3.1 - (len(orders) * 0.01)), 1),
                round(max(1.0, 2.9 - (len(orders) * 0.01)), 1),
            ],
        },
        "safety_incidents": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "values": [
                max(0, len(alerts) - 2), len(alerts),
                max(0, len(alerts) - 1), len(alerts) + 1,
                max(0, len(alerts) - 1), len(alerts),
            ],
        },
        "shift_efficiency": {
            "labels": ["Shift A", "Shift B", "Shift C"],
            "efficiency": [
                min(97, max(70, int(delivery_success) + 5)),
                min(95, max(65, int(delivery_success))),
                min(92, max(60, int(delivery_success) - 5)),
            ],
            "overtime": [
                max(0, len(orders) // 10),
                max(0, len(orders) // 12),
                max(0, len(orders) // 8),
            ],
        },
        "dwell_time": {
            "labels": ["6am-9am", "9am-12pm", "12pm-3pm", "3pm-6pm", "6pm-9pm"],
            "values": [
                max(15, min(90, processing * 3)),
                max(20, min(120, processing * 4)),
                max(18, min(100, processing * 3 + 5)),
                max(22, min(110, processing * 4 - 5)),
                max(12, min(80, processing * 2)),
            ],
        },
        "rma_vs_orders": {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "orders": [
                # Real per-week order counts for the last 4 weeks
                sum(1 for o in orders if (today - o.created_at.date()).days in range(28, 21)),
                sum(1 for o in orders if (today - o.created_at.date()).days in range(21, 14)),
                sum(1 for o in orders if (today - o.created_at.date()).days in range(14, 7)),
                sum(1 for o in orders if (today - o.created_at.date()).days in range(7, 0)),
            ],
            "rma": [max(1, len(return_cases) - 1), len(return_cases), len(return_cases), len(return_cases) + 1],
        },
        "rma_reasons": {
            "labels": ["Damaged", "Wrong Item", "Late Delivery", "Changed Mind"],
            "values": [
                len([case for case in return_cases if "dam" in case.reason.lower()]),
                len([case for case in return_cases if "wrong" in case.reason.lower()]),
                len([case for case in return_cases if "late" in case.reason.lower()]),
                len([case for case in return_cases if "changed" in case.reason.lower()]),
            ],
        },
        "attendance": {
            "present": len([user for user in users if user.is_active]),
            "late": len(alerts),
            "absent": max(0, len(users) // 5 - 1),
        },
        "pending_dues": total_pending_cod,
    }

    for m in metrics:
        if m.metric_type == "vendor_lead_time":
            report_metrics["vendor_lead_time"]["labels"].append(m.label)
            report_metrics["vendor_lead_time"]["values"].append(m.value_main)
        elif m.metric_type == "safety_incidents":
            report_metrics["safety_incidents"]["labels"].append(m.label)
            report_metrics["safety_incidents"]["values"].append(m.value_main)
        elif m.metric_type == "shift_efficiency":
            report_metrics["shift_efficiency"]["labels"].append(m.label)
            report_metrics["shift_efficiency"]["efficiency"].append(m.value_main)
            report_metrics["shift_efficiency"]["overtime"].append(m.value_secondary or 0)
        elif m.metric_type == "dwell_time":
            report_metrics["dwell_time"]["labels"].append(m.label)
            report_metrics["dwell_time"]["values"].append(m.value_main)

    # Build order lookups for legacy transaction resolution and slip generation
    order_map_by_str_id: dict[str, Order] = {str(o.id): o for o in orders}
    order_map_by_tracking: dict[str, Order] = {
        str(o.tracking_code).upper(): o
        for o in orders
        if o.tracking_code
    }

    def _extract_tracking_code(value: str | None) -> str | None:
        if not value:
            return None
        match = re.search(r"\b([A-Z]{2,5}-[A-Z0-9]{4,})\b", str(value).upper())
        return match.group(1) if match else None

    def _related_order_for_transaction(tx: LogisticsTransaction) -> dict | None:
        meta = dict(tx.metadata_json or {})
        order = None

        order_id = meta.get("order_id")
        if order_id:
            order = order_map_by_str_id.get(str(order_id))

        tracking_code = meta.get("tracking_code") or _extract_tracking_code(tx.description)
        if order is None and tracking_code:
            order = order_map_by_tracking.get(str(tracking_code).upper())

        if order is None:
            return None

        customer = user_map.get(order.customer_id)
        driver = user_map.get(order.assigned_driver_id) if order.assigned_driver_id else None
        vehicle = vehicle_map.get(order.assigned_vehicle_id) if order.assigned_vehicle_id else None

        return {
            "id": str(order.id),
            "tracking_code": order.tracking_code,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "scheduled_at": order.scheduled_at.isoformat() if order.scheduled_at else None,
            "service_time_block": order.service_time_block,
            "pickup_addr": order.pickup_addr,
            "delivery_addr": order.delivery_addr,
            "total_amount": float(order.total_amount or 0.0),
            "paid_amount": float(order.paid_amount or 0.0),
            "payment_mode": order.payment_mode,
            "payment_status": order.payment_status,
            "labor_count": order.labor_count,
            "vehicle_type": order.vehicle_type,
            "customer_name": customer.name if customer else None,
            "customer_phone": customer.phone if customer else None,
            "customer_email": customer.email if customer else None,
            "assigned_driver_name": driver.name if driver else None,
            "assigned_vehicle_code": vehicle.code if vehicle else None,
        }

    def _tx_hub_id(tx: LogisticsTransaction) -> UUID | None:
        """Return the resolved warehouse_id for a transaction, inferring from metadata if null."""
        if tx.warehouse_id:
            return tx.warehouse_id
        meta = tx.metadata_json or {}
        # Try order_id first
        oid_str = meta.get("order_id")
        if oid_str:
            order = order_map_by_str_id.get(str(oid_str))
            if order and order.warehouse_id:
                return order.warehouse_id
            # Even if the order has no warehouse_id, try via its assigned driver
            if order and order.assigned_driver_id:
                driver = user_map.get(order.assigned_driver_id)
                if driver and driver.warehouse_id:
                    return driver.warehouse_id
        # Try collected_by / user_id in metadata
        for key in ("collected_by", "user_id"):
            uid_str = meta.get(key)
            if uid_str:
                try:
                    uid = UUID(str(uid_str))
                except (ValueError, TypeError):
                    continue
                u = user_map.get(uid)
                if u and u.warehouse_id:
                    return u.warehouse_id
        return None

    finance_summary = {
        **finance_summary,
        "total_payroll_due": round(sum(item["amount"] for item in finance_staff_records + finance_driver_records if item.get("status") == "Pending"), 2),
    }

    return LogisticsBootstrapResponse(
        dashboard_stats=dashboard_stats,
        hubs=hubs,
        alerts=[LogisticsAlertItem(id=alert.id, type=alert.alert_type, title=alert.title, description=alert.description, severity=alert.severity, icon=alert.icon, timestamp=alert.created_at.strftime("%I:%M %p"), location=alert.location, recommendation=alert.recommendation, impact=alert.impact_json) for alert in alerts],
        drivers=drivers,
        top_drivers=[
            {
                "id": str(driver.id),
                "hubId": driver.hub_id,
                "name": driver.name,
                "rating": driver.rating,
                "trips": driver_order_counts.get(str(driver.id), 0),
                "ontime": (
                    round(driver_delivered_counts.get(str(driver.id), 0) / driver_order_counts.get(str(driver.id), 1) * 100)
                    if driver_order_counts.get(str(driver.id), 0) > 0 else 0
                ),
                "avatar": f"https://i.pravatar.cc/150?u={driver.id}",
            }
            for driver in sorted(drivers, key=lambda item: driver_order_counts.get(str(item.id), 0), reverse=True)[:5]
        ],
        vehicles=vehicles_payload,
        maintenance=[LogisticsMaintenanceItem(id=vehicle.id, hub_id=vehicle.warehouse_id, issue=vehicle.maintenance_issue or "Scheduled Maintenance", status=vehicle.status, status_class=_status_badge_class(vehicle.status)) for vehicle in vehicles if vehicle.status != "Active"],
        transactions=[
            LogisticsTransactionItem(
                id=tx.id,
                hub_id=_tx_hub_id(tx),
                transaction_code=tx.transaction_code,
                date=tx.transaction_date.strftime("%b %d, %Y"),
                desc=tx.description,
                type=tx.transaction_type,
                amount=tx.amount,
                status=tx.status,
                metadata_json=dict(tx.metadata_json or {}),
                related_order=_related_order_for_transaction(tx),
            )
            for tx in transactions
        ],
        reports=[LogisticsReportItem(id=f"report-{index}", hub_id=hub.id, title=f"{hub.name} Performance Report", date=_fmt_relative(_now() - timedelta(days=index)), icon="analytics", color=color) for index, (hub, color) in enumerate(zip(hubs, ["blue", "green", "orange"], strict=False), start=1)],
        users=[LogisticsUserItem(id=user.id, hub_id=user.warehouse_id, name=user.name, email=user.email, role=role_by_id.get(user.role_id, ""), status="Active" if user.is_active else "Inactive", last_login=user.last_login.isoformat() if user.last_login else "", username=user.username, pending_payout=(
                    next((item["amount"] for item in finance_staff_records if item["userId"] == str(user.id) and item.get("status") == "Pending"), 0.0)
                    or next((item["amount"] for item in finance_driver_records if item["userId"] == str(user.id) and item.get("status") == "Pending"), 0.0)
                ), mobile=user.phone, mobile_verified=bool(user.phone), email_verified=True, avatar=f"https://i.pravatar.cc/150?u={user.id}", approval_status=user.approval_status, approval_note=user.approval_note, approval_reviewed_at=user.approval_reviewed_at, company_name=user.company_name, tax_id=user.tax_id, contact_person=user.contact_person, business_email=user.business_email, business_phone=user.business_phone, submitted_at=user.created_at) for user in users if role_by_id.get(user.role_id) != "INDIVIDUAL"],
        returns=[_to_return_case_item(item) for item in return_cases],
        zones=[LogisticsZoneItem(id=zone.id, hub_id=zone.warehouse_id, name=zone.name, type=zone.zone_type, radius=zone.radius_km, status=zone.status, color=zone.color_token, lat=zone.lat, lng=zone.lng) for zone in zones],
        chats=[LogisticsChatThreadItem(id=thread.id, hub_id=thread.warehouse_id, name=thread.name, time=_fmt_relative(thread.last_message_at), last_message=thread.last_message, status=thread.status, phone=thread.phone, muted=thread.muted, messages=[LogisticsChatMessageItem(id=message.id, text=message.text, sender=message.sender, time=message.created_at.strftime("%I:%M %p")) for message in messages_by_thread.get(thread.id, [])]) for thread in chat_threads],
        escalations=[_to_logistics_escalation_item(esc) for esc in escalations],
        inventory=[{"id": str(item.id), "name": item.name, "category": item.category or "General", "quantity": item.quantity_on_hand, "unit": item.unit, "threshold": item.safety_stock, "location": item.aisle or (warehouse_map.get(item.warehouse_id).name if warehouse_map.get(item.warehouse_id) else "Unknown"), "status": "Low Stock" if item.quantity_on_hand <= item.safety_stock else "Good", "hubId": item.warehouse_id, "sku": item.sku} for item in inventory_items],
        notifications=[LogisticsNotificationItem(id=item.id, title=item.title, message=item.message, time=_fmt_relative(item.created_at), created_at=item.created_at, read=item.is_read, type=item.type) for item in notifications],
        tasks=[LogisticsTaskItem(id=item.id, text=item.text, status=item.status, target_time=item.target_time, repeat=item.repeat_rule, created_at=item.created_at, last_alert_time=item.last_alert_time, silenced=item.silenced) for item in tasks],
        ai_suggestion_chips=ai_suggestion_chips,
        ai_messages=ai_messages,
        finance_summary=finance_summary,
        finance_cod_records=finance_cod_records,
        finance_staff_records=finance_staff_records,
        finance_driver_records=finance_driver_records,
        fleet_logs=fleet_logs,
        vehicle_documents=vehicle_documents,
        driver_documents=driver_documents,
        report_ai_insights=report_ai_insights,
        report_damage_claims=report_damage_claims,
        report_security_logs=report_security_logs,
        report_metrics=report_metrics,
        equipment_ledger=[LogisticsEquipmentItem(id=eq.id, hub_id=eq.warehouse_id, item_type=eq.item_type, issued_count=eq.issued_count, returned_count=eq.returned_count, reference_code=eq.reference_code, status=eq.status) for eq in equipments]
    )


async def update_escalation_status(
    db: AsyncSession,
    escalation_id: UUID,
    data: LogisticsEscalationStatusUpdate,
) -> LogisticsEscalationItem:
    escalation = (
        await db.execute(select(LogisticsEscalation).where(LogisticsEscalation.id == escalation_id))
    ).scalar_one_or_none()
    if escalation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")

    escalation.status = (data.status or "").strip().upper()
    db.add(escalation)
    await db.flush()
    await db.refresh(escalation)
    return _to_logistics_escalation_item(escalation)
