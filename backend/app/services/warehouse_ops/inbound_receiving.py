"""Inbound issues and receiving: mismatch and damage reports, scheduling, acceptance, arrival and vendor take-back."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import DamageReport, Order, OrderItem
from app.models.user import User
from app.models.vendor import VendorSupportReply, VendorSupportTicket
from app.schemas.warehouse_operations import (
    InboundDamageReport,
    InboundMismatchReport,
    PickingResponse,
    ScheduleInboundRequest,
)
from app.services.warehouse_ops.common import (
    INBOUND_RESOLUTION_LABELS,
    _get_order,
    _get_warehouse,
    _inbound_report_reference,
    _inbound_tracking_code,
    _latest_inbound_issue_ticket,
    _linked_resolution_action,
    _validate_substatus_transition,
)


async def report_inbound_mismatch(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data: InboundMismatchReport,
    reported_by: User,
) -> None:
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order does not belong to this warehouse")
    if order.order_type != "VENDOR" or (order.pickup_type or "hub").lower() != "hub":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only hub-based vendor inbound orders support mismatch reporting")

    vendor = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == order.customer_id)
        )
    ).scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found for this shipment")

    details = (data.details or "").strip()
    description = (
        f"Inbound mismatch raised by warehouse manager {reported_by.name} for shipment {order.tracking_code}.\n"
        f"Mismatch type: {data.mismatch_type}."
    )
    if details:
        description += f"\nDetails: {details}"

    ticket = VendorSupportTicket(
        vendor_id=vendor.id,
        order_id=order.id,
        subject=f"Inbound mismatch: {data.mismatch_type}",
        description=description,
        priority="High",
        status="Open",
    )
    db.add(ticket)
    await db.flush()

    db.add(
        VendorSupportReply(
            ticket_id=ticket.id,
            from_name=f"Warehouse Team ({reported_by.name})",
            message=description,
        )
    )
    await db.flush()

    from app.services import ai_support_service

    support_ticket = await ai_support_service.sync_vendor_ticket_to_support_ticket(
        db=db,
        vendor=vendor,
        vendor_ticket=ticket,
        source="warehouse_inbound",
        metadata_updates={
            "issue_type": "mismatch",
            "resolution_action": "pending_review",
            "lm_steps": "Review mismatch details with vendor||Reply in the vendor thread||Set final resolution for warehouse",
        },
    )
    await ai_support_service.create_user_notification(
        db,
        user_id=vendor.id,
        title="Warehouse flagged an inbound mismatch",
        message=f"{order.tracking_code}: Cargo-Core is waiting for your confirmation on the mismatch.",
        notification_type="warning",
    )
    await ai_support_service.notify_support_manager_about_ticket(
        db,
        ticket=support_ticket,
        source="warehouse_inbound",
    )


async def report_inbound_damage(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data: InboundDamageReport,
    reported_by: User,
) -> DamageReport:
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order does not belong to this warehouse")
    if order.order_type != "VENDOR" or (order.pickup_type or "hub").lower() != "hub":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only hub-based vendor inbound orders support damage reporting")

    description = (
        f"Inbound damage reported by warehouse manager {reported_by.name} for shipment {order.tracking_code}. "
        f"Damaged items: {data.damaged_count}. {data.description.strip()}"
    )
    photos = [data.photo_url] if data.photo_url else []

    report = DamageReport(
        reference_code=_inbound_report_reference("DMG"),
        customer_id=order.customer_id,
        order_id=order.id,
        description=description,
        photos=photos,
        flow_type="pickup_inspection",
        status="reported",
        qr_code=_inbound_report_reference("QR"),
    )
    db.add(report)
    await db.flush()
    vendor = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == order.customer_id)
        )
    ).scalar_one_or_none()
    if vendor:
        ticket = VendorSupportTicket(
            vendor_id=vendor.id,
            order_id=order.id,
            subject="Inbound damage reported",
            description=description,
            priority="High",
            status="Open",
        )
        db.add(ticket)
        await db.flush()

        db.add(
            VendorSupportReply(
                ticket_id=ticket.id,
                from_name=f"Warehouse Team ({reported_by.name})",
                message=description,
            )
        )
        await db.flush()

        from app.services import ai_support_service

        support_ticket = await ai_support_service.sync_vendor_ticket_to_support_ticket(
            db=db,
            vendor=vendor,
            vendor_ticket=ticket,
            source="warehouse_inbound",
            metadata_updates={
                "issue_type": "damage",
                "linked_damage_report_id": str(report.id),
                "resolution_action": "pending_review",
                "lm_steps": "Inspect damage photos from the warehouse||Confirm with vendor whether stock moves or returns||Update final resolution for warehouse",
            },
        )
        await ai_support_service.create_user_notification(
            db,
            user_id=vendor.id,
            title="Warehouse reported inbound damage",
            message=f"{order.tracking_code}: Support needs your decision on the damaged shipment.",
            notification_type="alert",
        )
        await ai_support_service.notify_support_manager_about_ticket(
            db,
            ticket=support_ticket,
            source="warehouse_inbound",
        )
    return report


async def schedule_inbound_delivery(
    db: AsyncSession,
    warehouse_id: UUID,
    data: ScheduleInboundRequest,
) -> Order:
    warehouse = await _get_warehouse(db, warehouse_id)
    normalized_supplier = data.supplier_name.strip().lower()

    vendor = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(
                User.is_active.is_(True),
                or_(
                    func.lower(User.name) == normalized_supplier,
                    func.lower(func.coalesce(User.company_name, "")) == normalized_supplier,
                    func.lower(func.coalesce(User.contact_person, "")) == normalized_supplier,
                ),
            )
        )
    ).scalars().all()

    matched_vendor = next((user for user in vendor if getattr(user.role, "name", None) == "VENDOR"), None)
    if not matched_vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active vendor matched that supplier name. Use an existing vendor/company name.",
        )

    order = Order(
        tracking_code=_inbound_tracking_code(),
        order_type="VENDOR",
        status="CONFIRMED",
        priority="NORMAL",
        warehouse_substatus="AWAITING_INBOUND",
        customer_id=matched_vendor.id,
        warehouse_id=warehouse_id,
        pickup_addr=data.supplier_name.strip(),
        pickup_type="hub",
        delivery_addr=warehouse.address,
        cargo_type="Inbound Shipment",
        vehicle_type="Scheduled Delivery",
        labor_count=0,
        base_amount=0,
        vehicle_amount=0,
        labor_amount=0,
        materials_amount=0,
        packing_amount=0,
        platform_fee=0,
        tax_amount=0,
        total_amount=0,
        payment_mode="invoice",
        payment_status="pending",
        declared_value=0,
        scheduled_at=data.scheduled_at,
        delivery_notes=(data.notes or data.dock_preference or "").strip() or None,
        delivery_lat=warehouse.lat,
        delivery_lng=warehouse.lng,
    )
    db.add(order)
    await db.flush()

    db.add(
        OrderItem(
            order_id=order.id,
            sku="INBOUND-LOAD",
            quantity=data.expected_qty,
            box_count=max(1, (data.expected_qty + 9) // 10),
            estimated_volume=None,
        )
    )
    await db.flush()
    return order


# ======================
# Accept Order
# ======================

async def accept_order_into_warehouse(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Accept a CONFIRMED order into the warehouse queue.
    Vendor orders → AWAITING_INBOUND (goods must arrive first via Inbound).
    Non-vendor orders → AWAITING_PICK directly.
    """
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.status not in {"CONFIRMED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only CONFIRMED orders can be accepted into the warehouse queue (got {order.status})",
        )

    # Idempotent — if already accepted, just return success
    if order.warehouse_substatus in {"AWAITING_INBOUND", "AWAITING_PICK", "PICKING", "PICKED", "PACKING", "PACKED", "QC_PASSED"}:
        return PickingResponse(
            order_id=order_id,
            warehouse_substatus=order.warehouse_substatus,
            assigned_labourer_id=None,
            message="Order already in warehouse queue",
        )

    # Vendor orders with 'hub' pickup wait in Inbound until goods physically arrive
    # Vendor orders with 'doorstep' pickup go directly to picking queue (driver picks from vendor's location)
    # Non-vendor orders go directly to picking queue
    if order.order_type == "VENDOR" and (order.pickup_type or "hub").lower() == "hub":
        initial_substatus = "AWAITING_INBOUND"
    else:
        initial_substatus = "AWAITING_PICK"
    order.warehouse_substatus = initial_substatus
    db.add(order)
    await db.flush()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus=initial_substatus,
        assigned_labourer_id=None,
        message="Order accepted — awaiting inbound receipt" if initial_substatus == "AWAITING_INBOUND" else "Order accepted into warehouse queue",
    )


async def mark_inbound_received(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Mark a vendor order's goods as physically received — transitions AWAITING_INBOUND → AWAITING_PICK."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_substatus != "AWAITING_INBOUND":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is not in AWAITING_INBOUND state (current: {order.warehouse_substatus})",
        )

    latest_issue_ticket = await _latest_inbound_issue_ticket(db, order.id)
    if latest_issue_ticket:
        resolution_action = _linked_resolution_action(latest_issue_ticket)
        if resolution_action != "vendor_accept_move":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=INBOUND_RESOLUTION_LABELS.get(
                    resolution_action,
                    "Inbound issue is still under review. Resolve it with vendor support before moving to picking.",
                ),
            )

    _validate_substatus_transition(order.warehouse_substatus, "AWAITING_PICK")
    order.warehouse_substatus = "AWAITING_PICK"
    db.add(order)
    await db.flush()

    vendor = (
        await db.execute(select(User).where(User.id == order.customer_id))
    ).scalar_one_or_none()
    if vendor:
        from app.services import ai_support_service

        await ai_support_service.create_user_notification(
            db,
            user_id=vendor.id,
            title="Inbound issue cleared",
            message=f"{order.tracking_code}: Warehouse has moved the approved shipment to picking.",
            notification_type="success",
        )

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="AWAITING_PICK",
        assigned_labourer_id=None,
        message="Goods received — order moved to picking queue",
    )


async def generate_vendor_take_back(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    acted_by: User,
) -> PickingResponse:
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.order_type != "VENDOR" or (order.pickup_type or "hub").lower() != "hub":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only hub-based vendor inbound orders support vendor take-back generation",
        )

    latest_issue_ticket = await _latest_inbound_issue_ticket(db, order.id)
    resolution_action = _linked_resolution_action(latest_issue_ticket)
    if resolution_action != "vendor_take_back":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Support must first confirm that the vendor will take this shipment back.",
        )

    if order.warehouse_substatus != "ON_HOLD":
        _validate_substatus_transition(order.warehouse_substatus, "ON_HOLD")
        order.warehouse_substatus = "ON_HOLD"
        db.add(order)
        await db.flush()

    vendor = (
        await db.execute(select(User).where(User.id == order.customer_id))
    ).scalar_one_or_none()
    if vendor:
        from app.services import ai_support_service

        await ai_support_service.create_user_notification(
            db,
            user_id=vendor.id,
            title="Vendor take-back generated",
            message=f"{order.tracking_code}: Warehouse marked the damaged inbound for vendor take-back.",
            notification_type="warning",
        )

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="ON_HOLD",
        assigned_labourer_id=None,
        message=f"Vendor take-back generated by {acted_by.name}",
    )


async def mark_inbound_arrived(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Mark a vendor inbound order as physically arrived at the warehouse dock."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.order_type != "VENDOR" or (order.pickup_type or "hub").lower() != "hub":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only hub-based vendor inbound orders can be marked as arrived",
        )

    if order.warehouse_substatus != "AWAITING_INBOUND":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is not in AWAITING_INBOUND state (current: {order.warehouse_substatus})",
        )

    if order.arrived_at is None:
        order.arrived_at = datetime.now(UTC)
        db.add(order)
        await db.flush()

    message = "Order marked as arrived"
    from app.services import vendor_service

    debited, debit_note = await vendor_service.auto_debit_recurring_order_if_eligible(
        db,
        order=order,
        trigger="arrived",
    )
    if debited:
        message = "Order marked as arrived. Auto-debit completed from vendor wallet"
    elif debit_note:
        message = f"Order marked as arrived. Auto-debit skipped: {debit_note}"

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="AWAITING_INBOUND",
        assigned_labourer_id=None,
        message=message,
    )
