"""Distance and cost estimates for a recurring schedule, using OSRM road routes when reachable."""

import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsZone
from app.models.warehouse import Warehouse
from app.schemas.vendor import (
    VendorRecurringCostEstimate,
    VendorRecurringCostEstimateRequest,
)


def _safe_float(value) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _normalize_uuid(value) -> uuid.UUID | None:
    if not value:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except Exception:
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in km between two lat/lon points."""
    import math
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


_OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"
_OSRM_TIMEOUT_SECONDS = 5.0


def _fallback_route_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Fallback heuristic when route service is unavailable."""
    return max(1.0, round(_haversine_km(lat1, lon1, lat2, lon2) * 1.35, 1))


async def _road_route_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> tuple[float, str]:
    """Return road-route km using OSRM, falling back to a padded estimate."""
    url = f"{_OSRM_BASE_URL}/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false"}
    try:
        async with httpx.AsyncClient(timeout=_OSRM_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
        route = (payload.get("routes") or [None])[0]
        if payload.get("code") != "Ok" or not route:
            return _fallback_route_km(lat1, lon1, lat2, lon2), "road_route_fallback"
        meters = float(route.get("distance") or 0.0)
        return max(1.0, round(meters / 1000.0, 1)), "road_route"
    except Exception:
        return _fallback_route_km(lat1, lon1, lat2, lon2), "road_route_fallback"


async def _resolve_recurring_warehouse(
    db: AsyncSession,
    *,
    hub_id: uuid.UUID | None = None,
    hub_name: str | None = None,
    fallback_to_first: bool = True,
) -> tuple[Warehouse | None, str]:
    warehouse = None
    if hub_id:
        warehouse = (
            await db.execute(
                select(Warehouse).where(
                    Warehouse.id == hub_id,
                    Warehouse.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if warehouse:
            return warehouse, "hub_id"

    normalized_hub_name = (hub_name or "").strip()
    if normalized_hub_name:
        warehouse = (
            await db.execute(
                select(Warehouse).where(
                    Warehouse.is_active.is_(True),
                    Warehouse.name.ilike(f"%{normalized_hub_name}%"),
                ).order_by(Warehouse.created_at.asc()).limit(1)
            )
        ).scalar_one_or_none()
        if warehouse:
            return warehouse, "hub_name"

    if not fallback_to_first:
        return None, "unresolved"

    warehouse = (
        await db.execute(
            select(Warehouse).where(Warehouse.is_active.is_(True)).order_by(Warehouse.created_at.asc()).limit(1)
        )
    ).scalar_one_or_none()
    return warehouse, "first_active" if warehouse else "unresolved"


async def _resolve_recurring_pickup_origin(
    db: AsyncSession,
    *,
    warehouse: Warehouse | None,
) -> tuple[float | None, float | None, str | None, str]:
    if warehouse and warehouse.lat is not None and warehouse.lng is not None:
        return warehouse.lat, warehouse.lng, warehouse.name, "warehouse_coordinates"

    if warehouse:
        zone = (
            await db.execute(
                select(LogisticsZone).where(
                    LogisticsZone.warehouse_id == warehouse.id,
                    LogisticsZone.status.ilike("active"),
                    LogisticsZone.lat.is_not(None),
                    LogisticsZone.lng.is_not(None),
                ).order_by(LogisticsZone.created_at.asc()).limit(1)
            )
        ).scalar_one_or_none()
        if zone:
            return zone.lat, zone.lng, zone.name or warehouse.name, "geofence_zone"

    return None, None, warehouse.name if warehouse else None, "missing_coordinates"


def _build_recurring_estimate_note(
    *,
    warehouse_name: str | None,
    warehouse_source: str,
    pickup_source: str,
    pickup_reference: str | None,
    distance_method: str,
) -> str:
    hub_label = warehouse_name or "selected hub"
    used_fallback = distance_method == "road_route_fallback"
    if pickup_source == "geofence_zone":
        zone_label = pickup_reference or hub_label
        prefix = (
            f"Estimate uses road-route distance from active geofence zone '{zone_label}' because "
            f"'{hub_label}' has no saved warehouse coordinates."
        )
    elif pickup_source == "missing_coordinates":
        prefix = f"'{hub_label}' has no saved warehouse coordinates or active geofence center, so only the base fee is shown."
    else:
        prefix = f"Estimate uses road-route distance from '{hub_label}' warehouse coordinates."

    if used_fallback and pickup_source != "missing_coordinates":
        prefix = f"{prefix} Live routing was unavailable, so a buffered fallback estimate was used."

    if warehouse_source == "first_active":
        return f"{prefix} Selected hub could not be matched exactly, so the first active warehouse was used."
    if warehouse_source == "unresolved":
        return f"{prefix} No matching active warehouse was found."
    return prefix


async def estimate_recurring_cost(
    db: AsyncSession,
    data: "VendorRecurringCostEstimateRequest",
) -> "VendorRecurringCostEstimate":
    """Estimate the per-run cost for a recurring schedule.

    Calculates road-route distance from the resolved warehouse pickup origin to
    the destination coordinates, then applies the configured rate card
    (baseBookingFee + perKmRate). Falls back to a buffered estimate if live
    routing is unavailable.
    """
    from app.routers.rates import _load as _load_rates

    wh, warehouse_source = await _resolve_recurring_warehouse(
        db,
        hub_id=data.hub_id,
        hub_name=data.hub_name,
        fallback_to_first=True,
    )

    rate_cfg = _load_rates()
    base_fee = float(rate_cfg.get("baseBookingFee", 220))
    per_km = float(rate_cfg.get("perKmRate", 12))

    pickup_lat, pickup_lng, pickup_reference, pickup_source = await _resolve_recurring_pickup_origin(
        db,
        warehouse=wh,
    )
    dist_km = 0.0
    distance_method = "road_route"
    if pickup_lat is not None and pickup_lng is not None:
        dist_km, distance_method = await _road_route_distance_km(
            pickup_lat,
            pickup_lng,
            data.destination_lat,
            data.destination_lon,
        )

    distance_cost = round(dist_km * per_km, 2)
    total_estimate = round(base_fee + distance_cost, 2)
    resolved_hub_name = wh.name if wh else (data.hub_name or None)

    return VendorRecurringCostEstimate(
        distance_km=round(dist_km, 2),
        base_fee=base_fee,
        distance_cost=distance_cost,
        total_estimate=total_estimate,
        rate_per_km=per_km,
        distance_method=distance_method,
        resolved_hub_name=resolved_hub_name,
        pickup_source=pickup_source,
        pickup_reference=pickup_reference,
        note=_build_recurring_estimate_note(
            warehouse_name=resolved_hub_name,
            warehouse_source=warehouse_source,
            pickup_source=pickup_source,
            pickup_reference=pickup_reference,
            distance_method=distance_method,
        ),
    )
