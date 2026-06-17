from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.schemas.ai import (
    ContactSubmissionListResponse,
    ContactSubmissionResponse,
    ContactSubmissionStats,
    SupportAgentSummary,
    TicketListResponse,
    TicketResponse,
    TicketStats,
)
from app.services import ai_support_service

pytestmark = pytest.mark.asyncio


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


async def test_public_contact_submission_success(
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
    assert body["reference_code"] == "CS-1001"

    record_evidence(
        case_id="AISUP-INT-001",
        endpoint="POST /api/v1/ai/contact-submissions/public",
        input_data=payload,
        expected_output={"status_code": 201, "reference_code": "CS-1001"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_contact_submissions_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get("/api/v1/ai/contact-submissions")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="AISUP-INT-002",
        endpoint="GET /api/v1/ai/contact-submissions",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_public_contact_submission_validation_error_422(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.post("/api/v1/ai/contact-submissions/public", json={})
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="AISUP-INT-003",
        endpoint="POST /api/v1/ai/contact-submissions/public",
        input_data={},
        expected_output={"status_code": 422, "error_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_tickets_list_success(
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
    assert body["stats"]["total"] == 1
    assert body["tickets"][0]["reference_code"] == "TCK-1001"

    record_evidence(
        case_id="AISUP-INT-004",
        endpoint="GET /api/v1/ai/tickets",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "stats.total": 1, "first_reference": "TCK-1001"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_tickets_list_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get("/api/v1/ai/tickets")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="AISUP-INT-005",
        endpoint="GET /api/v1/ai/tickets",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_contact_submissions_list_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_list_contact_submissions(*, db):
        return ContactSubmissionListResponse(
            submissions=[_contact_submission_response()],
            stats=ContactSubmissionStats(total=1, new=1, in_progress=0, resolved=0, urgent=1),
            agents=[SupportAgentSummary(id=uuid4(), name="Support One", email="support@example.com")],
        )

    monkeypatch.setattr(ai_support_service, "list_contact_submissions", _fake_list_contact_submissions)

    response = await authorized_client.get("/api/v1/ai/contact-submissions")
    body = response.json()

    assert response.status_code == 200
    assert body["stats"]["total"] == 1
    assert body["submissions"][0]["reference_code"] == "CS-1001"

    record_evidence(
        case_id="AISUP-INT-006",
        endpoint="GET /api/v1/ai/contact-submissions",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "stats.total": 1, "first_reference": "CS-1001"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
