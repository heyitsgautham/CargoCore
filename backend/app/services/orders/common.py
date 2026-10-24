"""Order constants, status transitions, response mapping and shared lookups."""

import random
import re
import uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.labour import Labourer
from app.models.logistics import (
    LogisticsEscalation,
    LogisticsNotification,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import Role, User
from app.models.warehouse import Warehouse
from app.schemas.orders import (
    OrderItemResponse,
    OrderResponse,
)
from app.services import geocoding_service

ORDER_TYPES = {"INDIVIDUAL", "VENDOR", "SERVICE_MOVE"}
ORDER_STATUSES = {
    "DRAFT",
    "CONFIRMED",
    "ASSIGNED",
    "IN_TRANSIT",
    "DELIVERED",
    "CLOSED",
    "CANCELLED",
}
TERMINAL_ORDER_STATUSES = {"CLOSED", "CANCELLED"}
AUTO_ASSIGN_READY_ROLES = {"DISPATCHER", "DRIVER", "LABOURER"}
ALLOWED_TRANSITIONS = {
    "DRAFT": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"ASSIGNED", "CANCELLED"},
    "ASSIGNED": {"IN_TRANSIT", "CANCELLED"},
    "IN_TRANSIT": {"DELIVERED", "CANCELLED"},
    "DELIVERED": {"CLOSED"},
    "CLOSED": set(),
    "CANCELLED": set(),
}
ORDER_ESCALATION_REF_RE = re.compile(r"\[order:([0-9a-fA-F-]{36})\]")


async def _get_order(db: AsyncSession, order_id: UUID) -> Order:
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def _tracking_code() -> str:
    return f"QC-{uuid.uuid4().hex[:10].upper()}"


def _now() -> datetime:
    return datetime.now(UTC)


async def _hydrate_order_coordinates(order: Order) -> None:
    if order.pickup_addr and (order.pickup_lat is None or order.pickup_lng is None):
        try:
            results = await geocoding_service.search_address(order.pickup_addr, limit=1)
            if results:
                order.pickup_lat = float(results[0]["lat"])
                order.pickup_lng = float(results[0]["lon"])
        except Exception as e:
            # Don't fail order creation/update if pickup geocoding fails
            logger.warning(
                "Auto-geocoding failed for order {} pickup address: {}", order.id, e
            )

    if order.delivery_addr and (order.delivery_lat is None or order.delivery_lng is None):
        try:
            results = await geocoding_service.search_address(order.delivery_addr, limit=1)
            if results:
                order.delivery_lat = float(results[0]["lat"])
                order.delivery_lng = float(results[0]["lon"])
        except Exception as e:
            # Don't fail order creation/update if delivery geocoding fails
            logger.warning(
                "Auto-geocoding failed for order {} delivery address: {}", order.id, e
            )


def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return email
    masked_local = f"{local[:1]}***" if len(local) <= 2 else f"{local[:2]}***"
    return f"{masked_local}@{domain}"


def _generate_delivery_otp() -> str:
    return f"{random.randint(1000, 9999)}"


async def _push_notification(
    db: AsyncSession,
    title: str,
    message: str,
    notif_type: str = "info",
    audience_roles: list[str] | None = None,
    target_user_id: UUID | None = None,
) -> None:
    """Create a LogisticsNotification record.

    If target_user_id is set the notification is visible only to that specific user
    (used for vendor/customer order-event notifications).
    Otherwise audience_roles controls which roles can see it.
    """
    db.add(LogisticsNotification(
        title=title,
        message=message,
        type=notif_type,
        audience_roles=",".join(audience_roles) if audience_roles else None,
        target_user_id=target_user_id,
    ))


def _normalize_data_url(payload: str | None, mime_type: str) -> str | None:
    if not payload:
        return None
    if payload.startswith("data:"):
        return payload
    return f"data:{mime_type};base64,{payload}"


async def _resolve_warehouse_id(
    db: AsyncSession,
    warehouse_id: UUID | None,
) -> UUID:
    if warehouse_id:
        warehouse = await _get_active_warehouse(db, warehouse_id)
        return warehouse.id

    warehouse = await _select_auto_assignment_warehouse(db)
    return warehouse.id


async def _get_active_warehouse(
    db: AsyncSession,
    warehouse_id: UUID,
) -> Warehouse:
    warehouse = (
        await db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active warehouse not found",
        )
    return warehouse


async def _select_auto_assignment_warehouse(db: AsyncSession) -> Warehouse:
    active_warehouses = (
        await db.execute(
            select(Warehouse)
            .where(Warehouse.is_active.is_(True))
            .order_by(Warehouse.created_at.asc())
        )
    ).scalars().all()

    if not active_warehouses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active warehouses available for assignment",
        )

    open_order_counts = {
        warehouse_id: count
        for warehouse_id, count in (
            await db.execute(
                select(Order.warehouse_id, func.count(Order.id))
                .where(
                    Order.warehouse_id.is_not(None),
                    Order.status.not_in(TERMINAL_ORDER_STATUSES),
                )
                .group_by(Order.warehouse_id)
            )
        ).all()
        if warehouse_id is not None
    }
    operational_user_counts = {
        warehouse_id: count
        for warehouse_id, count in (
            await db.execute(
                select(User.warehouse_id, func.count(User.id))
                .join(Role, Role.id == User.role_id)
                .where(
                    User.warehouse_id.is_not(None),
                    User.is_active.is_(True),
                    Role.name.in_(AUTO_ASSIGN_READY_ROLES),
                )
                .group_by(User.warehouse_id)
            )
        ).all()
        if warehouse_id is not None
    }
    labour_counts = {
        warehouse_id: count
        for warehouse_id, count in (
            await db.execute(
                select(Labourer.warehouse_id, func.count(Labourer.id))
                .group_by(Labourer.warehouse_id)
            )
        ).all()
        if warehouse_id is not None
    }

    def is_operationally_ready(candidate: Warehouse) -> bool:
        return any((
            open_order_counts.get(candidate.id, 0) > 0,
            operational_user_counts.get(candidate.id, 0) > 0,
            labour_counts.get(candidate.id, 0) > 0,
        ))

    candidate_warehouses = [
        warehouse for warehouse in active_warehouses if is_operationally_ready(warehouse)
    ] or active_warehouses

    return min(
        candidate_warehouses,
        key=lambda item: (open_order_counts.get(item.id, 0), item.created_at),
    )


def _validate_transition(current_status: str, next_status: str) -> None:
    if next_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid transition from {current_status} to {next_status}",
        )


def _to_order_response(
    order: Order,
    *,
    driver_name: str | None = None,
    vehicle_code: str | None = None,
    customer_name: str | None = None,
    customer_phone: str | None = None,
    cancellation_fee: float = 0.0,
    wallet_refund_amount: float = 0.0,
    escalated: bool = False,
    escalation_id: UUID | None = None,
    escalation_status: str | None = None,
) -> OrderResponse:
    derived_weight_kg = order.cargo_weight_kg
    if derived_weight_kg is not None and float(derived_weight_kg) <= 0:
        derived_weight_kg = None

    derived_volume_m3 = order.cargo_volume_m3
    if derived_volume_m3 is not None and float(derived_volume_m3) <= 0:
        derived_volume_m3 = None
    if derived_volume_m3 is None:
        derived_volume_m3 = round(sum(float(item.estimated_volume or 0) for item in order.items), 2) if order.items else None
        if derived_volume_m3 == 0:
            derived_volume_m3 = None

    return OrderResponse(
        id=order.id,
        tracking_code=order.tracking_code,
        order_type=order.order_type,
        status=order.status,
        warehouse_substatus=order.warehouse_substatus,
        picking_started_at=order.picking_started_at,
        picking_completed_at=order.picking_completed_at,
        packing_started_at=order.packing_started_at,
        packing_completed_at=order.packing_completed_at,
        customer_id=order.customer_id,
        warehouse_id=order.warehouse_id,
        assigned_driver_id=order.assigned_driver_id,
        assigned_vehicle_id=order.assigned_vehicle_id,
        assigned_driver_name=driver_name,
        assigned_vehicle_code=vehicle_code,
        pickup_addr=order.pickup_addr,
        pickup_type=order.pickup_type,
        pickup_lat=order.pickup_lat,
        pickup_lng=order.pickup_lng,
        delivery_addr=order.delivery_addr,
        cargo_weight_kg=derived_weight_kg,
        cargo_volume_m3=derived_volume_m3,
        cargo_type=order.cargo_type,
        vehicle_type=order.vehicle_type,
        labor_count=order.labor_count,
        base_amount=order.base_amount,
        vehicle_amount=order.vehicle_amount,
        labor_amount=order.labor_amount,
        materials_amount=order.materials_amount,
        packing_amount=order.packing_amount,
        platform_fee=order.platform_fee,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        carry_forward_charge_amount=order.carry_forward_charge_amount,
        carry_forward_charge_paid_amount=order.carry_forward_charge_paid_amount,
        payment_mode=order.payment_mode,
        payment_status=order.payment_status,
        paid_amount=order.paid_amount,
        declared_value=order.declared_value,
        service_otp=order.service_otp,
        service_otp_sent_at=order.service_otp_sent_at,
        service_otp_verified_at=order.service_otp_verified_at,
        service_time_block=order.service_time_block,
        scheduled_at=order.scheduled_at,
        arrived_at=order.arrived_at,
        cancel_reason=order.cancel_reason,
        cancellation_fee=cancellation_fee,
        wallet_refund_amount=wallet_refund_amount,
        delivered_at=order.delivered_at,
        delivery_notes=order.delivery_notes,
        pod_photos=order.pod_photos or [],
        pod_signature=order.pod_signature,
        poc_signature=order.poc_signature,
        job_rating=order.job_rating,
        job_feedback=order.job_feedback,
        customer_rating=order.customer_rating,
        customer_feedback=order.customer_feedback,
        customer_name=customer_name,
        customer_phone=customer_phone,
        escalated=escalated,
        escalation_id=escalation_id,
        escalation_status=escalation_status,
        created_at=order.created_at,
        items=[OrderItemResponse.model_validate(item) for item in order.items],
    )


def _cancellation_terms(order: Order) -> tuple[float, str]:
    if order.status in {"DRAFT", "CONFIRMED"}:
        return 0.0, "Cancelled before dispatch - No fee"
    if order.status == "ASSIGNED":
        fee = round(float(order.total_amount or 0.0) * 0.05, 2)
        return fee, "Cancelled after driver assigned - 5% fee"
    if order.status == "IN_TRANSIT":
        fee = round(float(order.total_amount or 0.0) * 0.25, 2)
        return fee, "Cancelled mid-transit - 25% fee"
    return 0.0, "Cancelled"


async def _resolve_names(
    db: AsyncSession, orders: list[Order]
) -> tuple[dict, dict, dict, dict]:
    """Batch-resolve driver names, vehicle codes, and customer contacts for a list of orders."""
    driver_ids = {o.assigned_driver_id for o in orders if o.assigned_driver_id}
    vehicle_ids = {o.assigned_vehicle_id for o in orders if o.assigned_vehicle_id}
    customer_ids = {o.customer_id for o in orders if o.customer_id}

    driver_names: dict = {}
    if driver_ids:
        rows = (await db.execute(select(User.id, User.name).where(User.id.in_(driver_ids)))).all()
        driver_names = {row.id: row.name for row in rows}

    vehicle_codes: dict = {}
    if vehicle_ids:
        rows = (
            await db.execute(
                select(LogisticsVehicle.id, LogisticsVehicle.code, LogisticsVehicle.license_plate)
                .where(LogisticsVehicle.id.in_(vehicle_ids))
            )
        ).all()
        vehicle_codes = {row.id: f"{row.code} · {row.license_plate}" if row.license_plate else row.code for row in rows}

    customer_names: dict = {}
    customer_phones: dict = {}
    if customer_ids:
        rows = (await db.execute(select(User.id, User.name, User.phone).where(User.id.in_(customer_ids)))).all()
        customer_names = {row.id: row.name for row in rows}
        customer_phones = {row.id: row.phone for row in rows}

    return driver_names, vehicle_codes, customer_names, customer_phones


async def _resolve_open_order_escalations(
    db: AsyncSession,
    orders: list[Order],
) -> dict[str, LogisticsEscalation]:
    if not orders:
        return {}

    order_ids = {str(order.id) for order in orders if order.id}
    if not order_ids:
        return {}

    warehouse_ids = {order.warehouse_id for order in orders if order.warehouse_id}
    filters = [
        LogisticsEscalation.status == "OPEN",
        LogisticsEscalation.action_details.is_not(None),
    ]
    if warehouse_ids:
        filters.append(
            or_(
                LogisticsEscalation.warehouse_id.in_(warehouse_ids),
                LogisticsEscalation.warehouse_id.is_(None),
            )
        )

    escalations = (
        await db.execute(
            select(LogisticsEscalation)
            .where(*filters)
            .order_by(LogisticsEscalation.created_at.desc())
        )
    ).scalars().all()

    matches: dict[str, LogisticsEscalation] = {}
    for escalation in escalations:
        match = ORDER_ESCALATION_REF_RE.search(escalation.action_details or "")
        if not match:
            continue
        order_ref = match.group(1)
        if order_ref in order_ids and order_ref not in matches:
            matches[order_ref] = escalation
    return matches
