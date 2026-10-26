"""Dispatcher manifests and fleet documents."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.schemas.logistics import (
    LogisticsDocumentCreate,
    LogisticsDocumentItem,
    LogisticsDocumentUpdateStatus,
    LogisticsManifestCreate,
    LogisticsManifestItem,
)
from app.services import logistics_service

router = APIRouter()


@router.get("/manifests", response_model=list[LogisticsManifestItem])
async def list_manifests(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.list_manifests(db)


@router.post("/manifests", response_model=LogisticsManifestItem, status_code=status.HTTP_201_CREATED)
async def create_manifest(
    data: LogisticsManifestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.create_manifest(db, data, created_by_id=user.id)


@router.post("/manifests/{manifest_id}/push", response_model=LogisticsManifestItem)
async def push_manifest(
    manifest_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.push_manifest(db, manifest_id)


@router.post("/documents", response_model=LogisticsDocumentItem, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: LogisticsDocumentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.create_document(db, data)


@router.put("/documents/{doc_id}/status", response_model=LogisticsDocumentItem)
async def update_document_status(
    doc_id: UUID,
    data: LogisticsDocumentUpdateStatus,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.update_document_status(db, doc_id, data)
