from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from httpx import AsyncClient

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_openapi_global_paths_and_version() -> None:
    data = _load_openapi()
    assert str(data.get("openapi", "")).startswith("3.")

    paths = data.get("paths", {})
    assert "/health" in paths
    assert "/api/v1/tracking/drivers" in paths
    assert "/api/v1/tracking/orders/{order_id}/driver" in paths


@pytest.mark.asyncio
async def test_health_endpoint_contract(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get("/health")
    body = response.json()

    assert response.status_code == 200
    assert body == {"status": "ok"}

    record_evidence(
        case_id="PUB-CON-002",
        endpoint="GET /health",
        input_data={},
        expected_output={"status_code": 200, "body": {"status": "ok"}},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_tracking_schema_contract_defined(
    client: AsyncClient,
    record_evidence,
) -> None:
    # This validates the contract declaration in OpenAPI even when runtime call
    # without auth returns 401.
    data = _load_openapi()
    path_item = data["paths"]["/api/v1/tracking/drivers"]["get"]

    response = await client.get("/api/v1/tracking/drivers")
    body = response.json()

    assert "$ref" in path_item["responses"]["200"]["content"]["application/json"]["schema"]["items"]
    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="PUB-CON-003",
        endpoint="GET /api/v1/tracking/drivers",
        input_data={"authorization": None},
        expected_output={
            "openapi_200_item_schema_ref": "#/components/schemas/DriverLocationItem",
            "runtime_status_code": 401,
        },
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
