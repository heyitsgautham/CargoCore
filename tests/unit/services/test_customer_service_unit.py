from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services import customer_service


def _make_order(**overrides):
    base = {
        "id": uuid4(),
        "tracking_code": "QC-1234000099",
        "order_type": "INDIVIDUAL",
        "status": "ASSIGNED",
        "warehouse_substatus": "AWAITING_PICK",
        "pickup_addr": "Pickup A",
        "delivery_addr": "Drop B",
        "scheduled_at": datetime(2026, 4, 18, 9, 30, tzinfo=timezone.utc),
        "created_at": datetime(2026, 4, 17, 8, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 4, 17, 10, 0, tzinfo=timezone.utc),
        "delivered_at": None,
        "vehicle_type": "mini-truck",
        "cargo_type": None,
        "service_otp": None,
        "service_time_block": None,
        "labor_count": 2,
        "base_amount": 100.0,
        "vehicle_amount": 50.0,
        "labor_amount": 25.0,
        "materials_amount": 10.0,
        "packing_amount": 5.0,
        "platform_fee": 3.0,
        "tax_amount": 7.0,
        "total_amount": 200.0,
        "assigned_driver_id": uuid4(),
        "payment_status": "pending",
        "cancel_reason": None,
        "picking_started_at": datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc),
        "picking_completed_at": datetime(2026, 4, 17, 9, 20, tzinfo=timezone.utc),
        "packing_started_at": datetime(2026, 4, 17, 9, 30, tzinfo=timezone.utc),
        "packing_completed_at": datetime(2026, 4, 17, 9, 45, tzinfo=timezone.utc),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_ui_status_maps_known_values() -> None:
    assert customer_service._ui_status("ASSIGNED") == "dispatched"
    assert customer_service._ui_status("IN_TRANSIT") == "in-transit"


def test_ui_status_falls_back_for_unknown_values() -> None:
    assert customer_service._ui_status("SOMETHING_NEW") == "something_new"


def test_cargo_type_prefers_order_value() -> None:
    order = _make_order(cargo_type="Electronics")
    assert customer_service._cargo_type(order) == "Electronics"


def test_cargo_type_falls_back_by_order_type() -> None:
    assert customer_service._cargo_type(_make_order(order_type="INDIVIDUAL", cargo_type=None)) == "Household Goods"
    assert customer_service._cargo_type(_make_order(order_type="VENDOR", cargo_type=None)) == "Shipment"


def test_service_otp_prefers_existing_value() -> None:
    assert customer_service._service_otp(_make_order(service_otp="7531")) == "7531"


def test_service_otp_derives_from_tracking_code_digits() -> None:
    order = _make_order(service_otp=None, tracking_code="QC-AB12-7899")
    assert customer_service._service_otp(order) == "7899"


def test_service_time_block_uses_fallbacks() -> None:
    explicit = _make_order(service_time_block="09:00 AM - 11:00 AM")
    scheduled = _make_order(service_time_block=None, scheduled_at=datetime(2026, 4, 18, 14, 15, tzinfo=timezone.utc))
    missing = _make_order(service_time_block=None, scheduled_at=None)

    assert customer_service._service_time_block(explicit) == "09:00 AM - 11:00 AM"
    assert customer_service._service_time_block(scheduled) == "02:15 PM"
    assert customer_service._service_time_block(missing) == "TBD"


def test_progress_for_status_uses_ui_mapping() -> None:
    assert customer_service._progress_for_status("ASSIGNED") == 40
    assert customer_service._progress_for_status("DELIVERED") == 100
    assert customer_service._progress_for_status("UNKNOWN") == 0


def test_eta_label_for_delivered_and_cancelled_orders() -> None:
    delivered = _make_order(
        status="DELIVERED",
        delivered_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
    )
    cancelled = _make_order(status="CANCELLED")

    assert customer_service._eta_label(delivered).startswith("Delivered")
    assert customer_service._eta_label(cancelled) == "Cancelled"


def test_fmt_handles_none_and_datetime() -> None:
    assert customer_service._fmt(None) == ""
    rendered = customer_service._fmt(datetime(2026, 4, 17, 8, 45, tzinfo=timezone.utc))
    assert "17 Apr 2026" in rendered


def test_tracking_log_includes_created_and_cancelled_events() -> None:
    order = _make_order(status="CANCELLED", warehouse_substatus="ON_HOLD", cancel_reason="Customer requested")

    log = customer_service._tracking_log(order)

    assert log[0]["event"] == "Order created"
    assert any(entry["event"] == "Order cancelled" for entry in log)
    cancelled = [entry for entry in log if entry["event"] == "Order cancelled"][0]
    assert cancelled["description"] == "Customer requested"


def test_to_dashboard_order_maps_core_fields() -> None:
    order = _make_order(status="IN_TRANSIT")

    model = customer_service._to_dashboard_order(order)

    assert model.tracking_code == "QC-1234000099"
    assert model.ui_status == "in-transit"
    assert model.vehicle_type == "mini-truck"


def test_to_active_move_includes_driver_and_cost() -> None:
    order = _make_order()
    lookup = {
        order.assigned_driver_id: {
            "name": "Driver One",
            "phone": "9999990000",
            "rating": 4.9,
        }
    }

    model = customer_service._to_active_move(order, driver_lookup=lookup)

    assert model.driver is not None
    assert model.driver.name == "Driver One"
    assert model.cost.total == 200.0
    assert model.progress == 40


def test_to_user_profile_maps_role_and_status() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        name="Customer User",
        username="customer.user",
        email="customer@example.com",
        phone="9999988888",
        address="Address",
        role=SimpleNamespace(name="INDIVIDUAL"),
        is_active=True,
        created_at=datetime(2026, 4, 17, 7, 0, tzinfo=timezone.utc),
    )

    profile = customer_service._to_user_profile(user)

    assert profile.role == "INDIVIDUAL"
    assert profile.is_active is True
