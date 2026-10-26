"""Delivery hand-off: delivery OTP, proof of delivery upload and page, and payment capture."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.orders import (
    DeliveryOtpSendRequest,
    DeliveryOtpSendResponse,
    OrderResponse,
    PayOrderRequest,
    PODRequest,
)
from app.services import orders_service
from app.services.orders.delivery_proof_html import render_proof_of_delivery_html

router = APIRouter()


@router.post("/{order_id}/delivery-otp/send", response_model=DeliveryOtpSendResponse)
async def send_delivery_otp(
    order_id: UUID,
    data: DeliveryOtpSendRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    return await orders_service.send_delivery_otp(db, order_id, user, force_resend=data.force_resend)


@router.post("/{order_id}/proof-of-delivery", response_model=OrderResponse)
async def upload_proof_of_delivery(
    order_id: UUID,
    data: PODRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    return await orders_service.upload_proof_of_delivery(
        db,
        order_id,
        user,
        otp_code=data.otp_code,
        image_data=data.image_data,
        images_data=data.images_data,
        signature_data=data.signature_data,
        customer_name=data.customer_name,
        notes=data.notes,
    )


@router.get("/{order_id}/proof-of-delivery", response_class=HTMLResponse)
async def get_proof_of_delivery_html(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Proof of Delivery page for one order, filled from its delivery record."""
    order = await orders_service.get_order_detail(db, order_id, user)

    # Customer name and phone stay out of the log.
    logger.debug(
        "Rendering POD HTML for order {}: signature={} photos={} delivered_at={}",
        order.id,
        bool(order.pod_signature),
        len(order.pod_photos or []),
        order.delivered_at,
    )
    return render_proof_of_delivery_html(order)


@router.post("/{order_id}/pay")
async def pay_order(
    order_id: UUID,
    data: PayOrderRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Record a payment for an order. Online (Razorpay) or COD by driver."""
    from sqlalchemy import select as _select

    from app.models.order import Order as _Order
    from app.services import finance_service

    order = (await db.execute(_select(_Order).where(_Order.id == order_id))).scalar_one_or_none()
    if order is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")

    amount = data.amount if (data.amount and data.amount > 0) else order.total_amount

    pmt = await finance_service.record_order_payment(
        db=db,
        order_id=order_id,
        amount=amount,
        payment_mode=data.payment_mode,
        payment_method=data.payment_method,
        payment_ref=data.payment_ref,
        collected_by_user=user if data.payment_mode.upper() == "COD" else None,
        notes=data.notes,
    )
    await db.commit()

    return {
        "payment_id": str(pmt.id),
        "payment_ref": pmt.payment_ref,
        "order_id": str(order_id),
        "amount": pmt.amount,
        "status": pmt.status,
        "payment_mode": pmt.payment_mode,
        "payment_method": pmt.payment_method,
    }
