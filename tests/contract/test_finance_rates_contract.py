from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from httpx import AsyncClient

from app.routers import rates as rates_router
from app.services import finance_service

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_openapi_finance_rates_paths_exist() -> None:
    data = _load_openapi()
    paths = data.get("paths", {})

    assert "/api/v1/finance/summary" in paths
    assert "/api/v1/finance/payroll/run" in paths
    assert "/api/v1/rates" in paths
    assert "/api/v1/rates/inventory-seeded" in paths
    assert "/api/v1/rates/seed-inventory" in paths


@pytest.mark.asyncio
async def test_finance_summary_contract(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_finance_summary(_db, warehouse_id=None):
        return {
            "total_revenue": 10000.0,
            "total_expenses": 5000.0,
            "net_profit": 5000.0,
            "pending_cod": 1000.0,
        }

    monkeypatch.setattr(finance_service, "get_finance_summary", _fake_get_finance_summary)

    response = await authorized_client.get("/api/v1/finance/summary")
    body = response.json()

    assert response.status_code == 200
    assert set(["total_revenue", "total_expenses", "net_profit", "pending_cod"]).issubset(body.keys())

    record_evidence(
        case_id="FR-CON-001",
        endpoint="GET /api/v1/finance/summary",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "required_keys": ["total_revenue", "total_expenses", "net_profit", "pending_cod"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_rates_get_contract(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    monkeypatch.setattr(rates_router, "_load", lambda: {"baseBookingFee": 220, "perKmRate": 12, "dynamic": {"peak": 1.2}})

    response = await client.get("/api/v1/rates")
    body = response.json()

    assert response.status_code == 200
    assert set(["baseBookingFee", "perKmRate", "dynamic"]).issubset(body.keys())

    record_evidence(
        case_id="FR-CON-002",
        endpoint="GET /api/v1/rates",
        input_data={},
        expected_output={"status_code": 200, "required_keys": ["baseBookingFee", "perKmRate", "dynamic"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
