"""Builds the single bootstrap payload behind the logistics manager dashboard."""

from __future__ import annotations

from datetime import timedelta
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
from app.models.order import Order
from app.models.user import Role, User
from app.models.warehouse import ReturnGrading, Warehouse
from app.schemas.logistics import (
    LogisticsAlertItem,
    LogisticsBootstrapResponse,
    LogisticsChatMessageItem,
    LogisticsChatThreadItem,
    LogisticsDashboardStats,
    LogisticsEquipmentItem,
    LogisticsEscalationItem,
    LogisticsEscalationStatusUpdate,
    LogisticsMaintenanceItem,
    LogisticsNotificationItem,
    LogisticsReportItem,
    LogisticsTaskItem,
    LogisticsUserItem,
    LogisticsZoneItem,
)
from app.services.logistics.bootstrap_finance import (
    build_transaction_items,
    cod_records,
    finance_snapshot,
    payroll_records,
)
from app.services.logistics.bootstrap_network import (
    assistant_welcome,
    count_driver_alerts,
    driver_items,
    driver_order_stats,
    hub_items,
    vehicle_items,
)
from app.services.logistics.bootstrap_reports import (
    build_fleet_logs,
    entity_documents,
    report_payloads,
    weekly_series,
)
from app.services.logistics.bootstrap_returns import (
    backfill_return_cases,
    credited_reference_codes,
    latest_completed_gradings,
    to_return_case_item,
)
from app.services.logistics.formatting import (
    _fmt_relative,
    _now,
    _reconcile_restock_escalations,
    _status_badge_class,
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

    return_cases = await backfill_return_cases(return_cases, db, _all_orders, _all_users, return_gradings)

    _credited_ref_codes = await credited_reference_codes(return_cases, db)

    latest_completed_grading_by_rma, latest_completed_grading_by_order_id = latest_completed_gradings(return_gradings)

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

    sla_week, orders_week = await weekly_series(today, db, orders, delivery_success)

    finance_summary, revenue_today, revenue_week, revenue_trend = await finance_snapshot(db, today)

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

    stats = driver_order_stats(orders)
    driver_order_counts, driver_delivered_counts = stats.orders, stats.delivered

    # EXPENSE_DRIVER rows in LogisticsTransaction sum gives total earned per driver session

    hubs = hub_items(warehouses, users, orders, vehicles, role_by_id, user_map)

    driver_alert_counts = count_driver_alerts(alerts, driver_profiles, user_map)

    drivers = driver_items(driver_profiles, user_map, vehicle_by_driver, stats, driver_alert_counts)

    vehicles_payload = vehicle_items(user_map, active_driver_by_vehicle, vehicles)

    ai_suggestion_chips, ai_messages = assistant_welcome(hubs, alerts, active_deliveries, total_pending_cod)

    finance_cod_records = cod_records(user_map, orders)

    finance_staff_records, finance_driver_records = await payroll_records(db, users, role_by_id, orders, driver_order_counts)

    fleet_logs = build_fleet_logs(vehicles, transactions, vehicles_payload)

    vehicle_documents, driver_documents = entity_documents(vehicle_map, documents, user_map)

    report_ai_insights, report_damage_claims, report_security_logs, report_metrics = report_payloads(return_cases, notifications, total_revenue, total_pending_cod, total_expenses, vehicles, users, role_by_id, orders, alerts, delivery_success, processing, today, metrics)

    transaction_items = build_transaction_items(transactions, orders, user_map, vehicle_map)

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
        transactions=transaction_items,
        reports=[LogisticsReportItem(id=f"report-{index}", hub_id=hub.id, title=f"{hub.name} Performance Report", date=_fmt_relative(_now() - timedelta(days=index)), icon="analytics", color=color) for index, (hub, color) in enumerate(zip(hubs, ["blue", "green", "orange"], strict=False), start=1)],
        users=[LogisticsUserItem(id=user.id, hub_id=user.warehouse_id, name=user.name, email=user.email, role=role_by_id.get(user.role_id, ""), status="Active" if user.is_active else "Inactive", last_login=user.last_login.isoformat() if user.last_login else "", username=user.username, pending_payout=(
                    next((item["amount"] for item in finance_staff_records if item["userId"] == str(user.id) and item.get("status") == "Pending"), 0.0)
                    or next((item["amount"] for item in finance_driver_records if item["userId"] == str(user.id) and item.get("status") == "Pending"), 0.0)
                ), mobile=user.phone, mobile_verified=bool(user.phone), email_verified=True, avatar=f"https://i.pravatar.cc/150?u={user.id}", approval_status=user.approval_status, approval_note=user.approval_note, approval_reviewed_at=user.approval_reviewed_at, company_name=user.company_name, tax_id=user.tax_id, contact_person=user.contact_person, business_email=user.business_email, business_phone=user.business_phone, submitted_at=user.created_at) for user in users if role_by_id.get(user.role_id) != "INDIVIDUAL"],
        returns=[
            to_return_case_item(item, latest_completed_grading_by_rma, latest_completed_grading_by_order_id, _credited_ref_codes)
            for item in return_cases
        ],
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
