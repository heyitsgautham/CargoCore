from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from urllib.parse import unquote_plus
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.logistics import formatting as logistics_formatting
from app.services.logistics import meetings as logistics_meetings
from app.services.logistics import operations as logistics_operations


def _make_order(**overrides) -> SimpleNamespace:
    base = {
        "status": "CONFIRMED",
        "order_type": "VENDOR",
        "cargo_type": "Parcel",
        "vehicle_type": "Van",
        "service_time_block": None,
        "delivery_lat": None,
        "delivery_lng": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_fmt_relative_variants() -> None:
    now = logistics_formatting._now()
    assert logistics_formatting._fmt_relative(now) == "Just now"
    assert logistics_formatting._fmt_relative(now - timedelta(minutes=5)) == "5m ago"
    assert logistics_formatting._fmt_relative(now - timedelta(hours=2)) == "2h ago"


def test_status_badge_class_rules() -> None:
    assert logistics_formatting._status_badge_class("Overdue") == "bg-red-500/10 text-red-500"
    assert logistics_formatting._status_badge_class("Scheduled") == "bg-yellow-500/10 text-yellow-500"
    assert logistics_formatting._status_badge_class("Delivered") == "bg-green-500/10 text-green-500"


def test_title_case_status_and_driver_codes() -> None:
    user = SimpleNamespace(id=uuid4())
    title = logistics_formatting._title_case_status("in_transit")
    code = logistics_formatting._driver_code(user)
    shift = logistics_formatting._shift_code(user, started_at=datetime(2026, 4, 17, 9, 0, tzinfo=UTC))

    assert title == "In Transit"
    assert code.startswith("DRV-")
    assert shift.startswith("SHIFT-0417-")


def test_time_and_date_format_helpers() -> None:
    dt = datetime(2026, 4, 17, 9, 5, tzinfo=UTC)

    assert logistics_formatting._coerce_utc(None) is None
    assert logistics_formatting._format_duration_label(125) == "2h 05m"
    assert logistics_formatting._format_time_label(dt) == "09:05 AM"
    assert "Apr 17 2026" in logistics_formatting._format_date_label(dt)


def test_avatar_url_contains_encoded_name() -> None:
    url = logistics_formatting._avatar_url("Driver One")
    assert "ui-avatars.com" in url
    assert unquote_plus(url).find("Driver One") != -1


def test_order_job_type_and_status_helpers() -> None:
    house_shift = _make_order(order_type="INDIVIDUAL", cargo_type="House Move", vehicle_type="Truck")
    pickup = _make_order(order_type="VENDOR", cargo_type="Pickup")
    delivery = _make_order(order_type="VENDOR", cargo_type="Docs")

    assert logistics_formatting._order_job_type(house_shift) == "HOUSE_SHIFT"
    assert logistics_formatting._order_job_type(pickup) == "PARCEL_PICKUP"
    assert logistics_formatting._order_job_type(delivery) == "PARCEL_DELIVERY"

    assert logistics_formatting._is_terminal_order(_make_order(status="CLOSED")) is True
    assert logistics_formatting._is_completed_order(_make_order(status="DELIVERED")) is True
    assert logistics_formatting._is_active_order(_make_order(status="ASSIGNED")) is True


def test_vehicle_defaults_and_metrics() -> None:
    heavy = logistics_formatting._vehicle_defaults("Heavy Truck")
    van = logistics_formatting._vehicle_defaults("Cargo Van")
    bike = logistics_formatting._vehicle_defaults("Bike")

    assert heavy == (3.5, 3, 460)
    assert van == (1.5, 2, 340)
    assert bike == (1.0, 2, 280)

    vehicle = SimpleNamespace(
        vehicle_type="Cargo Van",
        mileage=143,
        assigned_driver_id=uuid4(),
    )
    metrics = logistics_formatting._vehicle_metrics(vehicle)

    assert metrics["telemetry_status"] == "LIVE"
    assert metrics["range_km"] > 0
    assert 18 <= metrics["fuel_level_pct"] <= 100


def test_profile_coords_and_haversine_distance() -> None:
    profile = SimpleNamespace(current_location="19.0760,72.8777")
    bad_profile = SimpleNamespace(current_location="invalid")

    lat, lng = logistics_formatting._parse_profile_coords(profile)
    assert lat == pytest.approx(19.0760)
    assert lng == pytest.approx(72.8777)
    assert logistics_formatting._parse_profile_coords(bad_profile) == (None, None)

    distance = logistics_formatting._haversine_km(19.0760, 72.8777, 19.2183, 72.9781)
    assert distance > 0


def test_manifest_distance_estimation_with_and_without_coordinates() -> None:
    warehouse = SimpleNamespace(lat=19.10, lng=72.90)
    orders_with_coords = [
        _make_order(delivery_lat=19.20, delivery_lng=72.95),
        _make_order(delivery_lat=19.30, delivery_lng=73.00),
    ]
    orders_without_coords = [_make_order(), _make_order()]

    with_coords = logistics_formatting._estimate_manifest_distance_km(warehouse, orders_with_coords)
    fallback = logistics_formatting._estimate_manifest_distance_km(None, orders_without_coords)

    assert with_coords > 0
    assert fallback == 17.0


def test_notification_visibility_helpers() -> None:
    user = SimpleNamespace(id=uuid4(), role=SimpleNamespace(name="DISPATCHER"))
    by_role = SimpleNamespace(audience_roles="DISPATCHER,LOGISTIC_MANAGER", target_user_id=None)
    all_roles = SimpleNamespace(audience_roles="", target_user_id=None)
    direct = SimpleNamespace(audience_roles="", target_user_id=user.id)

    assert logistics_formatting._notification_role_set(by_role) == {"DISPATCHER", "LOGISTIC_MANAGER"}
    assert logistics_formatting._notification_visible_to_user(by_role, user) is True
    assert logistics_formatting._notification_visible_to_user(all_roles, user) is True
    assert logistics_formatting._notification_visible_to_user(direct, user) is True
    assert logistics_formatting._notification_visible_to_role(direct, "DISPATCHER") is False


def test_duration_and_crew_role_helpers() -> None:
    assert logistics_formatting._estimate_duration_minutes(5.0, 2) >= 45

    labourer_with_skill = SimpleNamespace(skill_tags=["heavy_lift"], user=SimpleNamespace(role=SimpleNamespace(name="LABOURER")))
    labourer_with_role = SimpleNamespace(skill_tags=[], user=SimpleNamespace(role=SimpleNamespace(name="SUPERVISOR")))
    labourer_generic = SimpleNamespace(skill_tags=[], user=SimpleNamespace(role=SimpleNamespace(name="LABOURER")))

    assert logistics_formatting._crew_role(labourer_with_skill) == "Heavy Lift"
    assert logistics_formatting._crew_role(labourer_with_role) == "Supervisor"
    assert logistics_formatting._crew_role(labourer_generic) == "Crew"


def test_latest_attendance_event_and_crew_item() -> None:
    now = datetime.now(UTC)
    check_in = SimpleNamespace(event_type="CHECK_IN", created_at=now - timedelta(minutes=15))
    check_out = SimpleNamespace(event_type="CHECK_OUT", created_at=now - timedelta(minutes=5))

    labourer = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        user=SimpleNamespace(name="Crew Member", phone="9999992222", role=SimpleNamespace(name="LABOURER")),
        skill_tags=[],
        attendance_events=[check_in, check_out],
    )

    latest = logistics_formatting._latest_attendance_event(labourer)
    item = logistics_formatting._to_crew_item(labourer)

    assert latest is check_out
    assert item.status == "ASSIGNED"
    assert item.checked_in is False


def test_meeting_helpers_and_validation() -> None:
    assert logistics_meetings._normalize_meeting_type("zoom") == "zoom"
    assert logistics_meetings._normalize_meeting_type("teams") == "other"
    assert logistics_meetings._normalize_meeting_link("meet.google.com/abc-defg-hij") == "https://meet.google.com/abc-defg-hij"
    assert logistics_meetings._normalize_meeting_link("https://example.com/meeting") == "https://example.com/meeting"

    logistics_meetings._validate_meeting_time_range("09:00", "09:30")

    with pytest.raises(HTTPException) as bad_format:
        logistics_meetings._validate_meeting_time_range("9:00", "09:30")
    assert bad_format.value.status_code == 400

    with pytest.raises(HTTPException) as bad_range:
        logistics_meetings._validate_meeting_time_range("10:00", "09:30")
    assert bad_range.value.status_code == 400


def test_task_to_item_maps_repeat_field() -> None:
    task = SimpleNamespace(
        id=uuid4(),
        text="Call driver",
        status="pending",
        target_time=datetime(2026, 4, 17, 13, 0, tzinfo=UTC),
        repeat_rule="daily",
        created_at=datetime(2026, 4, 17, 10, 0, tzinfo=UTC),
        last_alert_time=None,
        silenced=False,
    )

    item = logistics_operations._task_to_item(task)

    assert item.text == "Call driver"
    assert item.repeat == "daily"
