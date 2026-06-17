from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services import customer_service

pytestmark = pytest.mark.asyncio


async def test_damage_review_queue_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_damage_review_queue(db, current_user, status, flow_type):
        return [
            {
                "id": "DMG-REF-1001",
                "order_id": "ORD-1001",
                "customer": "Casey Customer",
                "description": "Box arrived damaged.",
                "images": ["photo-1.png"],
                "flow_type": "pickup_inspection",
                "status": status or "Reported",
            }
        ]

    monkeypatch.setattr(customer_service, "get_damage_review_queue", _fake_get_damage_review_queue)

    response = await authorized_client.get("/api/v1/damage-reports?status=Reported&flow_type=pickup_inspection")
    body = response.json()

    assert response.status_code == 200
    assert isinstance(body, list)
    assert body[0]["id"] == "DMG-REF-1001"

    record_evidence(
        case_id="S2-INT-005",
        endpoint="GET /api/v1/damage-reports",
        input_data={"query": {"status": "Reported", "flow_type": "pickup_inspection"}},
        expected_output={"status_code": 200, "first_id": "DMG-REF-1001"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_damage_review_submit_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {
        "damage_severity": "LOW",
        "is_genuine": True,
        "recommended_settlement": "Partial Refund",
        "remarks": "Packaging dented, item usable.",
        "new_status": "Claims Reviewed",
    }

    async def _fake_submit_damage_review(db, current_user, reference_code, data):
        return {
            "id": reference_code,
            "order_id": "ORD-2001",
            "customer": "Vendor Ops",
            "description": "Transit scratch report.",
            "images": ["dmg-1.png"],
            "flow_type": "photo_review",
            "status": data.new_status,
        }

    monkeypatch.setattr(customer_service, "submit_damage_review", _fake_submit_damage_review)

    response = await authorized_client.post("/api/v1/damage-reports/DMG-REF-2001/review", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["id"] == "DMG-REF-2001"
    assert body["status"] == "Claims Reviewed"

    record_evidence(
        case_id="S2-INT-006",
        endpoint="POST /api/v1/damage-reports/{reference_code}/review",
        input_data={"path": {"reference_code": "DMG-REF-2001"}, "json": payload},
        expected_output={"status_code": 200, "status": "Claims Reviewed"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_damage_review_validation_error_422(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    response = await authorized_client.post("/api/v1/damage-reports/DMG-REF-3001/review", json={"new_status": 123})
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="S2-INT-007",
        endpoint="POST /api/v1/damage-reports/{reference_code}/review",
        input_data={"path": {"reference_code": "DMG-REF-3001"}, "json": {"new_status": 123}},
        expected_output={"status_code": 422, "detail_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
