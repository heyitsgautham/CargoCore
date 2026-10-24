from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.utils.jwt import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_token,
    try_decode_token,
)

SECRET = get_settings().secret_key


def test_access_token_round_trip_keeps_claims_and_marks_type() -> None:
    token = create_access_token({"sub": "user-1", "role": "DRIVER"})

    payload = decode_token(token)

    assert payload["sub"] == "user-1"
    assert payload["role"] == "DRIVER"
    assert payload["type"] == "access"
    assert payload["exp"] > payload["iat"]


def test_refresh_token_is_typed_and_outlives_the_access_token() -> None:
    access = decode_token(create_access_token({"sub": "u"}))
    refresh = decode_token(create_refresh_token({"sub": "u"}))

    assert refresh["type"] == "refresh"
    assert refresh["exp"] > access["exp"]


def test_each_token_gets_a_unique_jti_for_blacklisting() -> None:
    first = decode_token(create_access_token({"sub": "u"}))
    second = decode_token(create_access_token({"sub": "u"}))

    assert first["jti"] != second["jti"]


def test_expired_token_is_rejected_with_401() -> None:
    past = datetime.now(UTC) - timedelta(hours=2)
    token = jwt.encode(
        {"sub": "u", "iat": past, "exp": past + timedelta(minutes=5)},
        SECRET,
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_token_signed_with_another_secret_is_rejected() -> None:
    token = jwt.encode({"sub": "u"}, "not-the-server-secret", algorithm=ALGORITHM)

    assert try_decode_token(token) is None
    with pytest.raises(HTTPException):
        decode_token(token)


def test_unsigned_alg_none_token_is_rejected() -> None:
    token = jwt.encode({"sub": "admin"}, key=None, algorithm="none")

    assert try_decode_token(token) is None


@pytest.mark.parametrize("token", [None, "", "not-a-jwt", "a.b.c"])
def test_missing_or_malformed_tokens_decode_to_none(token) -> None:
    assert try_decode_token(token) is None
