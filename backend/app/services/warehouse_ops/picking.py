"""Picking: start, revert, confirm items, complete and progress."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.labour import Labourer
from app.models.order import OrderItem
from app.schemas.warehouse_operations import (
    PickingResponse,
    StartPickingRequest,
)
from app.services.warehouse_ops.common import (
    _format_user_name,
    _get_order,
    _get_warehouse,
    _validate_substatus_transition,
)

# ======================
# Picking Operations
# ======================

async def start_picking(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data: StartPickingRequest,
) -> PickingResponse:
    """Start picking process for an order."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    # Guard: vendor orders in AWAITING_INBOUND must go through Inbound first
    if order.warehouse_substatus == "AWAITING_INBOUND":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendor order goods have not been received yet. Complete inbound receiving first.",
        )

    # Idempotent: if already PICKING, return success immediately
    if order.warehouse_substatus == "PICKING":
        labourer_id = (
            await db.execute(
                select(Labourer.id).where(
                    Labourer.warehouse_id == warehouse_id,
                    Labourer.is_active.is_(True),
                    Labourer.assigned_order_id == order_id,
                ).limit(1)
            )
        ).scalar_one_or_none()
        return PickingResponse(
            order_id=order_id,
            warehouse_substatus="PICKING",
            assigned_labourer_id=labourer_id,
            message="Picking already in progress",
        )

    # Validate transition
    _validate_substatus_transition(order.warehouse_substatus, "PICKING")

    assigned_labourer_id = data.labourer_id
    if data.labourer_id:
        result = await db.execute(
            select(Labourer).where(
                Labourer.id == data.labourer_id,
                Labourer.warehouse_id == warehouse_id,
                Labourer.is_active.is_(True),
            )
        )
        labourer = result.scalar_one_or_none()
        if not labourer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Labourer not found or not active in this warehouse"
            )

        if labourer.assigned_order_id and labourer.assigned_order_id != order_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Selected labourer is already assigned to another order"
            )
        existing_assignments = (
            await db.execute(
                select(Labourer).where(
                    Labourer.warehouse_id == warehouse_id,
                    Labourer.assigned_order_id == order_id,
                    Labourer.id != labourer.id,
                )
            )
        ).scalars().all()
        for assigned_labourer in existing_assignments:
            assigned_labourer.assigned_order_id = None
        labourer.assigned_order_id = order_id
    else:
        labourer = (
            await db.execute(
                select(Labourer).where(
                    Labourer.warehouse_id == warehouse_id,
                    Labourer.is_active.is_(True),
                    Labourer.assigned_order_id == order_id,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if labourer:
            assigned_labourer_id = labourer.id
        else:
            labourer = (
                await db.execute(
                    select(Labourer).where(
                        Labourer.warehouse_id == warehouse_id,
                        Labourer.is_active.is_(True),
                        Labourer.assigned_order_id.is_(None),
                    ).limit(1)
                )
            ).scalar_one_or_none()
            if labourer:
                labourer.assigned_order_id = order_id
                assigned_labourer_id = labourer.id

    order.warehouse_substatus = "PICKING"
    order.picking_started_at = datetime.now(UTC)

    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="PICKING",
        assigned_labourer_id=assigned_labourer_id,
        message="Picking started successfully",
    )


async def revert_picking(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Undo start-picking: revert order from PICKING back to AWAITING_PICK."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    _validate_substatus_transition(order.warehouse_substatus, "AWAITING_PICK")

    order.warehouse_substatus = "AWAITING_PICK"
    order.picking_started_at = None

    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="AWAITING_PICK",
        assigned_labourer_id=None,
        message="Picking reverted to awaiting",
    )


async def complete_picking(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Complete picking process for an order and deduct inventory."""
    from app.models.inventory import InventoryItem, InventoryMovement
    from app.models.order import PickedItem

    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    _validate_substatus_transition(order.warehouse_substatus, "PICKED")

    order_items = (await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )).scalars().all()
    picked_items = (await db.execute(
        select(PickedItem).where(PickedItem.order_id == order_id)
    )).scalars().all()
    picked_by_sku = {picked_item.sku: picked_item for picked_item in picked_items}

    # Exclude packing materials (PKG-* or name-matched) — they are consumed during packing, not picking
    _PICK_PACKING_KWS = ["carton", "box", "bubble", "wrap", "tape", "crate", "blanket", "pad", "wardrobe", "packing", "pack"]
    cargo_items = []
    for _oi in order_items:
        if _oi.sku.startswith("PKG-"):
            continue
        _inv = (await db.execute(
            select(InventoryItem).where(InventoryItem.warehouse_id == warehouse_id, InventoryItem.sku == _oi.sku)
        )).scalar_one_or_none()
        if _inv:
            _text = ((_inv.name or "") + " " + (_inv.category or "")).lower()
            if any(kw in _text for kw in _PICK_PACKING_KWS):
                continue
        cargo_items.append(_oi)

    if picked_items:
        incomplete_items: list[str] = []
        for order_item in cargo_items:
            picked_item = picked_by_sku.get(order_item.sku)
            picked_qty = picked_item.quantity_picked if picked_item else 0
            if picked_qty < order_item.quantity:
                incomplete_items.append(
                    f"{order_item.sku} ({order_item.quantity - picked_qty} remaining)"
                )

        if incomplete_items:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="All order items must be confirmed before completing picking: "
                + ", ".join(incomplete_items),
            )
    else:
        # Only run fallback deduction if no prior movements exist for this order
        existing_movement = (
            await db.execute(
                select(InventoryMovement).where(
                    InventoryMovement.reference_order_id == order_id,
                    InventoryMovement.movement_type == "PICK",
                ).limit(1)
            )
        ).scalar_one_or_none()

        if not existing_movement:
            for order_item in cargo_items:  # Only deduct cargo items here; PKG-* deducted in complete_packing
                inventory_result = await db.execute(
                    select(InventoryItem).where(
                        InventoryItem.warehouse_id == warehouse_id,
                        InventoryItem.sku == order_item.sku,
                    )
                )
                inventory_item = inventory_result.scalar_one_or_none()

                if inventory_item:
                    deduct_qty = min(order_item.quantity, inventory_item.quantity_on_hand)
                    if deduct_qty > 0:
                        inventory_item.quantity_on_hand -= deduct_qty

                        movement = InventoryMovement(
                            item_id=inventory_item.id,
                            movement_type="PICK",
                            quantity=deduct_qty,
                            reference_order_id=order_id,
                            performed_by=None,
                        )
                        db.add(movement)

    order.warehouse_substatus = "PICKED"
    order.picking_completed_at = datetime.now(UTC)
    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="PICKED",
        assigned_labourer_id=None,
        message="Picking completed successfully.",
    )


async def confirm_pick_item(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data,  # ConfirmPickItemRequest
    user_id: UUID,
):
    """Confirm picking of a specific item (supports partial picking)."""
    from app.models.inventory import InventoryItem, InventoryMovement
    from app.models.order import PickedItem

    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    # Must be in PICKING status
    if order.warehouse_substatus != "PICKING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be in PICKING status to confirm items"
        )

    # Verify this SKU exists in the order
    order_item_result = await db.execute(
        select(OrderItem).where(
            OrderItem.order_id == order_id,
            OrderItem.sku == data.sku,
        )
    )
    order_item = order_item_result.scalar_one_or_none()
    if not order_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU {data.sku} not found in this order"
        )

    # Get or create PickedItem record
    picked_result = await db.execute(
        select(PickedItem).where(
            PickedItem.order_id == order_id,
            PickedItem.sku == data.sku,
        )
    )
    picked_item = picked_result.scalar_one_or_none()

    if not picked_item:
        picked_item = PickedItem(
            order_id=order_id,
            sku=data.sku,
            quantity_picked=0,
            quantity_required=order_item.quantity,
            picked_by=user_id,
            location=data.location,
            notes=data.notes,
        )
        db.add(picked_item)

    # Update picked quantity
    new_total = picked_item.quantity_picked + data.quantity_picked
    if new_total > picked_item.quantity_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pick {new_total} items (only {picked_item.quantity_required} required)"
        )

    picked_item.quantity_picked = new_total
    picked_item.picked_by = user_id
    if data.location:
        picked_item.location = data.location
    if data.notes:
        picked_item.notes = data.notes

    # Deduct inventory immediately
    inventory_result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.warehouse_id == warehouse_id,
            InventoryItem.sku == data.sku,
        )
    )
    inventory_item = inventory_result.scalar_one_or_none()

    if inventory_item:
        if inventory_item.quantity_on_hand < data.quantity_picked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for {data.sku}: "
                       f"need {data.quantity_picked}, available {inventory_item.quantity_on_hand}",
            )

        inventory_item.quantity_on_hand -= data.quantity_picked

        # Create movement record
        movement = InventoryMovement(
            item_id=inventory_item.id,
            movement_type="PICK",
            quantity=data.quantity_picked,
            reference_order_id=order_id,
            performed_by=user_id,
        )
        db.add(movement)

    await db.commit()
    picked_item = (
        await db.execute(
            select(PickedItem)
            .options(selectinload(PickedItem.picker))
            .where(PickedItem.id == picked_item.id)
        )
    ).scalar_one()

    from app.schemas.warehouse_operations import PickedItemResponse
    return PickedItemResponse(
        id=picked_item.id,
        order_id=picked_item.order_id,
        sku=picked_item.sku,
        quantity_picked=picked_item.quantity_picked,
        quantity_required=picked_item.quantity_required,
        picked_by=picked_item.picked_by,
        picker_name=_format_user_name(picked_item.picker),
        location=picked_item.location,
        notes=picked_item.notes,
        is_complete=picked_item.quantity_picked >= picked_item.quantity_required,
        created_at=picked_item.created_at,
        updated_at=picked_item.updated_at,
    )


async def get_pick_progress(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
):
    """Get picking progress for an order."""
    from app.models.order import PickedItem

    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    # Get all order items
    order_items_result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    order_items = order_items_result.scalars().all()

    # Get all picked items
    picked_items_result = await db.execute(
        select(PickedItem)
        .options(selectinload(PickedItem.picker))
        .where(PickedItem.order_id == order_id)
    )
    picked_items_list = picked_items_result.scalars().all()

    # Build picked items map
    picked_map = {pi.sku: pi for pi in picked_items_list}

    # Build response items
    items_response = []
    total_items = len(order_items)
    completed_count = 0

    for order_item in order_items:
        picked_item = picked_map.get(order_item.sku)

        if picked_item:
            from app.schemas.warehouse_operations import PickedItemResponse
            items_response.append(PickedItemResponse(
                id=picked_item.id,
                order_id=picked_item.order_id,
                sku=picked_item.sku,
                quantity_picked=picked_item.quantity_picked,
                quantity_required=picked_item.quantity_required,
                picked_by=picked_item.picked_by,
                picker_name=_format_user_name(picked_item.picker),
                location=picked_item.location,
                notes=picked_item.notes,
                is_complete=picked_item.quantity_picked >= picked_item.quantity_required,
                created_at=picked_item.created_at,
                updated_at=picked_item.updated_at,
            ))

            if picked_item.quantity_picked >= picked_item.quantity_required:
                completed_count += 1

    from app.schemas.warehouse_operations import PickProgressResponse
    return PickProgressResponse(
        order_id=order_id,
        total_items=total_items,
        picked_items=completed_count,
        is_complete=completed_count >= total_items,
        items=items_response,
    )
