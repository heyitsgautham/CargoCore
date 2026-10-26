"""Chart series, fleet logs, documents and report metrics for the logistics bootstrap."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import LogisticsDocument
from app.models.logistics import (
    LogisticsAlert,
    LogisticsDailyStats,
    LogisticsMetric,
    LogisticsNotification,
    LogisticsReturnCase,
    LogisticsTransaction,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.schemas.logistics import LogisticsVehicleItem
from app.services.logistics.formatting import (
    _fmt_relative,
    _now,
)


async def weekly_series(
    today: date, db: AsyncSession, orders: Sequence[Order], delivery_success: float
) -> tuple[list[int], list[int]]:
    """SLA percent and order count for each of the last 7 days, oldest first."""
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
    return sla_week, orders_week


def build_fleet_logs(
    vehicles: Sequence[LogisticsVehicle],
    transactions: Sequence[LogisticsTransaction],
    vehicles_payload: list[LogisticsVehicleItem],
) -> dict[str, list[dict]]:
    """Fuel, service, maintenance and cleaning logs for the fleet page, five rows each."""
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
    return fleet_logs


def entity_documents(
    vehicle_map: dict[UUID, LogisticsVehicle],
    documents: Sequence[LogisticsDocument],
    user_map: dict[UUID, User],
) -> tuple[list[dict], list[dict]]:
    """Vehicle documents and driver documents, each labelled with its vehicle code or driver name."""
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
    return vehicle_documents, driver_documents


def weekly_order_counts(orders: Sequence[Order], today: date, weeks: int = 4) -> list[int]:
    """Orders created in each of the last `weeks` 7-day windows, oldest window first, today included."""
    counts = [0] * weeks
    for order in orders:
        days_ago = (today - order.created_at.date()).days
        if 0 <= days_ago < weeks * 7:
            counts[weeks - 1 - days_ago // 7] += 1
    return counts


def report_payloads(
    return_cases: Sequence[LogisticsReturnCase],
    notifications: Sequence[LogisticsNotification],
    total_revenue: float,
    total_pending_cod: float,
    total_expenses: float,
    vehicles: Sequence[LogisticsVehicle],
    users: Sequence[User],
    role_by_id: dict[UUID, str],
    orders: Sequence[Order],
    alerts: Sequence[LogisticsAlert],
    delivery_success: float,
    processing: int,
    today: date,
    metrics: Sequence[LogisticsMetric],
) -> tuple[list[dict], list[dict], list[dict], dict]:
    """AI insights, damage claims, security log rows and chart metrics for the reports page."""
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
            "orders": weekly_order_counts(orders, today),
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
    return report_ai_insights, report_damage_claims, report_security_logs, report_metrics
