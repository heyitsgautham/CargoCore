"""Bulk uploads and vendor support tickets."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.vendor import (
    VendorBulkUpload,
    VendorSupportReply,
    VendorSupportTicket,
)
from app.schemas.vendor import (
    VendorBulkUploadCreate,
    VendorBulkUploadResponse,
    VendorBulkUploadUpdate,
    VendorSupportReplyCreate,
    VendorSupportTicketCreate,
    VendorSupportTicketResponse,
)
from app.services.vendor.account import _ticket_response
from app.services.vendor.billing import _bulk_upload_response
from app.services.vendor.shipments import _ensure_vendor


async def list_bulk_uploads(db: AsyncSession, user: User) -> list[VendorBulkUploadResponse]:
    _ensure_vendor(user)
    rows = (
        await db.execute(
            select(VendorBulkUpload)
            .where(VendorBulkUpload.vendor_id == user.id)
            .order_by(VendorBulkUpload.created_at.desc())
        )
    ).scalars().all()
    return [_bulk_upload_response(row) for row in rows]


async def create_bulk_upload(
    db: AsyncSession, user: User, data: VendorBulkUploadCreate
) -> VendorBulkUploadResponse:
    _ensure_vendor(user)
    upload = VendorBulkUpload(
        vendor_id=user.id,
        filename=data.filename,
        file_size_kb=data.file_size_kb,
        orders=data.orders,
        status=data.status,
        errors=data.errors,
        scheduled_for=data.scheduled_for,
    )
    db.add(upload)
    await db.flush()
    await db.refresh(upload)
    return _bulk_upload_response(upload)


async def update_bulk_upload(
    db: AsyncSession, user: User, upload_id: uuid.UUID, data: VendorBulkUploadUpdate
) -> VendorBulkUploadResponse:
    _ensure_vendor(user)
    upload = (
        await db.execute(
            select(VendorBulkUpload).where(
                VendorBulkUpload.id == upload_id,
                VendorBulkUpload.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulk upload not found")
    if data.status is not None:
        upload.status = data.status
    if data.errors is not None:
        upload.errors = data.errors
    if data.scheduled_for is not None:
        upload.scheduled_for = data.scheduled_for
    db.add(upload)
    await db.flush()
    await db.refresh(upload)
    return _bulk_upload_response(upload)


async def list_support_tickets(db: AsyncSession, user: User) -> list[VendorSupportTicketResponse]:
    _ensure_vendor(user)
    rows = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.vendor_id == user.id)
            .order_by(VendorSupportTicket.created_at.desc())
        )
    ).scalars().all()
    return [_ticket_response(row) for row in rows]


async def create_support_ticket(
    db: AsyncSession, user: User, data: VendorSupportTicketCreate
) -> VendorSupportTicketResponse:
    _ensure_vendor(user)
    order_id = uuid.UUID(data.shipment_id) if data.shipment_id else None
    ticket = VendorSupportTicket(
        vendor_id=user.id,
        order_id=order_id,
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        status="Open",
    )
    db.add(ticket)
    await db.flush()
    reply = VendorSupportReply(ticket_id=ticket.id, from_name="You", message=data.description)
    db.add(reply)
    await db.flush()
    from app.services import ai_support_service

    await ai_support_service.sync_vendor_ticket_to_support_ticket(
        db=db,
        vendor=user,
        vendor_ticket=ticket,
    )
    result = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.id == ticket.id)
        )
    ).scalar_one()
    return _ticket_response(result)


async def reply_support_ticket(
    db: AsyncSession, user: User, ticket_id: uuid.UUID, data: VendorSupportReplyCreate
) -> VendorSupportTicketResponse:
    _ensure_vendor(user)
    ticket = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(
                VendorSupportTicket.id == ticket_id,
                VendorSupportTicket.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    if ticket.status == "Resolved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This support ticket is already resolved and the chat is closed.",
        )
    reply = VendorSupportReply(ticket_id=ticket.id, from_name="You", message=data.message)
    db.add(reply)
    await db.flush()
    from app.services import ai_support_service

    await ai_support_service.sync_vendor_ticket_to_support_ticket(
        db=db,
        vendor=user,
        vendor_ticket=ticket,
    )
    refreshed = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.id == ticket.id)
        )
    ).scalar_one()
    return _ticket_response(refreshed)


async def resolve_support_ticket(
    db: AsyncSession, user: User, ticket_id: uuid.UUID
) -> VendorSupportTicketResponse:
    _ensure_vendor(user)
    ticket = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(
                VendorSupportTicket.id == ticket_id,
                VendorSupportTicket.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    ticket.status = "Resolved"
    db.add(ticket)
    await db.flush()
    from app.services import ai_support_service

    await ai_support_service.sync_vendor_ticket_to_support_ticket(
        db=db,
        vendor=user,
        vendor_ticket=ticket,
    )
    await db.refresh(ticket, attribute_names=["replies"])
    return _ticket_response(ticket)
