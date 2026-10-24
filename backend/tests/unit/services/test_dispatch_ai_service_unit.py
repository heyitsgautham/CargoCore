from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import dispatch_ai_service


def _order(
    *,
    tracking_code: str,
    priority: str,
    pickup_lat: float | None,
    pickup_lng: float | None,
    order_type: str = "VENDOR",
    cargo_type: str | None = None,
    vehicle_type: str | None = None,
):
    return SimpleNamespace(
        id=uuid4(),
        tracking_code=tracking_code,
        pickup_addr=f"Pickup {tracking_code}",
        delivery_addr=f"Drop {tracking_code}",
        priority=priority,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        order_type=order_type,
        cargo_type=cargo_type,
        vehicle_type=vehicle_type,
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


def test_haversine_suggestions_prefers_recent_non_packing_type_match() -> None:
    orders = [
        _order(
            tracking_code="ORD-MATCH",
            priority="NORMAL",
            pickup_lat=0.0,
            pickup_lng=0.0,
            order_type="SERVICE_MOVE",
            cargo_type="Furniture",
            vehicle_type="Van",
        )
    ]
    drivers = [
        {
            "id": "driver-near",
            "name": "Near Driver",
            "status": "active",
            "current_job": "None",
            "coords": (0.0, 0.01),
            "location_str": "0,0.01",
            "recent_non_packing_order": {
                "tracking_code": "OLD-NEAR",
                "order_type": "VENDOR",
                "cargo_type": "Electronics",
                "vehicle_type": "Truck",
            },
        },
        {
            "id": "driver-match",
            "name": "Match Driver",
            "status": "active",
            "current_job": "None",
            "coords": (0.0, 0.03),
            "location_str": "0,0.03",
            "recent_non_packing_order": {
                "tracking_code": "OLD-MATCH",
                "order_type": "SERVICE_MOVE",
                "cargo_type": "Furniture",
                "vehicle_type": "Van",
            },
        },
    ]

    suggestions = dispatch_ai_service._haversine_suggestions(orders, drivers)

    assert len(suggestions) == 1
    assert suggestions[0]["suggested_driver_id"] == "driver-match"
    assert "OLD-MATCH" in suggestions[0]["reason"]
    assert "order type" in suggestions[0]["reason"]


@pytest.mark.asyncio
async def test_return_trip_suggestions_only_include_on_shift_non_busy_driver() -> None:
    now = datetime.now(UTC)
    free_driver_id = uuid4()
    busy_driver_id = uuid4()

    pending_order = SimpleNamespace(
        id=uuid4(),
        tracking_code="PENDING-1",
        pickup_addr="Pickup A",
        delivery_addr="Drop A",
        pickup_lat=12.9700,
        pickup_lng=77.5900,
        priority="NORMAL",
    )
    recent_delivery = SimpleNamespace(
        id=uuid4(),
        tracking_code="DONE-1",
        delivery_addr="Last Drop",
        delivery_lat=12.9710,
        delivery_lng=77.5910,
        delivered_at=now - timedelta(minutes=20),
        packing_amount=0.0,
    )
    busy_delivery = SimpleNamespace(
        id=uuid4(),
        tracking_code="DONE-2",
        delivery_addr="Busy Drop",
        delivery_lat=12.9712,
        delivery_lng=77.5912,
        delivered_at=now - timedelta(minutes=10),
        packing_amount=0.0,
    )

    class _FakeScalarResult:
        def __init__(self, values):
            self._values = values

        def all(self):
            return self._values

    class _FakeResult:
        def __init__(self, values):
            self._values = values

        def all(self):
            return self._values

        def scalars(self):
            return _FakeScalarResult(self._values)

    class _FakeDb:
        def __init__(self):
            self._calls = 0

        async def execute(self, query):
            self._calls += 1
            if self._calls == 1:
                return _FakeResult([busy_driver_id])
            if self._calls == 2:
                return _FakeResult([
                    (
                        recent_delivery,
                        SimpleNamespace(id=free_driver_id, name="Free Driver"),
                        SimpleNamespace(current_location="12.9705,77.5905"),
                    ),
                    (
                        busy_delivery,
                        SimpleNamespace(id=busy_driver_id, name="Busy Driver"),
                        SimpleNamespace(current_location="12.9705,77.5905"),
                    ),
                ])
            raise AssertionError("Unexpected DB execute call")

    async def _fake_fetch_unassigned_orders(db, limit=40):
        return [pending_order]

    def _raise_gemini_config():
        raise dispatch_ai_service.GeminiConfigError("missing key")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(dispatch_ai_service, "_fetch_unassigned_orders", _fake_fetch_unassigned_orders)
    monkeypatch.setattr(dispatch_ai_service, "get_gemini_client", _raise_gemini_config)
    try:
        suggestions = await dispatch_ai_service.get_return_trip_suggestions(_FakeDb())
    finally:
        monkeypatch.undo()

    assert len(suggestions) == 1
    assert suggestions[0]["driver_id"] == str(free_driver_id)
    assert suggestions[0]["pending_tracking_code"] == "PENDING-1"
    assert suggestions[0]["ai_powered"] is False
    assert "non-packing order DONE-1" in suggestions[0]["reason"]


@pytest.mark.asyncio
async def test_return_trip_suggestions_allow_profile_location_when_delivery_coords_missing() -> None:
    now = datetime.now(UTC)
    free_driver_id = uuid4()

    pending_order = SimpleNamespace(
        id=uuid4(),
        tracking_code="PENDING-2",
        pickup_addr="Pickup B",
        delivery_addr="Drop B",
        pickup_lat=12.9700,
        pickup_lng=77.5900,
        priority="HIGH",
    )
    recent_delivery = SimpleNamespace(
        id=uuid4(),
        tracking_code="DONE-NO-GPS",
        delivery_addr="Last Drop Missing GPS",
        delivery_lat=None,
        delivery_lng=None,
        delivered_at=now - timedelta(minutes=15),
        packing_amount=0.0,
    )

    class _FakeScalarResult:
        def __init__(self, values):
            self._values = values

        def all(self):
            return self._values

    class _FakeResult:
        def __init__(self, values):
            self._values = values

        def all(self):
            return self._values

        def scalars(self):
            return _FakeScalarResult(self._values)

    class _FakeDb:
        def __init__(self):
            self._calls = 0

        async def execute(self, query):
            self._calls += 1
            if self._calls == 1:
                return _FakeResult([])
            if self._calls == 2:
                return _FakeResult([
                    (
                        recent_delivery,
                        SimpleNamespace(id=free_driver_id, name="Fallback Driver"),
                        SimpleNamespace(current_location="12.9705,77.5905"),
                    ),
                ])
            raise AssertionError("Unexpected DB execute call")

    async def _fake_fetch_unassigned_orders(db, limit=40):
        return [pending_order]

    def _raise_gemini_config():
        raise dispatch_ai_service.GeminiConfigError("missing key")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(dispatch_ai_service, "_fetch_unassigned_orders", _fake_fetch_unassigned_orders)
    monkeypatch.setattr(dispatch_ai_service, "get_gemini_client", _raise_gemini_config)
    try:
        suggestions = await dispatch_ai_service.get_return_trip_suggestions(_FakeDb())
    finally:
        monkeypatch.undo()

    assert len(suggestions) == 1
    assert suggestions[0]["driver_id"] == str(free_driver_id)
    assert suggestions[0]["pending_tracking_code"] == "PENDING-2"
    assert "DONE-NO-GPS" in suggestions[0]["reason"]


@pytest.mark.asyncio
async def test_return_trip_suggestions_exclude_driver_if_latest_completed_job_used_packing() -> None:
    now = datetime.now(UTC)
    driver_id = uuid4()

    pending_order = SimpleNamespace(
        id=uuid4(),
        tracking_code="PENDING-3",
        pickup_addr="Pickup C",
        delivery_addr="Drop C",
        pickup_lat=12.9700,
        pickup_lng=77.5900,
        priority="NORMAL",
    )
    latest_packing_delivery = SimpleNamespace(
        id=uuid4(),
        tracking_code="DONE-PACKING",
        delivery_addr="Packed Drop",
        delivery_lat=12.9710,
        delivery_lng=77.5910,
        delivered_at=now - timedelta(minutes=10),
        packing_amount=250.0,
    )
    older_non_packing_delivery = SimpleNamespace(
        id=uuid4(),
        tracking_code="DONE-NONPACK",
        delivery_addr="Older Drop",
        delivery_lat=12.9715,
        delivery_lng=77.5915,
        delivered_at=now - timedelta(minutes=25),
        packing_amount=0.0,
    )

    class _FakeScalarResult:
        def __init__(self, values):
            self._values = values

        def all(self):
            return self._values

    class _FakeResult:
        def __init__(self, values):
            self._values = values

        def all(self):
            return self._values

        def scalars(self):
            return _FakeScalarResult(self._values)

    class _FakeDb:
        def __init__(self):
            self._calls = 0

        async def execute(self, query):
            self._calls += 1
            if self._calls == 1:
                return _FakeResult([])
            if self._calls == 2:
                return _FakeResult([
                    (
                        latest_packing_delivery,
                        SimpleNamespace(id=driver_id, name="Packing Driver"),
                        SimpleNamespace(current_location="12.9705,77.5905"),
                    ),
                    (
                        older_non_packing_delivery,
                        SimpleNamespace(id=driver_id, name="Packing Driver"),
                        SimpleNamespace(current_location="12.9705,77.5905"),
                    ),
                ])
            raise AssertionError("Unexpected DB execute call")

    async def _fake_fetch_unassigned_orders(db, limit=40):
        return [pending_order]

    def _raise_gemini_config():
        raise dispatch_ai_service.GeminiConfigError("missing key")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(dispatch_ai_service, "_fetch_unassigned_orders", _fake_fetch_unassigned_orders)
    monkeypatch.setattr(dispatch_ai_service, "get_gemini_client", _raise_gemini_config)
    try:
        suggestions = await dispatch_ai_service.get_return_trip_suggestions(_FakeDb())
    finally:
        monkeypatch.undo()

    assert suggestions == []
