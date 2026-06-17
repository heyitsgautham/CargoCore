from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from httpx import AsyncClient

from app.database import get_db
from app.services import logistics_service

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_openapi_logistics_tracking_paths_exist() -> None:
    data = _load_openapi()
    paths = data.get("paths", {})

    assert "/api/v1/logistics/alerts" in paths
    assert "/api/v1/logistics/tasks" in paths
    assert "/api/v1/logistics/vehicles" in paths
    assert "/api/v1/tracking/drivers" in paths
    assert "/api/v1/tracking/orders/{order_id}/driver" in paths


@pytest.mark.asyncio
async def test_logistics_alerts_contract(
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
    assert isinstance(body, list)

    record_evidence(
        case_id="LT-CON-001",
        endpoint="GET /api/v1/logistics/alerts",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "response_type": "list"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_tracking_drivers_contract(
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
    assert set(["driver_id", "driver_name", "latitude", "longitude", "status"]).issubset(body[0].keys())

    record_evidence(
        case_id="LT-CON-002",
        endpoint="GET /api/v1/tracking/drivers",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "required_keys": ["driver_id", "driver_name", "latitude", "longitude", "status"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
