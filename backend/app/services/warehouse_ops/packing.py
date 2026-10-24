"""Packing stations and the packing step."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.labour import Labourer
from app.models.order import OrderItem
from app.models.warehouse import (
    PackingStation,
)
from app.schemas.warehouse_operations import (
    PackingStationCreate,
    PackingStationListResponse,
    PackingStationResponse,
    PackingStationUpdate,
    PickingResponse,
    StartPackingRequest,
)
from app.services.warehouse_ops.common import (
    _get_order,
    _get_warehouse,
    _validate_substatus_transition,
)

# ======================
# Packing Station Operations
# ======================

async def get_packing_stations(
    db: AsyncSession,
    warehouse_id: UUID,
) -> PackingStationListResponse:
    """Get all packing stations for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(PackingStation)
        .options(
            selectinload(PackingStation.assigned_labourer).selectinload(Labourer.user),
            selectinload(PackingStation.current_order),
        )
        .where(PackingStation.warehouse_id == warehouse_id)
        .order_by(PackingStation.station_number)
    )
    stations = result.scalars().all()

    items = []
    for station in stations:
        labourer_name = None
        if station.assigned_labourer and station.assigned_labourer.user:
            labourer_name = station.assigned_labourer.user.name

        order_tracking = None
        if station.current_order:
            order_tracking = station.current_order.tracking_code

        items.append(PackingStationResponse(
            id=station.id,
            warehouse_id=station.warehouse_id,
            station_number=station.station_number,
            status=station.status,
            assigned_labourer_id=station.assigned_labourer_id,
            assigned_labourer_name=labourer_name,
            current_order_id=station.current_order_id,
            current_order_tracking=order_tracking,
            items_packed_today=station.items_packed_today,
            created_at=station.created_at,
        ))

    return PackingStationListResponse(items=items, total=len(items))


async def create_packing_station(
    db: AsyncSession,
    warehouse_id: UUID,
    data: PackingStationCreate,
) -> PackingStationResponse:
    """Create a new packing station."""
    await _get_warehouse(db, warehouse_id)

    station = PackingStation(
        warehouse_id=warehouse_id,
        station_number=data.station_number,
        status=data.status,
    )
    db.add(station)
    await db.commit()
    await db.refresh(station)

    return PackingStationResponse(
        id=station.id,
        warehouse_id=station.warehouse_id,
        station_number=station.station_number,
        status=station.status,
        assigned_labourer_id=None,
        assigned_labourer_name=None,
        current_order_id=None,
        current_order_tracking=None,
        items_packed_today=0,
        created_at=station.created_at,
    )


async def update_packing_station(
    db: AsyncSession,
    warehouse_id: UUID,
    station_id: UUID,
    data: PackingStationUpdate,
) -> PackingStationResponse:
    """Update a packing station."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(PackingStation)
        .options(
            selectinload(PackingStation.assigned_labourer).selectinload(Labourer.user),
            selectinload(PackingStation.current_order),
        )
        .where(PackingStation.id == station_id, PackingStation.warehouse_id == warehouse_id)
    )
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packing station not found")

    if data.status is not None:
        station.status = data.status
    if data.assigned_labourer_id is not None:
        # Validate labourer belongs to this warehouse
        labourer_check = (
            await db.execute(
                select(Labourer).where(
                    Labourer.id == data.assigned_labourer_id,
                    Labourer.warehouse_id == warehouse_id,
                    Labourer.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not labourer_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Labourer not found or does not belong to this warehouse",
            )
        station.assigned_labourer_id = data.assigned_labourer_id
    if data.current_order_id is not None:
        station.current_order_id = data.current_order_id

    await db.commit()
    await db.refresh(station)

    labourer_name = None
    if station.assigned_labourer and station.assigned_labourer.user:
        labourer_name = station.assigned_labourer.user.name

    order_tracking = None
    if station.current_order:
        order_tracking = station.current_order.tracking_code

    return PackingStationResponse(
        id=station.id,
        warehouse_id=station.warehouse_id,
        station_number=station.station_number,
        status=station.status,
        assigned_labourer_id=station.assigned_labourer_id,
        assigned_labourer_name=labourer_name,
        current_order_id=station.current_order_id,
        current_order_tracking=order_tracking,
        items_packed_today=station.items_packed_today,
        created_at=station.created_at,
    )


async def start_packing(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data: StartPackingRequest,
) -> PickingResponse:
    """Start packing process for an order."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    if order.warehouse_substatus == "PACKING":
        station = (
            await db.execute(
                select(PackingStation).where(PackingStation.current_order_id == order_id)
            )
        ).scalar_one_or_none()
        return PickingResponse(
            order_id=order_id,
            warehouse_substatus="PACKING",
            assigned_labourer_id=station.assigned_labourer_id if station else None,
            message="Packing already in progress",
        )

    _validate_substatus_transition(order.warehouse_substatus, "PACKING")

    # Verify all cargo items were fully picked (exclude packing materials — consumed during packing, not picking)
    from app.models.inventory import InventoryItem as _InvItem
    from app.models.order import PickedItem
    _PACKING_NAME_KWS = ["carton", "box", "bubble", "wrap", "tape", "crate", "blanket", "pad", "wardrobe", "packing", "pack"]

    order_items = (await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )).scalars().all()

    # Build cargo_items list: exclude PKG-* and any inventory item whose name/category is packing-related
    cargo_items = []
    for _oi in order_items:
        if _oi.sku.startswith("PKG-"):
            continue
        _inv = (await db.execute(
            select(_InvItem).where(_InvItem.warehouse_id == warehouse_id, _InvItem.sku == _oi.sku)
        )).scalar_one_or_none()
        if _inv:
            _text = ((_inv.name or "") + " " + (_inv.category or "")).lower()
            if any(kw in _text for kw in _PACKING_NAME_KWS):
                continue  # packing material — skip
        cargo_items.append(_oi)
    picked_items = (await db.execute(
        select(PickedItem).where(PickedItem.order_id == order_id)
    )).scalars().all()
    picked_by_sku = {pi.sku: pi for pi in picked_items}
    incomplete = [
        f"{oi.sku} ({oi.quantity - (picked_by_sku[oi.sku].quantity_picked if oi.sku in picked_by_sku else 0)} remaining)"
        for oi in cargo_items
        if (picked_by_sku.get(oi.sku).quantity_picked if oi.sku in picked_by_sku else 0) < oi.quantity
    ]
    if incomplete:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot start packing — picking incomplete for: " + ", ".join(incomplete),
        )

    station = None
    if data.station_id:
        result = await db.execute(
            select(PackingStation).where(
                PackingStation.id == data.station_id,
                PackingStation.warehouse_id == warehouse_id,
            )
        )
        station = result.scalar_one_or_none()
        if not station:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packing station not found")
    else:
        station = (
            await db.execute(
                select(PackingStation).where(PackingStation.warehouse_id == warehouse_id).order_by(PackingStation.station_number)
            )
        ).scalars().first()
        if station is None:
            station = PackingStation(
                warehouse_id=warehouse_id,
                station_number="PACK-01",
                status="ACTIVE",
            )
            db.add(station)
            await db.flush()

    station.current_order_id = order_id
    station.status = "ACTIVE"
    order.warehouse_substatus = "PACKING"
    order.packing_started_at = datetime.now(UTC)

    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="PACKING",
        assigned_labourer_id=station.assigned_labourer_id,
        message="Packing started successfully",
    )


async def complete_packing(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Complete packing process for an order."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    _validate_substatus_transition(order.warehouse_substatus, "PACKED")

    # Detect packing material OrderItems (PKG-* SKU or inventory item with packing keywords).
    # This list is used both for the issuance guard and for later inventory deduction.
    from app.models.inventory import InventoryItem, InventoryMovement

    # Packing material keywords for name-based detection
    PACKING_NAME_KEYWORDS = ["carton", "box", "bubble", "wrap", "tape", "crate", "blanket", "pad", "wardrobe", "packing", "pack"]

    # Get ALL order items; we'll split into cargo vs packing materials below
    all_order_items = (await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )).scalars().all()

    packing_material_items = []
    for oi in all_order_items:
        # PKG-* prefix is always a packing material
        if oi.sku.startswith("PKG-"):
            packing_material_items.append(oi)
            continue
        # Check if this SKU's inventory item is packing-related by name/category
        inv_check = (await db.execute(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.sku == oi.sku,
            )
        )).scalar_one_or_none()
        if inv_check:
            item_text = ((inv_check.name or "") + " " + (inv_check.category or "")).lower()
            if any(kw in item_text for kw in PACKING_NAME_KEYWORDS):
                packing_material_items.append(oi)

    # Guard: only block if the order actually has packing material items AND they haven't been issued
    if packing_material_items:
        issued = (await db.execute(
            select(InventoryMovement).where(
                InventoryMovement.reference_order_id == order_id,
                func.upper(InventoryMovement.movement_type) == 'ISSUE'
            ).limit(1)
        )).scalar_one_or_none()

        if not issued:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot complete packing — packing materials have not been issued to this order. "
                    "Go to Packing Materials, select this order, and issue the required materials first."
                ),
            )

    # Update station if assigned
    result = await db.execute(
        select(PackingStation).where(PackingStation.current_order_id == order_id)
    )
    station = result.scalar_one_or_none()
    if station:
        station.current_order_id = None
        station.items_packed_today += 1

    assigned_labourers = (
        await db.execute(
            select(Labourer).where(
                Labourer.warehouse_id == warehouse_id,
                Labourer.assigned_order_id == order_id,
            )
        )
    ).scalars().all()
    for labourer in assigned_labourers:
        labourer.assigned_order_id = None

    if packing_material_items:
        # Idempotency: skip if PACK movements already recorded for this order
        already_packed = (await db.execute(
            select(InventoryMovement).where(
                InventoryMovement.reference_order_id == order_id,
                InventoryMovement.movement_type == "PACK",
            ).limit(1)
        )).scalar_one_or_none()

        if not already_packed:
            # Keyword fallback map: covers both seeded PKG-* SKUs and manually-named inventory items
            PKG_KEYWORD_MAP = {
                "PKG-CARTON":        ["carton", "box"],
                "PKG-BUBBLE-WRAP":   ["bubble", "wrap"],
                "PKG-PLASTIC-CRATE": ["crate", "plastic"],
                "PKG-BLANKET":       ["blanket", "pad"],
                "PKG-WARDROBE-BOX":  ["wardrobe"],
                "PKG-TAPE":          ["tape"],
            }

            for pm_item in packing_material_items:
                # 1. Exact SKU match
                inv = (await db.execute(
                    select(InventoryItem).where(
                        InventoryItem.warehouse_id == warehouse_id,
                        InventoryItem.sku == pm_item.sku,
                    )
                )).scalar_one_or_none()

                # 2. Keyword name match fallback (handles manually-named inventory items)
                if not inv:
                    keywords = PKG_KEYWORD_MAP.get(pm_item.sku, [pm_item.sku.replace("PKG-", "").lower()])
                    for kw in keywords:
                        inv = (await db.execute(
                            select(InventoryItem).where(
                                InventoryItem.warehouse_id == warehouse_id,
                                InventoryItem.name.ilike(f"%{kw}%"),
                            )
                        )).scalar_one_or_none()
                        if inv:
                            break

                if inv:
                    deduct_qty = min(pm_item.quantity, inv.quantity_on_hand)
                    if deduct_qty > 0:
                        inv.quantity_on_hand -= deduct_qty
                        db.add(InventoryMovement(
                            item_id=inv.id,
                            movement_type="PACK",
                            quantity=deduct_qty,
                            reference_order_id=order_id,
                            performed_by=None,
                        ))

    order.warehouse_substatus = "PACKED"
    order.packing_completed_at = datetime.now(UTC)
    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="PACKED",
        assigned_labourer_id=None,
        message="Packing completed successfully",
    )
