"""Creating, listing, reading, updating and soft-deleting orders."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.user import User
from app.schemas.orders import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)
from app.services.orders.common import (
    ORDER_STATUSES,
    ORDER_TYPES,
    _get_order,
    _hydrate_order_coordinates,
    _push_notification,
    _resolve_names,
    _resolve_open_order_escalations,
    _resolve_warehouse_id,
    _to_order_response,
    _tracking_code,
)


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


async def soft_delete_order(db: AsyncSession, order_id: UUID, caller: User) -> Order:
    order = (await db.execute(select(Order).where(Order.id == order_id, Order.is_deleted.is_(False)))).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order.is_deleted = True
    order.deleted_at = datetime.now(UTC)
    await db.flush()
    return order
