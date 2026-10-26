from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, InventoryMovement
from app.models.labour import Labourer
from app.models.logistics import LogisticsZone
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import LoadingDock, QualityCheck, ReturnGrading, Warehouse
from app.schemas.warehouse import (
    FloorPlanUpdate,
    WarehouseCreate,
    WarehouseKPIResponse,
    WarehouseListResponse,
    WarehouseResponse,
    WarehouseUpdate,
)


async def _get_warehouse(db: AsyncSession, warehouse_id: UUID) -> Warehouse:
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    warehouse = result.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return warehouse


async def list_warehouses(db: AsyncSession, page: int, page_size: int) -> WarehouseListResponse:
    total = (await db.execute(select(func.count(Warehouse.id)))).scalar_one()
    rows = (
        await db.execute(
            select(Warehouse)
            .order_by(Warehouse.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return WarehouseListResponse(
        items=[WarehouseResponse.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def create_warehouse(db: AsyncSession, data: WarehouseCreate) -> WarehouseResponse:
    existing = (
        await db.execute(
            select(Warehouse).where(func.lower(Warehouse.name) == data.name.strip().lower())
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Warehouse with this name already exists")

    warehouse = Warehouse(**data.model_dump())
    db.add(warehouse)
    await db.flush()

    # Auto-seed 6 loading docks for the new warehouse
    for i in range(1, 7):
        db.add(LoadingDock(warehouse_id=warehouse.id, dock_number=str(i), status="FREE"))
    await db.flush()

    await db.refresh(warehouse)
    return WarehouseResponse.model_validate(warehouse)


async def get_warehouse_detail(db: AsyncSession, warehouse_id: UUID) -> WarehouseResponse:
    warehouse = await _get_warehouse(db, warehouse_id)
    return WarehouseResponse.model_validate(warehouse)


async def update_warehouse(
    db: AsyncSession,
    warehouse_id: UUID,
    data: WarehouseUpdate,
) -> WarehouseResponse:
    warehouse = await _get_warehouse(db, warehouse_id)

    if data.name and data.name.strip().lower() != warehouse.name.lower():
        existing = (
            await db.execute(
                select(Warehouse).where(func.lower(Warehouse.name) == data.name.strip().lower())
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Warehouse with this name already exists")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(warehouse, key, value)

    db.add(warehouse)
    await db.flush()
    await db.refresh(warehouse)
    return WarehouseResponse.model_validate(warehouse)


async def delete_warehouse(db: AsyncSession, warehouse_id: UUID) -> None:
    warehouse = await _get_warehouse(db, warehouse_id)

    user_count = (await db.execute(select(func.count(User.id)).where(User.warehouse_id == warehouse_id))).scalar_one()
    inventory_count = (
        await db.execute(select(func.count(InventoryItem.id)).where(InventoryItem.warehouse_id == warehouse_id))
    ).scalar_one()
    order_count = (await db.execute(select(func.count(Order.id)).where(Order.warehouse_id == warehouse_id))).scalar_one()
    labour_count = (await db.execute(select(func.count(Labourer.id)).where(Labourer.warehouse_id == warehouse_id))).scalar_one()
    record_count = 0
    for model in (QualityCheck, ReturnGrading, LogisticsZone):
        record_count += (
            await db.execute(select(func.count()).select_from(model).where(model.warehouse_id == warehouse_id))
        ).scalar_one()

    if user_count or inventory_count or order_count or labour_count or record_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete warehouse with dependent records",
        )

    await db.delete(warehouse)
    await db.flush()


async def update_floor_plan(
    db: AsyncSession,
    warehouse_id: UUID,
    data: FloorPlanUpdate,
) -> WarehouseResponse:
    warehouse = await _get_warehouse(db, warehouse_id)
    warehouse.floor_plan_json = data.floor_plan_json
    db.add(warehouse)
    await db.flush()
    await db.refresh(warehouse)
    return WarehouseResponse.model_validate(warehouse)


async def get_warehouse_kpis(db: AsyncSession, warehouse_id: UUID) -> WarehouseKPIResponse:
    await _get_warehouse(db, warehouse_id)

    user_count = (await db.execute(select(func.count(User.id)).where(User.warehouse_id == warehouse_id))).scalar_one()
    inventory_sku_count = (
        await db.execute(select(func.count(InventoryItem.id)).where(InventoryItem.warehouse_id == warehouse_id))
    ).scalar_one()
    low_stock_count = (
        await db.execute(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.quantity_on_hand <= InventoryItem.safety_stock,
            )
        )
    ).scalar_one()
    labour_count = (await db.execute(select(func.count(Labourer.id)).where(Labourer.warehouse_id == warehouse_id))).scalar_one()
    order_count = (await db.execute(select(func.count(Order.id)).where(Order.warehouse_id == warehouse_id))).scalar_one()

    return WarehouseKPIResponse(
        warehouse_id=warehouse_id,
        user_count=user_count,
        inventory_sku_count=inventory_sku_count,
        low_stock_count=low_stock_count,
        labour_count=labour_count,
        order_count=order_count,
    )


async def mark_order_complete(db: AsyncSession, warehouse_id: UUID, order_id: UUID) -> None:
    """Mark an order as complete (PACKED status)."""
    await _get_warehouse(db, warehouse_id)

    order = (
        await db.execute(
            select(Order).where(Order.id == order_id, Order.warehouse_id == warehouse_id)
        )
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order.status = 'PACKED'
    db.add(order)
    await db.flush()


async def reassign_order(db: AsyncSession, warehouse_id: UUID, order_id: UUID) -> None:
    """Reassign order to an available laborer."""
    await _get_warehouse(db, warehouse_id)

    order = (
        await db.execute(
            select(Order).where(Order.id == order_id, Order.warehouse_id == warehouse_id)
        )
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Find an available laborer (not currently assigned)
    available_laborer = (
        await db.execute(
            select(Labourer).where(
                Labourer.warehouse_id == warehouse_id,
                Labourer.is_active == True,
                Labourer.assigned_order_id == None
            ).limit(1)
        )
    ).scalar_one_or_none()

    if available_laborer:
        # Unassign from any current laborer
        current_assigned = (
            await db.execute(
                select(Labourer).where(Labourer.assigned_order_id == order_id)
            )
        ).scalar_one_or_none()
        if current_assigned:
            current_assigned.assigned_order_id = None
            db.add(current_assigned)

        # Assign to new laborer
        available_laborer.assigned_order_id = order.id
        db.add(available_laborer)

        # Update order status to PICKING if it was pending
        if order.status in ['PENDING', 'CONFIRMED']:
            order.status = 'PICKING'
        db.add(order)

    await db.flush()


async def process_restock(db: AsyncSession, warehouse_id: UUID) -> None:
    """Process restock for all critical SKUs (auto-replenish to safety stock * 2)."""
    await _get_warehouse(db, warehouse_id)

    critical_items = (
        await db.execute(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.quantity_on_hand <= InventoryItem.safety_stock
            )
        )
    ).scalars().all()

    for item in critical_items:
        # Restock to double the safety stock level
        restock_qty = (item.safety_stock * 2) - item.quantity_on_hand
        item.quantity_on_hand += restock_qty

        # Create inventory movement record
        movement = InventoryMovement(
            item_id=item.id,
            movement_type='inbound',
            quantity=restock_qty,
            reference_order_id=None,
            performed_by=None
        )
        db.add(movement)
        db.add(item)

    await db.flush()
