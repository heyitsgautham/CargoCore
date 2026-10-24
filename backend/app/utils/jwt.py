import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"


def _create_token(
    data: dict[str, Any],
    expires_delta: timedelta,
    token_type: str,
) -> str:
    """Base token factory used by both access and refresh token helpers."""
    payload = data.copy()
    now = datetime.now(UTC)
    payload.update(
        {
            "iat": now,
            "exp": now + expires_delta,
            "jti": str(uuid.uuid4()),   # unique token ID for blacklisting
            "type": token_type,
        }
    )
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(data: dict[str, Any]) -> str:
    """Create a signed HS256 access JWT (expires in ACCESS_TOKEN_EXPIRE_MINUTES)."""
    return _create_token(
        data,
        timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access",
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a signed HS256 refresh JWT (expires in REFRESH_TOKEN_EXPIRE_DAYS)."""
    return _create_token(
        data,
        timedelta(days=settings.refresh_token_expire_days),
        token_type="refresh",
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT.

    Raises HTTP 401 on invalid signature, expiry, or malformed token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception
