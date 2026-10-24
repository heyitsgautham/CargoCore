import re
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.logistics import LogisticsDriverProfile
from app.models.order import Order
from app.models.user import Role, User
from app.models.vendor import VendorRecurringRule
from app.models.warehouse import Warehouse
from app.schemas.users import (
    AssignRoleRequest,
    AssignWarehouseRequest,
    UserAdminCreate,
    UserAdminResponse,
    UserAdminUpdate,
    UserListResponse,
)
from app.utils.hashing import hash_password
from app.utils.username import generate_unique_username, normalize_username

WAREHOUSE_SCOPED_ROLES = {"WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER"}
_DRIVER_PIN_RE = re.compile(r"^\d{4}$")
SOFT_DELETED_APPROVAL_NOTE = "__SOFT_DELETED__"
_VENDOR_INBOUND_CLEANUP_SUBSTATUSES = {"AWAITING_INBOUND", "ON_HOLD"}


async def _get_user(db: AsyncSession, user_id: UUID) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def _get_role(db: AsyncSession, role_name: str) -> Role:
    result = await db.execute(select(Role).where(Role.name == role_name.upper()))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


async def _ensure_active_warehouse(db: AsyncSession, warehouse_id: UUID) -> Warehouse:
    warehouse = (
        await db.execute(
            select(Warehouse).where(
                Warehouse.id == warehouse_id,
                Warehouse.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot assign warehouse-scoped users to an archived warehouse",
        )
    return warehouse


def _driver_email_fallback(email: str) -> str:
    local_part = (email or "").split("@")[0].strip()
    return local_part or "driver"


def _resolve_user_credentials(data: UserAdminCreate) -> tuple[str, str, str]:
    role_name = str(data.role or "").strip().upper()
    raw_username = (data.username or "").strip()
    raw_password = (data.password or "").strip()

    if role_name == "DRIVER":
        driver_id = raw_username or _driver_email_fallback(data.email)
        if not _DRIVER_PIN_RE.fullmatch(raw_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver PIN must be exactly 4 digits",
            )
        return role_name, driver_id, raw_password

    if len(raw_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    return role_name, raw_username, raw_password


def _to_response(user: User) -> UserAdminResponse:
    return UserAdminResponse(
        id=user.id,
        name=user.name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        role=user.role.name,
        warehouse_id=user.warehouse_id,
        is_active=user.is_active,
        approval_status=user.approval_status,
        approval_note=user.approval_note,
        approval_reviewed_at=user.approval_reviewed_at,
        company_name=user.company_name,
        tax_id=user.tax_id,
        contact_person=user.contact_person,
        business_email=user.business_email,
        business_phone=user.business_phone,
        last_login=user.last_login,
        created_at=user.created_at,
    )


async def _sync_warehouse_manager_assignment(
    db: AsyncSession,
    user: User,
    role_name: str,
    warehouse_id: UUID | None,
) -> None:
    if role_name != "WAREHOUSE_MANAGER":
        return

    managed_warehouses = (
        await db.execute(select(Warehouse).where(Warehouse.manager_id == user.id))
    ).scalars().all()

    for warehouse in managed_warehouses:
        if warehouse.id != warehouse_id:
            warehouse.manager_id = None
            db.add(warehouse)

    if warehouse_id is None:
        return

    warehouse = (
        await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    ).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    warehouse.manager_id = user.id
    db.add(warehouse)


async def list_users(
    db: AsyncSession,
    page: int,
    page_size: int,
    role: str | None = None,
    warehouse_id: UUID | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> UserListResponse:
    filters = [
        or_(
            User.approval_note.is_(None),
            User.approval_note != SOFT_DELETED_APPROVAL_NOTE,
        )
    ]
    if role:
        filters.append(Role.name == role.upper())
    if warehouse_id:
        filters.append(User.warehouse_id == warehouse_id)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    if search:
        like_pattern = f"%{search.strip()}%"
        filters.append((User.name.ilike(like_pattern)) | (User.email.ilike(like_pattern)) | (User.username.ilike(like_pattern)))

    total_query = select(func.count(User.id)).join(Role)
    data_query = (
        select(User)
        .join(Role)
        .options(selectinload(User.role))
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if filters:
        total_query = total_query.where(*filters)
        data_query = data_query.where(*filters)

    total = (await db.execute(total_query)).scalar_one()
    users = (await db.execute(data_query)).scalars().all()

    return UserListResponse(
        items=[_to_response(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )


def _require_warehouse_for_role(role_name: str, warehouse_id: UUID | None) -> None:
    if role_name in WAREHOUSE_SCOPED_ROLES and warehouse_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"warehouse_id is required for {role_name} users",
        )


async def create_user(db: AsyncSession, data: UserAdminCreate) -> UserAdminResponse:
    existing = await db.execute(select(User).where(User.email == data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    role_name, requested_username, raw_password = _resolve_user_credentials(data)

    normalized_username = normalize_username(requested_username or data.email.split("@")[0])
    if requested_username:
        existing_username = await db.execute(select(User).where(User.username == normalized_username))
        if existing_username.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already in use")
    else:
        normalized_username = await generate_unique_username(db, normalized_username)

    role = await _get_role(db, role_name)
    _require_warehouse_for_role(role.name, data.warehouse_id)
    if role.name in WAREHOUSE_SCOPED_ROLES and data.warehouse_id is not None:
        await _ensure_active_warehouse(db, data.warehouse_id)
    user = User(
        name=data.name,
        username=normalized_username,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(raw_password),
        role_id=role.id,
        warehouse_id=data.warehouse_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    if role.name == "DRIVER":
        db.add(LogisticsDriverProfile(
            user_id=user.id,
            warehouse_id=data.warehouse_id,
            status="Active",
            efficiency_score=85,
            avatar_color="bg-blue-600",
        ))
    await _sync_warehouse_manager_assignment(db, user, role.name, data.warehouse_id)
    await db.refresh(user, attribute_names=["role"])
    return _to_response(user)


async def get_user_detail(db: AsyncSession, user_id: UUID) -> UserAdminResponse:
    user = await _get_user(db, user_id)
    return _to_response(user)


async def update_user(db: AsyncSession, user_id: UUID, data: UserAdminUpdate) -> UserAdminResponse:
    user = await _get_user(db, user_id)
    if data.name is not None:
        user.name = data.name
    if data.phone is not None:
        user.phone = data.phone
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.approval_note is not None:
        user.approval_note = data.approval_note
    if data.approval_status is not None:
        approval_status = data.approval_status.strip().upper()
        if approval_status not in {"PENDING", "APPROVED", "REJECTED"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid approval status")
        if user.role.name != "VENDOR":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approval status can only be updated for vendor users")
        user.approval_status = approval_status
        user.approval_reviewed_at = datetime.now(UTC)
        if data.is_active is None:
            user.is_active = approval_status != "REJECTED"

    db.add(user)
    await db.flush()
    await db.refresh(user, attribute_names=["role"])
    return _to_response(user)


async def soft_delete_user(db: AsyncSession, user_id: UUID) -> None:
    user = await _get_user(db, user_id)
    if user.role.name == "LOGISTIC_MANAGER":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logistic manager account cannot be deleted",
        )

    await _sync_warehouse_manager_assignment(db, user, user.role.name, None)
    user.is_active = False
    user.approval_note = SOFT_DELETED_APPROVAL_NOTE

    if user.role.name == "VENDOR":
        recurring_rules = (
            await db.execute(
                select(VendorRecurringRule).where(
                    VendorRecurringRule.vendor_id == user.id,
                    VendorRecurringRule.active.is_(True),
                )
            )
        ).scalars().all()
        for rule in recurring_rules:
            rule.active = False
            db.add(rule)

        pending_inbound_orders = (
            await db.execute(
                select(Order).where(
                    Order.customer_id == user.id,
                    Order.order_type == "VENDOR",
                    Order.status.notin_(["DELIVERED", "CANCELLED", "CLOSED"]),
                    Order.warehouse_substatus.in_(_VENDOR_INBOUND_CLEANUP_SUBSTATUSES),
                )
            )
        ).scalars().all()
        for order in pending_inbound_orders:
            order.status = "CANCELLED"
            order.cancel_reason = "Vendor account deleted"
            db.add(order)

    db.add(user)
    await db.flush()


async def assign_role(db: AsyncSession, user_id: UUID, data: AssignRoleRequest) -> UserAdminResponse:
    user = await _get_user(db, user_id)
    role = await _get_role(db, data.role)
    _require_warehouse_for_role(role.name, user.warehouse_id)
    if role.name in WAREHOUSE_SCOPED_ROLES and user.warehouse_id is not None:
        await _ensure_active_warehouse(db, user.warehouse_id)
    user.role_id = role.id
    db.add(user)
    await db.flush()
    await _sync_warehouse_manager_assignment(db, user, role.name, user.warehouse_id)
    await db.refresh(user, attribute_names=["role"])
    return _to_response(user)


async def assign_warehouse(
    db: AsyncSession,
    user_id: UUID,
    data: AssignWarehouseRequest,
) -> UserAdminResponse:
    user = await _get_user(db, user_id)
    if user.role.name in WAREHOUSE_SCOPED_ROLES:
        _require_warehouse_for_role(user.role.name, data.warehouse_id)
        if data.warehouse_id is not None:
            await _ensure_active_warehouse(db, data.warehouse_id)
    user.warehouse_id = data.warehouse_id
    db.add(user)
    await db.flush()
    await _sync_warehouse_manager_assignment(db, user, user.role.name, data.warehouse_id)
    await db.refresh(user, attribute_names=["role"])
    return _to_response(user)
