"""Status transitions, returns, delivery OTPs, cancellation and escalation."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.logistics import (
    LogisticsEscalation,
    LogisticsReturnCase,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import ReturnGrading
from app.schemas.logistics import LogisticsEscalationItem
from app.schemas.orders import (
    CancelOrderRequest,
    DeliveryOtpSendResponse,
    OrderEscalateRequest,
    OrderResponse,
)
from app.services.orders.assignment import _release_order_resources
from app.services.orders.common import (
    _cancellation_terms,
    _generate_delivery_otp,
    _get_order,
    _mask_email,
    _now,
    _push_notification,
    _resolve_names,
    _to_order_response,
    _validate_transition,
)
from app.utils.email import delivery_otp_email_html, send_email


async def transition_order(
    db: AsyncSession, order_id: UUID, next_status: str, caller: "User | None" = None
) -> OrderResponse:
    order = await _get_order(db, order_id)
    _validate_transition(order.status, next_status)

    # --- Loophole guard #1: active dispatch states require a driver assignment ---
    if next_status in {"ASSIGNED", "IN_TRANSIT"}:
        if not order.assigned_driver_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A driver must be assigned to this order before it can be dispatched",
            )

    # --- Loophole guard #2: DRIVER role can only act on their own assigned order ---
    if caller is not None and caller.role.name == "DRIVER":
        if order.assigned_driver_id != caller.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the assigned driver for this order",
            )
        # Drivers may only trigger the IN_TRANSIT transition (not skip steps)
        if next_status not in {"IN_TRANSIT", "DELIVERED"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Drivers cannot trigger the {next_status} transition",
            )

    order.status = next_status

    # Ensure vehicle is marked In Use when order goes to IN_TRANSIT
    if next_status == "IN_TRANSIT" and order.assigned_vehicle_id:
        vehicle = (await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.id == order.assigned_vehicle_id))).scalar_one_or_none()
        if vehicle and vehicle.status != "In Use":
            vehicle.status = "In Use"
        # Record fuel expense (estimate based on vehicle type, 30km default)
        from app.services import finance_service as _fs
        vtype_key = (order.vehicle_type or "tempo").lower().replace(" ", "").replace("-", "")
        rate = _fs.FUEL_RATE_PER_KM.get(vtype_key, 10)
        est_km = 30
        await _fs.record_expense(
            db,
            expense_type="EXPENSE_FUEL",
            amount=rate * est_km,
            description=f"Fuel estimate ({est_km}km @ INR {rate}/km) for {order.tracking_code}",
            warehouse_id=order.warehouse_id,
            order_id=order.id,
            tracking_code=order.tracking_code,
        )

    # Release all resources when order is delivered, closed, or cancelled
    if next_status in ("DELIVERED", "CLOSED"):
        await _release_order_resources(db, order)
    
    # For COD orders: auto-record the payment on DELIVERED
    if next_status == "DELIVERED" and (order.payment_mode or "").upper() in {"COD", "CASH ON DELIVERY"}:
        if order.payment_status != "paid":
            from app.services import finance_service as _fs2
            await _fs2.record_order_payment(
                db=db,
                order_id=order.id,
                amount=order.total_amount - (order.paid_amount or 0.0),
                payment_mode="COD",
                payment_method="Cash on Delivery",
                payment_ref=None,
                collected_by_user=caller,
            )

    db.add(order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])

    # ── Notifications on status transition ──────────────────────────────────
    order_label = order.tracking_code or str(order.id)
    _STATUS_LABELS = {
        "ASSIGNED":   ("Order Assigned to Driver",  "success", f"{order_label} has been assigned to a driver and is being prepared for pickup."),
        "IN_TRANSIT": ("Order Out for Delivery",    "info",    f"{order_label} is now in transit and on its way to you."),
        "DELIVERED":  ("Order Delivered",           "success", f"{order_label} has been successfully delivered. Thank you!"),
        "CLOSED":     ("Order Closed",              "info",    f"{order_label} has been closed."),
    }
    if next_status in _STATUS_LABELS:
        lm_title, notif_type, customer_msg = _STATUS_LABELS[next_status]

        # Notify Logistics Manager on every major transition
        await _push_notification(
            db,
            title=lm_title,
            message=f"{order_label} status changed to {next_status}.",
            notif_type=notif_type,
            audience_roles=["LOGISTIC_MANAGER"],
        )

        # Notify the order owner (vendor or customer) personally
        if order.customer_id:
            await _push_notification(
                db,
                title=lm_title,
                message=customer_msg,
                notif_type=notif_type,
                target_user_id=order.customer_id,
            )

    dn, vc, cn, cp = await _resolve_names(db, [order])
    return _to_order_response(
        order,
        driver_name=dn.get(order.assigned_driver_id),
        vehicle_code=vc.get(order.assigned_vehicle_id),
        customer_name=cn.get(order.customer_id),
        customer_phone=cp.get(order.customer_id),
    )


async def complete_return_order(db: AsyncSession, order_id: UUID, caller: "User") -> "OrderResponse":
    """Driver-side completion for a PARCEL_PICKUP (reverse-logistics) job.

    Transitions the order to DELIVERED, sets warehouse_substatus=RETURN_ARRIVED,
    and auto-creates a pending ReturnGrading so the Warehouse Manager sees the
    inbound item in their inspection queue without any manual data entry.
    """
    order = await _get_order(db, order_id)

    if order.assigned_driver_id != caller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the assigned driver for this order",
        )

    _validate_transition(order.status, "DELIVERED")

    order.status = "DELIVERED"
    order.warehouse_substatus = "RETURN_ARRIVED"
    db.add(order)

    # Auto-create a pending return grading so the Warehouse Manager queue is populated.
    # If this is a scheduled return pickup order, delivery_notes holds the original
    # return reference code (for example "RMA-9921" or "DMG-209F82") — use that so
    # WM grading links back to the LM case.
    if order.warehouse_id:
        raw_reference = (order.delivery_notes or "").strip()
        if raw_reference.startswith(("RMA-", "DMG-")):
            rma_code = raw_reference
        else:
            rma_code = f"RMA-{order.tracking_code}"
        existing = (
            await db.execute(select(ReturnGrading).where(ReturnGrading.rma_code == rma_code))
        ).scalar_one_or_none()
        if not existing:
            grading = ReturnGrading(
                warehouse_id=order.warehouse_id,
                order_id=order.id,
                rma_code=rma_code,
                item_condition="Pending Inspection",
                condition_notes=None,
                disposition="pending",
                status="pending",
            )
            db.add(grading)

        # Sync the LM return case to "Arrived at Warehouse" so the Logistic Manager
        # knows the physical item is back and WM is about to inspect it.
        return_case = (await db.execute(
            select(LogisticsReturnCase).where(LogisticsReturnCase.reference_code == rma_code)
        )).scalar_one_or_none()
        if return_case and return_case.status == "Pickup Scheduled":
            return_case.status = "At Warehouse"
            db.add(return_case)

    await _release_order_resources(db, order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])
    dn, vc, cn, cp = await _resolve_names(db, [order])
    return _to_order_response(
        order,
        driver_name=dn.get(order.assigned_driver_id),
        vehicle_code=vc.get(order.assigned_vehicle_id),
        customer_name=cn.get(order.customer_id),
        customer_phone=cp.get(order.customer_id),
    )


async def _get_customer_for_order(db: AsyncSession, order: Order) -> User:
    customer = (await db.execute(select(User).where(User.id == order.customer_id))).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found for order")
    return customer


def _ensure_driver_access(order: Order, user: User) -> None:
    if order.assigned_driver_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This order is not assigned to the current driver",
        )


async def send_delivery_otp(
    db: AsyncSession,
    order_id: UUID,
    user: User,
    *,
    force_resend: bool = False,
) -> DeliveryOtpSendResponse:
    order = await _get_order(db, order_id)
    _ensure_driver_access(order, user)

    if order.status not in {"ASSIGNED", "IN_TRANSIT"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery OTP can only be sent for an active assigned delivery",
        )

    customer = await _get_customer_for_order(db, order)
    if not customer.email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer email is unavailable")

    recently_sent = (
        order.service_otp
        and order.service_otp_sent_at
        and not force_resend
        and (_now() - order.service_otp_sent_at).total_seconds() < 60
    )
    if recently_sent:
        return DeliveryOtpSendResponse(
            message="OTP already sent recently",
            email=_mask_email(customer.email),
            sent_at=order.service_otp_sent_at,
        )

    otp = _generate_delivery_otp()
    sent_at = _now()
    order.service_otp = otp
    order.service_otp_sent_at = sent_at
    order.service_otp_verified_at = None
    db.add(order)
    await db.flush()

    sent = await send_email(
        to=customer.email,
        subject=f"Cargo Core delivery OTP for {order.tracking_code}",
        html_body=delivery_otp_email_html(
            otp=otp,
            customer_name=customer.name or "Customer",
            tracking_code=order.tracking_code,
            delivery_address=order.delivery_addr,
        ),
    )
    if not sent:
        settings = get_settings()
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Delivery OTP email could not be sent. Check SMTP configuration.",
            )

        # Local/dev fallback: keep OTP generation successful even without SMTP.
        return DeliveryOtpSendResponse(
            message="Delivery OTP generated (email unavailable in development)",
            email=_mask_email(customer.email),
            sent_at=sent_at,
            debug_otp=otp,
        )

    return DeliveryOtpSendResponse(
        message="Delivery OTP sent successfully",
        email=_mask_email(customer.email),
        sent_at=sent_at,
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
