"""Proof of delivery, house-shift sign-off and ratings."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.orders import (
    OrderResponse,
)
from app.services.orders.assignment import _release_order_resources
from app.services.orders.common import (
    _get_order,
    _normalize_data_url,
    _now,
    _resolve_names,
    _to_order_response,
    _validate_transition,
)
from app.services.orders.transitions import _ensure_driver_access


async def upload_proof_of_delivery(
    db: AsyncSession,
    order_id: UUID,
    user: User,
    *,
    otp_code: str | None,
    image_data: str | None,
    images_data: list[str] | None,
    signature_data: str | None,
    customer_name: str | None = None,
    notes: str | None = None,
) -> OrderResponse:
    order = await _get_order(db, order_id)
    _ensure_driver_access(order, user)
    _validate_transition(order.status, "DELIVERED")

    normalized_images = []
    if image_data:
        normalized_images.append(_normalize_data_url(image_data, "image/jpeg"))
    if images_data:
        normalized_images.extend(
            normalized
            for normalized in (_normalize_data_url(item, "image/jpeg") for item in images_data)
            if normalized
        )
    if not normalized_images:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one POD image is required",
        )

    if not signature_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Customer signature is required",
        )

    if not order.service_otp:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery OTP has not been generated yet",
        )
    if not otp_code or str(otp_code).strip() != str(order.service_otp).strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid delivery OTP",
        )

    delivered_at = _now()
    order.status = "DELIVERED"
    order.delivered_at = delivered_at
    order.service_otp_verified_at = delivered_at
    order.delivery_notes = notes
    order.pod_photos = normalized_images
    order.pod_signature = _normalize_data_url(signature_data, "image/png")
    if customer_name:
        order.delivery_notes = f"{notes or ''}\nDelivered to: {customer_name}".strip()

    await _release_order_resources(db, order)
    db.add(order)
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


async def house_shift_signoff(
    db: AsyncSession,
    order_id: UUID,
    user: User,
    *,
    signature_data: str | None,
    customer_name: str | None = None,
    notes: str | None = None,
):
    """Record customer sign-off for a house-shift job (no OTP required)."""
    order = await _get_order(db, order_id)
    _ensure_driver_access(order, user)
    _validate_transition(order.status, "DELIVERED")

    if not signature_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Customer signature is required for house-shift sign-off",
        )

    delivered_at = _now()
    order.status = "DELIVERED"
    order.delivered_at = delivered_at
    order.poc_signature = _normalize_data_url(signature_data, "image/png")
    if customer_name:
        order.delivery_notes = f"{notes or ''}\nSigned off by: {customer_name}".strip()
    elif notes:
        order.delivery_notes = notes

    await _release_order_resources(db, order)
    db.add(order)
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


async def submit_job_rating(
    db: AsyncSession,
    order_id: UUID,
    user: User,
    *,
    rating: int,
    feedback: str | None = None,
):
    """Store driver self-rating (1–5) and optional feedback note for a completed job."""
    order = await _get_order(db, order_id)
    _ensure_driver_access(order, user)

    if not 1 <= rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rating must be between 1 and 5",
        )

    order.job_rating = rating
    order.job_feedback = feedback or None
    db.add(order)
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


async def submit_customer_rating(
    db: AsyncSession,
    order_id: UUID,
    user: User,
    *,
    rating: int,
    feedback: str | None = None,
):
    """Store customer/vendor rating (1–5) of the driver for a completed order."""
    order = await _get_order(db, order_id)

    if user.role.name in {"INDIVIDUAL", "VENDOR"} and order.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if order.status != "DELIVERED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rating can only be submitted for delivered orders",
        )

    if not 1 <= rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rating must be between 1 and 5",
        )

    order.customer_rating = rating
    order.customer_feedback = feedback or None
    db.add(order)
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
