"""Vendor dashboard, shipments list, settings, damage reports, team members and API keys."""

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import DamageReport as DamageReportModel
from app.models.user import User
from app.models.vendor import (
    VendorApiKey,
    VendorSupportTicket,
    VendorTeamMember,
)
from app.schemas.vendor import (
    VendorApiKeyCreate,
    VendorApiKeyResponse,
    VendorDamageReport,
    VendorDamageReportCreate,
    VendorDamageReportsResponse,
    VendorDashboardResponse,
    VendorSettings,
    VendorSettingsResponse,
    VendorShipmentsResponse,
    VendorStats,
    VendorSupportReplyResponse,
    VendorSupportTicketResponse,
    VendorTeamMemberCreate,
    VendorTeamMemberResponse,
)
from app.services.vendor.billing import (
    _analytics,
    _api_key_response,
    _invoice_summary,
    _orders_for_vendor,
)
from app.services.vendor.shipments import (
    _ensure_vendor,
    _profile,
    _resolve_assignment_maps,
    _shipment,
    _status_key,
)


def _ticket_response(ticket: VendorSupportTicket) -> VendorSupportTicketResponse:
    return VendorSupportTicketResponse(
        id=f"TK-{str(ticket.id).split('-')[0].upper()}",
        backend_id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        order_id=str(ticket.order_id) if ticket.order_id else None,
        created=ticket.created_at.strftime("%b %d, %Y"),
        priority=ticket.priority,
        status=ticket.status,
        replies=[
            VendorSupportReplyResponse(
                from_name=reply.from_name,
                message=reply.message,
                time=reply.created_at.strftime("%b %d, %Y %I:%M %p"),
            )
            for reply in ticket.replies
        ],
    )


async def get_vendor_dashboard(db: AsyncSession, user: User) -> VendorDashboardResponse:
    _ensure_vendor(user)
    orders = await _orders_for_vendor(db, user)
    driver_names, driver_phones, vehicle_codes, customer_names, customer_phones = await _resolve_assignment_maps(db, orders)
    analytics = _analytics(orders)
    status_keys = [_status_key(order.status) for order in orders]
    current_month = datetime.now().strftime("%Y-%m")

    monthly_spend = sum(
        order.total_amount
        for order in orders
        if order.created_at.strftime("%Y-%m") == current_month
    )

    # Fetch real wallet balance from WalletTransaction table
    from app.services.wallet_service import get_wallet_balance
    wallet_balance = await get_wallet_balance(db, user.id)

    invoices = _invoice_summary(orders, credit_balance=wallet_balance)

    stats = VendorStats(
        total_shipments=len(orders),
        active_shipments=sum(1 for key in status_keys if key == "transit"),
        pending_shipments=sum(1 for key in status_keys if key == "pending"),
        delivered_shipments=sum(1 for key in status_keys if key == "delivered"),
        cancelled_shipments=sum(1 for key in status_keys if key == "cancelled"),
        monthly_spend=monthly_spend,
        outstanding_amount=sum(invoice.amount - invoice.paid for invoice in invoices.invoices if invoice.status != "Paid"),
        paid_this_month=invoices.total_paid_this_month,
        credit_balance=round(wallet_balance, 2),
    )

    return VendorDashboardResponse(
        profile=_profile(user),
        stats=stats,
        recent_shipments=[
            _shipment(
                order,
                driver_name=driver_names.get(order.assigned_driver_id),
                driver_phone=driver_phones.get(order.assigned_driver_id),
                vehicle_code=vehicle_codes.get(order.assigned_vehicle_id),
                customer_name=customer_names.get(order.customer_id),
                customer_phone=customer_phones.get(order.customer_id),
            )
            for order in orders[:5]
        ],
        analytics=analytics,
        invoices=invoices,
    )


async def get_vendor_shipments(db: AsyncSession, user: User) -> VendorShipmentsResponse:
    _ensure_vendor(user)
    orders = await _orders_for_vendor(db, user)
    driver_names, driver_phones, vehicle_codes, customer_names, customer_phones = await _resolve_assignment_maps(db, orders)
    return VendorShipmentsResponse(
        shipments=[
            _shipment(
                order,
                driver_name=driver_names.get(order.assigned_driver_id),
                driver_phone=driver_phones.get(order.assigned_driver_id),
                vehicle_code=vehicle_codes.get(order.assigned_vehicle_id),
                customer_name=customer_names.get(order.customer_id),
                customer_phone=customer_phones.get(order.customer_id),
            )
            for order in orders
        ]
    )


async def get_vendor_settings(user: User) -> VendorSettingsResponse:
    _ensure_vendor(user)
    return VendorSettingsResponse(
        settings=VendorSettings(
            company_name=user.company_name or user.name,
            tax_id=user.tax_id or "",
            contact_person=user.contact_person or user.name,
            phone=user.business_phone or user.phone,
            email=user.business_email or user.email,
            address=user.address,
            notification_prefs={
                "email": user.notifications_email,
                "sms": user.notifications_sms,
                "push": user.notifications_push,
                "orderUpdates": user.notifications_push,
                "invoiceAlerts": user.notifications_email,
                "promotions": user.notifications_promo,
            },
        )
    )


async def update_vendor_settings(
    db: AsyncSession, user: User, data: VendorSettings
) -> VendorSettingsResponse:
    _ensure_vendor(user)
    user.company_name = data.company_name or user.company_name or user.name
    user.tax_id = data.tax_id or user.tax_id
    user.contact_person = data.contact_person or user.contact_person or user.name
    user.business_email = data.email or user.business_email or user.email
    user.business_phone = data.phone
    user.phone = data.phone or user.phone
    user.address = data.address
    user.notifications_email = data.notification_prefs.get("email", True)
    user.notifications_sms = data.notification_prefs.get("sms", bool(user.phone))
    user.notifications_push = data.notification_prefs.get("push", True)
    user.notifications_promo = data.notification_prefs.get("promotions", False)
    db.add(user)
    await db.flush()
    return await get_vendor_settings(user)


async def get_vendor_damage_reports(
    db: AsyncSession, user: User
) -> VendorDamageReportsResponse:
    _ensure_vendor(user)
    reports = (
        await db.execute(
            select(DamageReportModel)
            .where(DamageReportModel.customer_id == user.id)
            .order_by(DamageReportModel.created_at.desc())
        )
    ).scalars().all()
    return VendorDamageReportsResponse(
        reports=[
            VendorDamageReport(
                id=report.reference_code,
                order_id=str(report.order_id) if report.order_id else "",
                description=report.description,
                photos=report.photos or [],
                status=report.status,
                qr_code=report.qr_code,
                created_at=report.created_at.isoformat(),
            )
            for report in reports
        ]
    )


async def create_vendor_damage_report(
    db: AsyncSession, user: User, data: VendorDamageReportCreate
) -> VendorDamageReport:
    _ensure_vendor(user)
    report = DamageReportModel(
        reference_code=f"VDR-{uuid.uuid4().hex[:6].upper()}",
        customer_id=user.id,
        order_id=uuid.UUID(data.order_id) if data.order_id else None,
        description=data.description,
        photos=data.photos,
        status="reported",
        qr_code=f"QR-{uuid.uuid4().hex[:8].upper()}",
    )
    db.add(report)
    await db.flush()
    return VendorDamageReport(
        id=report.reference_code,
        order_id=str(report.order_id) if report.order_id else "",
        description=report.description,
        photos=report.photos or [],
        status=report.status,
        qr_code=report.qr_code,
        created_at=report.created_at.isoformat() if report.created_at else datetime.now().isoformat(),
    )


async def list_team_members(db: AsyncSession, user: User) -> list[VendorTeamMemberResponse]:
    _ensure_vendor(user)
    rows = (
        await db.execute(
            select(VendorTeamMember)
            .where(VendorTeamMember.vendor_id == user.id)
            .order_by(VendorTeamMember.created_at.desc())
        )
    ).scalars().all()
    return [VendorTeamMemberResponse.model_validate(row) for row in rows]


async def create_team_member(
    db: AsyncSession, user: User, data: VendorTeamMemberCreate
) -> VendorTeamMemberResponse:
    _ensure_vendor(user)
    member = VendorTeamMember(
        vendor_id=user.id,
        name=data.name,
        email=data.email.lower(),
        role=data.role,
        status="Invited",
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return VendorTeamMemberResponse.model_validate(member)


async def delete_team_member(db: AsyncSession, user: User, member_id: uuid.UUID) -> None:
    _ensure_vendor(user)
    member = (
        await db.execute(
            select(VendorTeamMember).where(
                VendorTeamMember.id == member_id,
                VendorTeamMember.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
    await db.delete(member)


async def list_api_keys(db: AsyncSession, user: User) -> list[VendorApiKeyResponse]:
    _ensure_vendor(user)
    rows = (
        await db.execute(
            select(VendorApiKey)
            .where(VendorApiKey.vendor_id == user.id)
            .order_by(VendorApiKey.created_at.desc())
        )
    ).scalars().all()
    return [_api_key_response(row) for row in rows]


async def create_api_key(
    db: AsyncSession, user: User, data: VendorApiKeyCreate
) -> VendorApiKeyResponse:
    _ensure_vendor(user)
    api_key = VendorApiKey(vendor_id=user.id, name=data.name)
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)
    return _api_key_response(api_key)


async def revoke_api_key(db: AsyncSession, user: User, key_id: uuid.UUID) -> VendorApiKeyResponse:
    _ensure_vendor(user)
    api_key = (
        await db.execute(
            select(VendorApiKey).where(
                VendorApiKey.id == key_id,
                VendorApiKey.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    api_key.status = "Revoked"
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)
    return _api_key_response(api_key)
