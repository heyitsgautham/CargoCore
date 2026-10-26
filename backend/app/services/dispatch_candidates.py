"""Data the dispatch AI ranks: distances, driver history matches, available drivers, unassigned orders, and the distance-only fallback ranking."""

from __future__ import annotations

import math
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsDriverProfile
from app.models.order import Order
from app.models.user import User

# ── Helpers ───────────────────────────────────────────────────────────────────


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(max(0.0, a)))


def _parse_location(loc_str: str | None) -> tuple[float, float] | None:
    """Parse a 'lat,lng' string into a (lat, lng) float tuple, or None."""
    if not loc_str or "," not in loc_str:
        return None
    try:
        lat_s, lng_s = loc_str.split(",", 1)
        return float(lat_s.strip()), float(lng_s.strip())
    except (ValueError, TypeError):
        return None


def _priority_rank(priority: str | None) -> int:
    return {"URGENT": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}.get(
        (priority or "NORMAL").upper(), 2
    )


def _normalized_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _active_driver_profile_statuses() -> list[str]:
    return ["active", "idle", "on_break", "on-duty"]


async def _fetch_busy_driver_ids(db: AsyncSession) -> set[str]:
    """Drivers already tied to a live order should not be suggested again."""
    active_order_statuses = {"ASSIGNED", "CONFIRMED", "IN_TRANSIT", "PICKING", "PACKING", "PICKED", "PACKED"}
    busy_driver_rows = (
        await db.execute(
            select(Order.assigned_driver_id)
            .where(
                Order.assigned_driver_id.isnot(None),
                Order.status.in_(active_order_statuses),
            )
            .distinct()
        )
    ).scalars().all()
    return {str(uid) for uid in busy_driver_rows}


def _driver_history_match_score(order: Order, driver: dict) -> int:
    """Score how well a driver's recent non-packing work matches this order."""
    recent = driver.get("recent_non_packing_order")
    if not recent:
        return 0

    score = 0
    if _normalized_text(getattr(order, "order_type", None)) == _normalized_text(recent.get("order_type")):
        score += 55
    if _normalized_text(getattr(order, "cargo_type", None)) == _normalized_text(recent.get("cargo_type")):
        score += 30
    if _normalized_text(getattr(order, "vehicle_type", None)) == _normalized_text(recent.get("vehicle_type")):
        score += 15
    return score


def _driver_history_match_labels(order: Order, driver: dict) -> list[str]:
    recent = driver.get("recent_non_packing_order")
    if not recent:
        return []

    labels: list[str] = []
    if _normalized_text(getattr(order, "order_type", None)) == _normalized_text(recent.get("order_type")):
        labels.append("order type")
    if _normalized_text(getattr(order, "cargo_type", None)) == _normalized_text(recent.get("cargo_type")):
        labels.append("cargo type")
    if _normalized_text(getattr(order, "vehicle_type", None)) == _normalized_text(recent.get("vehicle_type")):
        labels.append("vehicle type")
    return labels


async def _fetch_recent_non_packing_history(
    db: AsyncSession,
    driver_ids: list[UUID],
) -> dict[str, dict]:
    """Return each driver's most recent delivered non-packing order profile."""
    if not driver_ids:
        return {}

    recent_orders = (
        await db.execute(
            select(Order)
            .where(
                Order.assigned_driver_id.in_(driver_ids),
                Order.status == "DELIVERED",
                Order.packing_amount == 0,
            )
            .order_by(Order.delivered_at.desc().nullslast(), Order.updated_at.desc())
        )
    ).scalars().all()

    history_by_driver: dict[str, dict] = {}
    for order in recent_orders:
        driver_id = str(order.assigned_driver_id) if order.assigned_driver_id else None
        if not driver_id or driver_id in history_by_driver:
            continue
        history_by_driver[driver_id] = {
            "tracking_code": order.tracking_code or "",
            "order_type": order.order_type or "",
            "cargo_type": order.cargo_type or "",
            "vehicle_type": order.vehicle_type or "",
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        }
    return history_by_driver


# ── DB fetch helpers ──────────────────────────────────────────────────────────


async def _fetch_available_drivers(db: AsyncSession) -> list[dict]:
    """Return active drivers who do NOT have an active assigned order.

    A driver is excluded if they have any order with assigned_driver_id == their user_id
    and that order is in an active state (CONFIRMED, IN_TRANSIT, PICKING, PACKING, etc.).
    This prevents the AI from suggesting a driver who is already on a job.
    """
    # Find all driver user_ids that are currently assigned to an active order
    busy_driver_ids = await _fetch_busy_driver_ids(db)

    rows = (
        await db.execute(
            select(LogisticsDriverProfile, User)
            .join(User, User.id == LogisticsDriverProfile.user_id)
            .where(
                User.is_active.is_(True),
                func.lower(LogisticsDriverProfile.status).in_(
                    _active_driver_profile_statuses()
                ),
            )
        )
    ).all()

    history_by_driver = await _fetch_recent_non_packing_history(
        db,
        [user.id for _, user in rows],
    )

    drivers = []
    for profile, user in rows:
        if str(user.id) in busy_driver_ids:
            continue  # already assigned to an active order — skip
        coords = _parse_location(profile.current_location)
        drivers.append(
            {
                "id": str(user.id),
                "name": user.name,
                "status": profile.status,
                "current_job": profile.current_job or "None",
                "coords": coords,
                "location_str": profile.current_location or "Unknown",
                "recent_non_packing_order": history_by_driver.get(str(user.id)),
            }
        )
    return drivers


async def _fetch_unassigned_orders(db: AsyncSession, limit: int = 15) -> list[Order]:
    """Return CONFIRMED orders eligible for dispatcher direct-driver assignment.

    Only orders with no packing requirement AND no vehicle already assigned by the
    Warehouse Manager are returned.  If the WM has already assigned a vehicle the
    order is travelling the normal warehouse flow and should not appear in the
    dispatcher's AI clustering panel.

    Orders that include packing services (packing_amount > 0) are also excluded
    because drivers completing a previous move will have used up their packing
    materials and cannot fulfil a new packing job without restocking.
    """
    orders = (
        await db.execute(
            select(Order)
            .where(
                Order.status == "CONFIRMED",
                Order.assigned_driver_id.is_(None),
                Order.assigned_vehicle_id.is_(None),   # WM already owns it → skip
                Order.packing_amount == 0,
            )
            .order_by(Order.created_at.asc())
            .limit(limit)
        )
    ).scalars().all()
    return list(orders)


# ── Fallback (no AI) ──────────────────────────────────────────────────────────


def _haversine_suggestions(
    orders: list[Order], drivers: list[dict]
) -> list[dict]:
    """Simple nearest-driver fallback when Gemini is unavailable.

    Each driver is only suggested for ONE order (the closest one they can serve).
    Once a driver is assigned to an order they are removed from the available pool.
    """
    suggestions = []
    remaining_drivers = [d for d in drivers]  # mutable copy so we can pop assigned ones
    # Sort orders by priority so urgent orders get first pick of drivers
    sorted_orders = sorted(
        orders, key=lambda o: _priority_rank(getattr(o, "priority", "NORMAL") or "NORMAL")
    )
    for order in sorted_orders:
        if order.pickup_lat is None or order.pickup_lng is None:
            continue
        if not remaining_drivers:
            break  # no more drivers to assign
        best_driver, best_dist, best_idx, best_score = None, float("inf"), -1, float("-inf")
        for idx, d in enumerate(remaining_drivers):
            if not d["coords"]:
                continue
            dist = _haversine_km(
                d["coords"][0], d["coords"][1], order.pickup_lat, order.pickup_lng
            )
            history_score = _driver_history_match_score(order, d)
            composite_score = 100 - min(dist * 4, 80) + history_score
            if (
                composite_score > best_score
                or (math.isclose(composite_score, best_score) and dist < best_dist)
            ):
                best_score, best_dist, best_driver, best_idx = composite_score, dist, d, idx
        if best_driver:
            match_labels = _driver_history_match_labels(order, best_driver)
            recent = best_driver.get("recent_non_packing_order")
            conf = max(20, min(98, int(best_score)))
            if match_labels and recent:
                reason = (
                    f"Closest strong-fit available driver at {best_dist:.1f} km from pickup. "
                    f"Recent non-packing job {recent['tracking_code']} matched on {', '.join(match_labels)}."
                )
            else:
                reason = (
                    f"Closest available driver at {best_dist:.1f} km from pickup."
                    " (Gemini unavailable — distance-first match)"
                )
            suggestions.append(
                {
                    "order_tracking_code": order.tracking_code or "",
                    "order_id": str(order.id),
                    "pickup_addr": order.pickup_addr or "",
                    "delivery_addr": order.delivery_addr or "",
                    "priority": getattr(order, "priority", "NORMAL") or "NORMAL",
                    "suggested_driver_id": best_driver["id"],
                    "suggested_driver_name": best_driver["name"],
                    "distance_km": round(best_dist, 1),
                    "confidence": conf,
                    "reason": reason,
                    "ai_powered": False,
                }
            )
            remaining_drivers.pop(best_idx)  # driver is now assigned — remove from pool
    suggestions.sort(key=lambda s: (_priority_rank(s["priority"]), s["distance_km"]))
    return suggestions
