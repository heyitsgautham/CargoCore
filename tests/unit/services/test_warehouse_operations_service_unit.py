from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services import warehouse_operations_service as warehouse_ops


def _order(**overrides) -> SimpleNamespace:
    base = {
        "id": uuid4(),
        "tracking_code": "QC-TEST12345",
        "cargo_type": "General Cargo",
        "delivery_notes": "",
        "warehouse_substatus": "AWAITING_INBOUND",
        "arrived_at": None,
        "scheduled_at": datetime.now(timezone.utc) + timedelta(hours=3),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _ticket(
    *,
    notes: str,
    status_name: str = "open",
    reference_code: str = "SUP-123",
) -> SimpleNamespace:
    return SimpleNamespace(
        notes=notes,
        status=status_name,
        reference_code=reference_code,
    )


def test_validate_substatus_transition_rejects_unknown_target() -> None:
    with pytest.raises(HTTPException) as exc_info:
        warehouse_ops._validate_substatus_transition("AWAITING_PICK", "INVALID")

    assert exc_info.value.status_code == 400
    assert "invalid warehouse substatus" in str(exc_info.value.detail).lower()


@pytest.mark.parametrize("target", ["AWAITING_INBOUND", "AWAITING_PICK", "ON_HOLD"])
def test_validate_substatus_transition_allows_initial_statuses(target: str) -> None:
    warehouse_ops._validate_substatus_transition(None, target)


def test_validate_substatus_transition_rejects_invalid_initial_status() -> None:
    with pytest.raises(HTTPException) as exc_info:
        warehouse_ops._validate_substatus_transition(None, "PICKING")

    assert exc_info.value.status_code == 400
    assert "initial substatus" in str(exc_info.value.detail).lower()


def test_validate_substatus_transition_allows_declared_path() -> None:
    warehouse_ops._validate_substatus_transition("AWAITING_PICK", "PICKING")


def test_validate_substatus_transition_rejects_disallowed_path() -> None:
    with pytest.raises(HTTPException) as exc_info:
        warehouse_ops._validate_substatus_transition("AWAITING_PICK", "PACKING")

    assert exc_info.value.status_code == 400
    assert "cannot transition" in str(exc_info.value.detail).lower()


def test_to_quality_check_response_maps_performer_name() -> None:
    qc = SimpleNamespace(
        id=uuid4(),
        order_id=uuid4(),
        warehouse_id=uuid4(),
        goods_correct=True,
        count_correct=True,
        packaging_verified=True,
        labor_assigned=False,
        weight_verified=True,
        label_attached=True,
        is_passed=True,
        notes="Checked",
        performed_by=uuid4(),
        performer=SimpleNamespace(name="QC User"),
        checked_at=datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc),
        created_at=datetime(2026, 4, 17, 8, 0, tzinfo=timezone.utc),
    )

    response = warehouse_ops._to_quality_check_response(qc)

    assert response.performer_name == "QC User"
    assert response.is_passed is True


def test_format_user_name_helper() -> None:
    assert warehouse_ops._format_user_name(None) is None
    assert warehouse_ops._format_user_name(SimpleNamespace(name="Worker One")) == "Worker One"


def test_inbound_tracking_and_report_reference_format() -> None:
    tracking = warehouse_ops._inbound_tracking_code()
    reference = warehouse_ops._inbound_report_reference("MISMATCH")

    assert tracking.startswith("QC-")
    assert len(tracking) == 13
    assert reference.startswith("MISMATCH-")
    assert len(reference.split("-", 1)[1]) == 6


def test_parse_ticket_notes_metadata_extracts_meta_lines() -> None:
    notes = "\n".join(
        [
            "plain line",
            "[meta:source=warehouse_inbound]",
            "[meta:issue_type=mismatch]",
            "[meta:linked_order_id=abc]",
        ]
    )

    metadata = warehouse_ops._parse_ticket_notes_metadata(notes)

    assert metadata == {
        "source": "warehouse_inbound",
        "issue_type": "mismatch",
        "linked_order_id": "abc",
    }


def test_linked_issue_type_and_resolution_action_with_backward_compatibility() -> None:
    ticket = _ticket(
        notes="\n".join(
            [
                "[meta:issue_type=damage]",
                "[meta:resolution_action=pending_review]",
            ]
        ),
        status_name="resolved",
    )

    assert warehouse_ops._linked_issue_type(ticket) == "damage"
    assert warehouse_ops._linked_resolution_action(ticket) == "vendor_accept_move"


def test_ticket_reference_code_helper() -> None:
    ticket = _ticket(notes="[meta:source=warehouse_inbound]", reference_code="SUP-999")

    assert warehouse_ops._ticket_reference_code(ticket) == "SUP-999"
    assert warehouse_ops._ticket_reference_code(None) is None


def test_is_inbound_issue_ticket_requires_source_order_and_issue_type() -> None:
    order_id = uuid4()
    valid_ticket = _ticket(
        notes="\n".join(
            [
                "[meta:source=warehouse_inbound]",
                f"[meta:linked_order_id={order_id}]",
                "[meta:issue_type=mismatch]",
            ]
        )
    )
    invalid_ticket = _ticket(
        notes="\n".join(
            [
                "[meta:source=warehouse_inbound]",
                f"[meta:linked_order_id={order_id}]",
                "[meta:issue_type=other]",
            ]
        )
    )

    assert warehouse_ops._is_inbound_issue_ticket(valid_ticket, order_id) is True
    assert warehouse_ops._is_inbound_issue_ticket(invalid_ticket, order_id) is False


def test_inbound_status_variants() -> None:
    completed = _order(warehouse_substatus="PICKING")
    on_hold = _order(warehouse_substatus="ON_HOLD")
    arrived = _order(warehouse_substatus="AWAITING_INBOUND", arrived_at=datetime.now(timezone.utc))
    in_transit = _order(
        warehouse_substatus="AWAITING_INBOUND",
        arrived_at=None,
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    scheduled = _order(
        warehouse_substatus="AWAITING_INBOUND",
        arrived_at=None,
        scheduled_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    none_case = _order(warehouse_substatus=None)

    assert warehouse_ops._inbound_status(completed) == "Completed"
    assert warehouse_ops._inbound_status(on_hold) == "OnHold"
    assert warehouse_ops._inbound_status(arrived) == "Arrived"
    assert warehouse_ops._inbound_status(in_transit) == "InTransit"
    assert warehouse_ops._inbound_status(scheduled) == "Scheduled"
    assert warehouse_ops._inbound_status(none_case) is None


def test_dock_status_for_shipment_mapping() -> None:
    assert warehouse_ops._dock_status_for_shipment("Completed") == "Completed"
    assert warehouse_ops._dock_status_for_shipment("Arrived") == "Active"
    assert warehouse_ops._dock_status_for_shipment("Receiving") == "Active"
    assert warehouse_ops._dock_status_for_shipment("Scheduled") == "Scheduled"


def test_recurring_inbound_detection() -> None:
    recurring = _order(delivery_notes="RECURRING_RULE:abc|RUN:2026-04-17")
    adhoc = _order(delivery_notes="normal note")

    assert warehouse_ops._is_recurring_inbound(recurring) is True
    assert warehouse_ops._is_recurring_inbound(adhoc) is False


def test_strip_json_fences_for_markdown_wrapped_payload() -> None:
    wrapped = "```json\n{\"dock\":\"Dock 2\"}\n```"
    plain = "{\"dock\":\"Dock 2\"}"

    assert warehouse_ops._strip_json_fences(wrapped) == plain
    assert warehouse_ops._strip_json_fences(plain) == plain


def test_material_profile_for_inbound_scales_by_volume_and_boxes() -> None:
    high = warehouse_ops._material_profile_for_inbound(
        order=_order(cargo_type="Electronics"),
        expected_qty=140,
        box_count=30,
        estimated_volume=280.0,
    )
    medium = warehouse_ops._material_profile_for_inbound(
        order=_order(cargo_type="Cosmetics"),
        expected_qty=70,
        box_count=5,
        estimated_volume=140.0,
    )
    light = warehouse_ops._material_profile_for_inbound(
        order=_order(cargo_type="Documents"),
        expected_qty=12,
        box_count=1,
        estimated_volume=15.0,
    )

    assert "High-volume bulk unload" in high
    assert "palletized" in high
    assert "Medium dock unload" in medium
    assert "mixed loose + boxed" in medium
    assert "Light inbound unload" in light


def test_heuristic_inbound_receive_plan_high_risk_recurring_path() -> None:
    order = _order(delivery_notes="RECURRING_RULE:abc|RUN:2026-04-17")

    plan = warehouse_ops._heuristic_inbound_receive_plan(
        order=order,
        supplier_name="Acme Supplies",
        status_name="InTransit",
        expected_qty=130,
        box_count=18,
        estimated_volume=260.0,
        has_mismatch=True,
        has_damage=True,
        dock_names=["Dock 9"],
        active_dock_count=3,
    )

    assert plan.generated_by == "fallback"
    assert plan.asn.recurring is True
    assert plan.suggested_dock == "Dock 9"
    assert plan.workers == 5
    assert plan.risk_level == "High"
    assert plan.confidence >= 68
    assert "Acme Supplies" in plan.summary
    assert any("Mismatch follow-up needed" in item for item in plan.watchouts)


def test_heuristic_inbound_receive_plan_default_dock_selection() -> None:
    plan = warehouse_ops._heuristic_inbound_receive_plan(
        order=_order(delivery_notes=""),
        supplier_name="Vendor X",
        status_name="Scheduled",
        expected_qty=95,
        box_count=8,
        estimated_volume=80.0,
        has_mismatch=False,
        has_damage=False,
        dock_names=[],
        active_dock_count=0,
    )

    assert plan.suggested_dock == "Dock 2"
    assert plan.asn.recurring is False
    assert plan.generated_by == "fallback"
