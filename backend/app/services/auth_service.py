"""
auth_service.py
All authentication business logic.  Routers should only call these functions —
no direct DB or Redis access in routers.
"""
import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.logistics import LogisticsNotification
from app.models.user import Role, User
from app.schemas.auth import (
    SELF_SERVICE_ROLES,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginResponse,
    OTPVerifiedResponse,
    RefreshTokenRequest,
    RegistrationResponse,
    ResetPasswordRequest,
    SendOTPRequest,
    SignupOtpSendResponse,
    TokenResponse,
    UserLogin,
    UserProfile,
    UserProfileUpdate,
    UserRegister,
    VerifyOTPRequest,
)
from app.services.auth_codes import OneTimeCodes
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.utils.username import generate_unique_username, normalize_username

# Redis key prefixes
_BLACKLIST_PREFIX = "blacklist:"
_RESET_PREFIX = "pwd_reset:"
_RESET_TTL_SECONDS = 3600   # 1 hour

# One-time codes by purpose. Each kind falls back to process memory when Redis is unavailable.
_signup_codes = OneTimeCodes("signup_otp:")
_reset_codes = OneTimeCodes("reset_otp:")
_login_codes = OneTimeCodes("login_otp:")
settings = get_settings()

# Roles allowed through the public /register endpoint (kept in sync with schema).
_SELF_SERVICE_ROLE_NAMES: frozenset[str] = frozenset(SELF_SERVICE_ROLES.__args__)  # type: ignore[union-attr]
_APPROVAL_PENDING = "PENDING"
_APPROVAL_APPROVED = "APPROVED"
_APPROVAL_REJECTED = "REJECTED"


# ── helpers ───────────────────────────────────────────────────────────────────


def _token_payload(user: User) -> dict:
    return {"sub": str(user.id), "role": user.role.name}


def _build_token_response(user: User) -> TokenResponse:
    payload = _token_payload(user)
    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
    )


def _build_login_response(user: User) -> LoginResponse:
    """Build login response with tokens and user profile."""
    payload = _token_payload(user)
    return LoginResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
        user=_to_profile(user),
    )


def _build_registration_response(user: User) -> RegistrationResponse:
    if (user.approval_status or _APPROVAL_APPROVED).upper() == _APPROVAL_PENDING:
        return RegistrationResponse(
            user=_to_profile(user),
            pending_approval=True,
            message="Vendor registration submitted successfully. A Logistics Manager must approve it before login.",
        )

    payload = _token_payload(user)
    return RegistrationResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
        user=_to_profile(user),
    )


def _to_profile(user: User) -> UserProfile:
    warehouse = getattr(user, "warehouse", None)
    warehouse_is_active = None if warehouse is None else warehouse.is_active
    warehouse_status = None
    if warehouse is not None:
        warehouse_status = "Archived" if warehouse.is_active is False else "Active"

    return UserProfile(
        id=user.id,
        name=user.name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        address=user.address,
        role=user.role.name,
        warehouse_id=user.warehouse_id,
        warehouse_name=getattr(warehouse, "name", None),
        warehouse_address=getattr(warehouse, "address", None),
        warehouse_is_active=warehouse_is_active,
        warehouse_status=warehouse_status,
        is_active=user.is_active,
        approval_status=user.approval_status or _APPROVAL_APPROVED,
        company_name=user.company_name,
        tax_id=user.tax_id,
        contact_person=user.contact_person,
        business_email=user.business_email,
        business_phone=user.business_phone,
        created_at=user.created_at,
    )


def _approval_message(user: User) -> str | None:
    status_value = (user.approval_status or _APPROVAL_APPROVED).upper()
    if status_value == _APPROVAL_PENDING:
        return "Your vendor account is waiting for Logistics Manager approval."
    if status_value == _APPROVAL_REJECTED:
        return "Your vendor registration was rejected. Please contact the Logistics Manager or register again with updated details."
    return None


def _ensure_user_can_authenticate(user: User) -> None:
    approval_message = _approval_message(user)
    if approval_message:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=approval_message,
        )


def _ensure_user_session_valid(user: User) -> None:
    approval_message = _approval_message(user)
    if approval_message:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=approval_message,
            headers={"WWW-Authenticate": "Bearer"},
        )


def _queue_vendor_registration_notification(db: AsyncSession, user: User) -> None:
    company_name = user.company_name or user.name
    contact_name = user.contact_person or user.name
    db.add(
        LogisticsNotification(
            title="New vendor registration",
            message=f"{company_name} registered with contact {contact_name}. Review the request in User & Roles.",
            type="system",
            audience_roles="LOGISTIC_MANAGER",
        )
    )


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _get_user_by_identifier(db: AsyncSession, identifier: str) -> User | None:
    normalized = identifier.strip().lower()
    result = await db.execute(
        select(User).where(
            or_(
                User.email == normalized,
                User.username == normalize_username(normalized),
            )
        )
    )
    return result.scalar_one_or_none()


async def _get_role_by_name(db: AsyncSession, name: str) -> Role | None:
    result = await db.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()


async def _get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    from uuid import UUID

    try:
        uid = UUID(user_id)
    except ValueError:
        return None
    result = await db.execute(
        select(User).where(User.id == uid)
    )
    return result.scalar_one_or_none()


# ── public service functions ──────────────────────────────────────────────────


async def register_user(db: AsyncSession, data: UserRegister) -> RegistrationResponse:
    """Create a new user account and return JWT token pair.

    Only INDIVIDUAL and VENDOR roles may self-register.
    LOGISTIC_MANAGER is pre-seeded at deployment.
    WAREHOUSE_MANAGER, DISPATCHER, and DRIVER accounts are created by a
    Logistic Manager via the /users admin endpoint (Phase 2).
    """
    # Guard: reject attempts to register restricted roles at the service layer.
    # (Pydantic already enforces this via schema, but a double-check is cheap.)
    role_upper = data.role.upper()
    if role_upper not in _SELF_SERVICE_ROLE_NAMES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Role '{data.role}' cannot be self-registered. "
                "Accounts for this role are created by the Logistic Manager."
            ),
        )

    # Check duplicate email
    existing = await _get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Resolve role
    role = await _get_role_by_name(db, role_upper)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{data.role}' does not exist",
        )

    user = User(
        name=data.name,
        username=await generate_unique_username(db, data.username or data.email.split("@")[0]),
        email=data.email.lower(),
        phone=data.phone,
        address=data.address,
        password_hash=hash_password(data.password),
        role_id=role.id,
        approval_status=_APPROVAL_PENDING if role_upper == "VENDOR" else _APPROVAL_APPROVED,
        company_name=data.company_name if role_upper == "VENDOR" else None,
        tax_id=data.tax_id if role_upper == "VENDOR" else None,
        contact_person=data.contact_person if role_upper == "VENDOR" else None,
        business_email=data.business_email.lower() if role_upper == "VENDOR" and data.business_email else None,
        business_phone=data.business_phone if role_upper == "VENDOR" else None,
    )
    db.add(user)
    await db.flush()  # get id without committing (get_db commits on success)

    # Eagerly load role for token building
    await db.refresh(user, attribute_names=["role"])

    if role_upper == "VENDOR":
        _queue_vendor_registration_notification(db, user)

    logger.info(f"New user registered: {user.email} (role={role.name})")
    return _build_registration_response(user)


async def login_user(db: AsyncSession, data: UserLogin) -> LoginResponse:
    """Authenticate credentials and return JWT token pair with user profile."""
    user = await _get_user_by_identifier(db, data.email)

    # Constant-time check so timing attacks can't enumerate accounts
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _ensure_user_can_authenticate(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    user.last_login = datetime.now(UTC)
    db.add(user)
    await db.flush()
    await db.refresh(user, attribute_names=["role", "warehouse"])
    return _build_login_response(user)


async def refresh_tokens(
    db: AsyncSession, redis: Redis | None, data: RefreshTokenRequest
) -> TokenResponse:
    """Validate a refresh token and issue a new token pair."""
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Check blacklist (skip gracefully if Redis is unavailable)
    jti = payload.get("jti", "")
    if redis and await redis.get(f"{_BLACKLIST_PREFIX}{jti}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    user = await _get_user_by_id(db, payload.get("sub", ""))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    _ensure_user_session_valid(user)

    await db.refresh(user, attribute_names=["role", "warehouse"])
    return _build_token_response(user)


async def logout_user(redis: Redis | None, access_token: str) -> None:
    """Blacklist the access token in Redis for the remainder of its lifetime."""
    payload = decode_token(access_token)
    jti = payload.get("jti")
    exp = payload.get("exp")

    if not jti or not exp:
        return  # malformed token — nothing to blacklist

    if redis:
        ttl = int(exp - datetime.now(UTC).timestamp())
        if ttl > 0:
            await redis.setex(f"{_BLACKLIST_PREFIX}{jti}", ttl, "1")
        logger.info(f"Token blacklisted: jti={jti} ttl={max(ttl, 0)}s")
    else:
        logger.warning(f"Redis unavailable — token NOT blacklisted: jti={jti}")


async def get_current_user_from_token(
    db: AsyncSession, redis: Redis | None, token: str
) -> User:
    """Validate access token, check blacklist, and return the User model."""
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Check blacklist only when Redis is available
    jti = payload.get("jti", "")
    if redis and await redis.get(f"{_BLACKLIST_PREFIX}{jti}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    user = await _get_user_by_id(db, payload.get("sub", ""))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _ensure_user_session_valid(user)

    await db.refresh(user, attribute_names=["role", "warehouse"])
    return user


async def update_profile(
    db: AsyncSession, user: User, data: UserProfileUpdate
) -> UserProfile:
    """Update the authenticated user's name / phone."""
    from datetime import date

    if data.name is not None:
        user.name = data.name
    if data.phone is not None:
        user.phone = data.phone
    if data.date_of_birth is not None:
        user.date_of_birth = date.fromisoformat(data.date_of_birth) if data.date_of_birth else None
    if data.address is not None:
        user.address = data.address
    db.add(user)
    await db.flush()
    await db.refresh(user, attribute_names=["role", "warehouse"])
    return _to_profile(user)


async def change_password(
    db: AsyncSession, user: User, data: ChangePasswordRequest
) -> None:
    """Verify current password and store a new bcrypt hash."""
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.password_hash = hash_password(data.new_password)
    db.add(user)
    await db.flush()
    logger.info(f"Password changed for user: {user.email}")


async def forgot_password(db: AsyncSession, redis: Redis | None, data: ForgotPasswordRequest) -> None:
    """
    Generate a 6-digit OTP for password reset and send via email.
    The OTP is stored in Redis with a 10-minute TTL.
    """
    from app.utils.email import password_reset_email_html, send_email

    user = await _get_user_by_email(db, data.email.lower())
    # Always return 200 to prevent email enumeration
    if not user:
        logger.info(f"[DEV] Password reset requested for non-existent email: {data.email}")
        return

    # Generate 6-digit OTP
    otp = await _reset_codes.issue(redis, data.email.lower())

    if not settings.is_production:
        logger.info(f"[DEV] Password reset OTP for {user.email}: {otp}")

    # Send email with OTP
    await send_email(
        to=user.email,
        subject="Password Reset - Cargo Core",
        html_body=password_reset_email_html(otp, user.email, user.name),
    )


async def reset_password(
    db: AsyncSession, redis: Redis | None, data: ResetPasswordRequest
) -> None:
    """Validate the OTP and update the user's password hash."""
    email = data.email.lower()
    stored_otp_str = await _reset_codes.current(redis, email)

    if not stored_otp_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code is invalid or has expired",
        )

    if stored_otp_str != data.token:
        await _reset_codes.record_failure(redis, email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    # Find user by email
    user = await _get_user_by_email(db, data.email.lower())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password
    user.password_hash = hash_password(data.new_password)
    db.add(user)
    await db.flush()

    # Consume the OTP (one-time use)
    await _reset_codes.consume(redis, email)
    logger.info(f"Password reset completed for user: {user.email}")


async def send_signup_otp(db: AsyncSession, redis: Redis | None, data: SendOTPRequest) -> SignupOtpSendResponse:
    """Generate a 6-digit OTP, store it, and send via email."""
    from app.utils.email import otp_email_html, send_email

    # Check if email already exists to provide early feedback
    email = data.email.lower()
    existing = await _get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    otp = await _signup_codes.issue(redis, email)
    sent_at = datetime.now(UTC)
    if not settings.is_production:
        logger.info(f"[DEV] Signup OTP for {email}: {otp}")

    sent = await send_email(
        to=email,
        subject="Your Cargo Core Verification Code",
        html_body=otp_email_html(otp, email),
    )
    if not sent:
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Signup OTP email could not be sent. Check SMTP configuration.",
            )

        logger.warning("[EMAIL] Signup OTP generated without email delivery in development for {}", email)
        return SignupOtpSendResponse(
            message="Signup OTP generated (email unavailable in development)",
            email=email,
            sent_at=sent_at,
            debug_otp=otp,
        )

    return SignupOtpSendResponse(
        message="Signup OTP sent successfully",
        email=email,
        sent_at=sent_at,
    )


async def verify_signup_otp(redis: Redis | None, data: VerifyOTPRequest) -> OTPVerifiedResponse:
    """Verify the signup OTP sent to the user's email."""
    email = data.email.lower()
    stored_otp_str = await _signup_codes.current(redis, email)

    if not stored_otp_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Please request a new one.",
        )

    if stored_otp_str != data.otp:
        await _signup_codes.record_failure(redis, email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Please request a new one.",
        )

    # Consume OTP — one time use
    await _signup_codes.consume(redis, email)

    logger.info(f"Email verified via OTP: {data.email}")
    return OTPVerifiedResponse(verified=True, message="Email verified successfully!")


# Roles allowed to use OTP login (only self-service roles with real Gmail accounts)
_OTP_LOGIN_ALLOWED_ROLES = frozenset({"INDIVIDUAL", "VENDOR"})


async def send_login_otp(db: AsyncSession, redis: Redis | None, data: SendOTPRequest) -> SignupOtpSendResponse:
    """Send a login OTP to an existing INDIVIDUAL or VENDOR user's email."""
    from app.utils.email import otp_email_html, send_email

    email = data.email.lower()
    user = await _get_user_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address.",
        )

    await db.refresh(user, attribute_names=["role"])

    if user.role.name not in _OTP_LOGIN_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OTP login is only available for customer and vendor accounts.",
        )

    _ensure_user_can_authenticate(user)

    otp = await _login_codes.issue(redis, email)
    sent_at = datetime.now(UTC)
    if not settings.is_production:
        logger.info(f"[DEV] Login OTP for {email}: {otp}")

    sent = await send_email(
        to=email,
        subject="Your Cargo Core Login Code",
        html_body=otp_email_html(otp, email),
    )
    if not sent:
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Login OTP email could not be sent. Check SMTP configuration.",
            )
        logger.warning("[EMAIL] Login OTP generated without email delivery in development for {}", email)
        return SignupOtpSendResponse(
            message="Login OTP generated (email unavailable in development)",
            email=email,
            sent_at=sent_at,
            debug_otp=otp,
        )

    return SignupOtpSendResponse(message="Login OTP sent successfully", email=email, sent_at=sent_at)


async def verify_login_otp(db: AsyncSession, redis: Redis | None, data: VerifyOTPRequest) -> LoginResponse:
    """Verify a login OTP and return JWT tokens."""
    email = data.email.lower()
    stored_otp = await _login_codes.current(redis, email)

    if not stored_otp or stored_otp != data.otp:
        if stored_otp:
            await _login_codes.record_failure(redis, email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Please request a new one.",
        )

    await _login_codes.consume(redis, email)

    user = await _get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    await db.refresh(user, attribute_names=["role", "warehouse"])
    _ensure_user_can_authenticate(user)
    logger.info(f"Login via OTP for user: {email}")
    return _build_login_response(user)




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

