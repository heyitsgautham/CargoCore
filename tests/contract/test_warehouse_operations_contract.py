from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from httpx import AsyncClient

from app.services import warehouse_operations_service as ops_service

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"
WAREHOUSE_ID = "11111111-1111-1111-1111-111111111111"


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_openapi_warehouse_operations_paths_exist() -> None:
    data = _load_openapi()
    paths = data.get("paths", {})

    assert "/api/v1/warehouses/{warehouse_id}/operations/inbound" in paths
    assert "/api/v1/warehouses/{warehouse_id}/operations/inbound/schedule" in paths
    assert "/api/v1/warehouses/{warehouse_id}/operations/loading-docks" in paths
    assert "/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/start-picking" in paths
    assert "/api/v1/warehouses/{warehouse_id}/operations/performance" in paths


def test_openapi_warehouse_schemas_include_hub_status() -> None:
    data = _load_openapi()
    schemas = data.get("components", {}).get("schemas", {})

    create_props = schemas.get("WarehouseCreate", {}).get("properties", {})
    update_props = schemas.get("WarehouseUpdate", {}).get("properties", {})

    assert "hub_status" in create_props
    assert "hub_status" in update_props


@pytest.mark.asyncio
async def test_inbound_overview_contract(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_inbound_overview(_db, _warehouse_id):
        return {
            "stats": {
                "arrived_today": 1,
                "in_transit": 2,
                "mismatches_found": 0,
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
    assert set(["stats", "shipments", "dock_schedule"]).issubset(body.keys())

    record_evidence(
        case_id="WHOPS-CON-001",
        endpoint="GET /api/v1/warehouses/{warehouse_id}/operations/inbound",
        input_data={"warehouse_id": WAREHOUSE_ID},
        expected_output={"status_code": 200, "required_keys": ["stats", "shipments", "dock_schedule"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_loading_docks_contract(
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
    assert set(["items", "total"]).issubset(body.keys())

    record_evidence(
        case_id="WHOPS-CON-002",
        endpoint="GET /api/v1/warehouses/{warehouse_id}/operations/loading-docks",
        input_data={"warehouse_id": WAREHOUSE_ID},
        expected_output={"status_code": 200, "required_keys": ["items", "total"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
