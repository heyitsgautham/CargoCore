"""Return grading, zone metrics and warehouse performance."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.warehouse_operations import (
    PerformanceResponse,
    ReturnGradingCreate,
    ReturnGradingListResponse,
    ReturnGradingResponse,
    ReturnGradingUpdate,
    ZoneMetricsCreate,
    ZoneMetricsListResponse,
    ZoneMetricsResponse,
)
from app.services import warehouse_operations_service as ops_service

router = APIRouter()


# ======================
# Returns / Grading Endpoints
# ======================

@router.get("/returns", response_model=ReturnGradingListResponse)
async def list_return_gradings(
    warehouse_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
    status_filter: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Get all return gradings for a warehouse."""
    return await ops_service.get_return_gradings(db, warehouse_id, status_filter, page, page_size)


@router.post("/returns", response_model=ReturnGradingResponse, status_code=status.HTTP_201_CREATED)
async def create_return_grading(
    warehouse_id: UUID,
    data: ReturnGradingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Create a new return grading."""
    return await ops_service.create_return_grading(db, warehouse_id, data, graded_by=user.id)


@router.put("/returns/{grading_id}", response_model=ReturnGradingResponse)
async def update_return_grading(
    warehouse_id: UUID,
    grading_id: UUID,
    data: ReturnGradingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Update a return grading."""
    return await ops_service.update_return_grading(db, warehouse_id, grading_id, data)


@router.post("/returns/{grading_id}/photo", response_model=MessageResponse)
async def upload_damage_photo(
    warehouse_id: UUID,
    grading_id: UUID,
    file: UploadFile = File(...),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))] = None,
):
    """Upload a damage photo for a return grading."""
    photo_url = await ops_service.upload_damage_photo(db, warehouse_id, grading_id, file)
    return MessageResponse(message=f"Photo uploaded successfully: {photo_url[:50]}...")


@router.post("/returns/{grading_id}/complete", response_model=ReturnGradingResponse)
async def complete_return_grading(
    warehouse_id: UUID,
    grading_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Mark a return grading as completed."""
    return await ops_service.complete_return_grading(db, warehouse_id, grading_id, graded_by=user.id)


# ======================
# Zone Metrics Endpoints
# ======================

@router.get("/zones/{zone_id}/metrics", response_model=ZoneMetricsListResponse)
async def get_zone_metrics(
    warehouse_id: UUID,
    zone_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
):
    """Get metrics for a specific zone."""
    return await ops_service.get_zone_metrics(db, warehouse_id, zone_id, date_from, date_to)


@router.post("/zones/metrics", response_model=ZoneMetricsResponse, status_code=status.HTTP_201_CREATED)
async def record_zone_metrics(
    warehouse_id: UUID,
    data: ZoneMetricsCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Record metrics for a zone (upsert for today)."""
    return await ops_service.record_zone_metrics(db, warehouse_id, data)


# ======================
# Performance Endpoint
# ======================

@router.get("/performance", response_model=PerformanceResponse)
async def get_performance(
    warehouse_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
    time_range: str = Query(default="today", pattern="^(today|week|month)$"),
):
    """Get performance metrics for a warehouse."""
    return await ops_service.get_performance_metrics(db, warehouse_id, time_range)
