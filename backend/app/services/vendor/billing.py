"""Invoices, vendor analytics, response mappers and invoice payment."""

import uuid
from collections import OrderedDict
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.user import User
from app.models.vendor import (
    VendorApiKey,
    VendorBulkUpload,
)
from app.schemas.vendor import (
    VendorAnalytics,
    VendorApiKeyResponse,
    VendorBulkUploadResponse,
    VendorInvoicePayRequest,
    VendorInvoiceRecord,
    VendorInvoiceSummary,
    VendorMonthlyPoint,
)
from app.services.vendor.shipments import _ensure_vendor, _status_key


def _invoice_status(order: Order, now: datetime) -> str:
    if order.payment_status == "paid":
        return "Paid"
    paid_amount = getattr(order, 'paid_amount', 0) or 0
    if paid_amount > 0:
        return "Partial"
    due_date = order.created_at + timedelta(days=30)
    if due_date.date() < now.date():
        return "Overdue"
    return "Unpaid"


def _invoice_record(order: Order, now: datetime) -> VendorInvoiceRecord:
    invoice_status = _invoice_status(order, now)
    paid = getattr(order, 'paid_amount', 0) or 0
    if invoice_status == "Paid":
        paid = order.total_amount
    return VendorInvoiceRecord(
        id=f"INV-{order.tracking_code}",
        order_id=order.id,
        tracking_code=order.tracking_code,
        date=order.created_at.strftime("%b %d, %Y"),
        due_date=(order.created_at + timedelta(days=30)).strftime("%b %d, %Y"),
        amount=order.total_amount,
        paid=paid,
        status=invoice_status,
    )


async def _orders_for_vendor(db: AsyncSession, user: User) -> list[Order]:
    today = datetime.now(UTC).date()
    cutoff = today + timedelta(days=1)  # show recurring orders 1 day before their run date

    all_orders = (
        await db.execute(
            select(Order).where(Order.customer_id == user.id).order_by(Order.created_at.desc())
        )
    ).scalars().all()

    result = []
    for order in all_orders:
        # Recurring orders (identified by RECURRING_RULE marker) are only visible
        # from the day before their scheduled date so the vendor/WH doesn't see
        # them too far in advance.
        if order.delivery_notes and "RECURRING_RULE:" in order.delivery_notes:
            if order.scheduled_at and order.scheduled_at.date() > cutoff:
                continue
        result.append(order)
    return result



def _monthly_points(orders: list[Order]) -> list[VendorMonthlyPoint]:
    now = datetime.now()
    month_buckets: OrderedDict[str, dict[str, float | int]] = OrderedDict()
    for offset in range(5, -1, -1):
        month = ((now.month - offset - 1) % 12) + 1
        year = now.year + ((now.month - offset - 1) // 12)
        month_key = datetime(year, month, 1).strftime("%b")
        month_buckets[month_key] = {"spend": 0.0, "orders": 0}

    for order in orders:
        month_key = order.created_at.strftime("%b")
        if month_key in month_buckets:
            month_buckets[month_key]["orders"] += 1
            month_buckets[month_key]["spend"] += order.total_amount

    return [
        VendorMonthlyPoint(month=month, spend=float(values["spend"]), orders=int(values["orders"]))
        for month, values in month_buckets.items()
    ]


def _analytics(orders: list[Order]) -> VendorAnalytics:
    total = len(orders)
    delivered = sum(1 for order in orders if _status_key(order.status) == "delivered")
    cancelled = sum(1 for order in orders if _status_key(order.status) == "cancelled")
    successful = max(total - cancelled, 0)
    avg_order_value = sum(order.total_amount for order in orders) / total if total else 0

    transit_days = []
    for order in orders:
        if order.scheduled_at:
            transit_days.append(abs((order.scheduled_at - order.created_at).days) or 1)

    on_time = round((delivered / successful) * 100, 1) if successful else 0
    success_rate = round((successful / total) * 100, 1) if total else 0

    return VendorAnalytics(
        monthly=_monthly_points(orders),
        on_time=on_time,
        avg_transit_days=round(sum(transit_days) / len(transit_days), 1) if transit_days else 0,
        avg_order_value=round(avg_order_value, 2),
        success_rate=success_rate,
    )


def _invoice_summary(orders: list[Order], credit_balance: float = 0.0) -> VendorInvoiceSummary:
    now = datetime.now()
    invoices = [_invoice_record(order, now) for order in orders if order.total_amount > 0]
    total_overdue = sum(invoice.amount - invoice.paid for invoice in invoices if invoice.status == "Overdue")
    total_unpaid = sum(1 for invoice in invoices if invoice.status != "Paid")
    current_month = now.strftime("%Y-%m")
    total_paid_this_month = sum(
        invoice.paid
        for invoice in invoices
        if invoice.status == "Paid" and datetime.strptime(invoice.date, "%b %d, %Y").strftime("%Y-%m") == current_month
    )
    return VendorInvoiceSummary(
        invoices=invoices,
        total_overdue=total_overdue,
        total_unpaid=total_unpaid,
        total_paid_this_month=total_paid_this_month,
        credit_balance=round(credit_balance, 2),
    )


def _bulk_upload_response(upload: VendorBulkUpload) -> VendorBulkUploadResponse:
    return VendorBulkUploadResponse(
        id=upload.id,
        filename=upload.filename,
        date=upload.created_at.strftime("%b %d, %Y"),
        orders=upload.orders,
        status=upload.status,
        errors=upload.errors,
        scheduled_for=upload.scheduled_for,
    )


def _api_key_response(api_key: VendorApiKey) -> VendorApiKeyResponse:
    return VendorApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=api_key.key_value,
        created=api_key.created_at.strftime("%b %d, %Y"),
        last_used=api_key.last_used_at.strftime("%b %d, %Y") if api_key.last_used_at else "Never",
        status=api_key.status,
    )


async def pay_invoice(
    db: AsyncSession, user: User, order_id: uuid.UUID, data: VendorInvoicePayRequest
) -> VendorInvoiceRecord:
    _ensure_vendor(user)
    order = (
        await db.execute(
            select(Order).where(Order.id == order_id, Order.customer_id == user.id)
        )
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if order.payment_status == "paid":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice already paid")

    outstanding = max(float(order.total_amount or 0.0) - float(order.paid_amount or 0.0), 0.0)
    if outstanding <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice already settled")

    payment_amount = min(float(data.amount or 0.0), outstanding)
    if payment_amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount must be greater than zero")

    from app.services import finance_service

    await finance_service.record_order_payment(
        db=db,
        order_id=order.id,
        amount=payment_amount,
        payment_mode="ONLINE",
        payment_method=data.payment_method,
        payment_ref=None,
        collected_by_user=None,
        notes="Vendor invoice payment",
    )

    await db.flush()
    await db.refresh(order)
    return _invoice_record(order, datetime.now())
