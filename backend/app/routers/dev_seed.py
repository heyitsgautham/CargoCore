"""
dev_seed.py
Demo / test seed endpoint — injects realistic Bangalore GPS coordinates into
existing orders and driver profiles so the AI dispatch features work immediately
without any real deliveries or GPS movement.

ONLY register this router in development. It is gated behind a hard-coded dev
check so it cannot accidentally run against production data.

POST /api/v1/dev/seed-gps  — seeds coords on orders + driver locations
DELETE /api/v1/dev/seed-gps — wipes the seeded coords (reset to null)
"""
from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.logistics import LogisticsDriverProfile, LogisticsZone
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse

router = APIRouter(prefix="/api/v1/dev", tags=["Dev Seed"])

# ── Bangalore landmark coordinates ───────────────────────────────────────────
# Spread across the city so distances are meaningful for clustering / return trips.
_PICKUP_SPOTS = [
    (12.9716, 77.5946, "Majestic Bus Stand"),
    (12.9784, 77.6408, "Indiranagar 100ft Road"),
    (12.9352, 77.6245, "Koramangala 5th Block"),
    (13.0358, 77.5972, "Hebbal Flyover"),
    (12.9121, 77.6446, "BTM Layout 2nd Stage"),
    (12.9698, 77.7499, "Whitefield ITPL Gate"),
    (13.0100, 77.5500, "Yeshwanthpur Circle"),
    (12.9250, 77.5010, "Banashankari Temple"),
]

_DELIVERY_SPOTS = [
    (12.9279, 77.6271, "HSR Layout Sector 2"),
    (13.0456, 77.6200, "Hennur Road Junction"),
    (12.9165, 77.6011, "JP Nagar 7th Phase"),
    (12.9550, 77.7098, "Marathahalli Bridge"),
    (13.0200, 77.6500, "Thanisandra Main Road"),
    (12.9800, 77.5700, "Rajajinagar 3rd Block"),
    (12.9000, 77.5800, "Kanakapura Road"),
    (13.0600, 77.5800, "Yelahanka New Town"),
]

_DRIVER_SPOTS = [
    (12.9716, 77.5946, "Majestic Hub"),
    (12.9500, 77.6300, "Near Koramangala"),
    (13.0200, 77.6000, "Near Hebbal"),
    (12.9300, 77.6500, "Near BTM"),
    (12.9800, 77.7000, "Near Whitefield"),
    (13.0000, 77.5600, "Near Yeshwanthpur"),
]


def _rand_offset(base_lat: float, base_lng: float, km: float = 1.5):
    """Slightly randomise a coordinate within km radius for realism."""
    deg = km / 111.0
    return (
        round(base_lat + random.uniform(-deg, deg), 6),
        round(base_lng + random.uniform(-deg, deg), 6),
    )


@router.post("/seed-gps")
async def seed_gps_coordinates(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """
    Inject realistic Bangalore GPS coordinates into:
      • Up to 8 CONFIRMED orders (pickup + delivery coords)
      • Up to 3 DELIVERED orders from the last 2 hours (for return-trip suggestions)
      • All active driver profiles (current_location)

    Safe to call multiple times — re-seeds existing records rather than
    creating new ones. Returns a summary of what was updated.
    """
    summary = {"orders_seeded": 0, "delivered_seeded": 0, "drivers_seeded": 0, "detail": []}

    # ── 1. Seed CONFIRMED orders ───────────────────────────────────────────────
    confirmed_orders = (
        await db.execute(
            select(Order)
            .where(Order.status == "CONFIRMED")
            .order_by(Order.created_at.desc())
            .limit(8)
        )
    ).scalars().all()

    random.shuffle(_PICKUP_SPOTS)
    random.shuffle(_DELIVERY_SPOTS)

    for i, order in enumerate(confirmed_orders):
        p_lat, p_lng, p_name = _PICKUP_SPOTS[i % len(_PICKUP_SPOTS)]
        d_lat, d_lng, d_name = _DELIVERY_SPOTS[i % len(_DELIVERY_SPOTS)]

        order.pickup_lat, order.pickup_lng = _rand_offset(p_lat, p_lng, 0.5)
        order.delivery_lat, order.delivery_lng = _rand_offset(d_lat, d_lng, 0.5)
        if not order.pickup_addr or order.pickup_addr.strip() == "":
            order.pickup_addr = p_name
        if not order.delivery_addr or order.delivery_addr.strip() == "":
            order.delivery_addr = d_name

        db.add(order)
        summary["orders_seeded"] += 1
        summary["detail"].append(
            f"CONFIRMED {order.tracking_code}: pickup=({order.pickup_lat},{order.pickup_lng}) delivery=({order.delivery_lat},{order.delivery_lng})"
        )

    # ── 2. Seed recent DELIVERED orders (return-trip source) ──────────────────
    # These need delivered_at within the last 2 hours so the return-trip query picks them up.
    delivered_orders = (
        await db.execute(
            select(Order)
            .where(Order.status == "DELIVERED", Order.assigned_driver_id.isnot(None))
            .order_by(Order.delivered_at.desc().nullslast(), Order.created_at.desc())
            .limit(3)
        )
    ).scalars().all()

    now = datetime.now(UTC)
    for i, order in enumerate(delivered_orders):
        d_lat, d_lng, d_name = _DELIVERY_SPOTS[(i + 3) % len(_DELIVERY_SPOTS)]
        order.delivery_lat, order.delivery_lng = _rand_offset(d_lat, d_lng, 0.5)
        if not order.delivery_addr or order.delivery_addr.strip() == "":
            order.delivery_addr = d_name
        # Bump delivered_at to 20-60 min ago so it's within the 2-hour window
        order.delivered_at = now - timedelta(minutes=random.randint(20, 60))
        db.add(order)
        summary["delivered_seeded"] += 1
        summary["detail"].append(
            f"DELIVERED {order.tracking_code}: delivery=({order.delivery_lat},{order.delivery_lng}) delivered_at={order.delivered_at.strftime('%H:%M')}"
        )

    # ── 3. Seed driver locations ───────────────────────────────────────────────
    driver_rows = (
        await db.execute(
            select(LogisticsDriverProfile, User)
            .join(User, User.id == LogisticsDriverProfile.user_id)
            .where(User.is_active.is_(True))
            .limit(6)
        )
    ).all()

    random.shuffle(_DRIVER_SPOTS)
    for i, (profile, user) in enumerate(driver_rows):
        d_lat, d_lng, spot_name = _DRIVER_SPOTS[i % len(_DRIVER_SPOTS)]
        lat, lng = _rand_offset(d_lat, d_lng, 1.0)
        profile.current_location = f"{lat},{lng}"
        # Make sure status is something the AI considers "available"
        if (profile.status or "").lower() not in ("active", "idle", "on_break", "on-duty"):
            profile.status = "Active"
        db.add(profile)
        summary["drivers_seeded"] += 1
        summary["detail"].append(
            f"Driver {user.name}: location=({lat},{lng}) near {spot_name}"
        )

        # Broadcast to live dispatcher map via WebSocket
        try:
            import asyncio

            from app.routers.ws_fleet import fleet_manager
            asyncio.ensure_future(
                fleet_manager.broadcast({
                    "type": "location_update",
                    "driver_id": str(user.id),
                    "driver_name": user.name,
                    "latitude": lat,
                    "longitude": lng,
                    "status": profile.status,
                    "vehicle_code": None,
                    "vehicle_id": None,
                    "last_updated": now.isoformat(),
                    "source": "dev_seed",
                })
            )
        except Exception:
            pass

    # ── 4. Seed ASSIGNED / IN_TRANSIT orders (used by trip intelligence) ────────
    active_orders = (
        await db.execute(
            select(Order)
            .where(Order.status.in_(["ASSIGNED", "IN_TRANSIT"]))
            .order_by(Order.created_at.desc())
            .limit(8)
        )
    ).scalars().all()

    random.shuffle(_PICKUP_SPOTS)
    random.shuffle(_DELIVERY_SPOTS)
    for i, order in enumerate(active_orders):
        p_lat, p_lng, p_name = _PICKUP_SPOTS[i % len(_PICKUP_SPOTS)]
        d_lat, d_lng, d_name = _DELIVERY_SPOTS[i % len(_DELIVERY_SPOTS)]
        order.pickup_lat, order.pickup_lng = _rand_offset(p_lat, p_lng, 0.5)
        order.delivery_lat, order.delivery_lng = _rand_offset(d_lat, d_lng, 0.5)
        if not order.pickup_addr or order.pickup_addr.strip() == "":
            order.pickup_addr = p_name
        if not order.delivery_addr or order.delivery_addr.strip() == "":
            order.delivery_addr = d_name
        db.add(order)
        summary["orders_seeded"] += 1
        summary["detail"].append(
            f"ACTIVE {order.tracking_code} ({order.status}): pickup=({order.pickup_lat},{order.pickup_lng}) delivery=({order.delivery_lat},{order.delivery_lng})"
        )

    # ── 5. Seed exclusion zones so alternate route AI kicks in ────────────────
    # Real Bengaluru high-risk / restricted areas placed along common corridors
    _EXCLUSION_ZONES = [
        {"name": "Silk Board Junction Restriction", "lat": 12.9175, "lng": 77.6229, "radius_km": 1.8},
        {"name": "Marathahalli Signal Bottleneck", "lat": 12.9558, "lng": 77.7016, "radius_km": 1.5},
        {"name": "Hebbal Flyover No-Go Zone",       "lat": 13.0358, "lng": 77.5972, "radius_km": 1.2},
        {"name": "Whitefield IT Corridor Block",    "lat": 12.9698, "lng": 77.7499, "radius_km": 1.4},
        {"name": "KR Puram Bridge Closure",         "lat": 13.0000, "lng": 77.6800, "radius_km": 1.0},
    ]

    warehouses = (await db.execute(select(Warehouse).limit(5))).scalars().all()
    zones_seeded = 0
    for warehouse in warehouses:
        for zdef in _EXCLUSION_ZONES:
            existing = (
                await db.execute(
                    select(LogisticsZone).where(
                        LogisticsZone.warehouse_id == warehouse.id,
                        LogisticsZone.name == zdef["name"],
                    )
                )
            ).scalar_one_or_none()
            if existing:
                existing.zone_type = "exclusion"
                existing.lat = zdef["lat"]
                existing.lng = zdef["lng"]
                existing.radius_km = zdef["radius_km"]
                existing.status = "Active"
                db.add(existing)
            else:
                db.add(LogisticsZone(
                    warehouse_id=warehouse.id,
                    name=zdef["name"],
                    zone_type="exclusion",
                    lat=zdef["lat"],
                    lng=zdef["lng"],
                    radius_km=zdef["radius_km"],
                    status="Active",
                    color_token="red",
                ))
            zones_seeded += 1

    summary["zones_seeded"] = zones_seeded
    summary["detail"].append(f"Seeded {zones_seeded} exclusion zones across {len(warehouses)} warehouses")

    await db.commit()
    return {
        "status": "seeded",
        **summary,
        "next_steps": [
            "Open Dispatcher → Route Optimization",
            "Exclusion zones are now active — AI will detect them and compute alternate bypass routes",
            "Open Dispatcher → Smart Driver Assignment for assignment suggestions",
        ],
    }


@router.delete("/seed-gps")
async def clear_seeded_gps(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """Wipe all GPS coordinates from orders and driver profiles (reset to null)."""
    orders = (await db.execute(select(Order))).scalars().all()
    for order in orders:
        order.pickup_lat = None
        order.pickup_lng = None
        order.delivery_lat = None
        order.delivery_lng = None
        db.add(order)

    profiles = (await db.execute(select(LogisticsDriverProfile))).scalars().all()
    for profile in profiles:
        profile.current_location = None
        db.add(profile)

    _SEED_ZONE_NAMES = [
        "Silk Board Junction Restriction",
        "Marathahalli Signal Bottleneck",
        "Hebbal Flyover No-Go Zone",
        "Whitefield IT Corridor Block",
        "KR Puram Bridge Closure",
    ]
    zones = (
        await db.execute(select(LogisticsZone).where(LogisticsZone.name.in_(_SEED_ZONE_NAMES)))
    ).scalars().all()
    for zone in zones:
        await db.delete(zone)

    await db.commit()
    return {"status": "cleared", "orders_cleared": len(orders), "drivers_cleared": len(profiles), "zones_cleared": len(zones)}
