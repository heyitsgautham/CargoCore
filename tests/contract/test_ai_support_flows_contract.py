from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from httpx import AsyncClient

from app.schemas.ai import ContactSubmissionResponse, TicketListResponse, TicketResponse, TicketStats
from app.services import ai_support_service

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def _contact_submission_response() -> ContactSubmissionResponse:
    now = datetime.now(timezone.utc)
    return ContactSubmissionResponse(
        id=uuid4(),
        reference_code="CS-1001",
        name="Ava Customer",
        email="ava@example.com",
        phone="9999988888",
        subject="Need help with delayed order",
        category="support",
        message="Please help me check my order status.",
        priority="high",
        status="new",
        notes=None,
        assigned_to_user_id=None,
        assigned_agent_name=None,
        created_at=now,
        updated_at=now,
    )


def _ticket_response() -> TicketResponse:
    now = datetime.now(timezone.utc)
    return TicketResponse(
        id=uuid4(),
        reference_code="TCK-1001",
        title="Refund pending",
        description="Customer refund has not arrived.",
        priority="high",
        status="new",
        category="refund",
        customer_name="Ava Customer",
        notes=None,
        assigned_to_user_id=None,
        assigned_agent_name=None,
        created_at=now,
        updated_at=now,
        resolved_at=None,
        source="manual",
        source_label="Manual",
        requester_type=None,
        issue_type=None,
        resolution_action=None,
        resolution_label=None,
        linked_vendor_ticket_id=None,
        linked_vendor_ticket_code=None,
        linked_damage_report_id=None,
        linked_order_id=None,
        linked_order_tracking_code=None,
        linked_vendor_replies=[],
        can_delete=True,
        lm_action_steps=[],
    )


def test_openapi_ai_support_flows_paths_exist() -> None:
    data = _load_openapi()
    paths = data.get("paths", {})

    assert "/api/v1/ai/contact-submissions/public" in paths
    assert "/api/v1/ai/contact-submissions" in paths
    assert "/api/v1/ai/contact-submissions/{submission_id}" in paths
    assert "/api/v1/ai/tickets" in paths
    assert "/api/v1/ai/tickets/{ticket_id}" in paths


@pytest.mark.asyncio
async def test_public_contact_submission_contract(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {
        "name": "Ava Customer",
        "email": "ava@example.com",
        "phone": "9999988888",
        "subject": "Need help with delayed order",
        "category": "support",
        "priority": "high",
        "message": "Please help me check my order status.",
    }

    async def _fake_create_public_contact_submission(*, db, data):
        return _contact_submission_response()

    monkeypatch.setattr(ai_support_service, "create_public_contact_submission", _fake_create_public_contact_submission)

    response = await client.post("/api/v1/ai/contact-submissions/public", json=payload)
    body = response.json()

    assert response.status_code == 201
    assert set(["id", "reference_code", "subject", "status"]).issubset(body.keys())

    record_evidence(
        case_id="AISUP-CON-001",
        endpoint="POST /api/v1/ai/contact-submissions/public",
        input_data=payload,
        expected_output={"status_code": 201, "required_keys": ["id", "reference_code", "subject", "status"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_tickets_list_contract(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_list_tickets(*, db):
        return TicketListResponse(
            tickets=[_ticket_response()],
            stats=TicketStats(total=1, new=1, in_progress=0, resolved=0, urgent=1),
            agents=[],
        )

    monkeypatch.setattr(ai_support_service, "list_tickets", _fake_list_tickets)

    response = await authorized_client.get("/api/v1/ai/tickets")
    body = response.json()

    assert response.status_code == 200
    assert set(["tickets", "stats", "agents"]).issubset(body.keys())

    record_evidence(
        case_id="AISUP-CON-002",
        endpoint="GET /api/v1/ai/tickets",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "required_keys": ["tickets", "stats", "agents"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
