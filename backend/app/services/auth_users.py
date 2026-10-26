"""Look up users and roles, check that a user may sign in, and build the token, login, registration and profile payloads auth returns."""

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsNotification
from app.models.user import Role, User
from app.schemas.auth import (
    LoginResponse,
    RegistrationResponse,
    TokenResponse,
    UserProfile,
)
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.username import normalize_username

# Approval states for accounts that need a manager's sign-off before they can sign in.
_APPROVAL_PENDING = "PENDING"
_APPROVAL_APPROVED = "APPROVED"
_APPROVAL_REJECTED = "REJECTED"


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
