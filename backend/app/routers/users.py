from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.schemas.auth import MessageResponse
from app.schemas.users import (
    AssignRoleRequest,
    AssignWarehouseRequest,
    UserAdminCreate,
    UserAdminResponse,
    UserAdminUpdate,
    UserListResponse,
)
from app.services import users_service

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: str | None = Query(default=None),
    warehouse_id: UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
):
    return await users_service.list_users(
        db=db,
        page=page,
        page_size=page_size,
        role=role,
        warehouse_id=warehouse_id,
        is_active=is_active,
        search=search,
    )


@router.post("", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserAdminCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await users_service.create_user(db, data)


@router.get("/{user_id}", response_model=UserAdminResponse)
async def get_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await users_service.get_user_detail(db, user_id)


@router.put("/{user_id}", response_model=UserAdminResponse)
async def update_user(
    user_id: UUID,
    data: UserAdminUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await users_service.update_user(db, user_id, data)


@router.delete("/{user_id}", response_model=MessageResponse)
async def soft_delete_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    await users_service.soft_delete_user(db, user_id)
    return MessageResponse(message="User deactivated")


@router.post("/{user_id}/assign-role", response_model=UserAdminResponse)
async def assign_role(
    user_id: UUID,
    data: AssignRoleRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await users_service.assign_role(db, user_id, data)


@router.post("/{user_id}/assign-warehouse", response_model=UserAdminResponse)
async def assign_warehouse(
    user_id: UUID,
    data: AssignWarehouseRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await users_service.assign_warehouse(db, user_id, data)
