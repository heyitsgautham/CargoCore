"""
auth_service.py
All authentication business logic.  Routers should only call these functions —
no direct DB or Redis access in routers.
"""
from datetime import UTC, datetime

from fastapi import HTTPException, status
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.schemas.auth import (
    SELF_SERVICE_ROLES,
    ChangePasswordRequest,
    ForgotPasswordRequest,
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

# Google sign-in lives in auth_google; the router keeps calling it through here.
from app.services.auth_google import (
    google_login_or_register as google_login_or_register,
)
from app.services.auth_users import (
    _APPROVAL_APPROVED,
    _APPROVAL_PENDING,
    _build_login_response,
    _build_registration_response,
    _build_token_response,
    _ensure_user_can_authenticate,
    _ensure_user_session_valid,
    _get_role_by_name,
    _get_user_by_email,
    _get_user_by_id,
    _get_user_by_identifier,
    _queue_vendor_registration_notification,
    _to_profile,
)
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt import decode_token
from app.utils.username import generate_unique_username

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


