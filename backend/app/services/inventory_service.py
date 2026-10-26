from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import (
    InventoryItem,
    InventoryMovement,
    RestockRequest,
)
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
    PickingListItem,
    PickingListResponse,
)
from app.services.inventory_items import get_inventory_item

# Material requests live in material_request_service; the router keeps calling them through here.
from app.services.material_request_service import (
    approve_material_request as approve_material_request,
)
from app.services.material_request_service import (
    create_material_request as create_material_request,
)
from app.services.material_request_service import (
    list_material_requests as list_material_requests,
)
from app.services.material_request_service import (
    reject_material_request as reject_material_request,
)

# Restock requests live in restock_request_service; the router keeps calling them through here.
from app.services.restock_request_service import (
    create_restock_request as create_restock_request,
)
from app.services.restock_request_service import (
    escalate_restock_request as escalate_restock_request,
)
from app.services.restock_request_service import (
    list_restock_requests as list_restock_requests,
)
from app.services.restock_request_service import (
    update_restock_request_status as update_restock_request_status,
)

MOVEMENT_TYPES = {"INBOUND", "OUTBOUND", "ADJUSTMENT", "ISSUE", "RESTOCK", "RESERVED", "PICK"}


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
    item = await get_inventory_item(db, item_id)
    return InventoryResponse.model_validate(item)


async def update_item(db: AsyncSession, item_id: UUID, data: InventoryUpdate) -> InventoryResponse:
    item = await get_inventory_item(db, item_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return InventoryResponse.model_validate(item)


async def delete_item(db: AsyncSession, item_id: UUID) -> None:
    item = await get_inventory_item(db, item_id)
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

    item = await get_inventory_item(db, data.item_id)

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


