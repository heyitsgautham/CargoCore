"""Customer portal services.

The dashboard, tracking, payments, quotes and settings live here.
Damage reports live in app/services/customer/damage_reports.py and are re-exported below,
so the routers and the tests that patch them keep one import path.
"""

import uuid
from collections import OrderedDict
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import CustomerQuote as CustomerQuoteModel
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.customer import (
    CustomerDashboardMonthlyPoint,
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
)
from app.services.customer.damage_reports import (
    create_customer_damage_report as create_customer_damage_report,
)
from app.services.customer.damage_reports import (
    get_customer_damage_reports as get_customer_damage_reports,
)
from app.services.customer.damage_reports import (
    get_damage_review_queue as get_damage_review_queue,
)
from app.services.customer.damage_reports import (
    submit_damage_review as submit_damage_review,
)
from app.services.customer.order_views import (
    build_driver_lookup,
    eta_label,
    progress_for_status,
    to_active_move,
    to_dashboard_order,
    to_user_profile,
    tracking_log,
    ui_status,
)


async def get_customer_dashboard(db: AsyncSession, user: User) -> CustomerDashboardResponse:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer dashboard is only available for individual users")

    orders = (
        await db.execute(
            select(Order).where(Order.customer_id == user.id).order_by(Order.created_at.desc())
        )
    ).scalars().all()
    driver_lookup = await build_driver_lookup(db, orders)

    ui_statuses = [ui_status(order.status) for order in orders]
    stats = CustomerDashboardStats(
        total_orders=len(orders),
        active_orders=sum(1 for value in ui_statuses if value in ("in-transit", "dispatched")),
        pending_orders=sum(1 for value in ui_statuses if value == "pending"),
        delivered_orders=sum(1 for value in ui_statuses if value == "delivered"),
        cancelled_orders=sum(1 for value in ui_statuses if value == "cancelled"),
        total_spent=sum(order.total_amount for order in orders if order.payment_status == "paid" or ui_status(order.status) == "delivered"),
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

    active_order_list = [order for order in orders if ui_status(order.status) in ("in-transit", "dispatched")]
    return CustomerDashboardResponse(
        profile=to_user_profile(user),
        stats=stats,
        active_move=to_active_move(active_order_list[0], driver_lookup) if active_order_list else None,
        active_moves=[to_active_move(o, driver_lookup) for o in active_order_list],
        recent_orders=[to_dashboard_order(order) for order in orders[:5]],
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
                ui_status=ui_status(order.status),
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
                progress=progress_for_status(order.status),
                eta_label=eta_label(order),
                picking_started_at=order.picking_started_at,
                picking_completed_at=order.picking_completed_at,
                packing_started_at=order.packing_started_at,
                packing_completed_at=order.packing_completed_at,
                qc_passed_at=qc_checked_at,
                dispatched_at=order.updated_at if order.warehouse_substatus == "DISPATCHED" else None,
                transport_log=tracking_log(order, qc_checked_at),
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
        payment_status = "completed" if order.payment_status == "paid" or ui_status(order.status) == "delivered" else "pending"
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
        profile=to_user_profile(user),
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
