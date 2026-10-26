"""Cancelling an order, with refunds and fees, and escalating an order to staff."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsEscalation,
)
from app.models.user import User
from app.schemas.logistics import LogisticsEscalationItem
from app.schemas.orders import (
    CancelOrderRequest,
    OrderEscalateRequest,
    OrderResponse,
)
from app.services.orders.assignment import _release_order_resources
from app.services.orders.common import (
    _cancellation_terms,
    _get_order,
    _push_notification,
    _resolve_names,
    _to_order_response,
    _validate_transition,
)


async def cancel_order(
    db: AsyncSession,
    order_id: UUID,
    data: CancelOrderRequest,
    user: User,
) -> OrderResponse:
    from app.services.return_charge_service import release_attached_transport_charges

    order = await _get_order(db, order_id)
    if user.role.name in {"INDIVIDUAL", "VENDOR"} and order.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if user.role.name in {"INDIVIDUAL", "VENDOR"} and order.status == "IN_TRANSIT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This order is already in progress. Please contact support to request changes or cancellation.",
        )
    if user.role.name == "DISPATCHER" and order.status == "IN_TRANSIT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dispatcher cannot cancel an order once it is IN_TRANSIT. Escalate it instead.",
        )
    _validate_transition(order.status, "CANCELLED")
    cancellation_fee, cancellation_note = _cancellation_terms(order)
    wallet_refund_amount = 0.0

    # Determine the effective paid amount.
    # paid_amount is only set when a payment is explicitly recorded via /pay or /wallet-pay.
    # If the order was created with payment_status='paid' (e.g. Razorpay/online flow where
    # the frontend marks it paid but never calls the /pay endpoint), paid_amount stays 0.
    # In that case we treat total_amount as the effective paid amount for refund purposes.
    effective_paid = float(order.paid_amount or 0.0)
    if effective_paid <= 0 and order.payment_status in {"paid", "partial"}:
        # Infer from total_amount — the order was paid but paid_amount wasn't recorded
        effective_paid = float(order.total_amount or 0.0)
    elif effective_paid <= 0 and (order.payment_mode or "").strip().lower() == "partial":
        # Legacy booking flow: partial payments were captured in the UI but the backend order
        # stayed at payment_status='pending' with payment_mode='Partial'. Refund the expected 50%.
        effective_paid = round(float(order.total_amount or 0.0) / 2, 2)

    non_refundable_carry_forward = min(
        float(order.carry_forward_charge_paid_amount or 0.0),
        effective_paid,
    )
    refundable_paid = max(effective_paid - non_refundable_carry_forward, 0.0)

    if refundable_paid > 0:
        from app.services import wallet_service

        wallet_refund_amount = await wallet_service.credit_cancellation_refund(
            db,
            order=order,
            refund_amount=max(refundable_paid - cancellation_fee, 0.0),
            fee_amount=cancellation_fee,
        )


    # Release all assigned resources
    await _release_order_resources(db, order)
    await release_attached_transport_charges(db, order)
    order.status = "CANCELLED"
    order.cancel_reason = f"{data.reason} ({cancellation_note})"
    # Clear driver and vehicle assignment on the order since it's cancelled
    order.assigned_driver_id = None
    order.assigned_vehicle_id = None
    db.add(order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])

    # ── Notifications on cancellation ───────────────────────────────────────
    order_label = order.tracking_code or str(order.id)

    # Logistics Manager: all cancellations
    await _push_notification(
        db,
        title="Order Cancelled",
        message=f"{order_label} was cancelled. Reason: {data.reason}.",
        notif_type="warning",
        audience_roles=["LOGISTIC_MANAGER"],
    )

    # Customer/Vendor: cancellation notice
    if order.customer_id:
        await _push_notification(
            db,
            title="Order Cancelled",
            message=f"Your order {order_label} has been cancelled. {cancellation_note}.",
            notif_type="warning",
            target_user_id=order.customer_id,
        )

        # Separate refund notification if money was returned to wallet
        if wallet_refund_amount > 0:
            await _push_notification(
                db,
                title="Refund Processed",
                message=f"A refund of ₹{wallet_refund_amount:.2f} for {order_label} has been credited to your wallet.",
                notif_type="payment",
                target_user_id=order.customer_id,
            )

    dn, vc, cn, cp = await _resolve_names(db, [order])
    return _to_order_response(
        order,
        driver_name=dn.get(order.assigned_driver_id),
        vehicle_code=vc.get(order.assigned_vehicle_id),
        customer_name=cn.get(order.customer_id),
        customer_phone=cp.get(order.customer_id),
        cancellation_fee=cancellation_fee,
        wallet_refund_amount=wallet_refund_amount,
    )


async def escalate_order(
    db: AsyncSession,
    order_id: UUID,
    data: OrderEscalateRequest,
    user: User,
) -> LogisticsEscalationItem:
    order = await _get_order(db, order_id)

    if user.role.name in {"DISPATCHER", "WAREHOUSE_MANAGER"}:
        if not user.warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not assigned to a warehouse",
            )
        if order.warehouse_id != user.warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only escalate orders from your assigned warehouse",
            )

    if order.status in {"CANCELLED", "CLOSED"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot escalate an order in {order.status} status",
        )

    order_ref = f"[order:{order.id}]"
    existing = (
        await db.execute(
            select(LogisticsEscalation)
            .where(
                LogisticsEscalation.status == "OPEN",
                LogisticsEscalation.action_details.contains(order_ref),
            )
            .order_by(LogisticsEscalation.created_at.desc())
        )
    ).scalars().first()
    if existing is not None:
        return LogisticsEscalationItem(
            id=existing.id,
            hub_id=existing.warehouse_id,
            title=existing.title,
            priority=existing.priority,
            from_name=existing.requester_name,
            role=existing.requester_role,
            time=existing.created_at.strftime("%I:%M %p"),
            description=existing.description,
            action_details=existing.action_details,
            status=existing.status,
        )

    readable_role = (user.role.name or "DISPATCHER").replace("_", " ").title()
    order_status = (order.status or "UNKNOWN").replace("_", " ").title()
    escalation = LogisticsEscalation(
        warehouse_id=order.warehouse_id,
        title=f"Order {order.tracking_code} escalation",
        priority="High" if order.status == "IN_TRANSIT" else "Medium",
        requester_name=user.name or "Operations User",
        requester_role=readable_role,
        description=(
            f"{user.name or 'Operations user'} escalated order {order.tracking_code} "
            f"while it is in {order_status} status. Reason: {data.reason.strip()}"
        ),
        action_details=(
            f"Review order {order.tracking_code} and coordinate next action. "
            f"Current status: {order.status}. {order_ref}"
        ),
        status="OPEN",
    )
    db.add(escalation)
    await db.flush()
    await db.refresh(escalation)

    return LogisticsEscalationItem(
        id=escalation.id,
        hub_id=escalation.warehouse_id,
        title=escalation.title,
        priority=escalation.priority,
        from_name=escalation.requester_name,
        role=escalation.requester_role,
        time=escalation.created_at.strftime("%I:%M %p"),
        description=escalation.description,
        action_details=escalation.action_details,
        status=escalation.status,
    )
