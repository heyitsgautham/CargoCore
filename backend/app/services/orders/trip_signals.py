"""ETA, deviation and dispatch-action signals for trips in progress."""

import math
from datetime import UTC, datetime, timedelta

from loguru import logger

from app.models.logistics import (
    LogisticsZone,
)
from app.services.orders.common import _now
from app.services.orders.routing import _euclidean_km


def _parse_driver_location(location: str | None) -> tuple[float | None, float | None]:
    if not location or "," not in str(location):
        return None, None
    try:
        lat_str, lng_str = str(location).split(",", 1)
        return float(lat_str.strip()), float(lng_str.strip())
    except Exception:
        return None, None


def _clamp(value: int | float, minimum: int | float, maximum: int | float) -> int | float:
    return max(minimum, min(maximum, value))


def _eta_label_from_minutes(eta_minutes: int, reference_time: datetime | None = None) -> str:
    arrival = (reference_time or _now()) + timedelta(minutes=max(eta_minutes, 0))
    return arrival.astimezone(UTC).strftime("%I:%M %p").lstrip("0")


def _build_route_signal(key: str, label: str, severity: str) -> dict:
    return {"key": key, "label": label, "severity": severity}


def _derive_eta_confidence(
    *,
    has_pickup_coords: bool,
    has_delivery_coords: bool,
    has_live_driver_location: bool,
    order_status: str,
) -> str:
    if has_pickup_coords and has_delivery_coords and (order_status != "IN_TRANSIT" or has_live_driver_location):
        return "High"
    if has_delivery_coords:
        return "Medium"
    return "Low"


def _recommended_dispatch_action(
    *,
    no_go_zone_hit: bool,
    route_status: str,
    risk_level: str,
    order_status: str,
    priority: str,
    minutes_saved: int,
) -> tuple[str, str]:
    if no_go_zone_hit:
        return (
            "Push the alternate corridor to the driver now. The planned corridor overlaps a restricted or exclusion zone.",
            "Dispatch has selected a safer corridor. Open the updated navigation before continuing.",
        )
    if route_status == "Delayed":
        return (
            "Customer ETA is at risk. Push a route update, notify the customer, and keep this trip in the exception queue.",
            "This trip is running behind plan. Follow the updated route and keep dispatch informed.",
        )
    if risk_level in {"HIGH", "CRITICAL"} and minutes_saved >= 5:
        return (
            f"Push the alternate route now. It is currently projecting {minutes_saved} minutes of recovery.",
            f"An alternate route is available and may recover about {minutes_saved} minutes.",
        )
    if order_status == "ASSIGNED" and priority in {"URGENT", "HIGH"}:
        return (
            "Send the driver immediately and monitor first-mile progress. This trip has a tight operating window.",
            "This job is time-sensitive. Start navigation as soon as dispatch confirms the release.",
        )
    return (
        "Trip is on plan. Keep the primary corridor and monitor only if ETA confidence drops.",
        "Trip is on track. Use the planned route and continue normal navigation.",
    )


def _compute_alternate_waypoints(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    hit_zones: list[LogisticsZone],
) -> list[dict]:
    """Return a single bypass waypoint that steers around the first exclusion zone."""
    if not hit_zones:
        return []
    zone = hit_zones[0]
    if zone.lat is None or zone.lng is None:
        return []
    radius_km = zone.radius_km or 1.0
    mid_lat = (origin_lat + dest_lat) / 2
    mid_lng = (origin_lng + dest_lng) / 2
    dlat = dest_lat - origin_lat
    dlng = dest_lng - origin_lng
    route_len = math.sqrt(dlat ** 2 + dlng ** 2)
    if route_len < 1e-9:
        return []
    perp1 = (-dlng / route_len, dlat / route_len)
    perp2 = (dlng / route_len, -dlat / route_len)
    offset_deg = (radius_km + 2.5) * 0.009
    cand1 = (mid_lat + perp1[0] * offset_deg, mid_lng + perp1[1] * offset_deg)
    cand2 = (mid_lat + perp2[0] * offset_deg, mid_lng + perp2[1] * offset_deg)
    dist1 = _euclidean_km(cand1[0], cand1[1], zone.lat, zone.lng)
    dist2 = _euclidean_km(cand2[0], cand2[1], zone.lat, zone.lng)
    wp = cand1 if dist1 > dist2 else cand2
    return [{"lat": round(wp[0], 6), "lng": round(wp[1], 6)}]


async def _enrich_with_gemini(base: dict) -> dict:
    """Replace templated messages with Gemini-generated operational intelligence."""
    import json as _json

    try:
        from google.genai import types as genai_types

        from app.utils.gemini import generate_with_fallback

        signals_text = "\n".join(
            f"- [{s['severity'].upper()}] {s['label']}" for s in base.get("signals", [])
        ) or "No active risk signals."
        minutes_saved = max(0, -(base["alternate_route"]["delta_minutes"]))

        prompt = f"""You are a logistics AI analyst for Cargo-Core dispatch platform.

TRIP FACTS:
- Tracking: {base['tracking_code']} | Status: {base['order_status']} | Priority: {base['priority']}
- Route status: {base['route_status']} | Risk: {base['risk_level']} | Delay probability: {base['delay_probability_pct']}%
- ETA: {base['eta_label']} ({base['eta_minutes']} min) | Distance: {base['planned_distance_km']} km
- No-go zone hit: {base['no_go_zone_hit']} | Recommended route: {base['recommended_route']}
- Alternate saves: {minutes_saved} min

RISK SIGNALS:
{signals_text}

Return ONLY valid JSON (no markdown):
{{
  "dispatcher_recommendation": "...",
  "driver_message": "...",
  "alternate_route_summary": "..."
}}

Rules:
- dispatcher_recommendation: 40-70 words, operational, tells dispatcher exactly what to do and why
- driver_message: 20-35 words, direct and simple, as if spoken by radio dispatch to the driver
- alternate_route_summary: 15-25 words, what the alternate avoids or why it is faster"""

        response = await generate_with_fallback(
            contents=[genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=prompt)])],
            config=genai_types.GenerateContentConfig(temperature=0.3, response_mime_type="application/json"),
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        ai = _json.loads(text)
        result = {**base}
        if ai.get("dispatcher_recommendation"):
            result["dispatcher_recommendation"] = ai["dispatcher_recommendation"]
        if ai.get("driver_message"):
            result["driver_message"] = ai["driver_message"]
        if ai.get("alternate_route_summary"):
            result["alternate_route"] = {**base["alternate_route"], "summary": ai["alternate_route_summary"]}
        return result
    except Exception as exc:
        logger.warning(f"Gemini trip enrichment failed, using rule-based fallback: {exc}")
        return base
