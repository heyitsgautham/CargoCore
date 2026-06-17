from __future__ import annotations

from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.services import auth_service

from tests.utils.sample_data import make_login_response, make_registration_response

pytestmark = pytest.mark.asyncio

AUTH_BASE = "/api/v1/auth"


async def test_auth_register_success(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "phone": "9999999999",
        "password": "StrongPass123",
        "role": "INDIVIDUAL",
    }

    async def _fake_register_user(_db, _data):
        return make_registration_response(pending_approval=False, role_name="INDIVIDUAL")

    monkeypatch.setattr(auth_service, "register_user", _fake_register_user)

    response = await client.post(f"{AUTH_BASE}/register", json=payload)
    body = response.json()

    assert response.status_code == 201
    assert body["token_type"] == "bearer"
    assert body["pending_approval"] is False

    record_evidence(
        case_id="AUTH-INT-001",
        endpoint="POST /api/v1/auth/register",
        input_data=payload,
        expected_output={"status_code": 201, "pending_approval": False},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_auth_register_invalid_role_returns_422(
    client: AsyncClient,
    record_evidence,
) -> None:
    payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "phone": "9999999999",
        "password": "StrongPass123",
        "role": "INVALID_ROLE",
    }
    response = await client.post(f"{AUTH_BASE}/register", json=payload)
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="AUTH-INT-002",
        endpoint="POST /api/v1/auth/register",
        input_data=payload,
        expected_output={"status_code": 422, "error_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_auth_login_success(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {"email": "alice@example.com", "password": "StrongPass123"}

    async def _fake_login_user(_db, _data):
        return make_login_response(role_name="INDIVIDUAL")

    monkeypatch.setattr(auth_service, "login_user", _fake_login_user)

    response = await client.post(f"{AUTH_BASE}/login", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert "access_token" in body
    assert "user" in body

    record_evidence(
        case_id="AUTH-INT-003",
        endpoint="POST /api/v1/auth/login",
        input_data=payload,
        expected_output={"status_code": 200, "keys": ["access_token", "refresh_token", "user"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_auth_token_login_success(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    form_payload = {"username": "alice@example.com", "password": "StrongPass123"}

    async def _fake_login_user(_db, _data):
        login_data = make_login_response(role_name="INDIVIDUAL")
        return SimpleNamespace(**login_data)

    monkeypatch.setattr(auth_service, "login_user", _fake_login_user)

    response = await client.post(f"{AUTH_BASE}/token", data=form_payload)
    body = response.json()

    assert response.status_code == 200
    assert body["token_type"] == "bearer"

    record_evidence(
        case_id="AUTH-INT-004",
        endpoint="POST /api/v1/auth/token",
        input_data=form_payload,
        expected_output={"status_code": 200, "token_type": "bearer"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_auth_logout_missing_header_returns_401(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.post(f"{AUTH_BASE}/logout")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Missing or invalid Authorization header"

    record_evidence(
        case_id="AUTH-INT-005",
        endpoint="POST /api/v1/auth/logout",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Missing or invalid Authorization header"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_auth_me_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get(f"{AUTH_BASE}/me")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="AUTH-INT-006",
        endpoint="GET /api/v1/auth/me",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_auth_me_success(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    response = await authorized_client.get(f"{AUTH_BASE}/me")
    body = response.json()

    assert response.status_code == 200
    assert body["email"] == "test.user@example.com"
    assert body["role"] == "LOGISTIC_MANAGER"

    record_evidence(
        case_id="AUTH-INT-007",
        endpoint="GET /api/v1/auth/me",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "keys": ["id", "email", "role"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_auth_change_password_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {"current_password": "old-pass-123", "new_password": "new-pass-123"}

    async def _fake_change_password(_db, _user, _data):
        return None

    monkeypatch.setattr(auth_service, "change_password", _fake_change_password)

    response = await authorized_client.post(f"{AUTH_BASE}/change-password", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Password changed successfully"

    record_evidence(
        case_id="AUTH-INT-008",
        endpoint="POST /api/v1/auth/change-password",
        input_data=payload,
        expected_output={"status_code": 200, "message": "Password changed successfully"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_auth_send_otp_success(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {"email": "alice@example.com"}

    async def _fake_send_signup_otp(_db, _redis, data):
        return {
            "message": "OTP sent",
            "email": data.email,
            "sent_at": "2026-04-03T00:00:00+00:00",
            "debug_otp": "123456",
        }

    monkeypatch.setattr(auth_service, "send_signup_otp", _fake_send_signup_otp)

    response = await client.post(f"{AUTH_BASE}/send-otp", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "OTP sent"

    record_evidence(
        case_id="AUTH-INT-009",
        endpoint="POST /api/v1/auth/send-otp",
        input_data=payload,
        expected_output={"status_code": 200, "message": "OTP sent"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_auth_verify_otp_success(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {"email": "alice@example.com", "otp": "123456"}

    async def _fake_verify_signup_otp(_redis, _data):
        return {"verified": True, "message": "OTP verified"}

    monkeypatch.setattr(auth_service, "verify_signup_otp", _fake_verify_signup_otp)

    response = await client.post(f"{AUTH_BASE}/verify-otp", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["verified"] is True

    record_evidence(
        case_id="AUTH-INT-010",
        endpoint="POST /api/v1/auth/verify-otp",
        input_data=payload,
        expected_output={"status_code": 200, "verified": True},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
