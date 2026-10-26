"""Sign in or sign up with a Google ID token."""

import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import Role, User
from app.schemas.auth import (
    GoogleLoginRequest,
    LoginResponse,
)
from app.services.auth_users import (
    _APPROVAL_APPROVED,
    _APPROVAL_PENDING,
    _build_login_response,
    _ensure_user_can_authenticate,
    _queue_vendor_registration_notification,
)
from app.utils.hashing import hash_password
from app.utils.username import generate_unique_username

settings = get_settings()


async def google_login_or_register(db: AsyncSession, redis: Redis, data: GoogleLoginRequest) -> LoginResponse:
    try:
        if not settings.google_client_id:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google login is not configured on the server.",
            )

        idinfo = id_token.verify_oauth2_token(
            data.credential,
            google_requests.Request(),
            settings.google_client_id,
            clock_skew_in_seconds=10,
        )

        if not idinfo.get("email_verified", False):
            raise HTTPException(status_code=400, detail="Google account email is not verified")
        
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
        # check if user exists
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalars().first()

        if user:
            # Allow existing users to log in with Google
            _ensure_user_can_authenticate(user)
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated",
                )
            await db.refresh(user, attribute_names=["role", "warehouse"])
            return _build_login_response(user)
        else:
            # register flow
            role_result = await db.execute(select(Role).where(Role.name == data.role.upper()))
            role = role_result.scalars().first()
            if not role:
                raise HTTPException(status_code=400, detail='Role not found.')
                
            dummy_password = secrets.token_urlsafe(16)
            hashed_pwd = hash_password(dummy_password)
            user = User(
                name=name,
                username=await generate_unique_username(db, email.split('@')[0]),
                email=email,
                phone="",
                address="",
                password_hash=hashed_pwd,
                role_id=role.id,
                is_active=True,
                approval_status=_APPROVAL_PENDING if role.name == "VENDOR" else _APPROVAL_APPROVED,
                company_name=name if role.name == "VENDOR" else None,
                contact_person=name if role.name == "VENDOR" else None,
                business_email=email if role.name == "VENDOR" else None,
            )
            db.add(user)
            if role.name == "VENDOR":
                _queue_vendor_registration_notification(db, user)
            await db.commit()
            await db.refresh(user, attribute_names=["role"])

            if role.name == "VENDOR":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vendor registration submitted successfully. A Logistics Manager must approve it before login.",
                )

        user.last_login = datetime.now(UTC)
        db.add(user)
        await db.flush()
        return _build_login_response(user)

    except ValueError as e:
        logger.warning(
            "Google token verification failed: {} | client_id={} | token_prefix={}",
            str(e),
            settings.google_client_id,
            data.credential[:24] if data.credential else "",
        )
        raise HTTPException(status_code=400, detail=f"Invalid Google token: {str(e)}") from e
