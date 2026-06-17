from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services import auth_service


def _make_user(
    *,
    role_name: str = "INDIVIDUAL",
    approval_status: str | None = "APPROVED",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        name="Unit Test User",
        username="unit.user",
        email="unit.user@example.com",
        phone="9999999999",
        address="Unit Test Address",
        role=SimpleNamespace(name=role_name),
        warehouse_id=None,
        is_active=True,
        approval_status=approval_status,
        company_name="Unit Test Logistics",
        tax_id="TAX-123",
        contact_person="Unit Contact",
        business_email="biz@example.com",
        business_phone="8888888888",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_token_payload_contains_subject_and_role() -> None:
    user = _make_user(role_name="DISPATCHER")

    payload = auth_service._token_payload(user)

    assert payload == {"sub": str(user.id), "role": "DISPATCHER"}


@pytest.mark.parametrize(
    ("approval_status", "expected_fragment"),
    [
        ("PENDING", "waiting"),
        ("REJECTED", "rejected"),
        ("APPROVED", None),
        (None, None),
    ],
)
def test_approval_message_variants(
    approval_status: str | None,
    expected_fragment: str | None,
) -> None:
    message = auth_service._approval_message(
        _make_user(approval_status=approval_status)
    )

    if expected_fragment is None:
        assert message is None
    else:
        assert expected_fragment.lower() in message.lower()


def test_ensure_user_can_authenticate_rejects_pending_vendor() -> None:
    user = _make_user(role_name="VENDOR", approval_status="PENDING")

    with pytest.raises(HTTPException) as exc_info:
        auth_service._ensure_user_can_authenticate(user)

    assert exc_info.value.status_code == 403
    assert "approval" in str(exc_info.value.detail).lower()


def test_ensure_user_session_valid_rejects_rejected_vendor() -> None:
    user = _make_user(role_name="VENDOR", approval_status="REJECTED")

    with pytest.raises(HTTPException) as exc_info:
        auth_service._ensure_user_session_valid(user)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_ensure_user_can_authenticate_allows_approved_user() -> None:
    user = _make_user(approval_status="APPROVED")

    auth_service._ensure_user_can_authenticate(user)


def test_build_registration_response_pending_vendor_has_no_tokens() -> None:
    user = _make_user(role_name="VENDOR", approval_status="PENDING")

    response = auth_service._build_registration_response(user)

    assert response.pending_approval is True
    assert response.access_token is None
    assert response.refresh_token is None
    assert response.user is not None
    assert "must approve" in (response.message or "").lower()


def test_build_registration_response_approved_uses_token_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _make_user(approval_status="APPROVED")
    monkeypatch.setattr(auth_service, "create_access_token", lambda payload: f"access-{payload['sub']}")
    monkeypatch.setattr(auth_service, "create_refresh_token", lambda payload: f"refresh-{payload['sub']}")

    response = auth_service._build_registration_response(user)

    assert response.pending_approval is False
    assert response.access_token == f"access-{user.id}"
    assert response.refresh_token == f"refresh-{user.id}"
    assert response.user is not None


def test_build_login_response_contains_user_profile_and_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _make_user(role_name="LOGISTIC_MANAGER")
    monkeypatch.setattr(auth_service, "create_access_token", lambda payload: f"a-{payload['role']}")
    monkeypatch.setattr(auth_service, "create_refresh_token", lambda payload: f"r-{payload['role']}")

    response = auth_service._build_login_response(user)

    assert response.access_token == "a-LOGISTIC_MANAGER"
    assert response.refresh_token == "r-LOGISTIC_MANAGER"
    assert response.user.role == "LOGISTIC_MANAGER"
    assert response.user.email == "unit.user@example.com"


def test_to_profile_defaults_approval_to_approved() -> None:
    user = _make_user(approval_status=None)

    profile = auth_service._to_profile(user)

    assert profile.approval_status == "APPROVED"
    assert profile.username == "unit.user"
