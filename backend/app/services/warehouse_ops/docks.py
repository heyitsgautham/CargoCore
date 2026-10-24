"""Loading docks: truck assignment, release and maintenance."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.warehouse import (
    LoadingDock,
    QualityCheck,
)
from app.schemas.warehouse_operations import (
    AssignTruckRequest,
    DockVerificationData,
    LoadingDockCreate,
    LoadingDockListResponse,
    LoadingDockResponse,
)
from app.services.warehouse_ops.common import (
    _get_order,
    _get_warehouse,
    _validate_substatus_transition,
)

# ======================
# Loading Dock Operations
# ======================

async def get_loading_docks(
    db: AsyncSession,
    warehouse_id: UUID,
) -> LoadingDockListResponse:
    """Get all loading docks for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(LoadingDock)
        .options(selectinload(LoadingDock.assigned_order), selectinload(LoadingDock.assigned_vehicle))
        .where(LoadingDock.warehouse_id == warehouse_id)
        .order_by(LoadingDock.dock_number)
    )
    docks = result.scalars().all()

    # Lazy-seed: if this warehouse has no docks yet, create 6 now
    if not docks:
        for i in range(1, 7):
            db.add(LoadingDock(warehouse_id=warehouse_id, dock_number=str(i), status="FREE"))
        await db.flush()
        result = await db.execute(
            select(LoadingDock)
            .options(selectinload(LoadingDock.assigned_order), selectinload(LoadingDock.assigned_vehicle))
            .where(LoadingDock.warehouse_id == warehouse_id)
            .order_by(LoadingDock.dock_number)
        )
        docks = result.scalars().all()

    items = []
    now = datetime.now(UTC)
    for dock in docks:
        dwell_minutes = 0
        if dock.arrived_at and dock.status == "OCCUPIED":
            dwell_minutes = int((now - dock.arrived_at).total_seconds() / 60)

        order_tracking = None
        if dock.assigned_order:
            order_tracking = dock.assigned_order.tracking_code

        vehicle_code = None
        if dock.assigned_vehicle:
            v = dock.assigned_vehicle
            vehicle_code = f"{v.code} · {v.license_plate}" if v.license_plate else v.code

        items.append(LoadingDockResponse(
            id=dock.id,
            warehouse_id=dock.warehouse_id,
            dock_number=dock.dock_number,
            status=dock.status,
            assigned_vehicle_id=dock.assigned_vehicle_id,
            assigned_vehicle_code=vehicle_code,
            assigned_carrier=dock.assigned_carrier,
            assigned_order_id=dock.assigned_order_id,
            assigned_order_tracking=order_tracking,
            arrived_at=dock.arrived_at,
            loading_started_at=dock.loading_started_at,
            released_at=dock.released_at,
            dwell_minutes=dwell_minutes,
            created_at=dock.created_at,
        ))

    return LoadingDockListResponse(items=items, total=len(items))


async def create_loading_dock(
    db: AsyncSession,
    warehouse_id: UUID,
    data: LoadingDockCreate,
) -> LoadingDockResponse:
    """Create a new loading dock."""
    await _get_warehouse(db, warehouse_id)

    dock = LoadingDock(
        warehouse_id=warehouse_id,
        dock_number=data.dock_number,
        status="FREE",
    )
    db.add(dock)
    await db.commit()
    await db.refresh(dock)

    return LoadingDockResponse(
        id=dock.id,
        warehouse_id=dock.warehouse_id,
        dock_number=dock.dock_number,
        status=dock.status,
        assigned_vehicle_id=None,
        assigned_vehicle_code=None,
        assigned_carrier=None,
        assigned_order_id=None,
        assigned_order_tracking=None,
        arrived_at=None,
        loading_started_at=None,
        released_at=None,
        dwell_minutes=0,
        created_at=dock.created_at,
    )


async def assign_truck_to_dock(
    db: AsyncSession,
    warehouse_id: UUID,
    dock_id: UUID,
    data: AssignTruckRequest,
) -> LoadingDockResponse:
    """Assign a truck to a loading dock."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(LoadingDock)
        .options(selectinload(LoadingDock.assigned_order), selectinload(LoadingDock.assigned_vehicle))
        .where(LoadingDock.id == dock_id, LoadingDock.warehouse_id == warehouse_id)
    )
    dock = result.scalar_one_or_none()
    if not dock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loading dock not found")

    if dock.status != "FREE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dock is not available (current status: {dock.status})"
        )

    # Validate the vehicle exists and is available
    from app.models.logistics import LogisticsVehicle
    vehicle_result = await db.execute(
        select(LogisticsVehicle).where(LogisticsVehicle.id == data.vehicle_id)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    if vehicle.status == "In Use":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Vehicle {vehicle.code} is already in use")

    # If order is provided, update its substatus and persist vehicle on the order
    if data.order_id:
        order = await _get_order(db, data.order_id)
        if order.warehouse_id != warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order does not belong to this warehouse"
            )
        _validate_substatus_transition(order.warehouse_substatus, "ON_DOCK")
        order.warehouse_substatus = "ON_DOCK"
        order.assigned_vehicle_id = data.vehicle_id  # persist vehicle on order for dispatcher

    # Mark vehicle as In Use so it disappears from available lists
    vehicle.status = "In Use"

    dock.assigned_vehicle_id = data.vehicle_id
    dock.assigned_carrier = "Internal Fleet"
    dock.assigned_order_id = data.order_id
    dock.arrived_at = datetime.now(UTC)
    dock.status = "OCCUPIED"

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(LoadingDock)
        .options(selectinload(LoadingDock.assigned_order), selectinload(LoadingDock.assigned_vehicle))
        .where(LoadingDock.id == dock_id)
    )
    dock = result.scalar_one()

    order_tracking = dock.assigned_order.tracking_code if dock.assigned_order else None
    v = dock.assigned_vehicle
    vehicle_code = (f"{v.code} · {v.license_plate}" if v.license_plate else v.code) if v else None

    return LoadingDockResponse(
        id=dock.id,
        warehouse_id=dock.warehouse_id,
        dock_number=dock.dock_number,
        status=dock.status,
        assigned_vehicle_id=dock.assigned_vehicle_id,
        assigned_vehicle_code=vehicle_code,
        assigned_carrier=dock.assigned_carrier,
        assigned_order_id=dock.assigned_order_id,
        assigned_order_tracking=order_tracking,
        arrived_at=dock.arrived_at,
        loading_started_at=dock.loading_started_at,
        released_at=dock.released_at,
        dwell_minutes=0,
        created_at=dock.created_at,
    )


async def release_dock(
    db: AsyncSession,
    warehouse_id: UUID,
    dock_id: UUID,
    verification: DockVerificationData,
) -> LoadingDockResponse:
    """Release a loading dock after verification."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(LoadingDock)
        .options(selectinload(LoadingDock.assigned_order))
        .where(LoadingDock.id == dock_id, LoadingDock.warehouse_id == warehouse_id)
    )
    dock = result.scalar_one_or_none()
    if not dock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loading dock not found")

    if dock.status != "OCCUPIED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dock is not occupied (current status: {dock.status})"
        )

    # Verify all checks passed
    if not all([
        verification.items_scanned,
        verification.labor_present,
        verification.packing_loaded,
        verification.manifest_attached,
        verification.driver_confirmed,
        verification.weight_verified,
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All verification checks must pass before releasing dock"
        )

    # Update order substatus if assigned
    if dock.assigned_order:
        order = dock.assigned_order

        # Ensure QC was passed before allowing dispatch
        qc_passed = (
            await db.execute(
                select(QualityCheck).where(
                    QualityCheck.order_id == order.id,
                    QualityCheck.is_passed.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not qc_passed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Quality check must be passed before dispatching the order",
            )

        _validate_substatus_transition(order.warehouse_substatus, "DISPATCHED")
        order.warehouse_substatus = "DISPATCHED"

    now = datetime.now(UTC)
    dwell_minutes = 0
    if dock.arrived_at:
        dwell_minutes = int((now - dock.arrived_at).total_seconds() / 60)

    # If NO order was linked to this dock, there is nothing downstream to release the
    # vehicle — free it immediately so it doesn't stay stuck in "In Use" forever.
    # When an order IS linked, the vehicle stays "In Use" until the dispatcher moves
    # the order to IN_TRANSIT / DELIVERED (handled by _release_order_resources).
    if not dock.assigned_order and dock.assigned_vehicle_id:
        from app.models.logistics import LogisticsVehicle as _LV
        _veh = (await db.execute(select(_LV).where(_LV.id == dock.assigned_vehicle_id))).scalar_one_or_none()
        if _veh and _veh.status == "In Use":
            _veh.status = "Active"

    dock.released_at = now
    dock.status = "FREE"
    dock.assigned_vehicle_id = None
    dock.assigned_carrier = None
    dock.assigned_order_id = None
    dock.arrived_at = None
    dock.loading_started_at = None

    await db.commit()
    await db.refresh(dock)

    return LoadingDockResponse(
        id=dock.id,
        warehouse_id=dock.warehouse_id,
        dock_number=dock.dock_number,
        status=dock.status,
        assigned_vehicle_id=None,
        assigned_vehicle_code=None,
        assigned_carrier=None,
        assigned_order_id=None,
        assigned_order_tracking=None,
        arrived_at=None,
        loading_started_at=None,
        released_at=dock.released_at,
        dwell_minutes=dwell_minutes,
        created_at=dock.created_at,
    )


async def set_dock_maintenance(
    db: AsyncSession,
    warehouse_id: UUID,
    dock_id: UUID,
    is_maintenance: bool,
) -> LoadingDockResponse:
    """Set dock maintenance status."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(LoadingDock)
        .where(LoadingDock.id == dock_id, LoadingDock.warehouse_id == warehouse_id)
    )
    dock = result.scalar_one_or_none()
    if not dock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loading dock not found")

    if dock.status == "OCCUPIED" and is_maintenance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot set maintenance while dock is occupied"
        )

    dock.status = "MAINTENANCE" if is_maintenance else "FREE"

    await db.commit()
    await db.refresh(dock)

    return LoadingDockResponse(
        id=dock.id,
        warehouse_id=dock.warehouse_id,
        dock_number=dock.dock_number,
        status=dock.status,
        assigned_vehicle_id=dock.assigned_vehicle_id,
        assigned_vehicle_code=None,
        assigned_carrier=dock.assigned_carrier,
        assigned_order_id=dock.assigned_order_id,
        assigned_order_tracking=None,
        arrived_at=dock.arrived_at,
        loading_started_at=dock.loading_started_at,
        released_at=dock.released_at,
        dwell_minutes=0,
        created_at=dock.created_at,
    )
