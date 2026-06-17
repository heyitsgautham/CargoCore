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


def test_openapi_sprint2_changed_paths_exist() -> None:
    data = _load_openapi()
    paths = data.get("paths", {})

    required_operations = [
        ("/api/v1/ai/support/dashboard", "get"),
        ("/api/v1/ai/support/settings", "get"),
        ("/api/v1/ai/support/settings", "put"),
        ("/api/v1/ai/support/analytics", "get"),
        ("/api/v1/ai/support/analytics/insights/{insight_id}/execute", "post"),
        ("/api/v1/ai/tickets", "get"),
        ("/api/v1/ai/tickets", "post"),
        ("/api/v1/damage-reports", "get"),
        ("/api/v1/damage-reports/{reference_code}/review", "post"),
        ("/api/v1/orders/assignment-preview", "get"),
        ("/api/v1/orders/ai-driver-suggestions", "get"),
        ("/api/v1/orders/return-suggestions", "get"),
        ("/api/v1/orders/cluster", "post"),
        ("/api/v1/orders/optimize-routes", "post"),
        ("/api/v1/orders/batch-assign", "post"),
        ("/api/v1/orders/auto-balance", "post"),
    ]

    for path, method in required_operations:
        assert path in paths, f"Missing path in OpenAPI YAML: {path}"
        assert method in paths[path], f"Missing method in OpenAPI YAML: {method.upper()} {path}"


def test_openapi_sprint2_schema_bindings() -> None:
    data = _load_openapi()
    paths = data["paths"]

    support_settings_ref = (
        paths["/api/v1/ai/support/settings"]["put"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    )
    damage_review_ref = (
        paths["/api/v1/damage-reports/{reference_code}/review"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    )
    driver_suggestions_ref = (
        paths["/api/v1/orders/ai-driver-suggestions"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    )

    assert support_settings_ref.endswith("/SupportSettings")
    assert damage_review_ref.endswith("/DamageReviewUpdate")
    assert driver_suggestions_ref.endswith("/DriverSuggestionResponse")


@pytest.mark.asyncio
async def test_support_dashboard_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get("/api/v1/ai/support/dashboard")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="S2-CON-001",
        endpoint="GET /api/v1/ai/support/dashboard",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_damage_review_queue_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get("/api/v1/damage-reports")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="S2-CON-002",
        endpoint="GET /api/v1/damage-reports",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_dispatcher_intelligence_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get("/api/v1/orders/ai-driver-suggestions")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="S2-CON-003",
        endpoint="GET /api/v1/orders/ai-driver-suggestions",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
