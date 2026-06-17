from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services import ai_support_service


def test_normalize_analytics_range_defaults_and_accepts_valid_values() -> None:
    assert ai_support_service._normalize_analytics_range(None) == "7D"
    assert ai_support_service._normalize_analytics_range("24h") == "24H"
    assert ai_support_service._normalize_analytics_range("30D") == "30D"


def test_normalize_analytics_range_rejects_invalid_value() -> None:
    with pytest.raises(HTTPException) as exc_info:
        ai_support_service._normalize_analytics_range("365D")

    assert exc_info.value.status_code == 400
    assert "analytics range" in str(exc_info.value.detail).lower()


def test_analytics_bucket_starts_lengths_and_ordering() -> None:
    now = datetime(2026, 4, 17, 14, 42, tzinfo=timezone.utc)

    h24 = ai_support_service._analytics_bucket_starts("24H", now)
    d7 = ai_support_service._analytics_bucket_starts("7D", now)
    d30 = ai_support_service._analytics_bucket_starts("30D", now)
    d90 = ai_support_service._analytics_bucket_starts("90D", now)

    assert len(h24) == 24
    assert len(d7) == 7
    assert len(d30) == 30
    assert len(d90) == 13
    assert h24[0] < h24[-1]
    assert d7[0] < d7[-1]


def test_next_analytics_window_start_by_range() -> None:
    start = datetime(2026, 4, 17, 10, 0, tzinfo=timezone.utc)

    assert ai_support_service._next_analytics_window_start("24H", start) == start + timedelta(hours=1)
    assert ai_support_service._next_analytics_window_start("7D", start) == start + timedelta(days=1)
    assert ai_support_service._next_analytics_window_start("30D", start) == start + timedelta(days=1)
    assert ai_support_service._next_analytics_window_start("90D", start) == start + timedelta(weeks=1)


def test_analytics_label_by_range() -> None:
    bucket = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)

    assert ai_support_service._analytics_label("24H", bucket) == "09:00"
    assert len(ai_support_service._analytics_label("7D", bucket)) == 3
    assert "Apr" in ai_support_service._analytics_label("30D", bucket)


def test_bucket_for_datetime_normalization() -> None:
    value = datetime(2026, 4, 17, 15, 37, 22, tzinfo=timezone.utc)

    assert ai_support_service._bucket_for_datetime(value, "24H") == datetime(2026, 4, 17, 15, 0, tzinfo=timezone.utc)
    assert ai_support_service._bucket_for_datetime(value, "7D") == datetime(2026, 4, 17, 0, 0, tzinfo=timezone.utc)
    assert ai_support_service._bucket_for_datetime(value, "30D") == datetime(2026, 4, 17, 0, 0, tzinfo=timezone.utc)
    assert ai_support_service._bucket_for_datetime(value, "90D") == datetime(2026, 4, 13, 0, 0, tzinfo=timezone.utc)


def test_percent_delta_and_format_helpers() -> None:
    assert ai_support_service._percent_delta(10, 0) == 100.0
    assert ai_support_service._percent_delta(0, 0) == 0.0
    assert ai_support_service._percent_delta(120, 100) == 20.0

    assert ai_support_service._format_count(1530.1) == "1,530"
    assert ai_support_service._format_currency(999) == "\u20b9999"
    assert ai_support_service._format_currency(2500) == "\u20b92.5k"
    assert ai_support_service._format_duration_seconds(0) == "0s"
    assert ai_support_service._format_duration_seconds(22.2) == "22s"
    assert ai_support_service._format_duration_seconds(130) == "2m"


def test_trend_descriptor_positive_negative_and_inverse() -> None:
    msg, tone = ai_support_service._trend_descriptor(120, 100, "period", formatter=ai_support_service._format_count)
    assert "+20.0%" in msg
    assert tone == "positive"

    msg2, tone2 = ai_support_service._trend_descriptor(90, 100, "period", formatter=ai_support_service._format_count)
    assert "-10.0%" in msg2
    assert tone2 == "negative"

    msg3, tone3 = ai_support_service._trend_descriptor(40, 50, "period", formatter=ai_support_service._format_duration_seconds, inverse=True)
    assert tone3 == "positive"
    assert "-10s" in msg3


def test_escalation_reason_label_mapping() -> None:
    assert ai_support_service._escalation_reason_label("refund and payment issue") == "Refund Dispute"
    assert ai_support_service._escalation_reason_label("delivery delay and tracking") == "Late Delivery"
    assert ai_support_service._escalation_reason_label("item damaged") == "Damaged Item"
    assert ai_support_service._escalation_reason_label("driver was rude") == "Driver Conduct"
    assert ai_support_service._escalation_reason_label("random note") == "Other"


def test_analytics_marker_helpers() -> None:
    marker = ai_support_service._analytics_ticket_marker("clear_contact_backlog")

    assert marker == "[analytics:clear_contact_backlog]"
    assert ai_support_service._extract_analytics_ticket_marker("foo [analytics:clear_contact_backlog] bar") == "clear_contact_backlog"
    assert ai_support_service._extract_analytics_ticket_marker("no marker") is None


def test_build_analytics_insights_multi_signal_path() -> None:
    insights = ai_support_service._build_analytics_insights(
        top_reason_label="Refund Dispute",
        top_reason_pct=35,
        negative_sessions=8,
        total_sessions=20,
        open_contact_forms=3,
        urgent_tickets=1,
        under_review_damage_reports=2,
        executed_insight_ids={"clear_contact_backlog"},
    )

    insight_ids = [item.id for item in insights]

    assert "optimize_refund_playbooks" in insight_ids
    assert "stabilize_delivery_comms" in insight_ids
    assert "clear_contact_backlog" in insight_ids
    assert "fast_track_damage_reviews" in insight_ids
    assert len(insight_ids) == len(set(insight_ids))
    assert len(insights) <= 4

    backlog = [item for item in insights if item.id == "clear_contact_backlog"][0]
    assert backlog.executed is True


def test_build_analytics_insights_fallback_path() -> None:
    insights = ai_support_service._build_analytics_insights(
        top_reason_label="Other",
        top_reason_pct=5,
        negative_sessions=0,
        total_sessions=0,
        open_contact_forms=0,
        urgent_tickets=0,
        under_review_damage_reports=0,
        executed_insight_ids=set(),
    )

    assert len(insights) == 1
    assert insights[0].id == "clear_contact_backlog"
    assert "No major risk spike" in insights[0].text


def test_keyword_sentiment_label_behavior() -> None:
    assert ai_support_service._keyword_sentiment_label("refund delay issue") == "Negative"
    assert ai_support_service._keyword_sentiment_label("thank you great work") == "Positive"
    assert ai_support_service._keyword_sentiment_label("please check") == "Neutral"


def test_normalize_contact_status_and_priority() -> None:
    assert ai_support_service._normalize_contact_status(None) is None
    assert ai_support_service._normalize_contact_status(" In_Progress ") == "in_progress"
    assert ai_support_service._normalize_contact_priority("URGENT") == "urgent"

    with pytest.raises(HTTPException):
        ai_support_service._normalize_contact_status("done")
    with pytest.raises(HTTPException):
        ai_support_service._normalize_contact_priority("p0")


def test_ensure_support_manager_role_guard() -> None:
    allowed_user = SimpleNamespace(role=SimpleNamespace(name="LOGISTIC_MANAGER"))
    blocked_user = SimpleNamespace(role=SimpleNamespace(name="VENDOR"))

    ai_support_service._ensure_support_manager(allowed_user)
    with pytest.raises(HTTPException) as exc_info:
        ai_support_service._ensure_support_manager(blocked_user)
    assert exc_info.value.status_code == 403


def test_vendor_support_status_and_priority_mappings() -> None:
    assert ai_support_service._vendor_ticket_display_code(uuid4()).startswith("TK-")

    assert ai_support_service._support_status_from_vendor("Open") == "new"
    assert ai_support_service._support_status_from_vendor("In Progress") == "in_progress"
    assert ai_support_service._support_status_from_vendor("Resolved") == "resolved"
    assert ai_support_service._vendor_status_from_support("new") == "Open"
    assert ai_support_service._vendor_status_from_support("in_progress") == "In Progress"
    assert ai_support_service._vendor_status_from_support("resolved") == "Resolved"

    assert ai_support_service._support_priority_from_vendor("HIGH") == "high"
    assert ai_support_service._support_priority_from_vendor("unknown") == "medium"
    assert ai_support_service._vendor_priority_from_support("urgent") == "Urgent"


def test_handoff_ticket_priority_logic() -> None:
    assert ai_support_service._handoff_ticket_priority("legal notice sent") == "urgent"
    assert ai_support_service._handoff_ticket_priority("customer very upset") == "high"
    assert ai_support_service._handoff_ticket_priority(None) == "medium"


def test_split_and_compose_ticket_notes_metadata_round_trip() -> None:
    raw_notes = "\n".join(
        [
            "[meta:source=warehouse_inbound]",
            "[meta:linked_order_id=abc-123]",
            "Visible note line",
        ]
    )

    metadata, visible = ai_support_service._split_ticket_notes(raw_notes)

    assert metadata == {"source": "warehouse_inbound", "linked_order_id": "abc-123"}
    assert visible == "Visible note line"

    recomposed = ai_support_service._compose_ticket_notes(
        metadata={"source": "warehouse_inbound", "linked_order_id": "abc-123", "empty": ""},
        visible_notes="Visible note line",
    )

    assert "[meta:source=warehouse_inbound]" in (recomposed or "")
    assert "Visible note line" in (recomposed or "")


def test_linked_uuid_extractors_from_ticket_metadata() -> None:
    vendor_ticket_id = uuid4()
    order_id = uuid4()
    ticket = SimpleNamespace(
        notes="\n".join(
            [
                f"[meta:linked_vendor_ticket_id={vendor_ticket_id}]",
                f"[meta:linked_order_id={order_id}]",
            ]
        )
    )
    invalid_ticket = SimpleNamespace(
        notes="\n".join(
            [
                "[meta:linked_vendor_ticket_id=not-a-uuid]",
                "[meta:linked_order_id=bad]",
            ]
        )
    )

    assert ai_support_service._linked_vendor_ticket_uuid_from_ticket(ticket) == vendor_ticket_id
    assert ai_support_service._linked_order_uuid_from_ticket(ticket) == order_id
    assert ai_support_service._linked_vendor_ticket_uuid_from_ticket(invalid_ticket) is None
    assert ai_support_service._linked_order_uuid_from_ticket(invalid_ticket) is None
