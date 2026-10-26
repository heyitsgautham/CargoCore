"""One-time codes for signup, login and password reset."""

from unittest.mock import AsyncMock

import pytest
from loguru import logger

from app.main import app
from app.services import auth_codes, auth_service
from app.utils.redis import get_redis
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
    monkeypatch.setattr(auth_codes.secrets, "randbelow", lambda bound: 4207 if bound == 1_000_000 else 0)

    assert auth_codes.new_code() == "004207"


class FakeRedis:
    """The few Redis commands the code store uses, kept in a dict."""

    def __init__(self):
        self.data = {}

    async def get(self, key):
        value = self.data.get(key)
        return value.encode() if isinstance(value, str) else value

    async def setex(self, key, _ttl, value):
        self.data[key] = value

    async def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)

    async def incr(self, key):
        self.data[key] = int(self.data.get(key, 0)) + 1
        return self.data[key]

    async def expire(self, _key, _ttl):
        return True


@pytest.fixture()
def fake_redis():
    redis = FakeRedis()

    async def override():
        yield redis

    app.dependency_overrides[get_redis] = override
    return redis


async def _send_login_code(client) -> str:
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post("/api/v1/auth/send-login-otp", json={"email": REGISTER_PAYLOAD["email"]})
    assert response.status_code == 200
    return response.json()["debug_otp"]


def _wrong(code: str) -> str:
    return "000000" if code != "000000" else "111111"


async def test_login_code_dies_after_five_wrong_guesses(client, fake_redis):
    code = await _send_login_code(client)
    verify = {"email": REGISTER_PAYLOAD["email"]}

    for _ in range(auth_codes.MAX_FAILED_ATTEMPTS):
        response = await client.post("/api/v1/auth/verify-login-otp", json={**verify, "otp": _wrong(code)})
        assert response.status_code == 400

    response = await client.post("/api/v1/auth/verify-login-otp", json={**verify, "otp": code})
    assert response.status_code == 400


async def test_login_code_still_works_after_fewer_wrong_guesses(client, fake_redis):
    code = await _send_login_code(client)
    verify = {"email": REGISTER_PAYLOAD["email"]}

    for _ in range(auth_codes.MAX_FAILED_ATTEMPTS - 1):
        await client.post("/api/v1/auth/verify-login-otp", json={**verify, "otp": _wrong(code)})

    response = await client.post("/api/v1/auth/verify-login-otp", json={**verify, "otp": code})
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_a_new_code_resets_the_guess_count(client, fake_redis):
    first = await _send_login_code(client)
    verify = {"email": REGISTER_PAYLOAD["email"]}
    for _ in range(auth_codes.MAX_FAILED_ATTEMPTS - 1):
        await client.post("/api/v1/auth/verify-login-otp", json={**verify, "otp": _wrong(first)})

    second = (await client.post("/api/v1/auth/send-login-otp", json=verify)).json()["debug_otp"]
    await client.post("/api/v1/auth/verify-login-otp", json={**verify, "otp": _wrong(second)})

    response = await client.post("/api/v1/auth/verify-login-otp", json={**verify, "otp": second})
    assert response.status_code == 200


async def test_signup_code_dies_after_five_wrong_guesses(client, fake_redis):
    email = "new.person@example.com"
    code = (await client.post("/api/v1/auth/send-otp", json={"email": email})).json()["debug_otp"]

    for _ in range(auth_codes.MAX_FAILED_ATTEMPTS):
        await client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": _wrong(code)})

    response = await client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": code})
    assert response.status_code == 400


async def test_reset_code_dies_after_five_wrong_guesses(client, fake_redis, email_delivered):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    await client.post("/api/v1/auth/forgot-password", json={"email": REGISTER_PAYLOAD["email"]})
    code = fake_redis.data[f"reset_otp:{REGISTER_PAYLOAD['email']}"]
    reset = {"email": REGISTER_PAYLOAD["email"], "new_password": "ResetPass123"}

    for _ in range(auth_codes.MAX_FAILED_ATTEMPTS):
        response = await client.post("/api/v1/auth/reset-password", json={**reset, "token": _wrong(code)})
        assert response.json()["detail"] == "Invalid verification code"

    response = await client.post("/api/v1/auth/reset-password", json={**reset, "token": code})
    assert response.status_code == 400
    assert response.json()["detail"] == "Reset code is invalid or has expired"


async def test_memory_fallback_counts_guesses_too():
    codes = auth_codes.OneTimeCodes("test_otp:")
    code = await codes.issue(None, "a@example.com")

    for _ in range(auth_codes.MAX_FAILED_ATTEMPTS - 1):
        await codes.record_failure(None, "a@example.com")
    assert await codes.current(None, "a@example.com") == code

    await codes.record_failure(None, "a@example.com")
    assert await codes.current(None, "a@example.com") is None
