"""Hubs, drivers, vehicles and the assistant greeting for the logistics bootstrap."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from app.models.logistics import (
    LogisticsAlert,
    LogisticsDriverProfile,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.logistics import (
    LogisticsDriverItem,
    LogisticsHubItem,
    LogisticsVehicleItem,
)
from app.services.logistics.formatting import (
    _now,
)


@dataclass(frozen=True)
class DriverOrderStats:
    """Per-driver order tallies keyed by the driver's user id as a string. Draft orders do not count."""

    orders: dict[str, int] = field(default_factory=dict)
    delivered: dict[str, int] = field(default_factory=dict)
    rating_sums: dict[str, float] = field(default_factory=dict)
    rating_counts: dict[str, int] = field(default_factory=dict)


def driver_order_stats(orders: Sequence[Order]) -> DriverOrderStats:
    stats = DriverOrderStats()
    for order in orders:
        if not order.assigned_driver_id or order.status == "DRAFT":
            continue
        key = str(order.assigned_driver_id)
        stats.orders[key] = stats.orders.get(key, 0) + 1
        if order.status == "DELIVERED":
            stats.delivered[key] = stats.delivered.get(key, 0) + 1
        if order.customer_rating is not None:
            stats.rating_sums[key] = stats.rating_sums.get(key, 0) + order.customer_rating
            stats.rating_counts[key] = stats.rating_counts.get(key, 0) + 1
    return stats


def hub_items(
    warehouses: Sequence[Warehouse],
    users: Sequence[User],
    orders: Sequence[Order],
    vehicles: Sequence[LogisticsVehicle],
    role_by_id: dict[UUID, str],
    user_map: dict[UUID, User],
) -> list[LogisticsHubItem]:
    """One card per warehouse with load, staffing, fleet and status colours."""
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
    return hubs


def count_driver_alerts(
    alerts: Sequence[LogisticsAlert],
    driver_profiles: Sequence[LogisticsDriverProfile],
    user_map: dict[UUID, User],
) -> dict[str, int]:
    """Active alerts per driver, matched by the driver's name appearing in the alert location."""
    # Build per-driver order and alert counts for dynamic scorecard stats
    driver_alert_counts: dict = {}
    for alert in alerts:
        # Alerts that name a driver by name (best-effort)
        for profile in driver_profiles:
            u = user_map.get(profile.user_id)
            if u and u.name and u.name.lower() in (alert.location or "").lower():
                driver_alert_counts[str(u.id)] = driver_alert_counts.get(str(u.id), 0) + 1
    return driver_alert_counts


def driver_items(
    driver_profiles: Sequence[LogisticsDriverProfile],
    user_map: dict[UUID, User],
    vehicle_by_driver: dict[UUID, LogisticsVehicle],
    stats: DriverOrderStats,
    driver_alert_counts: dict[str, int],
) -> list[LogisticsDriverItem]:
    """Driver scorecards. Rating and efficiency come from real orders, with the stored score as fallback."""
    drivers = []
    for profile in driver_profiles:
        user = user_map.get(profile.user_id)
        if not user:
            continue
        assigned_vehicle = vehicle_by_driver.get(user.id)
        uid_str = str(user.id)
        # Rating: avg of customer_rating from delivered orders; 0.0 if none yet
        r_count = stats.rating_counts.get(uid_str, 0)
        driver_rating = round(stats.rating_sums.get(uid_str, 0) / r_count, 1) if r_count else 0.0
        # Efficiency: delivery completion rate from real orders; fall back to stored score
        total_trips = stats.orders.get(uid_str, 0)
        delivered_trips = stats.delivered.get(uid_str, 0)
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
    return drivers


def vehicle_items(
    user_map: dict[UUID, User],
    active_driver_by_vehicle: dict[UUID, UUID],
    vehicles: Sequence[LogisticsVehicle],
) -> list[LogisticsVehicleItem]:
    """Vehicle rows, naming the assigned driver or the driver on an active order."""
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
    return vehicles_payload


def assistant_welcome(
    hubs: list[LogisticsHubItem],
    alerts: Sequence[LogisticsAlert],
    active_deliveries: int,
    total_pending_cod: float,
) -> tuple[list[str], list[dict]]:
    """Suggestion chips and the opening assistant message for the dashboard chat."""
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
    return ai_suggestion_chips, ai_messages
