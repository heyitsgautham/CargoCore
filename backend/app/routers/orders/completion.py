"""After delivery: house-shift sign-off, job and customer ratings, packing returns, asset logs and the arrival simulator."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.orders import (
    AssetLogRequest,
    CustomerRatingRequest,
    HouseShiftSignoffRequest,
    JobRatingRequest,
    OrderResponse,
    PackingReturnRequest,
)
from app.services import orders_service

router = APIRouter()


@router.post("/{order_id}/house-shift-signoff", response_model=OrderResponse)
async def house_shift_signoff(
    order_id: UUID,
    data: HouseShiftSignoffRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    """Complete a house-shift job with customer sign-off signature (no OTP required)."""
    return await orders_service.house_shift_signoff(
        db,
        order_id,
        user,
        signature_data=data.signature_data,
        customer_name=data.customer_name,
        notes=data.notes,
    )


@router.post("/{order_id}/job-rating", response_model=OrderResponse)
async def submit_job_rating(
    order_id: UUID,
    data: JobRatingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    """Submit driver's self-rating (1–5 stars) and optional feedback for a completed job."""
    return await orders_service.submit_job_rating(
        db,
        order_id,
        user,
        rating=data.rating,
        feedback=data.feedback,
    )


@router.post("/{order_id}/customer-rating", response_model=OrderResponse)
async def submit_customer_rating(
    order_id: UUID,
    data: CustomerRatingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Submit customer/vendor rating (1–5 stars) of the driver for a completed order."""
    return await orders_service.submit_customer_rating(
        db,
        order_id,
        user,
        rating=data.rating,
        feedback=data.feedback,
    )


@router.post("/{order_id}/packing-return", response_model=OrderResponse)
async def submit_packing_return(
    order_id: UUID,
    data: PackingReturnRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    """Driver submits how many packing assets they are returning to warehouse."""
    from sqlalchemy import select as _select

    from app.models.order import Order as _Order

    order = (await db.execute(_select(_Order).where(_Order.id == order_id))).scalar_one_or_none()
    if order is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")

    order.packing_return_data = {
        "items": [{"name": i.name, "sku": i.sku, "count": i.count} for i in data.items],
        "notes": data.notes or "",
        "submitted_at": data.submitted_at,
        "submitted_by": str(user.id),
        "skipped": data.skipped,
    }
    await db.commit()
    await db.refresh(order)
    return await orders_service.get_order_detail(db, order_id, user)


@router.post("/{order_id}/asset-log")
async def save_asset_log(
    order_id: UUID,
    data: AssetLogRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """
    Dispatcher saves the packing asset return log for an order.
    For each item with returned > 0, creates an RETURN inventory movement
    to add the items back into warehouse stock.
    """
    from fastapi import HTTPException
    from sqlalchemy import select as _select

    from app.models.inventory import InventoryItem, InventoryMovement
    from app.models.order import Order as _Order

    order = (await db.execute(_select(_Order).where(_Order.id == order_id))).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    warehouse_id = order.warehouse_id
    restored_count = 0

    for item in data.items:
        if item.returned <= 0:
            continue

        inv_item = None

        # 1. Try exact SKU match first
        if item.sku:
            inv_item = (await db.execute(
                _select(InventoryItem).where(
                    InventoryItem.warehouse_id == warehouse_id,
                    InventoryItem.sku == item.sku,
                )
            )).scalar_one_or_none()

        # 2. Fall back to name-based match
        if inv_item is None and item.name:
            name_lower = item.name.lower()
            all_inv = (await db.execute(
                _select(InventoryItem).where(InventoryItem.warehouse_id == warehouse_id)
            )).scalars().all()
            for candidate in all_inv:
                candidate_text = ((candidate.name or "") + " " + (candidate.category or "")).lower()
                if any(word in candidate_text for word in name_lower.split() if len(word) > 3):
                    inv_item = candidate
                    break

        if inv_item is None:
            continue

        # Idempotency: skip if a RETURN movement already exists for this item + order
        existing = (await db.execute(
            _select(InventoryMovement).where(
                InventoryMovement.item_id == inv_item.id,
                InventoryMovement.reference_order_id == order_id,
                InventoryMovement.movement_type == "RETURN",
            ).limit(1)
        )).scalar_one_or_none()

        if existing:
            # Update quantity if the log is being revised
            existing.quantity = item.returned
            inv_item.quantity_on_hand = max(0, inv_item.quantity_on_hand - existing.quantity + item.returned)
        else:
            movement = InventoryMovement(
                item_id=inv_item.id,
                movement_type="RETURN",
                quantity=item.returned,
                reference_order_id=order_id,
                performed_by=user.id,
            )
            db.add(movement)
            inv_item.quantity_on_hand += item.returned

        restored_count += 1

    await db.commit()
    return {
        "order_id": str(order_id),
        "items_restored": restored_count,
        "message": f"Asset log saved. {restored_count} item type(s) restored to inventory.",
    }


@router.post("/{order_id}/simulate-arrival", response_model=dict)
async def simulate_driver_arrival(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Dev/demo endpoint: simulate the assigned driver arriving within 50 m of the
    pickup address.  Updates the driver's current_location so the live tracking
    map shows the truck near the pickup pin and the geofence alert fires on the
    customer's screen.
    """
    import random

    from fastapi import HTTPException
    from sqlalchemy import select as _select

    from app.models.logistics import LogisticsDriverProfile
    from app.models.order import Order as _Order

    order = (await db.execute(_select(_Order).where(_Order.id == order_id))).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only the customer who owns the order (or staff) may call this
    if str(order.customer_id) != str(user.id) and user.role not in {
        "LOGISTIC_MANAGER", "DISPATCHER", "WAREHOUSE_MANAGER", "ADMIN"
    }:
        raise HTTPException(status_code=403, detail="Not authorised")

    if not order.assigned_driver_id:
        raise HTTPException(status_code=400, detail="No driver assigned to this order yet")

    lat = order.pickup_lat
    lng = order.pickup_lng
    if lat is None or lng is None:
        raise HTTPException(status_code=400, detail="Pickup coordinates not available for this order")

    # Offset by ~30–50 m (≈0.00027°–0.00045°) so it looks natural
    offset_deg = 0.0003
    sim_lat = round(lat + random.uniform(-offset_deg, offset_deg), 6)
    sim_lng = round(lng + random.uniform(-offset_deg, offset_deg), 6)

    profile = (
        await db.execute(
            _select(LogisticsDriverProfile).where(
                LogisticsDriverProfile.user_id == order.assigned_driver_id
            )
        )
    ).scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    profile.current_location = f"{sim_lat},{sim_lng}"
    await db.commit()

    return {
        "order_id": str(order_id),
        "driver_id": str(order.assigned_driver_id),
        "simulated_lat": sim_lat,
        "simulated_lng": sim_lng,
        "message": "Driver location updated to within 50 m of pickup. Geofence alert will fire.",
    }
