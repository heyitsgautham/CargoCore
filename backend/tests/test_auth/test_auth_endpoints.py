"""
test_auth_endpoints.py
Integration tests for all 9 /api/v1/auth/* endpoints.
"""
import pytest
from httpx import AsyncClient

from tests.conftest import REGISTER_PAYLOAD

pytestmark = pytest.mark.asyncio


# ── POST /register ────────────────────────────────────────────────────────────


async def test_register_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["pending_approval"] is False


async def test_vendor_register_requires_approval(client: AsyncClient):
    payload = {
        **REGISTER_PAYLOAD,
        "email": "vendor@example.com",
        "role": "VENDOR",
        "company_name": "Acme Supplies",
        "contact_person": "Vendor Contact",
        "business_email": "ops@acme.example",
        "business_phone": "9000000000",
        "tax_id": "GST12345",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["pending_approval"] is True
    assert body["access_token"] is None
    assert body["user"]["approval_status"] == "PENDING"


async def test_register_duplicate_email(client: AsyncClient, registered_user_tokens):
    # Second registration with same email
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


async def test_register_invalid_role(client: AsyncClient):
    """Completely unknown role names are rejected by Pydantic (422)."""
    payload = {**REGISTER_PAYLOAD, "email": "newuser@example.com", "role": "SUPERMAN"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "restricted_role",
    ["LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER", "LABOURER"],
)
async def test_register_restricted_role_rejected(client: AsyncClient, restricted_role: str):
    """Roles that are not self-service must be rejected (422 from Pydantic)."""
    payload = {
        **REGISTER_PAYLOAD,
        "email": f"{restricted_role.lower()}@example.com",
        "role": restricted_role,
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    # Pydantic rejects disallowed Literal values before the service layer is reached
    assert response.status_code == 422


async def test_register_weak_password(client: AsyncClient):
    payload = {**REGISTER_PAYLOAD, "email": "weak@example.com", "password": "short"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422  # Pydantic validation


# ── POST /login ───────────────────────────────────────────────────────────────


async def test_login_success(client: AsyncClient, registered_user_tokens):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_token_login_success_for_swagger_authorize(client: AsyncClient, registered_user_tokens):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, registered_user_tokens):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "WrongPass999"},
    )
    assert response.status_code == 401


async def test_login_nonexistent_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "SomePass123"},
    )
    assert response.status_code == 401


async def test_pending_vendor_login_is_forbidden(client: AsyncClient):
    payload = {
        **REGISTER_PAYLOAD,
        "email": "awaiting-vendor@example.com",
        "role": "VENDOR",
        "company_name": "Awaiting Vendor",
    }
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 403
    assert "waiting for Logistics Manager approval" in response.json()["detail"]


# ── POST /refresh ─────────────────────────────────────────────────────────────


async def test_refresh_success(client: AsyncClient, registered_user_tokens):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": registered_user_tokens["refresh_token"]},
    )
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    # New access token should differ from the original
    assert new_tokens["access_token"] != registered_user_tokens["access_token"]


async def test_refresh_with_access_token_fails(client: AsyncClient, registered_user_tokens):
    """Passing an access token as a refresh token must be rejected."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": registered_user_tokens["access_token"]},
    )
    assert response.status_code == 401


# ── POST /logout ──────────────────────────────────────────────────────────────


async def test_logout_success(client: AsyncClient, registered_user_tokens, redis_mock):
    token = registered_user_tokens["access_token"]
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"
    # Verify blacklist was written
    redis_mock.setex.assert_called_once()


async def test_logout_blacklisted_token_cannot_access_me(
    client: AsyncClient, registered_user_tokens, redis_mock
):
    """After logout, the same access token should return 401 on /me."""
    token = registered_user_tokens["access_token"]

    # First call logout
    await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Now simulate Redis returning the blacklist hit
    redis_mock.get.return_value = b"1"

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


# ── GET /me ───────────────────────────────────────────────────────────────────


async def test_get_me_success(client: AsyncClient, registered_user_tokens):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {registered_user_tokens['access_token']}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["role"] == "INDIVIDUAL"


async def test_get_me_no_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_get_me_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert response.status_code == 401


# ── PUT /me ───────────────────────────────────────────────────────────────────


async def test_update_me(client: AsyncClient, registered_user_tokens):
    response = await client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {registered_user_tokens['access_token']}"},
        json={"name": "Updated Name", "phone": "8888888888"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["phone"] == "8888888888"


# ── POST /change-password ─────────────────────────────────────────────────────


async def test_change_password_success(client: AsyncClient, registered_user_tokens):
    response = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {registered_user_tokens['access_token']}"},
        json={
            "current_password": REGISTER_PAYLOAD["password"],
            "new_password": "NewStrongPass456",
        },
    )
    assert response.status_code == 200
    assert "success" in response.json()["message"].lower()


async def test_change_password_wrong_current(client: AsyncClient, registered_user_tokens):
    response = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {registered_user_tokens['access_token']}"},
        json={"current_password": "WrongOldPass", "new_password": "NewPass123"},
    )
    assert response.status_code == 400


# ── POST /forgot-password ─────────────────────────────────────────────────────


async def test_forgot_password_always_200(client: AsyncClient):
    """Both existing and non-existing emails should return 200 (no enumeration)."""
    for email in [REGISTER_PAYLOAD["email"], "nobody@example.com"]:
        response = await client.post(
            "/api/v1/auth/forgot-password", json={"email": email}
        )
        assert response.status_code == 200


# ── POST /reset-password ──────────────────────────────────────────────────────


async def test_reset_password_invalid_token(client: AsyncClient, redis_mock):
    """No OTP stored for the email means the reset is refused."""
    redis_mock.get.return_value = None
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"email": REGISTER_PAYLOAD["email"], "token": "123456", "new_password": "ResetPass123"},
    )
    assert response.status_code == 400


async def test_reset_password_wrong_code(client: AsyncClient, redis_mock):
    redis_mock.get.return_value = b"654321"
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"email": REGISTER_PAYLOAD["email"], "token": "123456", "new_password": "ResetPass123"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid verification code"


async def test_reset_password_success(client: AsyncClient, redis_mock, registered_user_tokens):
    """A matching OTP replaces the password and is consumed."""
    redis_mock.get.return_value = b"123456"

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"email": REGISTER_PAYLOAD["email"], "token": "123456", "new_password": "BrandNewPass789"},
    )

    assert response.status_code == 200
    redis_mock.delete.assert_awaited()
    redis_mock.get.return_value = None
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "BrandNewPass789"},
    )
    assert login.status_code == 200


# ── GET /health ───────────────────────────────────────────────────────────────


async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
