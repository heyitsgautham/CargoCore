from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginResponse,
    MessageResponse,
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
from app.services import auth_service
from app.utils.redis import get_redis

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Self-service sign-up (Individual & Vendor only)",
    description=(
        "Creates a new account for **INDIVIDUAL** or **VENDOR** roles only. "
        "Logistic Manager is pre-seeded at deployment. "
        "Warehouse Manager, Dispatcher, and Driver accounts are provisioned "
        "by the Logistic Manager via the /users admin endpoint."
    ),
)
async def register(
    data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    return await auth_service.register_user(db, data)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Issue JWT tokens with user profile",
)
async def login(
    data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    return await auth_service.login_user(db, data)


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Issue OAuth2 bearer token for Swagger UI",
    description=(
        "Form-based OAuth2 password flow endpoint used by Swagger UI's "
        "`Authorize` dialog. Enter your email or username in the `username` "
        "field. Use `/api/v1/auth/login` if you need the JSON response that "
        "also includes the user profile."
    ),
)
async def token_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    login_response = await auth_service.login_user(
        db,
        UserLogin(email=form_data.username, password=form_data.password),
    )
    return TokenResponse(
        access_token=login_response.access_token,
        refresh_token=login_response.refresh_token,
        token_type=login_response.token_type,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh(
    data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    return await auth_service.refresh_tokens(db, redis, data)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Invalidate access token via Redis blacklist",
)
async def logout(
    redis: Annotated[Redis, Depends(get_redis)],
    authorization: Annotated[str | None, Header()] = None,
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()
    await auth_service.logout_user(redis, token)
    return MessageResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
)
async def get_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await db.refresh(current_user, attribute_names=["warehouse", "role"])
    warehouse = current_user.warehouse
    return UserProfile(
        id=current_user.id,
        name=current_user.name,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        address=current_user.address,
        role=current_user.role.name,
        warehouse_id=current_user.warehouse_id,
        warehouse_name=warehouse.name if warehouse else None,
        warehouse_address=warehouse.address if warehouse else None,
        warehouse_is_active=warehouse.is_active if warehouse else None,
        warehouse_status="Archived" if warehouse and warehouse.is_active is False else ("Active" if warehouse else None),
        is_active=current_user.is_active,
        approval_status=current_user.approval_status,
        company_name=current_user.company_name,
        tax_id=current_user.tax_id,
        contact_person=current_user.contact_person,
        business_email=current_user.business_email,
        business_phone=current_user.business_phone,
        created_at=current_user.created_at,
    )


@router.put(
    "/me",
    response_model=UserProfile,
    summary="Update current user profile",
)
async def update_me(
    data: UserProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await auth_service.update_profile(db, current_user, data)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
)
async def change_password(
    data: ChangePasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await auth_service.change_password(db, current_user, data)
    return MessageResponse(message="Password changed successfully")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset email",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    await auth_service.forgot_password(db, redis, data)
    return MessageResponse(
        message="If that email is registered, a reset link has been sent"
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Confirm password reset with token",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    await auth_service.reset_password(db, redis, data)
    return MessageResponse(message="Password has been reset successfully")


@router.post(
    "/send-otp",
    response_model=SignupOtpSendResponse,
    summary="Send email verification OTP for signup",
)
async def send_otp(
    data: SendOTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    return await auth_service.send_signup_otp(db, redis, data)


@router.post(
    "/verify-otp",
    response_model=OTPVerifiedResponse,
    summary="Verify email OTP before completing signup",
)
async def verify_otp(
    data: VerifyOTPRequest,
    redis: Annotated[Redis, Depends(get_redis)],
):
    return await auth_service.verify_signup_otp(redis, data)

@router.post(
    "/send-login-otp",
    response_model=SignupOtpSendResponse,
    summary="Send login OTP to existing customer or vendor email",
)
async def send_login_otp(
    data: SendOTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    return await auth_service.send_login_otp(db, redis, data)


@router.post(
    "/verify-login-otp",
    response_model=LoginResponse,
    summary="Verify login OTP and issue JWT tokens",
)
async def verify_login_otp(
    data: VerifyOTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    return await auth_service.verify_login_otp(db, redis, data)


@router.post(
    '/google-login',
    response_model=LoginResponse,
    summary='Login or Register with Google',
)
async def google_login(
    data: GoogleLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    return await auth_service.google_login_or_register(db, redis, data)

