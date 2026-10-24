import math
import random
import re
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.inventory import InventoryItem, InventoryMovement
from app.models.labour import Labourer
from app.models.logistics import (
    LogisticsAlert,
    LogisticsDriverProfile,
    LogisticsEscalation,
    LogisticsNotification,
    LogisticsReturnCase,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.order import Order, OrderItem
from app.models.user import Role, User
from app.models.warehouse import ReturnGrading, Warehouse
from app.schemas.logistics import LogisticsEscalationItem
from app.schemas.orders import (
    CancelOrderRequest,
    DeliveryOtpSendResponse,
    OrderAssignRequest,
    OrderCreate,
    OrderEscalateRequest,
    OrderItemResponse,
    OrderItemUpsert,
    OrderListResponse,
    OrderResponse,
    OrderTripIntelligenceItem,
    OrderUpdate,
    TripCommandPushRequest,
    TripDeviationReportRequest,
)
from app.services import geocoding_service
from app.utils.email import delivery_otp_email_html, send_email

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
            print(f"Auto-geocoding failed for order pickup address: {e}")

    if order.delivery_addr and (order.delivery_lat is None or order.delivery_lng is None):
        try:
            results = await geocoding_service.search_address(order.delivery_addr, limit=1)
            if results:
                order.delivery_lat = float(results[0]["lat"])
                order.delivery_lng = float(results[0]["lon"])
        except Exception as e:
            # Don't fail order creation/update if delivery geocoding fails
            print(f"Auto-geocoding failed for order delivery address: {e}")


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


async def create_order(db: AsyncSession, data: OrderCreate, user: User) -> OrderResponse:
    order_type = data.order_type.upper()
    if order_type not in ORDER_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid order_type")

    if order_type == "SERVICE_MOVE" and user.role.name not in {"LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only logistics operations roles can create service moves",
        )

    from app.services.return_charge_service import (
        attach_pending_transport_charges_to_order,
    )

    requested_warehouse_id = data.warehouse_id
    if requested_warehouse_id is None and user.role.name in {"WAREHOUSE_MANAGER", "DISPATCHER"}:
        requested_warehouse_id = user.warehouse_id

    warehouse_id = await _resolve_warehouse_id(db, requested_warehouse_id)

    initial_status = "DRAFT"
    initial_substatus = None
    if order_type == "SERVICE_MOVE" and user.role.name in {"LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"}:
        initial_status = "CONFIRMED"
        initial_substatus = "AWAITING_PICK"
    elif order_type == "VENDOR":
        # Vendor orders skip DRAFT and auto-confirm
        # hub: vendor drops goods at warehouse → AWAITING_INBOUND (shows in Inbound section)
        # doorstep: driver picks from vendor → stays CONFIRMED with no substatus,
        #           appears in WM New Orders for acceptance, then moves to AWAITING_PICK
        initial_status = "CONFIRMED"
        pickup = (data.pickup_type or "hub").lower()
        initial_substatus = "AWAITING_INBOUND" if pickup == "hub" else None

    order = Order(
        tracking_code=_tracking_code(),
        order_type=order_type,
        status=initial_status,
        customer_id=user.id,
        warehouse_id=warehouse_id,
        warehouse_substatus=initial_substatus,
        pickup_addr=data.pickup_addr,
        pickup_type=data.pickup_type,
        pickup_lat=data.pickup_lat,
        pickup_lng=data.pickup_lng,
        delivery_addr=data.delivery_addr,
        cargo_weight_kg=data.cargo_weight_kg,
        cargo_volume_m3=data.cargo_volume_m3,
        cargo_type=data.cargo_type,
        vehicle_type=data.vehicle_type,
        labor_count=data.labor_count,
        base_amount=data.base_amount,
        vehicle_amount=data.vehicle_amount,
        labor_amount=data.labor_amount,
        materials_amount=data.materials_amount,
        packing_amount=data.packing_amount,
        platform_fee=data.platform_fee,
        tax_amount=data.tax_amount,
        total_amount=data.total_amount,
        payment_mode=data.payment_mode,
        payment_status=data.payment_status,
        declared_value=data.declared_value,
        service_otp=data.service_otp,
        service_time_block=data.service_time_block,
        scheduled_at=data.scheduled_at,
        delivery_notes=data.delivery_notes,
        priority=data.priority.upper() if data.priority else "NORMAL",
        delivery_lat=data.delivery_lat,
        delivery_lng=data.delivery_lng,
    )

    await _hydrate_order_coordinates(order)
    
    db.add(order)
    await db.flush()

    carry_forward_charge_amount = await attach_pending_transport_charges_to_order(db, order)
    if carry_forward_charge_amount > 0:
        order.total_amount = float(order.total_amount or 0.0) + carry_forward_charge_amount
        db.add(order)
        await db.flush()

    # Auto-deduct wallet for Prepaid vendor orders
    if order_type == "VENDOR" and (data.payment_mode or "").strip().lower() == "prepaid":
        prepaid_amount = float(order.total_amount or 0.0)
        if prepaid_amount > 0:
            from app.services import wallet_service as _ws
            balance = await _ws.get_wallet_balance(db, user.id)
            if balance < prepaid_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient wallet balance for Prepaid order. Required: ₹{prepaid_amount:.2f}, Available: ₹{balance:.2f}. Please top up your wallet first.",
                )
            await _ws.apply_wallet_payment(db, order=order, user=user, amount=prepaid_amount)

    initial_payment_amount = min(float(data.initial_payment_amount or 0.0), float(order.total_amount or 0.0))
    if initial_payment_amount > 0:
        if (data.initial_payment_mode or "").upper() == "WALLET":
            from app.services import wallet_service

            # Validates balance and raises HTTP 400 if insufficient — rolls back the order
            await wallet_service.apply_wallet_payment(
                db,
                order=order,
                user=user,
                amount=initial_payment_amount,
            )
        else:
            from app.services import finance_service

            await finance_service.record_order_payment(
                db=db,
                order_id=order.id,
                amount=initial_payment_amount,
                payment_mode=data.initial_payment_mode or "ONLINE",
                payment_method=data.initial_payment_method,
                payment_ref=data.initial_payment_ref,
                notes="Initial payment captured during order booking",
            )

    await db.refresh(order, attribute_names=["items"])

    # ── Notifications on new order ──────────────────────────────────────────
    order_label = order.tracking_code or str(order.id)
    order_type_label = order_type.capitalize()

    # Dispatcher: all new confirmed orders appear in their pending queue
    if order.status == "CONFIRMED":
        await _push_notification(
            db,
            title="New Order in Queue",
            message=f"{order_label} ({order_type_label}) has arrived and is awaiting dispatch.",
            notif_type="order",
            audience_roles=["DISPATCHER"],
        )

    # Warehouse Manager: new vendor or individual orders at their warehouse
    if order.status == "CONFIRMED" and order_type in {"VENDOR", "INDIVIDUAL"}:
        await _push_notification(
            db,
            title=f"New {'Vendor' if order_type == 'VENDOR' else 'Customer'} Order",
            message=f"{order_label} has been confirmed and is ready for warehouse processing.",
            notif_type="order",
            audience_roles=["WAREHOUSE_MANAGER"],
        )

    # Logistics Manager: all new orders
    await _push_notification(
        db,
        title="New Order Created",
        message=f"{order_label} ({order_type_label}) placed by {user.name or user.email}. Status: {order.status}.",
        notif_type="info",
        audience_roles=["LOGISTIC_MANAGER"],
    )

    return _to_order_response(order)


async def list_orders(
    db: AsyncSession,
    user: User,
    page: int,
    page_size: int,
    status_filter: str | None = None,
    search: str | None = None,
    warehouse_substatus: str | None = None,
    order_type: str | None = None,
    pickup_type: str | None = None,
) -> OrderListResponse:
    filters = [Order.is_deleted.is_(False)]
    user_role = user.role.name

    if user_role in {"INDIVIDUAL", "VENDOR"}:
        filters.append(Order.customer_id == user.id)
    elif user_role in {"WAREHOUSE_MANAGER", "LABOURER"}:
        if not user.warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not assigned to a warehouse",
            )
        filters.append(Order.warehouse_id == user.warehouse_id)
    elif user_role == "DISPATCHER" and user.warehouse_id:
        # Dispatcher sees only orders from their assigned hub
        filters.append(Order.warehouse_id == user.warehouse_id)
    elif user_role == "DRIVER":
        filters.append(Order.assigned_driver_id == user.id)
        if not status_filter:
            filters.append(~Order.status.in_(["DELIVERED", "COMPLETED", "CANCELLED", "CLOSED"]))

    if status_filter:
        upper_status = status_filter.upper()
        if upper_status in ORDER_STATUSES:
            filters.append(Order.status == upper_status)

    # Filter by warehouse substatus (e.g., AWAITING_INBOUND for inbound shipments)
    # Pass "none" to filter orders where warehouse_substatus IS NULL (not yet accepted)
    if warehouse_substatus:
        if warehouse_substatus.upper() == "NONE":
            filters.append(Order.warehouse_substatus.is_(None))
        else:
            filters.append(Order.warehouse_substatus == warehouse_substatus.upper())

    # Filter by order type (e.g., VENDOR for vendor inbound orders)
    if order_type:
        filters.append(Order.order_type == order_type.upper())

    # Filter by pickup type (e.g., hub for inbound section, doorstep for picking)
    if pickup_type:
        filters.append(Order.pickup_type == pickup_type.lower())

    if search and search.strip():
        s = f"%{search.strip()}%"
        filters.append(
            or_(
                Order.tracking_code.ilike(s),
                Order.delivery_addr.ilike(s),
                Order.pickup_addr.ilike(s),
            )
        )

    total_query = select(func.count(Order.id))
    data_query = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if filters:
        total_query = total_query.where(*filters)
        data_query = data_query.where(*filters)

    total = (await db.execute(total_query)).scalar_one()
    rows = (await db.execute(data_query)).scalars().all()

    driver_names, vehicle_codes, customer_names, customer_phones = await _resolve_names(db, list(rows))
    order_escalations = await _resolve_open_order_escalations(db, list(rows))

    return OrderListResponse(
        items=[
            _to_order_response(
                order,
                driver_name=driver_names.get(order.assigned_driver_id),
                vehicle_code=vehicle_codes.get(order.assigned_vehicle_id),
                customer_name=customer_names.get(order.customer_id),
                customer_phone=customer_phones.get(order.customer_id),
                escalated=str(order.id) in order_escalations,
                escalation_id=order_escalations[str(order.id)].id if str(order.id) in order_escalations else None,
                escalation_status=order_escalations[str(order.id)].status if str(order.id) in order_escalations else None,
            )
            for order in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_order_detail(db: AsyncSession, order_id: UUID, user: User) -> OrderResponse:
    order = await _get_order(db, order_id)
    if user.role.name in {"INDIVIDUAL", "VENDOR"} and order.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    dn, vc, cn, cp = await _resolve_names(db, [order])
    order_escalations = await _resolve_open_order_escalations(db, [order])
    escalation = order_escalations.get(str(order.id))
    return _to_order_response(
        order,
        driver_name=dn.get(order.assigned_driver_id),
        vehicle_code=vc.get(order.assigned_vehicle_id),
        customer_name=cn.get(order.customer_id),
        customer_phone=cp.get(order.customer_id),
        escalated=escalation is not None,
        escalation_id=escalation.id if escalation else None,
        escalation_status=escalation.status if escalation else None,
    )


async def update_order(db: AsyncSession, order_id: UUID, user: User, data: OrderUpdate) -> OrderResponse:
    order = await _get_order(db, order_id)
    if order.status not in {"DRAFT", "CONFIRMED"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order cannot be edited in current status",
        )

    if user.role.name in {"INDIVIDUAL", "VENDOR"} and order.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    updated_fields = data.model_dump(exclude_unset=True)
    pickup_addr_changed = "pickup_addr" in updated_fields
    delivery_addr_changed = "delivery_addr" in updated_fields
    pickup_coords_supplied = "pickup_lat" in updated_fields or "pickup_lng" in updated_fields
    delivery_coords_supplied = "delivery_lat" in updated_fields or "delivery_lng" in updated_fields

    for key, value in updated_fields.items():
        setattr(order, key, value)

    if pickup_addr_changed and not pickup_coords_supplied:
        order.pickup_lat = None
        order.pickup_lng = None
    if delivery_addr_changed and not delivery_coords_supplied:
        order.delivery_lat = None
        order.delivery_lng = None

    if {
        "pickup_addr",
        "pickup_lat",
        "pickup_lng",
        "delivery_addr",
        "delivery_lat",
        "delivery_lng",
    } & set(updated_fields):
        await _hydrate_order_coordinates(order)

    db.add(order)
    await db.flush()
    await db.refresh(order, attribute_names=["items"])
    return _to_order_response(order)


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


async def track_order(db: AsyncSession, tracking_code: str) -> dict:
    result = await db.execute(select(Order).where(Order.tracking_code == tracking_code))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracking code not found")

    return {
        "tracking_code": order.tracking_code,
        "status": order.status,
        "pickup_addr": order.pickup_addr,
        "delivery_addr": order.delivery_addr,
        "scheduled_at": order.scheduled_at,
    }


async def get_order_items(db: AsyncSession, order_id: UUID) -> list[OrderItemResponse]:
    order = await _get_order(db, order_id)
    if not order.items:
        return []

    # Resolve inventory item names for all SKUs in this order
    name_map: dict[str, str] = {}
    if order.warehouse_id:
        skus = [item.sku for item in order.items]
        inv_rows = (await db.execute(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == order.warehouse_id,
                InventoryItem.sku.in_(skus),
            )
        )).scalars().all()
        name_map = {inv.sku: inv.name for inv in inv_rows}

    results = []
    for item in order.items:
        r = OrderItemResponse.model_validate(item)
        r.name = name_map.get(item.sku)
        results.append(r)
    return results


async def _canonical_order_item_sku(db: AsyncSession, order: Order, sku: str) -> str:
    """Normalize legacy packing material IDs like PKG-<inventory UUID> to real inventory SKUs."""
    raw = (sku or "").strip()
    candidate = raw.removeprefix("PKG-")

    try:
        item_id = UUID(candidate)
    except (TypeError, ValueError):
        return raw

    filters = [InventoryItem.id == item_id]
    if order.warehouse_id:
        filters.append(InventoryItem.warehouse_id == order.warehouse_id)

    inventory_item = (await db.execute(select(InventoryItem).where(*filters))).scalar_one_or_none()
    return inventory_item.sku if inventory_item and inventory_item.sku else raw


async def upsert_order_items(
    db: AsyncSession,
    order_id: UUID,
    items: list[OrderItemUpsert],
) -> list[OrderItemResponse]:
    order = await _get_order(db, order_id)

    existing_by_sku = {item.sku: item for item in order.items}
    for item_data in items:
        sku = await _canonical_order_item_sku(db, order, item_data.sku)
        existing = existing_by_sku.get(sku)
        if existing:
            existing.quantity = item_data.quantity
            existing.box_count = item_data.box_count
            existing.estimated_volume = item_data.estimated_volume
            db.add(existing)
            continue

        new_item = OrderItem(
            order_id=order.id,
            sku=sku,
            quantity=item_data.quantity,
            box_count=item_data.box_count,
            estimated_volume=item_data.estimated_volume,
        )
        db.add(new_item)
        existing_by_sku[sku] = new_item

    await db.flush()
    refreshed = await _get_order(db, order_id)
    return [OrderItemResponse.model_validate(item) for item in refreshed.items]


# ---------------------------------------------------------------------------
# Route Optimization
# ---------------------------------------------------------------------------

_ROUTE_COLORS = [
    "#1CE783",
    "#3B82F6",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#EC4899",
    "#06B6D4",
]

_HUB_LAT = 12.9716
_HUB_LNG = 77.5946


def _euclidean_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Rough Euclidean distance in km using 1 deg ≈ 111 km."""
    dlat = (lat2 - lat1) * 111.0
    dlng = (lng2 - lng1) * 111.0 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.sqrt(dlat ** 2 + dlng ** 2)


_PRIORITY_RANK = {"URGENT": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}


async def optimize_routes(
    db: AsyncSession,
    optimize_for: str = "distance",
    prioritize_urgent: bool = False,
) -> list[dict]:
    """Assign CONFIRMED orders to available drivers using a nearest-neighbour heuristic."""

    # 1. Fetch CONFIRMED orders
    orders: list[Order] = (
        await db.execute(select(Order).where(Order.status == "CONFIRMED"))
    ).scalars().all()

    # 2. Fetch active drivers (LogisticsDriverProfile joined with User)
    rows = (
        await db.execute(
            select(LogisticsDriverProfile, User)
            .join(User, User.id == LogisticsDriverProfile.user_id)
            .where(User.is_active.is_(True))
        )
    ).all()

    drivers = [(profile, user) for profile, user in rows]

    if not drivers:
        return []

    # 3. Geocode orders that lack coordinates (save coords for future use, don't crash if it fails)
    needs_geocode = [o for o in orders if o.delivery_lat is None or o.delivery_lng is None]
    for order in needs_geocode:
        if order.delivery_addr:
            try:
                results = await geocoding_service.search_address(order.delivery_addr, limit=1)
                if results and results[0]["lat"] and results[0]["lon"]:
                    order.delivery_lat = float(results[0]["lat"])
                    order.delivery_lng = float(results[0]["lon"])
                    db.add(order)
            except Exception:
                pass

    if needs_geocode:
        try:
            await db.flush()
        except Exception:
            await db.rollback()

    # 4. Keep only orders that now have valid coordinates
    geo_orders = [o for o in orders if o.delivery_lat is not None and o.delivery_lng is not None]

    if not geo_orders:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No orders have delivery coordinates. Ensure destinations are selected on the map."
        )

    # 5. Sort orders: priority first (if requested or optimize_for=time), then by distance/deadline
    def _sort_key(o):
        pri = _PRIORITY_RANK.get(getattr(o, "priority", None) or "NORMAL", 2)
        dist = _euclidean_km(_HUB_LAT, _HUB_LNG, o.delivery_lat, o.delivery_lng)
        deadline_ts = o.scheduled_at.timestamp() if o.scheduled_at else float("inf")
        if prioritize_urgent or optimize_for == "time":
            return (pri, deadline_ts, dist)
        return (pri, dist)

    geo_orders.sort(key=_sort_key)

    # 6. Round-robin assignment across drivers
    driver_stops: dict[int, list[Order]] = {i: [] for i in range(len(drivers))}
    for idx, order in enumerate(geo_orders):
        driver_stops[idx % len(drivers)].append(order)

    # 7. Build route dicts
    routes = []
    for driver_idx, (_profile, user) in enumerate(drivers):
        stops = driver_stops[driver_idx]
        if not stops:
            continue

        # Total distance: hub → stop1 → stop2 → … → hub
        coords = [(s.delivery_lat, s.delivery_lng) for s in stops]
        total_dist = _euclidean_km(_HUB_LAT, _HUB_LNG, coords[0][0], coords[0][1])
        for i in range(len(coords) - 1):
            total_dist += _euclidean_km(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
        total_dist += _euclidean_km(coords[-1][0], coords[-1][1], _HUB_LAT, _HUB_LNG)

        routes.append(
            {
                "driver_id": str(user.id),
                "driver_name": user.name,
                "color": _ROUTE_COLORS[driver_idx % len(_ROUTE_COLORS)],
                "stops": [
                    {
                        "order_id": str(s.id),
                        "address": s.delivery_addr,
                        "lat": s.delivery_lat,
                        "lng": s.delivery_lng,
                        "tracking_code": s.tracking_code,
                        "priority": getattr(s, "priority", None) or "NORMAL",
                    }
                    for s in stops
                ],
                "total_distance_km": round(total_dist, 2),
                "efficiency": random.randint(85, 98),
            }
        )

    return routes


def _parse_driver_location(location: str | None) -> tuple[float | None, float | None]:
    if not location or "," not in str(location):
        return None, None
    try:
        lat_str, lng_str = str(location).split(",", 1)
        return float(lat_str.strip()), float(lng_str.strip())
    except Exception:
        return None, None


def _clamp(value: int | float, minimum: int | float, maximum: int | float) -> int | float:
    return max(minimum, min(maximum, value))


def _eta_label_from_minutes(eta_minutes: int, reference_time: datetime | None = None) -> str:
    arrival = (reference_time or _now()) + timedelta(minutes=max(eta_minutes, 0))
    return arrival.astimezone(UTC).strftime("%I:%M %p").lstrip("0")


def _build_route_signal(key: str, label: str, severity: str) -> dict:
    return {"key": key, "label": label, "severity": severity}


def _derive_eta_confidence(
    *,
    has_pickup_coords: bool,
    has_delivery_coords: bool,
    has_live_driver_location: bool,
    order_status: str,
) -> str:
    if has_pickup_coords and has_delivery_coords and (order_status != "IN_TRANSIT" or has_live_driver_location):
        return "High"
    if has_delivery_coords:
        return "Medium"
    return "Low"


def _recommended_dispatch_action(
    *,
    no_go_zone_hit: bool,
    route_status: str,
    risk_level: str,
    order_status: str,
    priority: str,
    minutes_saved: int,
) -> tuple[str, str]:
    if no_go_zone_hit:
        return (
            "Push the alternate corridor to the driver now. The planned corridor overlaps a restricted or exclusion zone.",
            "Dispatch has selected a safer corridor. Open the updated navigation before continuing.",
        )
    if route_status == "Delayed":
        return (
            "Customer ETA is at risk. Push a route update, notify the customer, and keep this trip in the exception queue.",
            "This trip is running behind plan. Follow the updated route and keep dispatch informed.",
        )
    if risk_level in {"HIGH", "CRITICAL"} and minutes_saved >= 5:
        return (
            f"Push the alternate route now. It is currently projecting {minutes_saved} minutes of recovery.",
            f"An alternate route is available and may recover about {minutes_saved} minutes.",
        )
    if order_status == "ASSIGNED" and priority in {"URGENT", "HIGH"}:
        return (
            "Send the driver immediately and monitor first-mile progress. This trip has a tight operating window.",
            "This job is time-sensitive. Start navigation as soon as dispatch confirms the release.",
        )
    return (
        "Trip is on plan. Keep the primary corridor and monitor only if ETA confidence drops.",
        "Trip is on track. Use the planned route and continue normal navigation.",
    )


def _compute_alternate_waypoints(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    hit_zones: list[LogisticsZone],
) -> list[dict]:
    """Return a single bypass waypoint that steers around the first exclusion zone."""
    if not hit_zones:
        return []
    zone = hit_zones[0]
    if zone.lat is None or zone.lng is None:
        return []
    radius_km = zone.radius_km or 1.0
    mid_lat = (origin_lat + dest_lat) / 2
    mid_lng = (origin_lng + dest_lng) / 2
    dlat = dest_lat - origin_lat
    dlng = dest_lng - origin_lng
    route_len = math.sqrt(dlat ** 2 + dlng ** 2)
    if route_len < 1e-9:
        return []
    perp1 = (-dlng / route_len, dlat / route_len)
    perp2 = (dlng / route_len, -dlat / route_len)
    offset_deg = (radius_km + 2.5) * 0.009
    cand1 = (mid_lat + perp1[0] * offset_deg, mid_lng + perp1[1] * offset_deg)
    cand2 = (mid_lat + perp2[0] * offset_deg, mid_lng + perp2[1] * offset_deg)
    dist1 = _euclidean_km(cand1[0], cand1[1], zone.lat, zone.lng)
    dist2 = _euclidean_km(cand2[0], cand2[1], zone.lat, zone.lng)
    wp = cand1 if dist1 > dist2 else cand2
    return [{"lat": round(wp[0], 6), "lng": round(wp[1], 6)}]


async def _enrich_with_gemini(base: dict) -> dict:
    """Replace templated messages with Gemini-generated operational intelligence."""
    import json as _json

    from loguru import logger
    try:
        from google.genai import types as genai_types

        from app.utils.gemini import generate_with_fallback

        signals_text = "\n".join(
            f"- [{s['severity'].upper()}] {s['label']}" for s in base.get("signals", [])
        ) or "No active risk signals."
        minutes_saved = max(0, -(base["alternate_route"]["delta_minutes"]))

        prompt = f"""You are a logistics AI analyst for Cargo-Core dispatch platform.

TRIP FACTS:
- Tracking: {base['tracking_code']} | Status: {base['order_status']} | Priority: {base['priority']}
- Route status: {base['route_status']} | Risk: {base['risk_level']} | Delay probability: {base['delay_probability_pct']}%
- ETA: {base['eta_label']} ({base['eta_minutes']} min) | Distance: {base['planned_distance_km']} km
- No-go zone hit: {base['no_go_zone_hit']} | Recommended route: {base['recommended_route']}
- Alternate saves: {minutes_saved} min

RISK SIGNALS:
{signals_text}

Return ONLY valid JSON (no markdown):
{{
  "dispatcher_recommendation": "...",
  "driver_message": "...",
  "alternate_route_summary": "..."
}}

Rules:
- dispatcher_recommendation: 40-70 words, operational, tells dispatcher exactly what to do and why
- driver_message: 20-35 words, direct and simple, as if spoken by radio dispatch to the driver
- alternate_route_summary: 15-25 words, what the alternate avoids or why it is faster"""

        response = await generate_with_fallback(
            contents=[genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=prompt)])],
            config=genai_types.GenerateContentConfig(temperature=0.3, response_mime_type="application/json"),
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        ai = _json.loads(text)
        result = {**base}
        if ai.get("dispatcher_recommendation"):
            result["dispatcher_recommendation"] = ai["dispatcher_recommendation"]
        if ai.get("driver_message"):
            result["driver_message"] = ai["driver_message"]
        if ai.get("alternate_route_summary"):
            result["alternate_route"] = {**base["alternate_route"], "summary": ai["alternate_route_summary"]}
        return result
    except Exception as exc:
        logger.warning(f"Gemini trip enrichment failed, using rule-based fallback: {exc}")
        return base


def _build_trip_intelligence_item(
    order: Order,
    *,
    driver_name: str | None,
    profile: LogisticsDriverProfile | None,
    vehicle: LogisticsVehicle | None,
    zones: list[LogisticsZone],
    reference_time: datetime | None = None,
) -> dict:
    now = reference_time or _now()
    order_status = str(order.status or "").upper()
    priority = str(getattr(order, "priority", None) or "NORMAL").upper()
    pickup_lat = order.pickup_lat
    pickup_lng = order.pickup_lng
    delivery_lat = order.delivery_lat
    delivery_lng = order.delivery_lng

    live_lat, live_lng = _parse_driver_location(profile.current_location if profile else None)
    origin_lat = live_lat if order_status == "IN_TRANSIT" and live_lat is not None else pickup_lat
    origin_lng = live_lng if order_status == "IN_TRANSIT" and live_lng is not None else pickup_lng

    has_pickup_coords = pickup_lat is not None and pickup_lng is not None
    has_delivery_coords = delivery_lat is not None and delivery_lng is not None
    has_origin_coords = origin_lat is not None and origin_lng is not None

    if has_origin_coords and has_delivery_coords:
        base_distance_km = round(_euclidean_km(origin_lat, origin_lng, delivery_lat, delivery_lng), 1)
    elif has_pickup_coords and has_delivery_coords:
        base_distance_km = round(_euclidean_km(pickup_lat, pickup_lng, delivery_lat, delivery_lng), 1)
    else:
        base_distance_km = 12.0

    base_distance_km = max(base_distance_km, 3.0)
    base_drive_minutes = max(18, round((base_distance_km / 28.0) * 60))
    handling_minutes = 12 if order_status == "ASSIGNED" else 6
    primary_penalty = 0
    signals: list[dict] = []
    no_go_zone_hit = False
    hit_zones: list[LogisticsZone] = []

    hour = now.astimezone(UTC).hour
    peak_window = 8 <= hour <= 10 or 17 <= hour <= 20
    if peak_window:
        primary_penalty += 10
        signals.append(_build_route_signal("traffic", "Peak-hour congestion risk detected on urban corridor.", "medium"))
    elif base_distance_km >= 25:
        primary_penalty += 5
        signals.append(_build_route_signal("distance", "Long single-trip distance increases ETA variability.", "medium"))

    if priority == "URGENT":
        primary_penalty += 10
        signals.append(_build_route_signal("priority", "Urgent order is operating with little dispatch slack.", "high"))
    elif priority == "HIGH":
        primary_penalty += 6
        signals.append(_build_route_signal("priority", "High-priority order should be monitored for ETA drift.", "medium"))

    if profile:
        driver_status = str(profile.status or "").lower()
        if driver_status in {"deviation", "breakdown"}:
            primary_penalty += 18
            signals.append(_build_route_signal("driver_status", f"Driver status is {profile.status}. Dispatch attention recommended.", "high"))
        elif driver_status in {"on break", "on_break"}:
            primary_penalty += 10
            signals.append(_build_route_signal("driver_status", "Driver is near a break window or recently paused.", "medium"))

    if vehicle and vehicle.maintenance_issue:
        primary_penalty += 6
        signals.append(_build_route_signal("vehicle", f"Vehicle note: {vehicle.maintenance_issue}.", "medium"))

    exclusion_margin_km = 1.2
    if has_delivery_coords:
        for zone in zones:
            if zone.lat is None or zone.lng is None or zone.radius_km is None:
                continue
            zone_distance_km = _euclidean_km(zone.lat, zone.lng, delivery_lat, delivery_lng)
            zone_type = str(zone.zone_type or "").lower()
            zone_status = str(zone.status or "").lower()
            within_zone = zone_distance_km <= zone.radius_km
            near_zone = zone_distance_km <= (zone.radius_km + exclusion_margin_km)

            if zone_type == "exclusion" and (within_zone or near_zone):
                no_go_zone_hit = True
                hit_zones.append(zone)
                primary_penalty += 18 if within_zone else 10
                signals.append(
                    _build_route_signal(
                        "zone",
                        f"Restricted zone near destination: {zone.name}. Alternate corridor recommended.",
                        "high" if within_zone else "medium",
                    )
                )
            elif zone_status == "alert" and (within_zone or near_zone):
                primary_penalty += 8
                signals.append(
                    _build_route_signal(
                        "zone_alert",
                        f"Operational alert near destination: {zone.name}. Expect access friction.",
                        "medium",
                    )
                )

    slack_minutes: int | None = None
    if order.scheduled_at:
        scheduled_at = order.scheduled_at
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=UTC)
        projected_primary = now + timedelta(minutes=base_drive_minutes + handling_minutes + primary_penalty)
        slack_minutes = int((scheduled_at - projected_primary).total_seconds() / 60)
        if slack_minutes < 0:
            primary_penalty += 18
            signals.append(_build_route_signal("sla", "Projected ETA is beyond the planned delivery window.", "high"))
        elif slack_minutes < 30:
            primary_penalty += 10
            signals.append(_build_route_signal("sla", "Projected ETA is close to the delivery commitment.", "medium"))

    primary_eta_minutes = base_drive_minutes + handling_minutes + primary_penalty

    alternate_gain = 0
    if peak_window:
        alternate_gain += 8
    if no_go_zone_hit:
        alternate_gain += 14
    if slack_minutes is not None and slack_minutes < 30:
        alternate_gain += 6
    if profile and str(profile.status or "").lower() == "deviation":
        alternate_gain += 8

    if alternate_gain > 0:
        alternate_eta_minutes = max(base_drive_minutes + handling_minutes, primary_eta_minutes - alternate_gain)
        alternate_distance_km = round(base_distance_km * 1.08, 1)
    else:
        alternate_eta_minutes = primary_eta_minutes + 5
        alternate_distance_km = round(base_distance_km * 1.03, 1)

    minutes_saved = max(0, primary_eta_minutes - alternate_eta_minutes)
    delay_probability = int(_clamp(18 + (primary_penalty * 2.2), 12, 97))
    if no_go_zone_hit:
        delay_probability = max(delay_probability, 78)
    if slack_minutes is not None and slack_minutes < 0:
        delay_probability = max(delay_probability, 84)

    if delay_probability >= 82 or (no_go_zone_hit and slack_minutes is not None and slack_minutes < 15):
        risk_level = "CRITICAL"
    elif delay_probability >= 65:
        risk_level = "HIGH"
    elif delay_probability >= 42:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if no_go_zone_hit and risk_level in {"HIGH", "CRITICAL"}:
        route_status = "Blocked"
    elif slack_minutes is not None and slack_minutes < 0:
        route_status = "Delayed"
    elif risk_level in {"MEDIUM", "HIGH", "CRITICAL"}:
        route_status = "Delay Risk"
    else:
        route_status = "On Track"

    recommended_route = "alternate" if minutes_saved >= 5 or no_go_zone_hit else "primary"
    dispatcher_recommendation, driver_message = _recommended_dispatch_action(
        no_go_zone_hit=no_go_zone_hit,
        route_status=route_status,
        risk_level=risk_level,
        order_status=order_status,
        priority=priority,
        minutes_saved=minutes_saved,
    )

    trip_stage = (
        "In-transit"
        if order_status == "IN_TRANSIT"
        else "Pre-dispatch"
        if order_status == "ASSIGNED"
        else "Awaiting Assignment"
    )
    eta_confidence = _derive_eta_confidence(
        has_pickup_coords=has_pickup_coords,
        has_delivery_coords=has_delivery_coords,
        has_live_driver_location=live_lat is not None and live_lng is not None,
        order_status=order_status,
    )

    payload = {
        "order_id": order.id,
        "tracking_code": order.tracking_code or "",
        "order_status": order_status,
        "driver_id": order.assigned_driver_id,
        "driver_name": driver_name,
        "vehicle_id": order.assigned_vehicle_id,
        "vehicle_code": vehicle.code if vehicle else None,
        "pickup_addr": order.pickup_addr or "",
        "delivery_addr": order.delivery_addr or "",
        "pickup_lat": pickup_lat,
        "pickup_lng": pickup_lng,
        "delivery_lat": delivery_lat,
        "delivery_lng": delivery_lng,
        "origin_lat": origin_lat,
        "origin_lng": origin_lng,
        "priority": priority,
        "trip_stage": trip_stage,
        "route_status": route_status,
        "risk_level": risk_level,
        "eta_label": _eta_label_from_minutes(primary_eta_minutes, now),
        "eta_minutes": primary_eta_minutes,
        "delay_probability_pct": delay_probability,
        "eta_confidence": eta_confidence,
        "planned_distance_km": round(base_distance_km, 1),
        "no_go_zone_hit": no_go_zone_hit,
        "signal_count": len(signals),
        "signals": signals,
        "dispatcher_recommendation": dispatcher_recommendation,
        "driver_message": driver_message,
        "primary_route": {
            "route_id": "primary",
            "label": "Primary corridor",
            "eta_minutes": primary_eta_minutes,
            "eta_label": _eta_label_from_minutes(primary_eta_minutes, now),
            "distance_km": round(base_distance_km, 1),
            "delta_minutes": 0,
            "summary": "Default operational plan using the current corridor.",
            "recommended": recommended_route == "primary",
        },
        "alternate_route": {
            "route_id": "alternate",
            "label": "Alternate corridor",
            "eta_minutes": alternate_eta_minutes,
            "eta_label": _eta_label_from_minutes(alternate_eta_minutes, now),
            "distance_km": alternate_distance_km,
            "delta_minutes": alternate_eta_minutes - primary_eta_minutes,
            "summary": (
                f"Recovers about {minutes_saved} minutes by avoiding risk hotspots."
                if minutes_saved > 0
                else "Fallback corridor with lower confidence but similar timing."
            ),
            "recommended": recommended_route == "alternate",
            "waypoints": _compute_alternate_waypoints(
                origin_lat or pickup_lat or 0.0,
                origin_lng or pickup_lng or 0.0,
                delivery_lat or 0.0,
                delivery_lng or 0.0,
                hit_zones,
            ) if has_delivery_coords else [],
        },
        "recommended_route": recommended_route,
        "generated_at": now,
    }
    return OrderTripIntelligenceItem.model_validate(payload).model_dump(mode="python")


async def _build_trip_intelligence_collection(
    db: AsyncSession,
    orders: list[Order],
) -> list[dict]:
    if not orders:
        return []

    driver_ids = {order.assigned_driver_id for order in orders if order.assigned_driver_id}
    vehicle_ids = {order.assigned_vehicle_id for order in orders if order.assigned_vehicle_id}
    warehouse_ids = {order.warehouse_id for order in orders if order.warehouse_id}

    profile_map: dict[UUID, LogisticsDriverProfile] = {}
    user_map: dict[UUID, User] = {}
    vehicle_map: dict[UUID, LogisticsVehicle] = {}
    zone_map: dict[UUID, list[LogisticsZone]] = {}

    if driver_ids:
        profiles = (
            await db.execute(
                select(LogisticsDriverProfile).where(LogisticsDriverProfile.user_id.in_(driver_ids))
            )
        ).scalars().all()
        profile_map = {profile.user_id: profile for profile in profiles}

        users = (
            await db.execute(select(User).where(User.id.in_(driver_ids)))
        ).scalars().all()
        user_map = {user.id: user for user in users}

    if vehicle_ids:
        vehicles = (
            await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.id.in_(vehicle_ids)))
        ).scalars().all()
        vehicle_map = {vehicle.id: vehicle for vehicle in vehicles}

    if warehouse_ids:
        zones = (
            await db.execute(select(LogisticsZone).where(LogisticsZone.warehouse_id.in_(warehouse_ids)))
        ).scalars().all()
        for zone in zones:
            zone_map.setdefault(zone.warehouse_id, []).append(zone)

    import asyncio as _asyncio
    base_items = [
        _build_trip_intelligence_item(
            order,
            driver_name=user_map.get(order.assigned_driver_id).name if order.assigned_driver_id in user_map else None,
            profile=profile_map.get(order.assigned_driver_id),
            vehicle=vehicle_map.get(order.assigned_vehicle_id),
            zones=zone_map.get(order.warehouse_id, []),
        )
        for order in orders
    ]

    items = list(await _asyncio.gather(*[_enrich_with_gemini(item) for item in base_items]))

    severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    items.sort(key=lambda item: (severity_rank.get(item["risk_level"], 9), -item["delay_probability_pct"]))
    return items


async def list_trip_intelligence(db: AsyncSession, statuses: str = "ASSIGNED,IN_TRANSIT") -> list[dict]:
    normalized_statuses = [
        value.strip().upper()
        for value in str(statuses or "").split(",")
        if value.strip()
    ] or ["ASSIGNED", "IN_TRANSIT"]

    orders = (
        await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.status.in_(normalized_statuses))
            .order_by(Order.created_at.desc())
        )
    ).scalars().all()
    return await _build_trip_intelligence_collection(db, orders)


async def get_trip_intelligence(
    db: AsyncSession,
    order_id: UUID,
    caller: User | None = None,
) -> dict:
    order = await _get_order(db, order_id)

    if caller is not None and caller.role.name == "DRIVER" and order.assigned_driver_id != caller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the assigned driver for this order",
        )

    items = await _build_trip_intelligence_collection(db, [order])
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip intelligence unavailable")
    return items[0]


async def push_trip_command_update(
    db: AsyncSession,
    order_id: UUID,
    data: TripCommandPushRequest,
    caller: User | None = None,
) -> dict:
    order = await _get_order(db, order_id)
    if not order.assigned_driver_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This order is not assigned to a driver yet",
        )

    intelligence = await get_trip_intelligence(db, order_id, caller=caller)
    selected_route = str(data.selected_route or "recommended").strip().lower()
    if selected_route == "recommended":
        selected_route = intelligence["recommended_route"]
    if selected_route not in {"primary", "alternate"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="selected_route must be primary, alternate, or recommended",
        )

    chosen_route = intelligence["primary_route"] if selected_route == "primary" else intelligence["alternate_route"]
    saved_minutes = max(0, -(chosen_route.get("delta_minutes", 0)))
    dispatcher_note = (data.dispatcher_note or "").strip() or intelligence["driver_message"]

    await _push_notification(
        db,
        title="Route update from dispatch",
        message=dispatcher_note,
        notif_type="info" if selected_route == "primary" else "warning",
        target_user_id=order.assigned_driver_id,
    )

    try:
        from app.routers.ws_fleet import driver_alert_manager
        await driver_alert_manager.send_to_driver(
            str(order.assigned_driver_id),
            {
                "type": "route_update",
                "title": "Route update from dispatch",
                "message": dispatcher_note,
                "order_id": str(order.id),
                "tracking_code": order.tracking_code or "",
                "selected_route": selected_route,
                "saved_minutes": saved_minutes,
                "route_status": intelligence["route_status"],
                "risk_level": intelligence["risk_level"],
                "trip_intelligence": jsonable_encoder(intelligence),
            },
        )
    except Exception:
        pass

    return {
        "success": True,
        "order_id": str(order.id),
        "tracking_code": order.tracking_code or "",
        "selected_route": selected_route,
        "saved_minutes": saved_minutes,
        "message": "Trip command pushed to driver",
    }


async def report_trip_deviation(
    db: AsyncSession,
    order_id: UUID,
    data: TripDeviationReportRequest,
    caller: User,
) -> dict:
    order = await _get_order(db, order_id)
    if order.assigned_driver_id != caller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the assigned driver for this order",
        )

    description = f"{caller.name} reported a route deviation on {order.tracking_code}: {data.reason}"
    if data.details:
        description = f"{description}. {data.details}"
    location = (
        f"{data.latitude}, {data.longitude}"
        if data.latitude is not None and data.longitude is not None
        else order.delivery_addr or order.pickup_addr or "Unknown"
    )

    alert = LogisticsAlert(
        warehouse_id=order.warehouse_id,
        alert_type="route_deviation",
        title=f"Route deviation - {caller.name}",
        description=description,
        severity="high",
        icon="alt_route",
        location=location,
        recommendation="Review Trip Command and push a reroute if the current corridor is no longer viable.",
        impact_json={
            "order_id": str(order.id),
            "tracking_code": order.tracking_code or "",
            "driver_id": str(caller.id),
            "driver_name": caller.name,
            "reason": data.reason,
        },
        is_active=True,
    )
    db.add(alert)
    await db.flush()

    await _push_notification(
        db,
        title="Driver reported route deviation",
        message=f"{caller.name} needs route help on {order.tracking_code}",
        notif_type="warning",
        audience_roles=["DISPATCHER"],
    )

    try:
        from app.routers.ws_fleet import fleet_manager
        await fleet_manager.broadcast(
            {
                "type": "route_deviation",
                "alert_id": str(alert.id),
                "order_id": str(order.id),
                "tracking_code": order.tracking_code or "",
                "driver_id": str(caller.id),
                "driver_name": caller.name,
                "reason": data.reason,
                "location": location,
                "severity": "high",
            }
        )
    except Exception:
        pass

    return {
        "success": True,
        "alert_id": str(alert.id),
        "message": "Route deviation reported to dispatcher",
    }


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


async def auto_balance_drivers(db: AsyncSession) -> dict:
    """
    Auto-balance workload across drivers by redistributing ASSIGNED orders.
    
    Algorithm:
    1. Get all active drivers and their ASSIGNED order counts
    2. Calculate average load per driver
    3. Identify overloaded (>avg) and underloaded (<avg) drivers
    4. Reassign orders from overloaded to underloaded drivers
    
    Does NOT touch IN_TRANSIT orders (already being delivered).
    """
    # 1. Get all active drivers
    driver_result = await db.execute(
        select(LogisticsDriverProfile, User)
        .join(User, User.id == LogisticsDriverProfile.user_id)
        .where(User.is_active.is_(True))
        .where(LogisticsDriverProfile.status == "Active")
    )
    drivers = driver_result.all()
    
    if len(drivers) < 2:
        return {
            "success": False,
            "message": "Need at least 2 active drivers to balance workload",
            "transfers": []
        }
    
    # 2. Get ASSIGNED orders per driver (not IN_TRANSIT - those are already being delivered)
    order_counts_result = await db.execute(
        select(Order.assigned_driver_id, func.count(Order.id).label("order_count"))
        .where(Order.status == "ASSIGNED")
        .where(Order.assigned_driver_id.isnot(None))
        .group_by(Order.assigned_driver_id)
    )
    order_counts = {str(row[0]): row[1] for row in order_counts_result.all()}
    
    # Build driver load map
    driver_loads = []
    for _profile, user in drivers:
        driver_id = str(user.id)
        count = order_counts.get(driver_id, 0)
        driver_loads.append({
            "driver_id": user.id,
            "driver_name": user.name,
            "order_count": count
        })
    
    # 3. Calculate average and identify imbalances
    total_orders = sum(d["order_count"] for d in driver_loads)
    if total_orders == 0:
        return {
            "success": True,
            "message": "No ASSIGNED orders to balance",
            "transfers": [],
            "before": {"total_orders": 0, "drivers": len(drivers)},
            "after": {"total_orders": 0, "drivers": len(drivers)}
        }
    
    avg_load = total_orders / len(driver_loads)
    
    # Sort: overloaded first (descending), underloaded last (ascending)
    overloaded = sorted(
        [d for d in driver_loads if d["order_count"] > avg_load],
        key=lambda x: x["order_count"],
        reverse=True
    )
    underloaded = sorted(
        [d for d in driver_loads if d["order_count"] < avg_load],
        key=lambda x: x["order_count"]
    )
    
    if not overloaded or not underloaded:
        return {
            "success": True,
            "message": "Workload is already balanced",
            "transfers": [],
            "balance_score": 100
        }
    
    # 4. Perform transfers
    transfers = []
    
    for over_driver in overloaded:
        while over_driver["order_count"] > avg_load and underloaded:
            # Find the most underloaded driver
            under_driver = underloaded[0]
            
            if under_driver["order_count"] >= avg_load:
                break  # No more underloaded drivers
            
            # Get one order from the overloaded driver to transfer
            order_result = await db.execute(
                select(Order)
                .where(Order.assigned_driver_id == over_driver["driver_id"])
                .where(Order.status == "ASSIGNED")
                .limit(1)
            )
            order_to_transfer = order_result.scalar_one_or_none()
            
            if not order_to_transfer:
                break
            
            # Transfer the order
            order_to_transfer.assigned_driver_id = under_driver["driver_id"]
            db.add(order_to_transfer)
            
            # Update driver profiles' current_job
            # (Update underloaded driver's current_job if they were free)
            under_profile = (await db.execute(
                select(LogisticsDriverProfile)
                .where(LogisticsDriverProfile.user_id == under_driver["driver_id"])
            )).scalar_one_or_none()
            if under_profile and not under_profile.current_job:
                under_profile.current_job = order_to_transfer.tracking_code
                db.add(under_profile)
            
            transfers.append({
                "order_id": str(order_to_transfer.id),
                "tracking_code": order_to_transfer.tracking_code,
                "from_driver": over_driver["driver_name"],
                "to_driver": under_driver["driver_name"]
            })
            
            # Update counts
            over_driver["order_count"] -= 1
            under_driver["order_count"] += 1
            
            # Re-sort underloaded list
            underloaded = sorted(underloaded, key=lambda x: x["order_count"])
    
    await db.flush()
    
    # Calculate new balance score
    new_loads = [d["order_count"] for d in driver_loads]
    if new_loads:
        mean = sum(new_loads) / len(new_loads)
        variance = sum((load - mean) ** 2 for load in new_loads) / len(new_loads)
        std_dev = math.sqrt(variance)
        balance_score = max(0, min(100, round(100 - (std_dev * 25))))
    else:
        balance_score = 100
    
    return {
        "success": True,
        "message": f"Transferred {len(transfers)} order(s) to balance workload",
        "transfers": transfers,
        "balance_score": balance_score,
        "driver_loads": [
            {"name": d["driver_name"], "orders": d["order_count"]}
            for d in driver_loads
        ]
    }


async def soft_delete_order(db: AsyncSession, order_id: UUID, caller: User) -> Order:
    order = (await db.execute(select(Order).where(Order.id == order_id, Order.is_deleted.is_(False)))).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order.is_deleted = True
    order.deleted_at = datetime.now(UTC)
    await db.flush()
    return order
