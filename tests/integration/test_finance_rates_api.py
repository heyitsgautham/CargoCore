from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.database import get_db
from app.routers import rates as rates_router
from app.services import finance_service

pytestmark = pytest.mark.asyncio


async def test_finance_summary_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_finance_summary(_db, warehouse_id=None):
        return {
            "total_revenue": 10000.0,
            "total_expenses": 4000.0,
            "net_profit": 6000.0,
            "pending_cod": 1200.0,
        }

    monkeypatch.setattr(finance_service, "get_finance_summary", _fake_get_finance_summary)

    response = await authorized_client.get("/api/v1/finance/summary")
    body = response.json()

    assert response.status_code == 200
    assert body["net_profit"] == 6000.0

    record_evidence(
        case_id="FR-INT-001",
        endpoint="GET /api/v1/finance/summary",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "net_profit": 6000.0},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_finance_summary_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get("/api/v1/finance/summary")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="FR-INT-002",
        endpoint="GET /api/v1/finance/summary",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_finance_payroll_run_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    dependency_override_manager,
    record_evidence,
) -> None:
    payload = {
        "user_payouts": [
            {
                "user_id": "11111111-1111-1111-1111-111111111111",
                "amount": 3500,
                "record_type": "staff",
                "name": "Staff One",
            }
        ]
    }

    async def _fake_run_payroll(_db, payouts):
        assert len(payouts) == 1
        return {"processed": 1, "total_amount": 3500.0}

    class _CommitCapableDB:
        async def commit(self) -> None:
            return None

    async def _override_db_with_commit():
        yield _CommitCapableDB()

    dependency_override_manager(get_db, _override_db_with_commit)
    monkeypatch.setattr(finance_service, "run_payroll", _fake_run_payroll)

    response = await authorized_client.post("/api/v1/finance/payroll/run", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["processed"] == 1

    record_evidence(
        case_id="FR-INT-003",
        endpoint="POST /api/v1/finance/payroll/run",
        input_data=payload,
        expected_output={"status_code": 200, "processed": 1},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_finance_payroll_validation_error_422(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    response = await authorized_client.post("/api/v1/finance/payroll/run", json={})
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="FR-INT-004",
        endpoint="POST /api/v1/finance/payroll/run",
        input_data={},
        expected_output={"status_code": 422, "error_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_rates_get_public_success(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    monkeypatch.setattr(rates_router, "_load", lambda: {"baseBookingFee": 220, "dynamic": {"peak": 1.2}})

    response = await client.get("/api/v1/rates")
    body = response.json()

    assert response.status_code == 200
    assert body["baseBookingFee"] == 220

    record_evidence(
        case_id="FR-INT-005",
        endpoint="GET /api/v1/rates",
        input_data={},
        expected_output={"status_code": 200, "baseBookingFee": 220},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_rates_update_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    saved = {}

    def _fake_load():
        return {"baseBookingFee": 220, "dynamic": {"peak": 1.2, "emergency": 2.5}}

    def _fake_save(data):
        saved["payload"] = data

    monkeypatch.setattr(rates_router, "_load", _fake_load)
    monkeypatch.setattr(rates_router, "_save", _fake_save)

    payload = {"dynamic": {"peak": 1.3}}
    response = await authorized_client.put("/api/v1/rates", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["dynamic"]["peak"] == 1.3
    assert saved["payload"]["dynamic"]["peak"] == 1.3

    record_evidence(
        case_id="FR-INT-006",
        endpoint="PUT /api/v1/rates",
        input_data=payload,
        expected_output={"status_code": 200, "dynamic.peak": 1.3},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_rates_update_empty_payload_returns_400(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    response = await authorized_client.put("/api/v1/rates", json={})
    body = response.json()

    assert response.status_code == 400
    assert body["detail"] == "Empty payload"

    record_evidence(
        case_id="FR-INT-007",
        endpoint="PUT /api/v1/rates",
        input_data={},
        expected_output={"status_code": 400, "detail": "Empty payload"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_rates_update_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.put("/api/v1/rates", json={"baseBookingFee": 300})
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="FR-INT-008",
        endpoint="PUT /api/v1/rates",
        input_data={"authorization": None, "json": {"baseBookingFee": 300}},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
