from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem
from app.models.labour import Labourer
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse
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
    warehouse = Warehouse(**data.model_dump())
    db.add(warehouse)
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

    if user_count or inventory_count or order_count or labour_count:
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
