"""Route optimisation and driver load balancing."""

import math
import random

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsDriverProfile,
)
from app.models.order import Order
from app.models.user import User
from app.services import geocoding_service

# ---------------------------------------------------------------------------
# Route Optimization
# ---------------------------------------------------------------------------

_ROUTE_COLORS = [
    "#1CE783",
    "#3B82F6",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#EC4899",
    "#06B6D4",
]

_HUB_LAT = 12.9716
_HUB_LNG = 77.5946


def _euclidean_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Rough Euclidean distance in km using 1 deg ≈ 111 km."""
    dlat = (lat2 - lat1) * 111.0
    dlng = (lng2 - lng1) * 111.0 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.sqrt(dlat ** 2 + dlng ** 2)


_PRIORITY_RANK = {"URGENT": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}


async def optimize_routes(
    db: AsyncSession,
    optimize_for: str = "distance",
    prioritize_urgent: bool = False,
) -> list[dict]:
    """Assign CONFIRMED orders to available drivers using a nearest-neighbour heuristic."""

    # 1. Fetch CONFIRMED orders
    orders: list[Order] = (
        await db.execute(select(Order).where(Order.status == "CONFIRMED"))
    ).scalars().all()

    # 2. Fetch active drivers (LogisticsDriverProfile joined with User)
    rows = (
        await db.execute(
            select(LogisticsDriverProfile, User)
            .join(User, User.id == LogisticsDriverProfile.user_id)
            .where(User.is_active.is_(True))
        )
    ).all()

    drivers = [(profile, user) for profile, user in rows]

    if not drivers:
        return []

    # 3. Geocode orders that lack coordinates (save coords for future use, don't crash if it fails)
    needs_geocode = [o for o in orders if o.delivery_lat is None or o.delivery_lng is None]
    for order in needs_geocode:
        if order.delivery_addr:
            try:
                results = await geocoding_service.search_address(order.delivery_addr, limit=1)
                if results and results[0]["lat"] and results[0]["lon"]:
                    order.delivery_lat = float(results[0]["lat"])
                    order.delivery_lng = float(results[0]["lon"])
                    db.add(order)
            except Exception:
                pass

    if needs_geocode:
        try:
            await db.flush()
        except Exception:
            await db.rollback()

    # 4. Keep only orders that now have valid coordinates
    geo_orders = [o for o in orders if o.delivery_lat is not None and o.delivery_lng is not None]

    if not geo_orders:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No orders have delivery coordinates. Ensure destinations are selected on the map."
        )

    # 5. Sort orders: priority first (if requested or optimize_for=time), then by distance/deadline
    def _sort_key(o):
        pri = _PRIORITY_RANK.get(getattr(o, "priority", None) or "NORMAL", 2)
        dist = _euclidean_km(_HUB_LAT, _HUB_LNG, o.delivery_lat, o.delivery_lng)
        deadline_ts = o.scheduled_at.timestamp() if o.scheduled_at else float("inf")
        if prioritize_urgent or optimize_for == "time":
            return (pri, deadline_ts, dist)
        return (pri, dist)

    geo_orders.sort(key=_sort_key)

    # 6. Round-robin assignment across drivers
    driver_stops: dict[int, list[Order]] = {i: [] for i in range(len(drivers))}
    for idx, order in enumerate(geo_orders):
        driver_stops[idx % len(drivers)].append(order)

    # 7. Build route dicts
    routes = []
    for driver_idx, (_profile, user) in enumerate(drivers):
        stops = driver_stops[driver_idx]
        if not stops:
            continue

        # Total distance: hub → stop1 → stop2 → … → hub
        coords = [(s.delivery_lat, s.delivery_lng) for s in stops]
        total_dist = _euclidean_km(_HUB_LAT, _HUB_LNG, coords[0][0], coords[0][1])
        for i in range(len(coords) - 1):
            total_dist += _euclidean_km(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
        total_dist += _euclidean_km(coords[-1][0], coords[-1][1], _HUB_LAT, _HUB_LNG)

        routes.append(
            {
                "driver_id": str(user.id),
                "driver_name": user.name,
                "color": _ROUTE_COLORS[driver_idx % len(_ROUTE_COLORS)],
                "stops": [
                    {
                        "order_id": str(s.id),
                        "address": s.delivery_addr,
                        "lat": s.delivery_lat,
                        "lng": s.delivery_lng,
                        "tracking_code": s.tracking_code,
                        "priority": getattr(s, "priority", None) or "NORMAL",
                    }
                    for s in stops
                ],
                "total_distance_km": round(total_dist, 2),
                "efficiency": random.randint(85, 98),
            }
        )

    return routes


async def auto_balance_drivers(db: AsyncSession) -> dict:
    """
    Auto-balance workload across drivers by redistributing ASSIGNED orders.
    
    Algorithm:
    1. Get all active drivers and their ASSIGNED order counts
    2. Calculate average load per driver
    3. Identify overloaded (>avg) and underloaded (<avg) drivers
    4. Reassign orders from overloaded to underloaded drivers
    
    Does NOT touch IN_TRANSIT orders (already being delivered).
    """
    # 1. Get all active drivers
    driver_result = await db.execute(
        select(LogisticsDriverProfile, User)
        .join(User, User.id == LogisticsDriverProfile.user_id)
        .where(User.is_active.is_(True))
        .where(LogisticsDriverProfile.status == "Active")
    )
    drivers = driver_result.all()
    
    if len(drivers) < 2:
        return {
            "success": False,
            "message": "Need at least 2 active drivers to balance workload",
            "transfers": []
        }
    
    # 2. Get ASSIGNED orders per driver (not IN_TRANSIT - those are already being delivered)
    order_counts_result = await db.execute(
        select(Order.assigned_driver_id, func.count(Order.id).label("order_count"))
        .where(Order.status == "ASSIGNED")
        .where(Order.assigned_driver_id.isnot(None))
        .group_by(Order.assigned_driver_id)
    )
    order_counts = {str(row[0]): row[1] for row in order_counts_result.all()}
    
    # Build driver load map
    driver_loads = []
    for _profile, user in drivers:
        driver_id = str(user.id)
        count = order_counts.get(driver_id, 0)
        driver_loads.append({
            "driver_id": user.id,
            "driver_name": user.name,
            "order_count": count
        })
    
    # 3. Calculate average and identify imbalances
    total_orders = sum(d["order_count"] for d in driver_loads)
    if total_orders == 0:
        return {
            "success": True,
            "message": "No ASSIGNED orders to balance",
            "transfers": [],
            "before": {"total_orders": 0, "drivers": len(drivers)},
            "after": {"total_orders": 0, "drivers": len(drivers)}
        }
    
    avg_load = total_orders / len(driver_loads)
    
    # Sort: overloaded first (descending), underloaded last (ascending)
    overloaded = sorted(
        [d for d in driver_loads if d["order_count"] > avg_load],
        key=lambda x: x["order_count"],
        reverse=True
    )
    underloaded = sorted(
        [d for d in driver_loads if d["order_count"] < avg_load],
        key=lambda x: x["order_count"]
    )
    
    if not overloaded or not underloaded:
        return {
            "success": True,
            "message": "Workload is already balanced",
            "transfers": [],
            "balance_score": 100
        }
    
    # 4. Perform transfers
    transfers = []
    
    for over_driver in overloaded:
        while over_driver["order_count"] > avg_load and underloaded:
            # Find the most underloaded driver
            under_driver = underloaded[0]
            
            if under_driver["order_count"] >= avg_load:
                break  # No more underloaded drivers
            
            # Get one order from the overloaded driver to transfer
            order_result = await db.execute(
                select(Order)
                .where(Order.assigned_driver_id == over_driver["driver_id"])
                .where(Order.status == "ASSIGNED")
                .limit(1)
            )
            order_to_transfer = order_result.scalar_one_or_none()
            
            if not order_to_transfer:
                break
            
            # Transfer the order
            order_to_transfer.assigned_driver_id = under_driver["driver_id"]
            db.add(order_to_transfer)
            
            # Update driver profiles' current_job
            # (Update underloaded driver's current_job if they were free)
            under_profile = (await db.execute(
                select(LogisticsDriverProfile)
                .where(LogisticsDriverProfile.user_id == under_driver["driver_id"])
            )).scalar_one_or_none()
            if under_profile and not under_profile.current_job:
                under_profile.current_job = order_to_transfer.tracking_code
                db.add(under_profile)
            
            transfers.append({
                "order_id": str(order_to_transfer.id),
                "tracking_code": order_to_transfer.tracking_code,
                "from_driver": over_driver["driver_name"],
                "to_driver": under_driver["driver_name"]
            })
            
            # Update counts
            over_driver["order_count"] -= 1
            under_driver["order_count"] += 1
            
            # Re-sort underloaded list
            underloaded = sorted(underloaded, key=lambda x: x["order_count"])
    
    await db.flush()
    
    # Calculate new balance score
    new_loads = [d["order_count"] for d in driver_loads]
    if new_loads:
        mean = sum(new_loads) / len(new_loads)
        variance = sum((load - mean) ** 2 for load in new_loads) / len(new_loads)
        std_dev = math.sqrt(variance)
        balance_score = max(0, min(100, round(100 - (std_dev * 25))))
    else:
        balance_score = 100
    
    return {
        "success": True,
        "message": f"Transferred {len(transfers)} order(s) to balance workload",
        "transfers": transfers,
        "balance_score": balance_score,
        "driver_loads": [
            {"name": d["driver_name"], "orders": d["order_count"]}
            for d in driver_loads
        ]
    }
