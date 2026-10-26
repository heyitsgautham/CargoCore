"""One-time codes for signup, login and password reset."""

from unittest.mock import AsyncMock

import pytest
from loguru import logger

from app.services import auth_service
from tests.conftest import REGISTER_PAYLOAD


@pytest.fixture()
def captured_messages():
    messages = []
    sink = logger.add(lambda message: messages.append(message.record["message"]), level="DEBUG")
    yield messages
    logger.remove(sink)


@pytest.fixture()
def email_delivered(monkeypatch):
    monkeypatch.setattr("app.utils.email.send_email", AsyncMock(return_value=True))


def _stored_code(redis_mock) -> str:
    """The code the service wrote to Redis with setex(key, ttl, code)."""
    return redis_mock.setex.await_args.args[2]


@pytest.mark.parametrize("app_env", ["production", "development"])
async def test_reset_code_reaches_the_log_only_outside_production(
    client, redis_mock, registered_user_tokens, captured_messages, email_delivered, monkeypatch, app_env
):
    monkeypatch.setattr(auth_service.settings, "app_env", app_env)

    response = await client.post("/api/v1/auth/forgot-password", json={"email": REGISTER_PAYLOAD["email"]})

    assert response.status_code == 200
    code = _stored_code(redis_mock)
    logged = any(code in message for message in captured_messages)
    assert logged is (app_env != "production")


async def test_login_code_stays_out_of_production_logs(
    client, redis_mock, captured_messages, email_delivered, monkeypatch
):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    monkeypatch.setattr(auth_service.settings, "app_env", "production")

    response = await client.post("/api/v1/auth/send-login-otp", json={"email": REGISTER_PAYLOAD["email"]})

    assert response.status_code == 200
    assert "debug_otp" not in response.json() or response.json()["debug_otp"] is None
    code = _stored_code(redis_mock)
    assert not any(code in message for message in captured_messages)


async def test_signup_code_stays_out_of_production_logs(client, redis_mock, captured_messages, email_delivered, monkeypatch):
    monkeypatch.setattr(auth_service.settings, "app_env", "production")

    response = await client.post("/api/v1/auth/send-otp", json={"email": "new.person@example.com"})

    assert response.status_code == 200
    code = _stored_code(redis_mock)
    assert not any(code in message for message in captured_messages)


def test_codes_are_six_digits_from_the_secrets_module(monkeypatch):
    monkeypatch.setattr(auth_service.secrets, "randbelow", lambda bound: 4207 if bound == 1_000_000 else 0)

    assert auth_service._new_otp() == "004207"
