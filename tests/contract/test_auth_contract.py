from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from httpx import AsyncClient

from app.services import auth_service

from tests.utils.sample_data import make_login_response, make_registration_response

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_openapi_auth_paths_and_methods_exist() -> None:
    data = _load_openapi()
    paths = data.get("paths", {})

    assert "/api/v1/auth/register" in paths
    assert "post" in paths["/api/v1/auth/register"]
    assert "/api/v1/auth/login" in paths
    assert "post" in paths["/api/v1/auth/login"]
    assert "/api/v1/auth/token" in paths
    assert "post" in paths["/api/v1/auth/token"]


@pytest.mark.asyncio
async def test_register_response_contract(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {
        "name": "Bob",
        "email": "bob@example.com",
        "phone": "9999999999",
        "password": "StrongPass123",
        "role": "INDIVIDUAL",
    }

    async def _fake_register_user(_db, _data):
        return make_registration_response(pending_approval=False, role_name="INDIVIDUAL")

    monkeypatch.setattr(auth_service, "register_user", _fake_register_user)

    response = await client.post("/api/v1/auth/register", json=payload)
    body = response.json()

    assert response.status_code == 201
    assert set(["access_token", "refresh_token", "token_type", "pending_approval"]).issubset(body.keys())
    assert isinstance(body["pending_approval"], bool)

    record_evidence(
        case_id="AUTH-CON-002",
        endpoint="POST /api/v1/auth/register",
        input_data=payload,
        expected_output={"status_code": 201, "required_keys": ["access_token", "refresh_token", "token_type"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_login_response_contract(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {"email": "bob@example.com", "password": "StrongPass123"}

    async def _fake_login_user(_db, _data):
        return make_login_response(role_name="INDIVIDUAL")

    monkeypatch.setattr(auth_service, "login_user", _fake_login_user)

    response = await client.post("/api/v1/auth/login", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert set(["access_token", "refresh_token", "token_type", "user"]).issubset(body.keys())
    assert set(["id", "email", "role"]).issubset(body["user"].keys())

    record_evidence(
        case_id="AUTH-CON-003",
        endpoint="POST /api/v1/auth/login",
        input_data=payload,
        expected_output={"status_code": 200, "required_keys": ["access_token", "refresh_token", "user"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_register_validation_error_contract(
    client: AsyncClient,
    record_evidence,
) -> None:
    payload = {
        "name": "Bob",
        "email": "bob@example.com",
        "password": "StrongPass123",
        "role": "UNKNOWN_ROLE",
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    body = response.json()

    assert response.status_code == 422
    assert isinstance(body.get("detail"), list)

    record_evidence(
        case_id="AUTH-CON-004",
        endpoint="POST /api/v1/auth/register",
        input_data=payload,
        expected_output={"status_code": 422, "detail_type": "list"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
