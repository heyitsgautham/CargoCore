from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from app.services.ai_chat.self_service import _format_self_service_order_message


def _order(**overrides):
    base = {
        "tracking_code": "QC-DEMO102",
        "status": "CONFIRMED",
        "warehouse_substatus": "AWAITING_INBOUND",
        "scheduled_at": datetime(2026, 10, 25, 18, 38, 55, 143844, tzinfo=UTC),
        "pickup_addr": "13 MG Road, Bengaluru",
        "delivery_addr": "41 Indiranagar, Bengaluru",
    }
    return SimpleNamespace(**{**base, **overrides})


def test_order_reply_shows_the_schedule_in_india_time_not_iso() -> None:
    message = _format_self_service_order_message(_order(), "VENDOR", "QC-DEMO102")

    assert "- Scheduled: 26 Oct 2026, 12:08 AM IST" in message
    assert "T18:38" not in message


def test_order_reply_without_a_schedule() -> None:
    message = _format_self_service_order_message(_order(scheduled_at=None), "INDIVIDUAL")

    assert "- Scheduled: Not scheduled yet" in message
