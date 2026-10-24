import uuid
from collections import OrderedDict
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsReturnCase
from app.models.order import CustomerQuote as CustomerQuoteModel
from app.models.order import DamageReport as DamageReportModel
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.auth import UserProfile
from app.schemas.customer import (
    CustomerDamageReport,
    CustomerDamageReportCreate,
    CustomerDamageReportsResponse,
    CustomerDashboardActiveMove,
    CustomerDashboardCostSummary,
    CustomerDashboardDriver,
    CustomerDashboardMonthlyPoint,
    CustomerDashboardOrder,
    CustomerDashboardResponse,
    CustomerDashboardStats,
    CustomerPaymentRecord,
    CustomerPaymentsSummary,
    CustomerProfileResponse,
    CustomerQuote,
    CustomerQuotesResponse,
    CustomerSettings,
    CustomerSettingsResponse,
    CustomerTrackingOrder,
    CustomerTrackingResponse,
    DamageReviewQueueItem,
    DamageReviewUpdate,
)


def _ui_status(status_value: str) -> str:
    mapping = {
        "DRAFT": "pending",
        "CONFIRMED": "pending",
        "ASSIGNED": "dispatched",
        "IN_TRANSIT": "in-transit",
        "DELIVERED": "delivered",
        "CLOSED": "delivered",
        "CANCELLED": "cancelled",
    }
    return mapping.get(status_value.upper(), status_value.lower())


def _cargo_type(order: Order) -> str:
    if order.cargo_type:
        return order.cargo_type
    return "Household Goods" if order.order_type.upper() == "INDIVIDUAL" else "Shipment"


def _service_otp(order: Order) -> str:
    if order.service_otp:
        return order.service_otp
    digits = "".join(ch for ch in order.tracking_code if ch.isdigit())
    return (digits[-4:] or "0000").zfill(4)


def _service_time_block(order: Order) -> str:
    if order.service_time_block:
        return order.service_time_block
    if order.scheduled_at:
        return order.scheduled_at.strftime("%I:%M %p")
    return "TBD"


def _progress_for_status(status_value: str) -> int:
    mapping = {
        "pending": 15,
        "dispatched": 40,
        "in-transit": 65,
        "delivered": 100,
        "cancelled": 0,
    }
    return mapping.get(_ui_status(status_value), 0)


def _eta_label(order: Order) -> str:
    if order.status in {"DELIVERED", "CLOSED"}:
        return f"Delivered {_fmt(order.delivered_at or order.updated_at)}".strip()
    if order.status == "CANCELLED":
        return "Cancelled"
    if order.scheduled_at:
        return order.scheduled_at.strftime("%d %b, %I:%M %p")
    return "TBD"


def _fmt(dt) -> str:
    if dt is None:
        return ""
    return dt.strftime("%d %b %Y, %I:%M %p")


def _tracking_log(order: Order, qc_checked_at=None) -> list[dict]:
    created = _fmt(order.created_at)
    ws = order.warehouse_substatus or ""
    # Backfill display: confirmed orders with no substatus yet still show as queued
    if not ws and order.status in {"CONFIRMED", "ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        ws = "AWAITING_PICK"

    AFTER_AWAITING = {"PICKING", "PICKED", "PACKING", "PACKED", "QC_PASSED", "READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_PICKING  = {"PICKED", "PACKING", "PACKED", "QC_PASSED", "READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_PICKED   = {"PACKING", "PACKED", "QC_PASSED", "READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_PACKING  = {"PACKED", "QC_PASSED", "READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_PACKED   = {"QC_PASSED", "READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_QC       = {"READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_READY    = {"ON_DOCK", "DISPATCHED"}

    entries = [
        {"event": "Order created", "time": created, "icon": "receipt_long", "color": "blue"},
    ]

    if order.status in {"CONFIRMED", "ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        entries.append({"event": "Order confirmed", "time": created, "icon": "check_circle", "color": "green"})

    # Warehouse: Queued for picking
    if ws in AFTER_AWAITING | {"AWAITING_PICK"}:
        entries.append({
            "event": "Queued for Picking",
            "description": "Your order has been queued at the warehouse and is awaiting a pick team.",
            "time": created,
            "icon": "hourglass_empty",
            "color": "amber",
        })

    # Warehouse: On hold
    if ws == "ON_HOLD":
        entries.append({
            "event": "Order On Hold",
            "description": "Your order is temporarily on hold — usually due to insufficient labourers.",
            "time": _fmt(order.updated_at),
            "icon": "pause_circle",
            "color": "red",
        })

    # Warehouse: Picking started
    if ws in AFTER_AWAITING:
        entries.append({
            "event": "Picking started",
            "description": "Warehouse staff have started gathering your items from the shelves.",
            "time": _fmt(order.picking_started_at) or "In progress",
            "icon": "shopping_basket",
            "color": "blue",
        })

    # Warehouse: Picking completed
    if ws in AFTER_PICKED | {"PICKED"}:
        entries.append({
            "event": "Picking completed",
            "description": "All items have been gathered and are ready to be packed.",
            "time": _fmt(order.picking_completed_at) or "Completed",
            "icon": "inventory_2",
            "color": "cyan",
        })

    # Warehouse: Packing started
    if ws in AFTER_PICKED:
        entries.append({
            "event": "Packing started",
            "description": "Your items are being boxed and prepared for dispatch.",
            "time": _fmt(order.packing_started_at) or "In progress",
            "icon": "package_2",
            "color": "amber",
        })

    # Warehouse: Packing completed
    if ws in AFTER_PACKING | {"PACKED"}:
        entries.append({
            "event": "Packing completed",
            "description": "All items are securely packed and awaiting quality check.",
            "time": _fmt(order.packing_completed_at) or "Completed",
            "icon": "deployed_code",
            "color": "green",
        })

    # Warehouse: Quality check passed
    if ws in AFTER_QC | {"QC_PASSED"}:
        entries.append({
            "event": "Quality check passed",
            "description": "Your shipment has passed all quality and safety checks.",
            "time": _fmt(qc_checked_at) or "Verified",
            "icon": "verified",
            "color": "green",
        })

    # Warehouse: Ready for dispatch / on dock
    if ws in AFTER_READY | {"READY_FOR_DISPATCH"} or order.status in {"ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        entries.append({
            "event": "Ready for dispatch",
            "description": "Your shipment is on the loading dock and ready to be picked up.",
            "time": _fmt(order.updated_at) if ws in AFTER_READY | {"READY_FOR_DISPATCH"} else created,
            "icon": "local_shipping",
            "color": "blue",
        })

    # Driver assigned
    if order.status in {"ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        entries.append({
            "event": "Driver assigned",
            "description": "A driver and vehicle have been assigned to your shipment.",
            "time": _fmt(order.updated_at),
            "icon": "person_pin_circle",
            "color": "blue",
        })

    # In transit
    if ws == "DISPATCHED" or order.status in {"IN_TRANSIT", "DELIVERED", "CLOSED"}:
        entries.append({
            "event": "Shipment in transit",
            "description": "Your shipment is on its way to the destination.",
            "time": _fmt(order.updated_at) if ws == "DISPATCHED" else created,
            "icon": "local_shipping",
            "color": "green",
        })

    # Delivered
    if order.status in {"DELIVERED", "CLOSED"}:
        entries.append({
            "event": "Delivery completed",
            "description": "Your order has been delivered successfully.",
            "time": _fmt(order.delivered_at or order.updated_at),
            "icon": "where_to_vote",
            "color": "green",
        })

    # Cancelled
    if order.status == "CANCELLED":
        entries.append({
            "event": "Order cancelled",
            "description": order.cancel_reason or "No reason provided",
            "time": _fmt(order.updated_at),
            "icon": "cancel",
            "color": "red",
        })

    return entries


def _to_dashboard_order(order: Order) -> CustomerDashboardOrder:
    return CustomerDashboardOrder(
        id=order.id,
        tracking_code=order.tracking_code,
        order_type=order.order_type,
        status=order.status,
        ui_status=_ui_status(order.status),
        pickup_addr=order.pickup_addr,
        delivery_addr=order.delivery_addr,
        scheduled_at=order.scheduled_at,
        created_at=order.created_at,
        vehicle_type=order.vehicle_type or order.order_type.lower(),
        total_amount=order.total_amount,
    )


def _to_active_move(order: Order, driver_lookup: dict | None = None) -> CustomerDashboardActiveMove:
    driver_payload = (driver_lookup or {}).get(order.assigned_driver_id)
    return CustomerDashboardActiveMove(
        id=order.id,
        tracking_code=order.tracking_code,
        status=order.status,
        ui_status=_ui_status(order.status),
        pickup_addr=order.pickup_addr,
        delivery_addr=order.delivery_addr,
        scheduled_at=order.scheduled_at,
        created_at=order.created_at,
        vehicle_type=order.vehicle_type or order.order_type.lower(),
        cargo_type=_cargo_type(order),
        progress=_progress_for_status(order.status),
        eta_label=_eta_label(order),
        service_otp=_service_otp(order),
        service_time_block=_service_time_block(order),
        labor_count=order.labor_count,
        driver=CustomerDashboardDriver(
            name=driver_payload["name"] if driver_payload else None,
            phone=driver_payload["phone"] if driver_payload else None,
            rating=driver_payload["rating"] if driver_payload else None,
        ),
        cost=CustomerDashboardCostSummary(
            base=order.base_amount,
            vehicle=order.vehicle_amount,
            labor=order.labor_amount,
            materials=order.materials_amount,
            packing=order.packing_amount,
            platform_fee=order.platform_fee,
            taxes=order.tax_amount,
            total=order.total_amount,
        ),
    )


async def _build_driver_lookup(db: AsyncSession, orders: list[Order]) -> dict:
    driver_ids = {order.assigned_driver_id for order in orders if order.assigned_driver_id}
    if not driver_ids:
        return {}

    rows = (
        await db.execute(
            select(User.id, User.name, User.phone).where(User.id.in_(driver_ids))
        )
    ).all()
    return {
        row.id: {
            "name": row.name,
            "phone": row.phone,
            "rating": None,
        }
        for row in rows
    }


def _to_user_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        name=user.name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        address=user.address,
        role=user.role.name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


async def get_customer_dashboard(db: AsyncSession, user: User) -> CustomerDashboardResponse:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer dashboard is only available for individual users")

    orders = (
        await db.execute(
            select(Order).where(Order.customer_id == user.id).order_by(Order.created_at.desc())
        )
    ).scalars().all()
    driver_lookup = await _build_driver_lookup(db, orders)

    ui_statuses = [_ui_status(order.status) for order in orders]
    stats = CustomerDashboardStats(
        total_orders=len(orders),
        active_orders=sum(1 for value in ui_statuses if value in ("in-transit", "dispatched")),
        pending_orders=sum(1 for value in ui_statuses if value == "pending"),
        delivered_orders=sum(1 for value in ui_statuses if value == "delivered"),
        cancelled_orders=sum(1 for value in ui_statuses if value == "cancelled"),
        total_spent=sum(order.total_amount for order in orders if order.payment_status == "paid" or _ui_status(order.status) == "delivered"),
    )

    now = datetime.now()
    month_buckets: OrderedDict[str, int] = OrderedDict()
    for offset in range(5, -1, -1):
        month = ((now.month - offset - 1) % 12) + 1
        year = now.year + ((now.month - offset - 1) // 12)
        month_key = datetime(year, month, 1).strftime("%b")
        month_buckets[month_key] = 0

    for order in orders:
        month_key = order.created_at.strftime("%b")
        if month_key in month_buckets:
            month_buckets[month_key] += float(order.total_amount or 0)

    active_order_list = [order for order in orders if _ui_status(order.status) in ("in-transit", "dispatched")]
    return CustomerDashboardResponse(
        profile=_to_user_profile(user),
        stats=stats,
        active_move=_to_active_move(active_order_list[0], driver_lookup) if active_order_list else None,
        active_moves=[_to_active_move(o, driver_lookup) for o in active_order_list],
        recent_orders=[_to_dashboard_order(order) for order in orders[:5]],
        monthly_activity=[CustomerDashboardMonthlyPoint(month=month, count=count) for month, count in month_buckets.items()],
    )


async def get_customer_tracking(db: AsyncSession, user: User) -> CustomerTrackingResponse:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer tracking is only available for individual users")

    from app.models.warehouse import QualityCheck

    orders = (
        await db.execute(
            select(Order).where(Order.customer_id == user.id).order_by(Order.created_at.desc())
        )
    ).scalars().all()

    # Fetch QC checked_at for all orders in one query
    order_ids = [o.id for o in orders]
    qc_map: dict = {}
    if order_ids:
        qc_rows = (
            await db.execute(
                select(QualityCheck.order_id, QualityCheck.checked_at)
                .where(
                    QualityCheck.order_id.in_(order_ids),
                    QualityCheck.is_passed.is_(True),
                )
            )
        ).all()
        qc_map = {row.order_id: row.checked_at for row in qc_rows}

    warehouse_map: dict = {}
    warehouse_ids = list({order.warehouse_id for order in orders if order.warehouse_id})
    if warehouse_ids:
        warehouse_rows = (
            await db.execute(
                select(Warehouse).where(Warehouse.id.in_(warehouse_ids))
            )
        ).scalars().all()
        warehouse_map = {
            warehouse.id: warehouse
            for warehouse in warehouse_rows
        }

    tracking_orders = []
    for order in orders:
        qc_checked_at = qc_map.get(order.id)
        warehouse = warehouse_map.get(order.warehouse_id)
        tracking_orders.append(
            CustomerTrackingOrder(
                id=order.id,
                tracking_code=order.tracking_code,
                status=order.status,
                ui_status=_ui_status(order.status),
                warehouse_id=warehouse.id if warehouse else order.warehouse_id,
                warehouse_name=warehouse.name if warehouse else None,
                warehouse_address=warehouse.address if warehouse else None,
                warehouse_lat=warehouse.lat if warehouse else None,
                warehouse_lng=warehouse.lng if warehouse else None,
                warehouse_substatus=order.warehouse_substatus,
                pickup_addr=order.pickup_addr,
                delivery_addr=order.delivery_addr,
                scheduled_at=order.scheduled_at,
                created_at=order.created_at,
                progress=_progress_for_status(order.status),
                eta_label=_eta_label(order),
                picking_started_at=order.picking_started_at,
                picking_completed_at=order.picking_completed_at,
                packing_started_at=order.packing_started_at,
                packing_completed_at=order.packing_completed_at,
                qc_passed_at=qc_checked_at,
                dispatched_at=order.updated_at if order.warehouse_substatus == "DISPATCHED" else None,
                transport_log=_tracking_log(order, qc_checked_at),
            )
        )

    return CustomerTrackingResponse(orders=tracking_orders)


async def get_customer_payments(db: AsyncSession, user: User) -> CustomerPaymentsSummary:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer payments are only available for individual users")

    orders = (
        await db.execute(
            select(Order).where(Order.customer_id == user.id).order_by(Order.created_at.desc())
        )
    ).scalars().all()

    records: list[CustomerPaymentRecord] = []
    total_paid = 0.0
    pending_amount = 0.0
    for order in orders:
        payment_status = "completed" if order.payment_status == "paid" or _ui_status(order.status) == "delivered" else "pending"
        if payment_status == "completed":
            total_paid += order.total_amount
        else:
            pending_amount += order.total_amount
        records.append(
            CustomerPaymentRecord(
                id=f"PAY-{str(order.id).split('-')[0].upper()}",
                order_id=order.id,
                tracking_code=order.tracking_code,
                amount=order.total_amount,
                mode=order.payment_mode or "Order Billing",
                status=payment_status,
                created_at=order.created_at,
            )
        )
    return CustomerPaymentsSummary(total_paid=total_paid, pending_amount=pending_amount, records=records)


async def get_customer_profile(user: User) -> CustomerProfileResponse:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer profile is only available for individual users")

    return CustomerProfileResponse(
        profile=_to_user_profile(user),
        alt_phone=user.alt_phone,
        date_of_birth=user.date_of_birth.isoformat() if user.date_of_birth else None,
        address=user.address,
        language=user.preferred_language,
        currency=user.preferred_currency,
        default_payment=user.default_payment_method,
        notification_prefs={
            "push": user.notifications_push,
            "sms": user.notifications_sms,
            "email": user.notifications_email,
            "geofence": user.notifications_geofence,
            "promo": user.notifications_promo,
        },
        privacy_prefs={
            "location": user.privacy_location,
            "analytics": user.privacy_analytics,
            "marketing": user.privacy_marketing,
        },
    )


async def get_customer_quotes(db: AsyncSession, user: User) -> CustomerQuotesResponse:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer quotes are only available for individual users")

    quotes = (
        await db.execute(
            select(CustomerQuoteModel).where(CustomerQuoteModel.customer_id == user.id).order_by(CustomerQuoteModel.created_at.desc())
        )
    ).scalars().all()

    return CustomerQuotesResponse(
        quotes=[
            CustomerQuote(
                id=quote.reference_code,
                cargo_type=quote.cargo_type,
                from_location=quote.from_location,
                to_location=quote.to_location,
                labor_count=quote.labor_count,
                packing=quote.packing,
                total=quote.total_amount,
                date=quote.created_at.date().isoformat(),
                status=quote.status,
            )
            for quote in quotes
        ]
    )


async def convert_customer_quote(db: AsyncSession, user: User, quote_id: str) -> dict:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer quotes are only available for individual users")

    quote = (
        await db.execute(
            select(CustomerQuoteModel).where(CustomerQuoteModel.customer_id == user.id, CustomerQuoteModel.reference_code == quote_id)
        )
    ).scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")

    order = Order(
        tracking_code=f"QC-{uuid.uuid4().hex[:10].upper()}",
        order_type="INDIVIDUAL",
        status="CONFIRMED",
        customer_id=user.id,
        pickup_addr=quote.from_location,
        delivery_addr=quote.to_location,
        cargo_type=quote.cargo_type,
        labor_count=quote.labor_count,
        packing_amount=500 if quote.packing else 0,
        total_amount=quote.total_amount,
        payment_mode=user.default_payment_method,
        payment_status="pending",
        service_otp=str(uuid.uuid4().int)[-4:],
    )
    db.add(order)
    quote.status = "converted"
    db.add(quote)
    await db.flush()

    return {"order_id": str(order.id), "tracking_code": order.tracking_code}


async def get_customer_damage_reports(db: AsyncSession, user: User) -> CustomerDamageReportsResponse:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer damage reports are only available for individual users")

    reports = (
        await db.execute(
            select(DamageReportModel).where(DamageReportModel.customer_id == user.id).order_by(DamageReportModel.created_at.desc())
        )
    ).scalars().all()

    ref_codes = [r.reference_code for r in reports if r.reference_code]
    return_cases: dict = {}
    if ref_codes:
        cases = (await db.execute(
            select(LogisticsReturnCase).where(LogisticsReturnCase.reference_code.in_(ref_codes))
        )).scalars().all()
        return_cases = {c.reference_code: c for c in cases}

    def _resolve_status(report_status: str, return_case: LogisticsReturnCase | None) -> str:
        rc_status = return_case.status if return_case else None
        if return_case and getattr(return_case, "flow_type", None) == "photo_review" and rc_status in {"Inspected", "Physically Inspected"}:
            return "Claims Reviewed"
        return rc_status or report_status

    def _resolve_flow_type(report: DamageReportModel, return_case: LogisticsReturnCase | None) -> str:
        if return_case and getattr(return_case, "flow_type", None):
            return return_case.flow_type
        if getattr(report, "flow_type", None):
            return report.flow_type
        return "photo_review"

    return CustomerDamageReportsResponse(
        reports=[
            CustomerDamageReport(
                id=report.reference_code,
                order_id=str(report.order_id) if report.order_id else "",
                description=report.description,
                photos=report.photos or [],
                flow_type=_resolve_flow_type(report, return_cases.get(report.reference_code)),
                status=_resolve_status(
                    report.status,
                    return_cases.get(report.reference_code),
                ),
                qr_code=report.qr_code,
                created_at=report.created_at.isoformat(),
                refund_amount=return_cases[report.reference_code].refund_amount if report.reference_code in return_cases else None,
                condition=return_cases[report.reference_code].condition if report.reference_code in return_cases else None,
            )
            for report in reports
        ]
    )


async def create_customer_damage_report(db: AsyncSession, user: User, data: CustomerDamageReportCreate) -> CustomerDamageReport:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer damage reports are only available for individual users")

    order_uuid: uuid.UUID | None = None
    if data.order_id:
        try:
            order_uuid = uuid.UUID(data.order_id)
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid order ID format: '{data.order_id}'. Please select a valid order.",
            )

    resolution_type = data.resolution_type if data.resolution_type in {"photo_review", "pickup_inspection"} else "photo_review"

    report = DamageReportModel(
        reference_code=f"DMG-{uuid.uuid4().hex[:6].upper()}",
        customer_id=user.id,
        order_id=order_uuid,
        description=data.description,
        photos=data.photos,
        flow_type=resolution_type,
        status="reported",
        qr_code=f"QR-{uuid.uuid4().hex[:8].upper()}",
    )
    db.add(report)
    await db.flush()

    # Auto-create a LogisticsReturnCase so it appears in the
    # Logistics Manager's Reverse Logistics view immediately.
    order_total = 0.0
    warehouse_id = None
    if order_uuid:
        order_row = (await db.execute(select(Order).where(Order.id == order_uuid))).scalar_one_or_none()
        if order_row:
            order_total = order_row.total_amount or 0.0
            warehouse_id = order_row.warehouse_id

    return_case = LogisticsReturnCase(
        warehouse_id=warehouse_id,
        order_id=order_uuid,
        reference_code=report.reference_code,
        customer_name=user.name or user.email,
        reason=data.description[:255],
        flow_type=resolution_type,
        condition="Reported",
        status="Pickup Requested" if resolution_type == "pickup_inspection" else "Reported",
        original_price=order_total,
        refund_amount=0.0,
        images=data.photos or [],
    )
    db.add(return_case)

    await db.flush()

    return CustomerDamageReport(
        id=report.reference_code,
        order_id=str(report.order_id) if report.order_id else "",
        description=report.description,
        photos=report.photos or [],
        flow_type=resolution_type,
        status=return_case.status,
        qr_code=report.qr_code,
        created_at=report.created_at.isoformat() if report.created_at else datetime.now().isoformat(),
    )


async def get_damage_review_queue(
    db: AsyncSession,
    user: User,
    status_filter: str | None = None,
    flow_type: str | None = None,
) -> list[DamageReviewQueueItem]:
    linked_cases = (
        await db.execute(
            select(LogisticsReturnCase).order_by(LogisticsReturnCase.created_at.desc())
        )
    ).scalars().all()

    cases_by_ref = {case.reference_code: case for case in linked_cases if case.reference_code}
    reports = (
        await db.execute(
            select(DamageReportModel).order_by(DamageReportModel.created_at.desc())
        )
    ).scalars().all()

    items: list[DamageReviewQueueItem] = []
    for report in reports:
        case = cases_by_ref.get(report.reference_code)
        resolved_flow = getattr(case, "flow_type", None) or getattr(report, "flow_type", None) or "photo_review"
        resolved_status = case.status if case else "Reported"

        if flow_type and resolved_flow != flow_type:
            continue
        if status_filter and resolved_status != status_filter:
            continue

        if user.warehouse_id and case and case.warehouse_id and case.warehouse_id != user.warehouse_id:
            continue

        items.append(
            DamageReviewQueueItem(
                id=report.reference_code,
                order_id=str(report.order_id) if report.order_id else "",
                customer=case.customer_name if case else (user.name or user.email),
                description=report.description,
                images=report.photos or [],
                flow_type=resolved_flow,
                status=resolved_status,
            )
        )

    return items


async def submit_damage_review(
    db: AsyncSession,
    user: User,
    reference_code: str,
    data: DamageReviewUpdate,
) -> DamageReviewQueueItem:
    report = (
        await db.execute(
            select(DamageReportModel).where(DamageReportModel.reference_code == reference_code)
        )
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Damage report not found")

    case = (
        await db.execute(
            select(LogisticsReturnCase).where(LogisticsReturnCase.reference_code == reference_code)
        )
    ).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked return case not found")

    if case.flow_type != "photo_review":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Damage review is only available for photo review cases")

    case.status = data.new_status or "Claims Reviewed"
    if data.damage_severity:
        case.condition = data.damage_severity
    if data.is_genuine is not None:
        case.wm_is_genuine = data.is_genuine
    if data.recommended_settlement:
        case.wm_recommended_outcome = data.recommended_settlement
    if data.remarks:
        case.wm_inspection_remarks = data.remarks
    db.add(case)

    report.status = "reviewed"
    db.add(report)
    await db.flush()

    return DamageReviewQueueItem(
        id=report.reference_code,
        order_id=str(report.order_id) if report.order_id else "",
        customer=case.customer_name,
        description=report.description,
        images=report.photos or [],
        flow_type=case.flow_type,
        status=case.status,
    )


async def get_customer_settings(user: User) -> CustomerSettingsResponse:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer settings are only available for individual users")

    return CustomerSettingsResponse(
        settings=CustomerSettings(
            language=user.preferred_language,
            currency=user.preferred_currency,
            default_payment=user.default_payment_method,
            notification_prefs={
                "push": user.notifications_push,
                "sms": user.notifications_sms,
                "email": user.notifications_email,
                "geofence": user.notifications_geofence,
                "promo": user.notifications_promo,
            },
            privacy_prefs={
                "location": user.privacy_location,
                "analytics": user.privacy_analytics,
                "marketing": user.privacy_marketing,
            },
        )
    )


async def update_customer_settings(db: AsyncSession, user: User, settings: CustomerSettings) -> CustomerSettingsResponse:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer settings are only available for individual users")

    user.preferred_language = settings.language
    user.preferred_currency = settings.currency
    user.default_payment_method = settings.default_payment
    user.notifications_push = settings.notification_prefs.get("push", True)
    user.notifications_sms = settings.notification_prefs.get("sms", bool(user.phone))
    user.notifications_email = settings.notification_prefs.get("email", True)
    user.notifications_geofence = settings.notification_prefs.get("geofence", True)
    user.notifications_promo = settings.notification_prefs.get("promo", False)
    user.privacy_location = settings.privacy_prefs.get("location", True)
    user.privacy_analytics = settings.privacy_prefs.get("analytics", True)
    user.privacy_marketing = settings.privacy_prefs.get("marketing", False)
    db.add(user)
    await db.flush()

    return CustomerSettingsResponse(settings=settings)


async def delete_customer_account(db: AsyncSession, user: User) -> None:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deletion is only available for individual users",
        )

    user.is_active = False
    db.add(user)
    await db.flush()
