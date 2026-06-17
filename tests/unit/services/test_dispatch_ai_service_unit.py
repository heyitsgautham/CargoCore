from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from app.services import dispatch_ai_service


def _order(*, tracking_code: str, priority: str, pickup_lat: float | None, pickup_lng: float | None):
    return SimpleNamespace(
        id=uuid4(),
        tracking_code=tracking_code,
        pickup_addr=f"Pickup {tracking_code}",
        delivery_addr=f"Drop {tracking_code}",
        priority=priority,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
    )


def test_haversine_km_is_positive_and_symmetric() -> None:
    a_to_b = dispatch_ai_service._haversine_km(19.0760, 72.8777, 19.2183, 72.9781)
    b_to_a = dispatch_ai_service._haversine_km(19.2183, 72.9781, 19.0760, 72.8777)

    assert a_to_b > 0
    assert round(a_to_b, 6) == round(b_to_a, 6)


def test_parse_location_valid_and_invalid_inputs() -> None:
    assert dispatch_ai_service._parse_location("19.0760,72.8777") == (19.076, 72.8777)
    assert dispatch_ai_service._parse_location(None) is None
    assert dispatch_ai_service._parse_location("bad") is None
    assert dispatch_ai_service._parse_location("19.07,not-a-number") is None


def test_priority_rank_ordering_and_default() -> None:
    assert dispatch_ai_service._priority_rank("URGENT") < dispatch_ai_service._priority_rank("HIGH")
    assert dispatch_ai_service._priority_rank("HIGH") < dispatch_ai_service._priority_rank("NORMAL")
    assert dispatch_ai_service._priority_rank("UNKNOWN") == 2
    assert dispatch_ai_service._priority_rank(None) == 2


def test_haversine_suggestions_assigns_unique_driver_per_order() -> None:
    orders = [
        _order(tracking_code="ORD-N", priority="NORMAL", pickup_lat=0.0, pickup_lng=0.2),
        _order(tracking_code="ORD-U", priority="URGENT", pickup_lat=0.0, pickup_lng=0.9),
    ]
    drivers = [
        {"id": "driver-1", "name": "Driver One", "status": "active", "current_job": "None", "coords": (0.0, 0.0), "location_str": "0,0"},
        {"id": "driver-2", "name": "Driver Two", "status": "active", "current_job": "None", "coords": (0.0, 1.0), "location_str": "0,1"},
    ]

    suggestions = dispatch_ai_service._haversine_suggestions(orders, drivers)

    assert len(suggestions) == 2
    assert suggestions[0]["priority"] == "URGENT"
    assert suggestions[0]["suggested_driver_id"] == "driver-2"
    assert suggestions[1]["suggested_driver_id"] == "driver-1"
    assert len({s["suggested_driver_id"] for s in suggestions}) == 2
    assert all(s["ai_powered"] is False for s in suggestions)


def test_haversine_suggestions_skips_orders_without_coordinates() -> None:
    orders = [
        _order(tracking_code="ORD-1", priority="HIGH", pickup_lat=None, pickup_lng=None),
        _order(tracking_code="ORD-2", priority="LOW", pickup_lat=0.0, pickup_lng=0.0),
    ]
    drivers = [
        {"id": "driver-1", "name": "Driver One", "status": "active", "current_job": "None", "coords": (0.0, 0.1), "location_str": "0,0.1"},
    ]

    suggestions = dispatch_ai_service._haversine_suggestions(orders, drivers)

    assert len(suggestions) == 1
    assert suggestions[0]["order_tracking_code"] == "ORD-2"


def test_haversine_suggestions_skips_drivers_without_coords() -> None:
    orders = [_order(tracking_code="ORD-1", priority="HIGH", pickup_lat=0.0, pickup_lng=0.0)]
    drivers = [
        {"id": "driver-1", "name": "Driver One", "status": "active", "current_job": "None", "coords": None, "location_str": "unknown"},
    ]

    suggestions = dispatch_ai_service._haversine_suggestions(orders, drivers)

    assert suggestions == []
