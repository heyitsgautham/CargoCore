from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.database import get_db
from app.services import logistics_service

pytestmark = pytest.mark.asyncio


async def test_logistics_alerts_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_list_alerts(_db):
        return []

    monkeypatch.setattr(logistics_service, "list_alerts", _fake_list_alerts)

    response = await authorized_client.get("/api/v1/logistics/alerts")
    body = response.json()

    assert response.status_code == 200
    assert body == []

    record_evidence(
        case_id="LT-INT-001",
        endpoint="GET /api/v1/logistics/alerts",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "body": []},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_logistics_alerts_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get("/api/v1/logistics/alerts")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="LT-INT-002",
        endpoint="GET /api/v1/logistics/alerts",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_logistics_task_validation_error_422(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    response = await authorized_client.post("/api/v1/logistics/tasks", json={})
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="LT-INT-003",
        endpoint="POST /api/v1/logistics/tasks",
        input_data={},
        expected_output={"status_code": 422, "error_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_tracking_drivers_success_with_db_override(
    authorized_client: AsyncClient,
    dependency_override_manager,
    record_evidence,
) -> None:
    class _FakeResult:
        def __init__(self, rows):
            self._rows = rows

        def all(self):
            return self._rows

    class _FakeDB:
        async def execute(self, _query):
            driver_profile = type(
                "DriverProfile",
                (),
                {
                    "status": "Active",
                    "current_location": "19.0760,72.8777",
                    "updated_at": datetime(2026, 4, 17, 10, 0, tzinfo=timezone.utc),
                },
            )()
            driver_user = type(
                "DriverUser",
                (),
                {
                    "id": uuid4(),
                    "name": "Driver One",
                },
            )()
            vehicle = type(
                "Vehicle",
                (),
                {
                    "id": uuid4(),
                    "code": "VH-101",
                    "updated_at": datetime(2026, 4, 17, 10, 5, tzinfo=timezone.utc),
                },
            )()
            return _FakeResult([(driver_profile, driver_user, vehicle)])

    async def _override_tracking_db():
        yield _FakeDB()

    dependency_override_manager(get_db, _override_tracking_db)

    response = await authorized_client.get("/api/v1/tracking/drivers")
    body = response.json()

    assert response.status_code == 200
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["driver_name"] == "Driver One"

    record_evidence(
        case_id="LT-INT-004",
        endpoint="GET /api/v1/tracking/drivers",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "first_driver_name": "Driver One"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_tracking_order_driver_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get("/api/v1/tracking/orders/11111111-1111-1111-1111-111111111111/driver")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="LT-INT-005",
        endpoint="GET /api/v1/tracking/orders/{order_id}/driver",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
