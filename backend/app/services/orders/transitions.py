"""Status transitions, returns, delivery OTPs, cancellation and escalation."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.logistics import (
    LogisticsReturnCase,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import ReturnGrading
from app.schemas.orders import (
    DeliveryOtpSendResponse,
    OrderResponse,
)
from app.services.orders.assignment import _release_order_resources
from app.services.orders.common import (
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


