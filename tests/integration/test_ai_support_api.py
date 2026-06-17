from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.services import ai_support_service

pytestmark = pytest.mark.asyncio


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _support_settings_payload() -> dict:
    return {
        "tone": "Professional and empathetic",
        "language_mode": "English",
        "sentiment_threshold": 80,
        "refund_limit_inr": 15000,
        "system_prompt": "You are the support assistant. Resolve user issues clearly, politely, and with actionable steps.",
        "autonomous_replies": True,
        "legal_threat_detection": True,
        "real_time_sentiment_analysis": True,
        "proactive_human_handover": False,
    }


async def test_support_dashboard_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_support_dashboard(db):
        return {
            "stats": {
                "total_sessions": 4,
                "active_sessions": 2,
                "human_engaged_sessions": 1,
                "sessions_needing_human": 1,
                "open_escalations": 1,
                "open_contact_forms": 3,
                "new_contact_forms": 2,
                "resolved_contact_forms": 1,
                "user_messages_today": 12,
                "assistant_messages_today": 20,
            },
            "priority_sessions": [],
            "recent_contact_submissions": [],
            "activity_feed": [],
        }

    monkeypatch.setattr(ai_support_service, "get_support_dashboard", _fake_get_support_dashboard)

    response = await authorized_client.get("/api/v1/ai/support/dashboard")
    body = response.json()

    assert response.status_code == 200
    assert "stats" in body
    assert body["stats"]["active_sessions"] == 2

    record_evidence(
        case_id="S2-INT-001",
        endpoint="GET /api/v1/ai/support/dashboard",
        input_data={},
        expected_output={"status_code": 200, "stats.active_sessions": 2},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_support_settings_update_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = _support_settings_payload()

    async def _fake_update_support_settings(db, user, data):
        return {
            "settings": data.model_dump(),
            "integrations": [
                {
                    "provider": "gmail",
                    "label": "Gmail",
                    "description": "Outbound support email",
                    "connected": True,
                    "connection_source": "env",
                    "status_note": "Connected",
                    "editable": False,
                }
            ],
            "updated_at": _iso_now(),
            "autonomous_reply_guidance": "Autonomous mode is active.",
            "rag_recommended": False,
        }

    monkeypatch.setattr(ai_support_service, "update_support_settings", _fake_update_support_settings)

    response = await authorized_client.put("/api/v1/ai/support/settings", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["settings"]["sentiment_threshold"] == 80
    assert body["integrations"][0]["provider"] == "gmail"

    record_evidence(
        case_id="S2-INT-002",
        endpoint="PUT /api/v1/ai/support/settings",
        input_data=payload,
        expected_output={"status_code": 200, "settings.sentiment_threshold": 80},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_support_analytics_and_execute_insight_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    insight_id = "escalation-spike"

    async def _fake_get_support_analytics(db, time_range):
        return {
            "range": time_range,
            "generated_at": _iso_now(),
            "metrics": [
                {
                    "id": "resolution_rate",
                    "label": "Resolution Rate",
                    "icon": "analytics",
                    "value": 74.2,
                    "formatted_value": "74.2%",
                    "trend": "+3.1%",
                    "trend_direction": "up",
                }
            ],
            "resolution_chart": {
                "labels": ["Mon", "Tue"],
                "ai_resolved": [6, 7],
                "human_escalated": [2, 3],
            },
            "escalation_reasons": [
                {"label": "Legal risk", "count": 2, "pct": 25},
                {"label": "Sentiment drop", "count": 6, "pct": 75},
            ],
            "sentiment_chart": {
                "labels": ["Mon", "Tue"],
                "ai_handled": [82.4, 80.1],
                "human_handled": [60.0, 58.5],
            },
            "insights": [
                {
                    "id": insight_id,
                    "icon": "insights",
                    "title": "Escalations rising",
                    "text": "Escalations rose in the last 24h.",
                    "tone": "amber",
                    "action_label": "Create follow-up",
                    "executed": False,
                }
            ],
        }

    async def _fake_execute_support_analytics_insight(db, insight_id, time_range):
        return {
            "insight_id": insight_id,
            "ticket_id": str(uuid4()),
            "ticket_reference_code": "TCK-7788",
            "message": f"Insight {insight_id} executed for {time_range}",
        }

    monkeypatch.setattr(ai_support_service, "get_support_analytics", _fake_get_support_analytics)
    monkeypatch.setattr(ai_support_service, "execute_support_analytics_insight", _fake_execute_support_analytics_insight)

    analytics_response = await authorized_client.get("/api/v1/ai/support/analytics?range=7D")
    analytics_body = analytics_response.json()

    execute_response = await authorized_client.post(
        f"/api/v1/ai/support/analytics/insights/{insight_id}/execute?range=7D"
    )
    execute_body = execute_response.json()

    assert analytics_response.status_code == 200
    assert analytics_body["range"] == "7D"
    assert execute_response.status_code == 200
    assert execute_body["insight_id"] == insight_id

    record_evidence(
        case_id="S2-INT-003",
        endpoint="GET/POST /api/v1/ai/support/analytics*",
        input_data={"range": "7D", "insight_id": insight_id},
        expected_output={"analytics_status": 200, "execute_status": 200},
        actual_output={
            "analytics_status": analytics_response.status_code,
            "analytics_body": analytics_body,
            "execute_status": execute_response.status_code,
            "execute_body": execute_body,
        },
        status="PASS",
    )


async def test_support_settings_validation_error_422(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    payload = _support_settings_payload()
    payload["sentiment_threshold"] = 101

    response = await authorized_client.put("/api/v1/ai/support/settings", json=payload)
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="S2-INT-004",
        endpoint="PUT /api/v1/ai/support/settings",
        input_data=payload,
        expected_output={"status_code": 422, "detail_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
