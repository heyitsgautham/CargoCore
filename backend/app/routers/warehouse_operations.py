"""Warehouse Operations Router.

Endpoints for warehouse lifecycle operations: picking, packing, quality checks,
loading dock management, returns grading, and zone metrics.
"""
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
    AssignTruckRequest,
    ConfirmPickItemRequest,
    DockVerificationData,
    InboundDamageReport,
    InboundMismatchReport,
    InboundReceivePlanResponse,
    InboundResponse,
    LoadingDockCreate,
    LoadingDockListResponse,
    LoadingDockResponse,
    PackingStationCreate,
    PackingStationListResponse,
    PackingStationResponse,
    PackingStationUpdate,
    PerformanceResponse,
    PickedItemResponse,
    PickingResponse,
    PickProgressResponse,
    QualityCheckListResponse,
    QualityCheckResponse,
    QualityCheckUpdate,
    ReturnGradingCreate,
    ReturnGradingListResponse,
    ReturnGradingResponse,
    ReturnGradingUpdate,
    ScheduleInboundRequest,
    StartPackingRequest,
    StartPickingRequest,
    ZoneMetricsCreate,
    ZoneMetricsListResponse,
    ZoneMetricsResponse,
)
from app.services import warehouse_operations_service as ops_service

router = APIRouter(
    prefix="/api/v1/warehouses/{warehouse_id}/operations",
    tags=["Warehouse Operations"],
)


# ======================
# Inbound Endpoints
# ======================

@router.get("/inbound", response_model=InboundResponse)
async def get_inbound_overview(
    warehouse_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Get inbound ASN verification dashboard data for a warehouse."""
    return await ops_service.get_inbound_overview(db, warehouse_id)


@router.get("/orders/{order_id}/ai-receive-plan", response_model=InboundReceivePlanResponse)
async def get_inbound_receive_plan(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Generate a real AI receive plan for a hub-based vendor inbound shipment."""
    return await ops_service.get_inbound_receive_plan(db, warehouse_id, order_id)


@router.post("/orders/{order_id}/report-mismatch", response_model=MessageResponse)
async def report_inbound_mismatch(
    warehouse_id: UUID,
    order_id: UUID,
    data: InboundMismatchReport,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Create a persistent mismatch escalation for a vendor inbound shipment."""
    await ops_service.report_inbound_mismatch(db, warehouse_id, order_id, data, user)
    return MessageResponse(message="Mismatch reported successfully")


@router.post("/orders/{order_id}/report-damage", response_model=MessageResponse)
async def report_inbound_damage(
    warehouse_id: UUID,
    order_id: UUID,
    data: InboundDamageReport,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Create a persistent damage report for a vendor inbound shipment."""
    await ops_service.report_inbound_damage(db, warehouse_id, order_id, data, user)
    return MessageResponse(message="Damage reported successfully")


@router.post("/inbound/schedule", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def schedule_inbound_delivery(
    warehouse_id: UUID,
    data: ScheduleInboundRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Create a real inbound vendor shipment scheduled for this warehouse."""
    order = await ops_service.schedule_inbound_delivery(db, warehouse_id, data)
    return MessageResponse(message=f"Inbound delivery scheduled as {order.tracking_code}")


# ======================
# Picking Endpoints
# ======================

@router.post("/orders/{order_id}/accept", response_model=PickingResponse)
async def accept_order(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Accept an order into the warehouse queue (sets warehouse_substatus = AWAITING_PICK)."""
    return await ops_service.accept_order_into_warehouse(db, warehouse_id, order_id)


@router.post("/orders/{order_id}/receive-inbound", response_model=PickingResponse)
async def receive_inbound(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Mark vendor goods as physically received — transitions AWAITING_INBOUND → AWAITING_PICK."""
    return await ops_service.mark_inbound_received(db, warehouse_id, order_id)


@router.post("/orders/{order_id}/generate-take-back", response_model=PickingResponse)
async def generate_take_back(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Generate the warehouse-side vendor take-back action for a damaged inbound shipment."""
    return await ops_service.generate_vendor_take_back(db, warehouse_id, order_id, user)


@router.post("/orders/{order_id}/mark-arrived", response_model=PickingResponse)
async def mark_arrived(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Mark a hub-based vendor inbound order as physically arrived at the warehouse."""
    return await ops_service.mark_inbound_arrived(db, warehouse_id, order_id)


@router.post("/orders/{order_id}/start-picking", response_model=PickingResponse)
async def start_picking(
    warehouse_id: UUID,
    order_id: UUID,
    data: StartPickingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Start picking process for an order."""
    return await ops_service.start_picking(db, warehouse_id, order_id, data)


@router.post("/orders/{order_id}/revert-picking", response_model=PickingResponse)
async def revert_picking(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Undo start-picking: revert order from PICKING back to AWAITING_PICK."""
    return await ops_service.revert_picking(db, warehouse_id, order_id)


@router.post("/orders/{order_id}/complete-picking", response_model=PickingResponse)
async def complete_picking(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Complete picking process for an order."""
    return await ops_service.complete_picking(db, warehouse_id, order_id)


@router.post("/orders/{order_id}/pick-item", response_model=PickedItemResponse)
async def confirm_pick_item(
    warehouse_id: UUID,
    order_id: UUID,
    data: ConfirmPickItemRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Confirm picking of a specific item (supports partial picking)."""
    return await ops_service.confirm_pick_item(db, warehouse_id, order_id, data, user.id)


@router.get("/orders/{order_id}/pick-progress", response_model=PickProgressResponse)
async def get_pick_progress(
    warehouse_id: UUID,
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("WAREHOUSE_MANAGER", "LOGISTIC_MANAGER"))],
):
    """Get picking progress for an order."""
    return await ops_service.get_pick_progress(db, warehouse_id, order_id)


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
