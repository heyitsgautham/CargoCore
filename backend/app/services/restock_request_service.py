"""Restock requests: raise, list, approve or reject, and escalate a request for more stock."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import (
    InventoryItem,
    InventoryMovement,
    RestockRequest,
)
from app.models.logistics import LogisticsEscalation
from app.models.user import User
from app.schemas.inventory import (
    RestockRequestCreate,
    RestockRequestListResponse,
    RestockRequestResponse,
    RestockRequestStatusUpdate,
)
from app.services import finance_service
from app.services.inventory_items import get_inventory_item


async def _get_restock_request(db: AsyncSession, request_id: UUID) -> RestockRequest:
    result = await db.execute(select(RestockRequest).where(RestockRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restock request not found")
    return req


def _to_restock_response(req: RestockRequest, item: InventoryItem, requester: User | None) -> RestockRequestResponse:
    return RestockRequestResponse(
        id=req.id,
        item_id=req.item_id,
        warehouse_id=req.warehouse_id,
        quantity=req.quantity,
        status=req.status,
        requested_by=req.requested_by,
        requested_by_name=requester.name if requester else None,
        manager_notes=req.manager_notes,
        item_sku=item.sku,
        item_name=item.name,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


async def create_restock_request(db: AsyncSession, data: RestockRequestCreate, user: User) -> RestockRequestResponse:
    item = await get_inventory_item(db, data.item_id)
    req = RestockRequest(
        item_id=item.id,
        warehouse_id=item.warehouse_id,
        quantity=data.quantity,
        status="PENDING",
        requested_by=user.id,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return _to_restock_response(req, item, user)


async def list_restock_requests(
    db: AsyncSession, page: int, page_size: int, warehouse_id: UUID | None, status_filter: str | None, user: User
) -> RestockRequestListResponse:
    query = (
        select(RestockRequest, InventoryItem, User)
        .join(InventoryItem, RestockRequest.item_id == InventoryItem.id)
        .outerjoin(User, RestockRequest.requested_by == User.id)
        .order_by(RestockRequest.created_at.desc())
    )
    
    if user.role.name == "WAREHOUSE_MANAGER" and user.warehouse_id:
        query = query.where(RestockRequest.warehouse_id == user.warehouse_id)
    elif warehouse_id:
        query = query.where(RestockRequest.warehouse_id == warehouse_id)

    if status_filter:
        query = query.where(RestockRequest.status == status_filter.upper())
        
    total_query = select(func.count(RestockRequest.id))
    if user.role.name == "WAREHOUSE_MANAGER" and user.warehouse_id:
        total_query = total_query.where(RestockRequest.warehouse_id == user.warehouse_id)
    elif warehouse_id:
        total_query = total_query.where(RestockRequest.warehouse_id == warehouse_id)
    if status_filter:
        total_query = total_query.where(RestockRequest.status == status_filter.upper())

    total = (await db.execute(total_query)).scalar_one()
    rows = (await db.execute(query.offset((page - 1) * page_size).limit(page_size))).all()

    items = [_to_restock_response(req, item, requester) for req, item, requester in rows]
    return RestockRequestListResponse(items=items, total=total, page=page, page_size=page_size)


async def update_restock_request_status(
    db: AsyncSession, request_id: UUID, data: RestockRequestStatusUpdate, user: User
) -> RestockRequestResponse:
    req = await _get_restock_request(db, request_id)
    if req.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is already processed")

    req.status = data.status
    req.manager_notes = data.manager_notes
    
    item = await get_inventory_item(db, req.item_id)
    
    if req.status == "APPROVED":
        item.quantity_on_hand += req.quantity
        movement = InventoryMovement(
            item_id=item.id,
            movement_type="RESTOCK",
            quantity=req.quantity,
            performed_by=user.id,
        )
        db.add(movement)
        db.add(item)

        # Auto-record procurement expense
        total_cost = req.quantity * (item.cost_price or 0.0)
        if total_cost > 0:
            funding_source = getattr(data, "funding_source", "APP_REVENUE") or "APP_REVENUE"
            await finance_service.record_expense(
                db,
                expense_type="EXPENSE_PROCUREMENT",
                amount=total_cost,
                description=f"Procurement: {req.quantity}\u00d7 {item.name}",
                warehouse_id=req.warehouse_id,
                order_id=None,
                tracking_code=item.sku,
                extra_metadata={
                    "funding_source": funding_source,
                    "item_sku": item.sku,
                    "cost_price": item.cost_price,
                    "qty": req.quantity,
                    "restock_request_id": str(req.id),
                },
            )

    linked_escalations = (
        await db.execute(
            select(LogisticsEscalation).where(
                LogisticsEscalation.action_details.contains(str(request_id)),
                LogisticsEscalation.status == "OPEN",
            )
        )
    ).scalars().all()
    for escalation in linked_escalations:
        escalation.status = req.status
        db.add(escalation)
        
    db.add(req)
    await db.flush()
    await db.refresh(req)
    
    user_result = await db.execute(select(User).where(User.id == req.requested_by))
    requester = user_result.scalar_one_or_none()
    
    return _to_restock_response(req, item, requester)


async def escalate_restock_request(
    db: AsyncSession, request_id: UUID, user: User
) -> RestockRequestResponse:
    """Mark a PENDING restock as escalated and create a LogisticsEscalation ticket for the LM."""
    req = await _get_restock_request(db, request_id)
    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING requests can be escalated"
        )

    existing_note = req.manager_notes or ""
    if "[ESCALATED]" not in existing_note:
        req.manager_notes = f"[ESCALATED] Urgent review needed by Logistics Manager. {existing_note}".strip()

    db.add(req)

    item = await get_inventory_item(db, req.item_id)
    requester_name = getattr(user, "name", None) or getattr(user, "full_name", None) or getattr(user, "email", "Warehouse Manager")
    warehouse_id = getattr(user, "warehouse_id", None)

    # Create escalation ticket visible in LM Communication → Escalations
    already_escalated = (await db.execute(
        select(LogisticsEscalation).where(
            LogisticsEscalation.action_details.contains(str(request_id))
        )
    )).scalar_one_or_none()

    if not already_escalated:
        escalation = LogisticsEscalation(
            warehouse_id=warehouse_id,
            title=f"Urgent Restock: {item.name}",
            priority="High",
            requester_name=requester_name,
            requester_role="Warehouse Manager",
            description=(
                f"{requester_name} has escalated an urgent restock request for '{item.name}' "
                f"(SKU: {item.sku or 'N/A'}). Current stock is critically low and requires "
                f"immediate approval from Logistics Manager."
            ),
            action_details=f"Approve restock of {req.quantity} units for {item.name} [ref:{request_id}]",
            status="OPEN",
        )
        db.add(escalation)

    await db.flush()
    await db.refresh(req)

    user_result = await db.execute(select(User).where(User.id == req.requested_by))
    requester = user_result.scalar_one_or_none()

    return _to_restock_response(req, item, requester)
