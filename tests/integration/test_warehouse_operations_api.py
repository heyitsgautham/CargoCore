from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.services import warehouse_operations_service as ops_service

pytestmark = pytest.mark.asyncio

WAREHOUSE_ID = "11111111-1111-1111-1111-111111111111"
ORDER_ID = "22222222-2222-2222-2222-222222222222"


async def test_inbound_overview_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_inbound_overview(_db, _warehouse_id):
        return {
            "stats": {
                "arrived_today": 2,
                "in_transit": 3,
                "mismatches_found": 1,
                "damage_reports": 0,
            },
            "shipments": [],
            "dock_schedule": [],
        }

    monkeypatch.setattr(ops_service, "get_inbound_overview", _fake_get_inbound_overview)

    endpoint = f"/api/v1/warehouses/{WAREHOUSE_ID}/operations/inbound"
    response = await authorized_client.get(endpoint)
    body = response.json()

    assert response.status_code == 200
    assert body["stats"]["in_transit"] == 3

    record_evidence(
        case_id="WHOPS-INT-001",
        endpoint="GET /api/v1/warehouses/{warehouse_id}/operations/inbound",
        input_data={"warehouse_id": WAREHOUSE_ID},
        expected_output={"status_code": 200, "stats.in_transit": 3},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_schedule_inbound_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {
        "supplier_name": "Acme Supplies",
        "expected_qty": 120,
        "scheduled_at": datetime(2026, 4, 18, 10, 0, tzinfo=timezone.utc).isoformat(),
        "dock_preference": "Dock 2",
        "notes": "Handle pallets carefully",
    }

    async def _fake_schedule_inbound_delivery(_db, _warehouse_id, _data):
        return SimpleNamespace(tracking_code="QC-8800112233")

    monkeypatch.setattr(ops_service, "schedule_inbound_delivery", _fake_schedule_inbound_delivery)

    endpoint = f"/api/v1/warehouses/{WAREHOUSE_ID}/operations/inbound/schedule"
    response = await authorized_client.post(endpoint, json=payload)
    body = response.json()

    assert response.status_code == 201
    assert "QC-8800112233" in body["message"]

    record_evidence(
        case_id="WHOPS-INT-002",
        endpoint="POST /api/v1/warehouses/{warehouse_id}/operations/inbound/schedule",
        input_data=payload,
        expected_output={"status_code": 201, "message_contains": "QC-8800112233"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_inbound_overview_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    endpoint = f"/api/v1/warehouses/{WAREHOUSE_ID}/operations/inbound"
    response = await client.get(endpoint)
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="WHOPS-INT-003",
        endpoint="GET /api/v1/warehouses/{warehouse_id}/operations/inbound",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_schedule_inbound_validation_error_422(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    endpoint = f"/api/v1/warehouses/{WAREHOUSE_ID}/operations/inbound/schedule"
    response = await authorized_client.post(endpoint, json={})
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="WHOPS-INT-004",
        endpoint="POST /api/v1/warehouses/{warehouse_id}/operations/inbound/schedule",
        input_data={},
        expected_output={"status_code": 422, "error_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_loading_docks_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_loading_docks(_db, _warehouse_id):
        return {
            "items": [],
            "total": 0,
        }

    monkeypatch.setattr(ops_service, "get_loading_docks", _fake_get_loading_docks)

    endpoint = f"/api/v1/warehouses/{WAREHOUSE_ID}/operations/loading-docks"
    response = await authorized_client.get(endpoint)
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 0

    record_evidence(
        case_id="WHOPS-INT-005",
        endpoint="GET /api/v1/warehouses/{warehouse_id}/operations/loading-docks",
        input_data={"warehouse_id": WAREHOUSE_ID},
        expected_output={"status_code": 200, "total": 0},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
