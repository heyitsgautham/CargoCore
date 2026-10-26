"""Packing stations, quality checks and loading docks."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.warehouse_operations import (
    AssignTruckRequest,
    DockVerificationData,
    LoadingDockCreate,
    LoadingDockListResponse,
    LoadingDockResponse,
    PackingStationCreate,
    PackingStationListResponse,
    PackingStationResponse,
    PackingStationUpdate,
    PickingResponse,
    QualityCheckListResponse,
    QualityCheckResponse,
    QualityCheckUpdate,
    StartPackingRequest,
)
from app.services import warehouse_operations_service as ops_service

router = APIRouter()


# ======================
# Packing Station Endpoints
# ======================

@router.get("/packing-stations", response_model=PackingStationListResponse)
async def list_packing_stations(
    warehouse_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Get all packing stations for a warehouse."""
    return await ops_service.get_packing_stations(db, warehouse_id)


@router.post("/packing-stations", response_model=PackingStationResponse, status_code=status.HTTP_201_CREATED)
async def create_packing_station(
    warehouse_id: UUID,
    data: PackingStationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Create a new packing station."""
    return await ops_service.create_packing_station(db, warehouse_id, data)


@router.put("/packing-stations/{station_id}", response_model=PackingStationResponse)
async def update_packing_station(
    warehouse_id: UUID,
    station_id: UUID,
    data: PackingStationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Update a packing station."""
    return await ops_service.update_packing_station(db, warehouse_id, station_id, data)


@router.post("/orders/{order_id}/start-packing", response_model=PickingResponse)
async def start_packing(
    warehouse_id: UUID,
    order_id: UUID,
    data: StartPackingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Start packing process for an order."""
    return await ops_service.start_packing(db, warehouse_id, order_id, data)


@router.post("/orders/{order_id}/complete-packing", response_model=PickingResponse)
async def complete_packing(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Complete packing process for an order."""
    return await ops_service.complete_packing(db, warehouse_id, order_id)


# ======================
# Quality Check Endpoints
# ======================

@router.post("/orders/{order_id}/quality-check", response_model=QualityCheckResponse, status_code=status.HTTP_201_CREATED)
async def create_quality_check(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Create a new quality check for an order."""
    return await ops_service.create_quality_check(db, warehouse_id, order_id, performed_by=user.id)


@router.get("/quality-checks", response_model=QualityCheckListResponse)
async def list_quality_checks(
    warehouse_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
    order_id: UUID | None = Query(default=None),
):
    """List quality checks for a warehouse, optionally filtered by order."""
    return await ops_service.list_quality_checks(db, warehouse_id, order_id)


@router.get("/quality-checks/{check_id}", response_model=QualityCheckResponse)
async def get_quality_check(
    warehouse_id: UUID,
    check_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Get a quality check by ID."""
    return await ops_service.get_quality_check(db, warehouse_id, check_id)


@router.put("/quality-checks/{check_id}", response_model=QualityCheckResponse)
async def update_quality_check(
    warehouse_id: UUID,
    check_id: UUID,
    data: QualityCheckUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Update a quality check."""
    return await ops_service.update_quality_check(db, warehouse_id, check_id, data, performed_by=user.id)


@router.post("/quality-checks/{check_id}/pass", response_model=QualityCheckResponse)
async def pass_quality_check(
    warehouse_id: UUID,
    check_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Mark a quality check as passed and advance order to QC_PASSED."""
    return await ops_service.pass_quality_check(db, warehouse_id, check_id, performed_by=user.id)


# ======================
# Loading Dock Endpoints
# ======================

@router.get("/loading-docks", response_model=LoadingDockListResponse)
async def list_loading_docks(
    warehouse_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """Get all loading docks for a warehouse."""
    return await ops_service.get_loading_docks(db, warehouse_id)


@router.post("/loading-docks", response_model=LoadingDockResponse, status_code=status.HTTP_201_CREATED)
async def create_loading_dock(
    warehouse_id: UUID,
    data: LoadingDockCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Create a new loading dock."""
    return await ops_service.create_loading_dock(db, warehouse_id, data)


@router.post("/loading-docks/{dock_id}/assign", response_model=LoadingDockResponse)
async def assign_truck_to_dock(
    warehouse_id: UUID,
    dock_id: UUID,
    data: AssignTruckRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """Assign a truck to a loading dock."""
    return await ops_service.assign_truck_to_dock(db, warehouse_id, dock_id, data)


@router.post("/loading-docks/{dock_id}/release", response_model=LoadingDockResponse)
async def release_dock(
    warehouse_id: UUID,
    dock_id: UUID,
    verification: DockVerificationData,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """Release a loading dock after verification."""
    return await ops_service.release_dock(db, warehouse_id, dock_id, verification)


@router.post("/loading-docks/{dock_id}/maintenance", response_model=LoadingDockResponse)
async def set_dock_maintenance(
    warehouse_id: UUID,
    dock_id: UUID,
    is_maintenance: bool = Query(default=True),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))] = None,
):
    """Set dock maintenance status."""
    return await ops_service.set_dock_maintenance(db, warehouse_id, dock_id, is_maintenance)
