import json
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import (
    InventoryItem,
    InventoryMovement,
    MaterialRequest,
    RestockRequest,
)
from app.models.logistics import LogisticsEscalation
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.inventory import (
    InventoryCreate,
    InventoryListResponse,
    InventoryMovementCreate,
    InventoryMovementResponse,
    InventoryResponse,
    InventoryUpdate,
    MaterialRequestApprove,
    MaterialRequestCreate,
    MaterialRequestListResponse,
    MaterialRequestReject,
    MaterialRequestResponse,
    PickingListItem,
    PickingListResponse,
    RestockRequestCreate,
    RestockRequestListResponse,
    RestockRequestResponse,
    RestockRequestStatusUpdate,
)
from app.services import finance_service

MOVEMENT_TYPES = {"INBOUND", "OUTBOUND", "ADJUSTMENT", "ISSUE", "RESTOCK", "RESERVED", "PICK"}


async def _get_item(db: AsyncSession, item_id: UUID) -> InventoryItem:
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    return item


def _split_zone_and_aisle(raw_aisle: str | None) -> tuple[str | None, str | None]:
    value = (raw_aisle or "").strip()
    if not value:
        return None, None
    if "-" in value:
        zone, aisle = value.split("-", 1)
        return zone.strip() or None, aisle.strip() or None
    return None, value


def _build_floor_plan_lookup(floor_plan_json: dict | None) -> dict[str, dict]:
    if not isinstance(floor_plan_json, dict):
        return {}

    groups = {str(group.get("id")): group for group in floor_plan_json.get("groups", []) if isinstance(group, dict)}
    sections = {str(section.get("id")): section for section in floor_plan_json.get("sections", []) if isinstance(section, dict)}
    racks = {str(rack.get("id")): rack for rack in floor_plan_json.get("racks", []) if isinstance(rack, dict)}

    lookup: dict[str, dict] = {}
    for product in floor_plan_json.get("products", []):
        if not isinstance(product, dict):
            continue

        sku = str(product.get("sku") or "").strip()
        rack = racks.get(str(product.get("rackId")))
        section = sections.get(str(rack.get("sectionId"))) if rack else None
        group = groups.get(str(section.get("groupId"))) if section else None

        cell_label = None
        cell_index = product.get("cell")
        cols = int(rack.get("cols") or 0) if rack else 0
        if isinstance(cell_index, int) and cols > 0:
            row = ((cell_index - 1) // cols) + 1
            col = ((cell_index - 1) % cols) + 1
            cell_label = f"R{row}C{col}"
        elif cell_index is not None:
            cell_label = str(cell_index)

        if sku:
            lookup[sku] = {
                "zone": group.get("name") if group else None,
                "section": section.get("label") if section else None,
                "rack": rack.get("label") if rack else None,
                "cell": cell_label,
            }

    return lookup


def _build_location_payload(
    inventory_item: InventoryItem | None,
    floor_plan_lookup: dict[str, dict],
    sku: str,
) -> dict:
    floor_plan_location = floor_plan_lookup.get(sku, {})
    zone_from_aisle, aisle = _split_zone_and_aisle(inventory_item.aisle if inventory_item else None)
    zone = floor_plan_location.get("zone") or zone_from_aisle
    section = floor_plan_location.get("section")
    rack = floor_plan_location.get("rack")
    shelf = inventory_item.shelf if inventory_item else None
    bin_code = inventory_item.bin if inventory_item else None
    cell = floor_plan_location.get("cell")

    parts = []
    if zone:
        parts.append(f"Zone {zone}")
    if aisle:
        parts.append(f"Aisle {aisle}")
    if section:
        parts.append(f"Section {section}")
    if rack:
        parts.append(f"Rack {rack}")
    if shelf:
        parts.append(f"Shelf {shelf}")
    if bin_code:
        parts.append(f"Bin {bin_code}")
    if cell:
        parts.append(f"Cell {cell}")

    return {
        "zone": zone,
        "aisle": aisle,
        "section": section,
        "rack": rack,
        "shelf": shelf,
        "bin": bin_code,
        "cell": cell,
        "location_path": " / ".join(parts) if parts else "Location not mapped",
    }


def _to_movement_response(
    movement: InventoryMovement,
    item: InventoryItem,
    order: Order | None = None,
    performer: User | None = None,
) -> InventoryMovementResponse:
    return InventoryMovementResponse(
        id=movement.id,
        item_id=movement.item_id,
        warehouse_id=item.warehouse_id,
        movement_type=(movement.movement_type or "").upper(),
        quantity=movement.quantity,
        reference_order_id=movement.reference_order_id,
        reference_order_tracking=order.tracking_code if order else None,
        performed_by=movement.performed_by,
        performed_by_name=performer.name if performer else None,
        item_sku=item.sku,
        item_name=item.name,
        item_category=item.category,
        item_unit=item.unit,
        created_at=movement.created_at,
    )


async def list_items(
    db: AsyncSession,
    page: int,
    page_size: int,
    warehouse_id: UUID | None,
    sku: str | None = None,
) -> InventoryListResponse:
    filters = []
    if warehouse_id:
        filters.append(InventoryItem.warehouse_id == warehouse_id)
    if sku:
        filters.append(InventoryItem.sku == sku)

    total_query = select(func.count(InventoryItem.id))
    data_query = (
        select(InventoryItem)
        .order_by(InventoryItem.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if filters:
        total_query = total_query.where(*filters)
        data_query = data_query.where(*filters)

    total = (await db.execute(total_query)).scalar_one()
    rows = (await db.execute(data_query)).scalars().all()

    return InventoryListResponse(
        items=[InventoryResponse.model_validate(item) for item in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def list_categories(
    db: AsyncSession,
    warehouse_id: UUID | None,
) -> list[str]:
    query = select(InventoryItem.category).distinct().order_by(InventoryItem.category.asc())
    if warehouse_id:
        query = query.where(InventoryItem.warehouse_id == warehouse_id)

    rows = (await db.execute(query)).scalars().all()

    categories: list[str] = []
    for raw in rows:
        value = (raw or "").strip()
        if not value:
            continue
        if value.lower() == "uncategorized":
            value = "General"
        if value not in categories:
            categories.append(value)

    if "General" not in categories:
        categories.insert(0, "General")

    return categories


async def create_item(db: AsyncSession, data: InventoryCreate) -> InventoryResponse:
    item = InventoryItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return InventoryResponse.model_validate(item)


async def get_item_detail(db: AsyncSession, item_id: UUID) -> InventoryResponse:
    item = await _get_item(db, item_id)
    return InventoryResponse.model_validate(item)


async def update_item(db: AsyncSession, item_id: UUID, data: InventoryUpdate) -> InventoryResponse:
    item = await _get_item(db, item_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return InventoryResponse.model_validate(item)


async def delete_item(db: AsyncSession, item_id: UUID) -> None:
    item = await _get_item(db, item_id)
    # Movements and restock requests keep a NOT NULL item_id, so deleting the
    # item would fail at flush. Keep the stock history and refuse instead.
    history = (
        await db.execute(select(func.count()).select_from(InventoryMovement).where(InventoryMovement.item_id == item_id))
    ).scalar_one() + (
        await db.execute(select(func.count()).select_from(RestockRequest).where(RestockRequest.item_id == item_id))
    ).scalar_one()
    if history:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This item has stock movements or restock requests. Set its quantity to zero instead of deleting it.",
        )
    await db.delete(item)
    await db.flush()


async def create_movement(
    db: AsyncSession,
    data: InventoryMovementCreate,
    user: User,
) -> InventoryMovementResponse:
    movement_type = data.movement_type.upper()
    if movement_type not in MOVEMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid movement_type")

    item = await _get_item(db, data.item_id)

    # Types that reduce inventory
    outbound_types = {"OUTBOUND", "ISSUE", "PICK"}
    # Types that increase inventory
    inbound_types = {"INBOUND", "RESTOCK", "ADJUSTMENT"}

    if movement_type in outbound_types and item.quantity_on_hand < data.quantity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient stock")

    if movement_type in outbound_types:
        item.quantity_on_hand -= data.quantity
    elif movement_type in inbound_types:
        item.quantity_on_hand += data.quantity
    # RESERVED doesn't change quantity - just tracks reservation

    movement = InventoryMovement(
        item_id=item.id,
        movement_type=movement_type,
        quantity=data.quantity,
        reference_order_id=data.reference_order_id,
        performed_by=user.id,
    )

    db.add(item)
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    row = (
        await db.execute(
            select(InventoryMovement, InventoryItem, Order, User)
            .join(InventoryItem, InventoryMovement.item_id == InventoryItem.id)
            .outerjoin(Order, InventoryMovement.reference_order_id == Order.id)
            .outerjoin(User, InventoryMovement.performed_by == User.id)
            .where(InventoryMovement.id == movement.id)
        )
    ).one()
    return _to_movement_response(*row)


async def list_movements(
    db: AsyncSession,
    page: int,
    page_size: int,
    item_id: UUID | None,
    warehouse_id: UUID | None,
    reference_order_id: UUID | None,
) -> list[InventoryMovementResponse]:
    query = (
        select(InventoryMovement, InventoryItem, Order, User)
        .join(InventoryItem, InventoryMovement.item_id == InventoryItem.id)
        .outerjoin(Order, InventoryMovement.reference_order_id == Order.id)
        .outerjoin(User, InventoryMovement.performed_by == User.id)
        .order_by(InventoryMovement.created_at.desc())
    )
    if item_id:
        query = query.where(InventoryMovement.item_id == item_id)
    if warehouse_id:
        query = query.where(InventoryItem.warehouse_id == warehouse_id)
    if reference_order_id:
        query = query.where(InventoryMovement.reference_order_id == reference_order_id)

    rows = (
        await db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )
    ).all()

    return [_to_movement_response(*row) for row in rows]


async def low_stock_items(db: AsyncSession, warehouse_id: UUID | None) -> list[InventoryResponse]:
    query = select(InventoryItem).where(InventoryItem.quantity_on_hand <= InventoryItem.safety_stock)
    if warehouse_id:
        query = query.where(InventoryItem.warehouse_id == warehouse_id)

    rows = (await db.execute(query.order_by(InventoryItem.quantity_on_hand.asc()))).scalars().all()
    return [InventoryResponse.model_validate(row) for row in rows]


async def generate_pick_list(db: AsyncSession, order_id: UUID) -> PickingListResponse:
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not order.warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order must be assigned to a warehouse before generating pick list",
        )

    warehouse = (
        await db.execute(
            select(Warehouse).where(Warehouse.id == order.warehouse_id)
        )
    ).scalar_one_or_none()
    floor_plan_lookup = _build_floor_plan_lookup(warehouse.floor_plan_json if warehouse else None)

    order_items = (await db.execute(select(OrderItem).where(OrderItem.order_id == order_id))).scalars().all()
    if not order_items:
        return PickingListResponse(order_id=order_id, items=[])

    result_items: list[PickingListItem] = []
    for order_item in order_items:
        inventory_result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == order.warehouse_id,
                InventoryItem.sku == order_item.sku,
            )
        )
        inventory_item = inventory_result.scalar_one_or_none()
        available = inventory_item.quantity_on_hand if inventory_item else 0
        shortage = max(order_item.quantity - available, 0)
        location_payload = _build_location_payload(inventory_item, floor_plan_lookup, order_item.sku)
        result_items.append(
            PickingListItem(
                sku=order_item.sku,
                item_name=inventory_item.name if inventory_item else order_item.sku,
                required_quantity=order_item.quantity,
                available_quantity=available,
                shortage_quantity=shortage,
                unit=inventory_item.unit if inventory_item else "pcs",
                scan_code=inventory_item.sku if inventory_item else order_item.sku,
                zone=location_payload["zone"],
                aisle=location_payload["aisle"],
                section=location_payload["section"],
                rack=location_payload["rack"],
                shelf=location_payload["shelf"],
                bin=location_payload["bin"],
                cell=location_payload["cell"],
                location_path=location_payload["location_path"],
                is_fully_available=available >= order_item.quantity,
            )
        )

    return PickingListResponse(order_id=order_id, items=result_items)


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
    item = await _get_item(db, data.item_id)
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
    
    item = await _get_item(db, req.item_id)
    
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

    item = await _get_item(db, req.item_id)
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


# ─────────────────────────────────────────────────────────────────────────────
# Material Request Functions (WM requests new packing material -> LM approves)
# ─────────────────────────────────────────────────────────────────────────────


_RATES_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "rates_config.json"


def _to_material_request_response(req: MaterialRequest, requester: User | None = None, approver: User | None = None) -> MaterialRequestResponse:
    return MaterialRequestResponse(
        id=req.id,
        material_name=req.material_name,
        category=req.category,
        unit=req.unit,
        suggested_rate=req.suggested_rate,
        reason=req.reason,
        status=req.status,
        requested_by=req.requested_by,
        requested_by_name=getattr(requester, "full_name", None) or getattr(requester, "email", None) if requester else None,
        approved_by=req.approved_by,
        approved_by_name=getattr(approver, "full_name", None) or getattr(approver, "email", None) if approver else None,
        approved_rate=req.approved_rate,
        manager_notes=req.manager_notes,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


async def create_material_request(
    db: AsyncSession, data: MaterialRequestCreate, user: User
) -> MaterialRequestResponse:
    """WM creates a request for a new packing material."""
    req = MaterialRequest(
        material_name=data.material_name,
        category=data.category,
        unit=data.unit,
        suggested_rate=data.suggested_rate,
        reason=data.reason,
        status="PENDING",
        requested_by=user.id,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return _to_material_request_response(req, user)


async def list_material_requests(
    db: AsyncSession, status_filter: str | None, user: User
) -> MaterialRequestListResponse:
    """List material requests. LM sees all, WM sees only their own."""
    query = select(MaterialRequest)
    
    # WM only sees their own requests
    if user.role == "WAREHOUSE_MANAGER":
        query = query.where(MaterialRequest.requested_by == user.id)
    
    if status_filter:
        query = query.where(MaterialRequest.status == status_filter.upper())
    
    query = query.order_by(MaterialRequest.created_at.desc())
    result = await db.execute(query)
    requests = result.scalars().all()
    
    # Fetch user names
    items = []
    for req in requests:
        requester = None
        approver = None
        if req.requested_by:
            user_result = await db.execute(select(User).where(User.id == req.requested_by))
            requester = user_result.scalar_one_or_none()
        if req.approved_by:
            user_result = await db.execute(select(User).where(User.id == req.approved_by))
            approver = user_result.scalar_one_or_none()
        items.append(_to_material_request_response(req, requester, approver))
    
    return MaterialRequestListResponse(items=items, total=len(items))


async def _get_material_request(db: AsyncSession, request_id: UUID) -> MaterialRequest:
    result = await db.execute(select(MaterialRequest).where(MaterialRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material request not found")
    return req


def _material_sku(material_name: str) -> str:
    """Generate a stable inventory SKU from a material name. e.g. 'Bubble Wrap' → 'PKG-BUBBLE-WRAP'"""
    return "PKG-" + material_name.upper().replace(" ", "-")


async def sync_packing_materials_to_inventory(
    db: AsyncSession,
    materials: list[dict],
) -> None:
    """
    Upsert inventory items for every packing material in all active warehouses.
    - Creates the item if it doesn't exist (quantity_on_hand = 0, safety_stock = 10).
    - Updates selling_price if the item already exists (preserves current stock).
    Called whenever the LM saves rate governance or approves a new material request.
    """
    # Get all active warehouses
    warehouse_result = await db.execute(
        select(Warehouse).where(Warehouse.is_active == True)
    )
    warehouses = warehouse_result.scalars().all()

    for material in materials:
        name = material.get("name") or ""
        rate = float(material.get("rate") or 0)
        unit = material.get("unit") or "pcs"
        if not name:
            continue
        sku = _material_sku(name)

        for warehouse in warehouses:
            # Check if item already exists
            existing_result = await db.execute(
                select(InventoryItem).where(
                    InventoryItem.warehouse_id == warehouse.id,
                    InventoryItem.sku == sku,
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                # Only update the price; leave stock levels untouched
                existing.selling_price = rate
                db.add(existing)
            else:
                # Create a new inventory record with zero stock
                new_item = InventoryItem(
                    warehouse_id=warehouse.id,
                    sku=sku,
                    name=name,
                    category="Packing Materials",
                    unit=unit,
                    quantity_on_hand=0,
                    safety_stock=10,
                    cost_price=round(rate * 0.8, 2),
                    selling_price=rate,
                )
                db.add(new_item)

    await db.flush()


def _add_material_to_rates(material_name: str, rate: float, unit: str) -> None:
    """Add a new material to rates_config.json"""
    # Generate a camelCase id from the name
    material_id = "".join(
        word.capitalize() if i > 0 else word.lower()
        for i, word in enumerate(material_name.split())
    )
    
    # Load current rates
    if _RATES_CONFIG_PATH.exists():
        with open(_RATES_CONFIG_PATH, encoding="utf-8") as f:
            rates = json.load(f)
    else:
        rates = {}
    
    # Ensure materials is a list
    if not isinstance(rates.get("materials"), list):
        # Convert old dict format to list
        old_materials = rates.get("materials", {})
        rates["materials"] = [
            {"id": "box", "name": "Box", "rate": old_materials.get("box", 50), "unit": "pcs"},
            {"id": "bubbleWrap", "name": "Bubble Wrap", "rate": old_materials.get("bubbleWrap", 20), "unit": "m"},
            {"id": "crate", "name": "Crate Rental", "rate": old_materials.get("crate", 200), "unit": "pcs"},
        ]
    
    # Check if material already exists
    existing_ids = [m.get("id") for m in rates["materials"]]
    if material_id in existing_ids:
        # Update existing
        for m in rates["materials"]:
            if m.get("id") == material_id:
                m["rate"] = rate
                m["unit"] = unit
                break
    else:
        # Add new material
        rates["materials"].append({
            "id": material_id,
            "name": material_name,
            "rate": rate,
            "unit": unit,
        })
    
    # Save
    with open(_RATES_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(rates, f, indent=2)


async def approve_material_request(
    db: AsyncSession, request_id: UUID, data: MaterialRequestApprove, user: User
) -> MaterialRequestResponse:
    """LM approves a material request and auto-adds to rates config."""
    req = await _get_material_request(db, request_id)
    
    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING requests can be approved"
        )
    
    req.status = "APPROVED"
    req.approved_by = user.id
    req.approved_rate = data.approved_rate
    req.manager_notes = data.manager_notes
    
    db.add(req)
    await db.flush()
    await db.refresh(req)
    
    # Add material to rates config
    _add_material_to_rates(req.material_name, data.approved_rate, req.unit)

    # Sync the new material to inventory across all active warehouses
    await sync_packing_materials_to_inventory(
        db,
        [{"name": req.material_name, "rate": data.approved_rate, "unit": req.unit}],
    )

    # Fetch users for response
    requester = None
    if req.requested_by:
        user_result = await db.execute(select(User).where(User.id == req.requested_by))
        requester = user_result.scalar_one_or_none()
    
    return _to_material_request_response(req, requester, user)


async def reject_material_request(
    db: AsyncSession, request_id: UUID, data: MaterialRequestReject, user: User
) -> MaterialRequestResponse:
    """LM rejects a material request."""
    req = await _get_material_request(db, request_id)
    
    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING requests can be rejected"
        )
    
    req.status = "REJECTED"
    req.approved_by = user.id
    req.manager_notes = data.manager_notes
    
    db.add(req)
    await db.flush()
    await db.refresh(req)
    
    # Fetch users for response
    requester = None
    if req.requested_by:
        user_result = await db.execute(select(User).where(User.id == req.requested_by))
        requester = user_result.scalar_one_or_none()
    
    return _to_material_request_response(req, requester, user)
