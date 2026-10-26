"""Inbound receiving and picking."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.warehouse_operations import (
    ConfirmPickItemRequest,
    InboundDamageReport,
    InboundMismatchReport,
    InboundReceivePlanResponse,
    InboundResponse,
    PickedItemResponse,
    PickingResponse,
    PickProgressResponse,
    ScheduleInboundRequest,
    StartPickingRequest,
)
from app.services import warehouse_operations_service as ops_service

router = APIRouter()


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
