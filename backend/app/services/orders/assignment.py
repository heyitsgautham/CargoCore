"""Confirming orders, choosing a warehouse and assigning drivers and vehicles."""

from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, InventoryMovement
from app.models.labour import Labourer
from app.models.logistics import (
    LogisticsDriverProfile,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.schemas.orders import (
    OrderAssignRequest,
    OrderResponse,
)
from app.services.orders.common import (
    _get_active_warehouse,
    _get_order,
    _resolve_names,
    _select_auto_assignment_warehouse,
    _to_order_response,
    _validate_transition,
)
from app.services.orders.trip_intelligence import get_trip_intelligence


async def get_order_assignment_preview(
    db: AsyncSession,
    warehouse_id: UUID | None = None,
) -> dict:
    if warehouse_id:
        warehouse = await _get_active_warehouse(db, warehouse_id)
        return {
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "warehouse_address": warehouse.address,
            "assignment_type": "selected",
            "message": f"This order will go to {warehouse.name} because you selected it.",
        }

    warehouse = await _select_auto_assignment_warehouse(db)
    return {
        "warehouse_id": warehouse.id,
        "warehouse_name": warehouse.name,
        "warehouse_address": warehouse.address,
        "assignment_type": "auto",
        "message": f"If you book now, the order will auto-assign to {warehouse.name} based on current hub readiness and open load.",
    }


async def confirm_order(db: AsyncSession, order_id: UUID, user: User) -> OrderResponse:
    order = await _get_order(db, order_id)

    # WAREHOUSE_MANAGER can only confirm orders assigned to their warehouse
    if user.role.name == "WAREHOUSE_MANAGER":
        if not user.warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not assigned to a warehouse",
            )
        if order.warehouse_id != user.warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only confirm orders assigned to your warehouse",
            )

    _validate_transition(order.status, "CONFIRMED")

    # Check inventory availability for all order items (cargo + packing materials)
    # PKG-* items are only validated if the warehouse has set up those inventory records.
    if order.items and order.warehouse_id:
        insufficient: list[str] = []
        items_to_deduct: list[tuple[InventoryItem, int]] = []

        for item in order.items:
            inv = (
                await db.execute(
                    select(InventoryItem).where(
                        InventoryItem.warehouse_id == order.warehouse_id,
                        InventoryItem.sku == item.sku,
                    )
                )
            ).scalar_one_or_none()

            # If no inventory record exists for this SKU, skip (untracked item)
            if inv is None:
                continue

            available = inv.quantity_on_hand
            if available < item.quantity:
                # User-friendly name: strip PKG- prefix for packing material SKUs
                display = item.sku.replace("PKG-", "").replace("-", " ").title() if item.sku.startswith("PKG-") else item.sku
                insufficient.append(
                    f"{display} (need {item.quantity}, have {available})"
                )
            else:
                items_to_deduct.append((inv, item.quantity))

        if insufficient:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Insufficient stock for: " + ", ".join(insufficient),
            )

        # Deduct inventory and record OUTBOUND movements for each item
        for inv_item, qty in items_to_deduct:
            inv_item.quantity_on_hand -= qty
            db.add(inv_item)
            db.add(
                InventoryMovement(
                    item_id=inv_item.id,
                    movement_type="OUTBOUND",
                    quantity=qty,
                    reference_order_id=order.id,
                    performed_by=user.id,
                )
            )


    # Guard: for ONLINE payment orders, payment must be completed before confirming
    if order.payment_mode and order.payment_mode.upper() == "ONLINE" and order.payment_status != "paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Online payment must be completed before confirming the order",
        )

    order.status = "CONFIRMED"
    # Set initial warehouse substatus so order appears in warehouse picking queue
    order.warehouse_substatus = "AWAITING_PICK"
    db.add(order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])
    return _to_order_response(order)



async def assign_order(db: AsyncSession, order_id: UUID, data: OrderAssignRequest) -> OrderResponse:
    order = await _get_order(db, order_id)

    # If the order is already dispatched/in-transit and we're patching just the vehicle,
    # skip the status transition — keep the current status, only update the vehicle.
    already_active = order.status in ("ASSIGNED", "IN_TRANSIT")
    vehicle_patch_only = (
        already_active
        and data.vehicle_id is not None
        and (data.driver_id is None or data.driver_id == order.assigned_driver_id)
    )

    if not vehicle_patch_only:
        _validate_transition(order.status, "ASSIGNED")

    # Check if driver already has an active order (ASSIGNED or IN_TRANSIT)
    if data.driver_id and not vehicle_patch_only:
        existing_order = (await db.execute(
            select(Order).where(
                Order.assigned_driver_id == data.driver_id,
                Order.status.in_(["ASSIGNED", "IN_TRANSIT"]),
                Order.id != order_id  # Exclude current order (for re-assignment cases)
            )
        )).scalar_one_or_none()
        if existing_order:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Driver is already assigned to an active order ({existing_order.tracking_code}). Complete or unassign that order first."
            )

    if data.driver_id:
        order.assigned_driver_id = data.driver_id
    order.assigned_vehicle_id = data.vehicle_id
    if not vehicle_patch_only:
        order.status = "ASSIGNED"


    # Update driver profile current_job
    if data.driver_id:
        profile = (await db.execute(select(LogisticsDriverProfile).where(LogisticsDriverProfile.user_id == data.driver_id))).scalar_one_or_none()
        if profile:
            profile.current_job = order.tracking_code
            db.add(profile)

    # Mark vehicle as In Use
    if data.vehicle_id:
        vehicle = (await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.id == data.vehicle_id))).scalar_one_or_none()
        if vehicle:
            vehicle.status = "In Use"
    # Auto-assign available labourers up to labor_count
    if order.labor_count and order.labor_count > 0:
        available = (await db.execute(
            select(Labourer)
            .where(Labourer.assigned_order_id.is_(None), Labourer.is_active == True)
            .limit(order.labor_count)
        )).scalars().all()
        for labourer in available:
            labourer.assigned_order_id = order.id
    db.add(order)
    # Auto-record labour and driver shift expenses
    from app.services import finance_service as _fs
    if order.labor_count and order.labor_count > 0:
        await _fs.record_expense(
            db,
            expense_type="EXPENSE_LABOUR",
            amount=order.labor_count * _fs.LABOUR_RATE_PER_HEAD,
            description=f"Labour ({order.labor_count} helpers) for {order.tracking_code}",
            warehouse_id=order.warehouse_id,
            order_id=order.id,
            tracking_code=order.tracking_code,
        )
    await _fs.record_expense(
        db,
        expense_type="EXPENSE_DRIVER",
        amount=_fs.DRIVER_SHIFT_RATE,
        description=f"Driver shift fee for {order.tracking_code}",
        warehouse_id=order.warehouse_id,
        order_id=order.id,
        tracking_code=order.tracking_code,
    )
    await db.flush()
    await db.refresh(order, attribute_names=["items"])
    dn, vc, cn, cp = await _resolve_names(db, [order])
    response = _to_order_response(
        order,
        driver_name=dn.get(order.assigned_driver_id),
        vehicle_code=vc.get(order.assigned_vehicle_id),
        customer_name=cn.get(order.customer_id),
        customer_phone=cp.get(order.customer_id),
    )

    # Notify the assigned driver in real-time via WebSocket
    if data.driver_id:
        try:
            from app.routers.ws_fleet import driver_alert_manager
            trip_intelligence = await get_trip_intelligence(db, order.id)
            await driver_alert_manager.send_to_driver(str(data.driver_id), {
                "type": "job_assigned",
                "order_id": str(order.id),
                "tracking_code": order.tracking_code or "",
                "order_type": order.order_type or "PARCEL_DELIVERY",
                "title": "New Job Assigned",
                "message": f"Order {order.tracking_code} has been dispatched to you",
                "pickup_addr": order.pickup_addr or "",
                "delivery_addr": order.delivery_addr or "",
                "trip_intelligence": jsonable_encoder(trip_intelligence),
            })
        except Exception:
            pass  # WebSocket notification is best-effort; don't fail the assignment

    return response


async def _release_order_resources(db: AsyncSession, order: Order) -> None:
    """Release vehicle, driver, and labourers when an order is completed or cancelled."""
    # Release vehicle
    if order.assigned_vehicle_id:
        vehicle = (await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.id == order.assigned_vehicle_id))).scalar_one_or_none()
        if vehicle and vehicle.status == "In Use":
            vehicle.status = "Active"

    # Release labourers assigned to this order
    labourers = (await db.execute(
        select(Labourer).where(Labourer.assigned_order_id == order.id)
    )).scalars().all()
    for labourer in labourers:
        labourer.assigned_order_id = None

    # Update driver profile: clear current_job and snap location to delivery point.
    #
    # WHY: When a driver marks a job as DELIVERED, they are physically at the delivery
    # address at that instant. Anchoring current_location to delivery coords means:
    #   1. The AI dispatch engine immediately knows where the driver is without waiting
    #      for the next GPS ping.
    #   2. Return-trip suggestions fire correctly right after delivery (the driver is
    #      genuinely near the delivery point).
    #   3. In demo/test mode (phone on a desk), the system behaves identically to a
    #      real deployment where GPS would report the same location.
    #
    # This is standard "dead reckoning from job events" used by all major logistics platforms.
    if order.assigned_driver_id:
        profile = (await db.execute(
            select(LogisticsDriverProfile).where(LogisticsDriverProfile.user_id == order.assigned_driver_id)
        )).scalar_one_or_none()
        if profile:
            if profile.current_job == order.tracking_code:
                profile.current_job = None

            # Snap to delivery coordinates if the completed order has them
            if order.delivery_lat is not None and order.delivery_lng is not None:
                profile.current_location = f"{order.delivery_lat},{order.delivery_lng}"

            db.add(profile)
            await db.flush()

            # Broadcast the position update over WebSocket so the dispatcher map
            # moves the driver pin to the delivery address in real time.
            try:
                driver_user = (await db.execute(
                    select(User).where(User.id == order.assigned_driver_id)
                )).scalar_one_or_none()

                if driver_user and order.delivery_lat is not None:
                    import asyncio

                    from app.routers.ws_fleet import fleet_manager
                    asyncio.ensure_future(
                        fleet_manager.broadcast({
                            "type": "location_update",
                            "driver_id": str(driver_user.id),
                            "driver_name": driver_user.name,
                            "latitude": order.delivery_lat,
                            "longitude": order.delivery_lng,
                            "status": profile.status,
                            "vehicle_code": None,
                            "vehicle_id": None,
                            "last_updated": order.delivered_at.isoformat() if order.delivered_at else None,
                            # Extra field so the frontend knows this was a job-completion anchor,
                            # not a live GPS ping — useful for future display differentiation.
                            "source": "job_completion",
                        })
                    )
            except Exception:
                pass  # WebSocket broadcast is best-effort; never fail the DB commit
