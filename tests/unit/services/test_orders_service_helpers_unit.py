from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import orders_service


def _order(status: str, total_amount: float) -> SimpleNamespace:
    return SimpleNamespace(status=status, total_amount=total_amount)


def test_mask_email_masks_local_part() -> None:
    assert orders_service._mask_email("logistics.team@example.com") == "lo***@example.com"


def test_mask_email_returns_input_without_domain() -> None:
    assert orders_service._mask_email("invalid-email") == "invalid-email"


def test_normalize_data_url_returns_none_for_empty_payload() -> None:
    assert orders_service._normalize_data_url(None, "image/png") is None
    assert orders_service._normalize_data_url("", "image/png") is None


def test_normalize_data_url_preserves_existing_data_url() -> None:
    payload = "data:image/png;base64,ABC123"
    assert orders_service._normalize_data_url(payload, "image/png") == payload


def test_normalize_data_url_wraps_base64_payload() -> None:
    assert (
        orders_service._normalize_data_url("ABC123", "image/png")
        == "data:image/png;base64,ABC123"
    )


def test_validate_transition_allows_supported_transition() -> None:
    orders_service._validate_transition("DRAFT", "CONFIRMED")


def test_validate_transition_rejects_unsupported_transition() -> None:
    with pytest.raises(HTTPException) as exc_info:
        orders_service._validate_transition("CONFIRMED", "DELIVERED")

    assert exc_info.value.status_code == 409
    assert "invalid transition" in str(exc_info.value.detail).lower()


def test_cancellation_terms_for_assigned_order_is_five_percent() -> None:
    fee, label = orders_service._cancellation_terms(_order("ASSIGNED", 1000.0))

    assert fee == 50.0
    assert "5%" in label


def test_cancellation_terms_for_in_transit_order_is_twenty_five_percent() -> None:
    fee, label = orders_service._cancellation_terms(_order("IN_TRANSIT", 1000.0))

    assert fee == 250.0
    assert "25%" in label


def test_parse_driver_location_parses_valid_coordinates() -> None:
    lat, lng = orders_service._parse_driver_location("19.0760, 72.8777")

    assert lat == pytest.approx(19.0760)
    assert lng == pytest.approx(72.8777)


@pytest.mark.parametrize(
    "location",
    [None, "", "nonsense", "12.9", "12.9,abc"],
)
def test_parse_driver_location_returns_none_for_invalid_input(
    location: str | None,
) -> None:
    assert orders_service._parse_driver_location(location) == (None, None)


def test_clamp_respects_min_and_max() -> None:
    assert orders_service._clamp(-1, 0, 10) == 0
    assert orders_service._clamp(5, 0, 10) == 5
    assert orders_service._clamp(11, 0, 10) == 10


def test_eta_label_from_minutes_uses_reference_time() -> None:
    reference = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    label = orders_service._eta_label_from_minutes(75, reference_time=reference)

    assert label == "11:15 AM"


def test_build_route_signal_shape() -> None:
    signal = orders_service._build_route_signal("traffic", "Peak-hour traffic", "medium")

    assert signal == {
        "key": "traffic",
        "label": "Peak-hour traffic",
        "severity": "medium",
    }


@pytest.mark.parametrize(
    ("has_pickup_coords", "has_delivery_coords", "has_live_driver_location", "order_status", "expected"),
    [
        (True, True, True, "IN_TRANSIT", "High"),
        (True, True, False, "ASSIGNED", "High"),
        (False, True, False, "ASSIGNED", "Medium"),
        (False, False, False, "ASSIGNED", "Low"),
    ],
)
def test_derive_eta_confidence_branches(
    has_pickup_coords: bool,
    has_delivery_coords: bool,
    has_live_driver_location: bool,
    order_status: str,
    expected: str,
) -> None:
    confidence = orders_service._derive_eta_confidence(
        has_pickup_coords=has_pickup_coords,
        has_delivery_coords=has_delivery_coords,
        has_live_driver_location=has_live_driver_location,
        order_status=order_status,
    )

    assert confidence == expected


def test_recommended_dispatch_action_for_no_go_zone() -> None:
    dispatch_action, driver_action = orders_service._recommended_dispatch_action(
        no_go_zone_hit=True,
        route_status="On Time",
        risk_level="LOW",
        order_status="ASSIGNED",
        priority="NORMAL",
        minutes_saved=0,
    )

    assert "restricted" in dispatch_action.lower()
    assert "updated navigation" in driver_action.lower()


def test_recommended_dispatch_action_for_delayed_route() -> None:
    dispatch_action, driver_action = orders_service._recommended_dispatch_action(
        no_go_zone_hit=False,
        route_status="Delayed",
        risk_level="LOW",
        order_status="ASSIGNED",
        priority="NORMAL",
        minutes_saved=0,
    )

    assert "eta" in dispatch_action.lower()
    assert "running behind" in driver_action.lower()


def test_recommended_dispatch_action_for_high_risk_with_recovery() -> None:
    dispatch_action, driver_action = orders_service._recommended_dispatch_action(
        no_go_zone_hit=False,
        route_status="On Time",
        risk_level="HIGH",
        order_status="ASSIGNED",
        priority="NORMAL",
        minutes_saved=8,
    )

    assert "8 minutes" in dispatch_action
    assert "alternate route" in driver_action.lower()


def test_recommended_dispatch_action_for_urgent_assigned_order() -> None:
    dispatch_action, driver_action = orders_service._recommended_dispatch_action(
        no_go_zone_hit=False,
        route_status="On Time",
        risk_level="LOW",
        order_status="ASSIGNED",
        priority="URGENT",
        minutes_saved=1,
    )

    assert "time-sensitive" in driver_action.lower()
    assert "tight operating window" in dispatch_action.lower()


def test_recommended_dispatch_action_default_on_plan() -> None:
    dispatch_action, driver_action = orders_service._recommended_dispatch_action(
        no_go_zone_hit=False,
        route_status="On Time",
        risk_level="LOW",
        order_status="IN_TRANSIT",
        priority="NORMAL",
        minutes_saved=1,
    )

    assert "on plan" in dispatch_action.lower()
    assert "on track" in driver_action.lower()
