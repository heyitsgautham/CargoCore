from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services import vendor_service


def _make_user(*, role_name: str = "VENDOR") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        name="Vendor User",
        username="vendor.user",
        email="vendor@example.com",
        phone="9999991111",
        address="Vendor Address",
        role=SimpleNamespace(name=role_name),
        warehouse_id=None,
        is_active=True,
        approval_status="APPROVED",
        company_name="Vendor Co",
        tax_id="GST-01",
        contact_person="Vendor Contact",
        business_email="ops@vendor.example.com",
        business_phone="8888877777",
        created_at=datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc),
    )


def _make_order(**overrides) -> SimpleNamespace:
    base = {
        "id": uuid4(),
        "tracking_code": "QC-ABC1234567",
        "status": "CONFIRMED",
        "warehouse_substatus": None,
        "pickup_addr": "Vendor Hub",
        "delivery_addr": "Client Site",
        "assigned_driver_id": None,
        "assigned_vehicle_id": None,
        "cargo_type": "Widgets",
        "cargo_weight_kg": 12.5,
        "vehicle_type": "Mini Truck",
        "payment_mode": "invoice",
        "payment_status": "pending",
        "labor_count": 2,
        "total_amount": 1200.0,
        "scheduled_at": datetime(2026, 4, 20, 9, 0, tzinfo=timezone.utc),
        "created_at": datetime.now(timezone.utc) - timedelta(days=3),
        "base_amount": 700.0,
        "vehicle_amount": 250.0,
        "labor_amount": 120.0,
        "materials_amount": 50.0,
        "packing_amount": 40.0,
        "platform_fee": 20.0,
        "tax_amount": 20.0,
        "delivery_notes": None,
        "cancel_reason": None,
        "paid_amount": 0.0,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_ensure_vendor_rejects_non_vendor_user() -> None:
    with pytest.raises(HTTPException) as exc_info:
        vendor_service._ensure_vendor(_make_user(role_name="INDIVIDUAL"))

    assert exc_info.value.status_code == 403


def test_status_key_and_shipment_status_key_mappings() -> None:
    assert vendor_service._status_key("ASSIGNED") == "transit"
    assert vendor_service._shipment_status_key("CONFIRMED", "AWAITING_PICK") == "warehouse"
    assert vendor_service._shipment_status_key("IN_TRANSIT", None) == "transit"


def test_status_label_and_progress_values() -> None:
    assert vendor_service._status_label("warehouse") == "In Warehouse"
    assert vendor_service._status_label("custom_status") == "Custom Status"
    assert vendor_service._progress("warehouse") == 35
    assert vendor_service._progress("unknown") == 0


def test_eta_label_variants() -> None:
    delivered = _make_order(status="DELIVERED")
    cancelled = _make_order(status="CANCELLED")
    scheduled = _make_order(status="ASSIGNED", scheduled_at=datetime(2026, 4, 30, 11, 0, tzinfo=timezone.utc))

    assert vendor_service._eta_label(delivered) == "Delivered"
    assert vendor_service._eta_label(cancelled) == "Cancelled"
    assert "2026" in vendor_service._eta_label(scheduled)


def test_history_includes_cancelled_reason() -> None:
    order = _make_order(status="CANCELLED", cancel_reason="Customer stopped shipment")

    history = vendor_service._history(order)

    assert history[0].status == "Created"
    assert any("Cancelled: Customer stopped shipment" == item.status for item in history)


def test_parse_rule_details_handles_invalid_json() -> None:
    assert vendor_service._parse_rule_details("not-json") == {}
    assert vendor_service._parse_rule_details("[]") == {}
    assert vendor_service._parse_rule_details('{"hub":"A"}') == {"hub": "A"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (1, True),
        ("yes", True),
        ("enabled", True),
        ("false", False),
        (0, False),
    ],
)
def test_is_auto_debit_enabled_variants(value, expected: bool) -> None:
    assert vendor_service._is_auto_debit_enabled({"autoDebitEnabled": value}) is expected


def test_parse_rule_marker_valid_and_invalid() -> None:
    rule_id = uuid4()
    valid = f"RECURRING_RULE:{rule_id}|RUN:2026-04-20"

    parsed_rule_id, run_iso = vendor_service._parse_rule_marker(valid)
    assert parsed_rule_id == rule_id
    assert run_iso == "2026-04-20"

    assert vendor_service._parse_rule_marker("invalid") == (None, None)


def test_append_auto_debit_event_is_idempotent_for_same_marker() -> None:
    order = _make_order(delivery_notes="seed")

    vendor_service._append_auto_debit_event(
        order,
        run_iso="2026-04-20",
        event_type="SUCCESS",
        message="Debited",
    )
    first = order.delivery_notes
    vendor_service._append_auto_debit_event(
        order,
        run_iso="2026-04-20",
        event_type="SUCCESS",
        message="Debited",
    )

    assert order.delivery_notes == first
    assert order.delivery_notes.count("AUTODEBIT_EVENT|") == 1


def test_latest_auto_debit_note_formats_event_types() -> None:
    notes = "\n".join(
        [
            "AUTODEBIT_EVENT|RUN:2026-04-20|TYPE:SUCCESS|TS:2026-04-20T00:00:00|MSG:Debited from wallet",
            "AUTODEBIT_EVENT|RUN:2026-04-21|TYPE:DEBT|TS:2026-04-21T00:00:00|MSG:Wallet -50",
        ]
    )

    message = vendor_service._latest_auto_debit_note(notes)

    assert message == "Auto-debit processed with wallet debt: Wallet -50"


def test_safe_float_and_tracking_code() -> None:
    assert vendor_service._safe_float("12.5") == 12.5
    assert vendor_service._safe_float("abc") is None
    code = vendor_service._tracking_code()
    assert code.startswith("QC-")
    assert len(code) == 13


def test_next_run_for_frequency_rules() -> None:
    current = date(2026, 4, 17)  # Friday

    assert vendor_service._next_run_for_frequency(current, "daily") == date(2026, 4, 18)
    assert vendor_service._next_run_for_frequency(current, "bi-weekly") == date(2026, 5, 1)
    assert vendor_service._next_run_for_frequency(current, "1st of month") == date(2026, 5, 1)
    assert vendor_service._next_run_for_frequency(current, "15th of month") == date(2026, 5, 15)
    assert vendor_service._next_run_for_frequency(current, "every monday") == date(2026, 4, 20)
    assert vendor_service._next_run_for_frequency(current, "unknown") == date(2026, 4, 24)


def test_scheduled_datetime_parsing_and_fallback() -> None:
    dt = vendor_service._scheduled_datetime("2026-04-20", "14:45")
    assert dt is not None
    assert dt.hour == 14
    assert dt.minute == 45

    fallback = vendor_service._scheduled_datetime("2026-04-20", "bad")
    assert fallback is not None
    assert fallback.hour == 9
    assert fallback.minute == 0

    assert vendor_service._scheduled_datetime("not-a-date", "10:30") is None


def test_compact_route_truncates_long_values() -> None:
    route = "A" * 300
    compact = vendor_service._compact_route(route)

    assert len(compact) == 255
    assert compact.endswith("...")


def test_invoice_status_and_record_variants() -> None:
    now = datetime.now(timezone.utc)
    overdue = _make_order(created_at=now - timedelta(days=40), payment_status="pending", paid_amount=0.0)
    partial = _make_order(created_at=now - timedelta(days=5), payment_status="pending", paid_amount=100.0)
    paid = _make_order(created_at=now - timedelta(days=5), payment_status="paid", paid_amount=0.0, total_amount=900.0)

    assert vendor_service._invoice_status(overdue, now) == "Overdue"
    assert vendor_service._invoice_status(partial, now) == "Partial"
    assert vendor_service._invoice_status(paid, now) == "Paid"

    paid_record = vendor_service._invoice_record(paid, now)
    assert paid_record.status == "Paid"
    assert paid_record.paid == 900.0


def test_invoice_summary_computes_totals() -> None:
    now = datetime.now(timezone.utc)
    overdue = _make_order(created_at=now - timedelta(days=40), payment_status="pending", paid_amount=0.0, total_amount=1000.0)
    paid = _make_order(created_at=now - timedelta(days=2), payment_status="paid", paid_amount=0.0, total_amount=800.0)

    summary = vendor_service._invoice_summary([overdue, paid], credit_balance=125.5)

    assert summary.total_overdue == 1000.0
    assert summary.total_unpaid == 1
    assert summary.credit_balance == 125.5
    assert summary.total_paid_this_month >= 800.0


def test_shipment_includes_driver_cost_and_auto_debit_note() -> None:
    notes = "AUTODEBIT_EVENT|RUN:2026-04-20|TYPE:SUCCESS|TS:2026-04-20T00:00:00|MSG:Debited"
    order = _make_order(delivery_notes=notes, warehouse_substatus="PICKING")

    shipment = vendor_service._shipment(
        order,
        driver_name="Driver One",
        driver_phone="9999988888",
        vehicle_code="VH-01",
    )

    assert shipment.status_key == "warehouse"
    assert shipment.assigned_driver_name == "Driver One"
    assert shipment.cost.total == 1200.0
    assert shipment.auto_debit_note == "Auto-debit success: Debited"


def test_analytics_returns_success_and_on_time_metrics() -> None:
    now = datetime.now(timezone.utc)
    orders = [
        _make_order(status="DELIVERED", created_at=now - timedelta(days=10), scheduled_at=now - timedelta(days=8), total_amount=1000.0),
        _make_order(status="CANCELLED", created_at=now - timedelta(days=6), scheduled_at=now - timedelta(days=5), total_amount=600.0),
        _make_order(status="IN_TRANSIT", created_at=now - timedelta(days=2), scheduled_at=now + timedelta(days=1), total_amount=700.0),
    ]

    analytics = vendor_service._analytics(orders)

    assert analytics.success_rate == pytest.approx(66.7, rel=1e-3)
    assert analytics.on_time == pytest.approx(50.0, rel=1e-3)
    assert analytics.avg_order_value == pytest.approx(766.67, rel=1e-3)
    assert len(analytics.monthly) == 6
