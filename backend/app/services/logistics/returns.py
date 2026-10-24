"""Return cases: review, refunds and pickup scheduling."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import DamageReport, Order
from app.models.warehouse import ReturnGrading, Warehouse
from app.schemas.logistics import (
    LogisticsReturnCaseItem,
    LogisticsReturnCaseUpdate,
)
from app.services.logistics.formatting import _now
from app.services.logistics.lookups import (
    _build_return_case_item,
    _get_completed_return_grading,
    _get_return_case,
    _wallet_refund_credited,
)


async def update_return_case(db: AsyncSession, case_id: UUID, data: LogisticsReturnCaseUpdate) -> LogisticsReturnCaseItem:
    case = await _get_return_case(db, case_id)
    case.status = data.status
    if data.refund_amount is not None:
        case.refund_amount = data.refund_amount
    if data.condition is not None:
        case.condition = data.condition
    db.add(case)

    # Sync DamageReport status so customer sees the outcome
    completed_grading = await _get_completed_return_grading(db, case)
    should_apply_transport_charge = (
        data.status == "Rejected"
        and (
            data.apply_transport_charge
            or (
                getattr(case, "flow_type", None) == "pickup_inspection"
                and completed_grading is not None
                and (
                    completed_grading.is_genuine is False
                    or (completed_grading.recommended_outcome or "").strip().lower() == "reject claim"
                )
            )
        )
    )

    if should_apply_transport_charge:
        from app.models.order import Order as OriginalOrder
        from app.services.return_charge_service import (
            apply_rejected_claim_transport_charge,
        )

        customer_id = None
        if case.order_id:
            original_order = (await db.execute(
                select(OriginalOrder).where(OriginalOrder.id == case.order_id)
            )).scalar_one_or_none()
            customer_id = getattr(original_order, "customer_id", None)
        if customer_id:
            await apply_rejected_claim_transport_charge(
                db,
                case=case,
                customer_id=customer_id,
            )

    if case.reference_code:
        damage_report = (await db.execute(
            select(DamageReport).where(DamageReport.reference_code == case.reference_code)
        )).scalar_one_or_none()
        if damage_report:
            if data.status == "Approved":
                damage_report.status = "resolved"
                # Credit customer wallet and debit finance revenue
                if case.refund_amount and case.refund_amount > 0:
                    from app.services.wallet_service import credit_return_refund
                    await credit_return_refund(
                        db,
                        customer_id=damage_report.customer_id,
                        order_id=case.order_id,
                        refund_amount=case.refund_amount,
                        reference_code=case.reference_code,
                            warehouse_id=case.warehouse_id,
                    )
            elif data.status == "Rejected":
                damage_report.status = "rejected"
            elif data.status == "Pending":
                damage_report.status = "inspected"
            db.add(damage_report)

    await db.flush()
    credited = await _wallet_refund_credited(db, case.reference_code)
    return await _build_return_case_item(
        db,
        case,
        completed_grading=completed_grading,
        wallet_credited=credited,
    )


async def issue_return_refund(db: AsyncSession, case_id: UUID) -> dict:
    case = await _get_return_case(db, case_id)
    if case.status not in {"Approved", "Partially Approved", "Refunded"}:
        raise HTTPException(status_code=400, detail="Return case is not approved for wallet refund")
    if not case.refund_amount or case.refund_amount <= 0:
        raise HTTPException(status_code=400, detail="No refund amount set on this return case")

    damage_report = None
    if case.reference_code:
        damage_report = (await db.execute(
            select(DamageReport).where(DamageReport.reference_code == case.reference_code)
        )).scalar_one_or_none()

    if not damage_report:
        raise HTTPException(status_code=400, detail="No linked customer damage report found — cannot determine wallet recipient")

    from app.services.wallet_service import credit_return_refund
    credited = await credit_return_refund(
        db,
        customer_id=damage_report.customer_id,
        order_id=case.order_id,
        refund_amount=case.refund_amount,
        reference_code=case.reference_code,
        warehouse_id=case.warehouse_id,
    )
    case.status = "Refunded"
    db.add(case)
    damage_report.status = "resolved"
    db.add(damage_report)
    await db.flush()
    return {
        "credited": credited,
        "amount": case.refund_amount,
        "reference_code": case.reference_code,
        "message": "Refund credited to customer wallet" if credited else "Refund was already issued",
    }


async def schedule_return_pickup(db: AsyncSession, case_id: UUID) -> LogisticsReturnCaseItem:
    """Schedule a driver pickup for an approved return case.

    Creates a PARCEL_PICKUP order so the dispatcher can assign a driver to
    collect the item from the customer and bring it back to the warehouse.
    The order's delivery_notes stores the case reference_code so the chain
    can be followed all the way through to the WM grading step.
    """
    case = await _get_return_case(db, case_id)
    if case.status not in ("Approved", "Pickup Approved", "Pickup Scheduled"):
        raise HTTPException(status_code=400, detail=f"Cannot schedule pickup: return case status is '{case.status}'")

    # Fetch original order and warehouse
    original_order = (await db.execute(select(Order).where(Order.id == case.order_id))).scalar_one_or_none() if case.order_id else None
    warehouse = (await db.execute(select(Warehouse).where(Warehouse.id == case.warehouse_id))).scalar_one_or_none() if case.warehouse_id else None

    # Create PARCEL_PICKUP order only when we have all required data.
    # If missing, skip the order (dispatcher can create it manually) but still
    # pre-create the ReturnGrading so WM sees the incoming item.
    if original_order and warehouse:
        short_ref = case.reference_code.replace("RMA-", "").replace("DMG-", "")[:8] if case.reference_code else case_id.hex[:8].upper()
        pickup_tracking = f"RTN-{short_ref}"

        existing_pickup = (await db.execute(select(Order).where(Order.tracking_code == pickup_tracking))).scalar_one_or_none()
        if existing_pickup:
            pickup_tracking = f"RTN-{short_ref}-{_now().strftime('%H%M')}"

        # Check again after timestamp suffix
        if not (await db.execute(select(Order).where(Order.tracking_code == pickup_tracking))).scalar_one_or_none():
            pickup_order = Order(
                tracking_code=pickup_tracking,
                order_type="PARCEL_PICKUP",
                status="CONFIRMED",
                customer_id=original_order.customer_id,
                warehouse_id=case.warehouse_id,
                pickup_addr=original_order.delivery_addr,
                delivery_addr=warehouse.address,
                delivery_lat=warehouse.lat,
                delivery_lng=warehouse.lng,
                cargo_type="Return Parcel",
                total_amount=0.0,
                payment_mode="INTERNAL",
                payment_status="paid",
                delivery_notes=case.reference_code,
            )
            db.add(pickup_order)

    # Pre-create a pending ReturnGrading so the Warehouse Manager sees the
    # incoming item in their queue immediately — before the driver even arrives.
    # The WM will see it as "Awaiting Pickup" until the driver drops it off.
    rma_code = case.reference_code or f"RMA-{pickup_tracking}"
    existing_grading = (await db.execute(
        select(ReturnGrading).where(ReturnGrading.rma_code == rma_code)
    )).scalar_one_or_none()
    if not existing_grading:
        grading = ReturnGrading(
            warehouse_id=case.warehouse_id,
            order_id=case.order_id,
            rma_code=rma_code,
            item_condition="Awaiting Pickup",
            condition_notes="Approved by Logistic Manager. Driver pickup scheduled.",
            disposition="pending",
            status="pending",
        )
        db.add(grading)

    case.flow_type = "pickup_inspection"
    case.status = "Pickup Scheduled"
    db.add(case)

    await db.flush()
    return await _build_return_case_item(db, case, wallet_credited=False)
