"""Keep support tickets in step with AI handoffs and vendor support tickets."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.models.vendor import VendorSupportTicket
from app.services.support.common import (
    _utc_now,
)
from app.services.support.contacts import (
    get_default_support_manager,
)
from app.services.support.ticket_helpers import (
    _close_support_session_once,
    _compose_ticket_notes,
    _find_ai_handoff_ticket_for_session,
    _handoff_ticket_priority,
    _linked_session_uuid_from_ticket,
    _next_ticket_reference,
    _split_ticket_notes,
    _support_priority_from_vendor,
    _support_status_from_vendor,
    _ticket_source_metadata,
)


async def mark_ai_handoff_ticket_in_progress(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    agent: User | None = None,
) -> None:
    ticket = await _find_ai_handoff_ticket_for_session(db, session_id)
    if not ticket or ticket.status == "resolved":
        return
    if ticket.status == "new":
        ticket.status = "in_progress"
    if agent is not None:
        ticket.assigned_to_user_id = agent.id
    db.add(ticket)
    await db.flush()


async def resolve_ai_handoff_ticket_for_session(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    actor: User | None = None,
) -> SupportTicket | None:
    ticket = await _find_ai_handoff_ticket_for_session(db, session_id)
    if not ticket:
        return None
    if ticket.status != "resolved":
        ticket.status = "resolved"
        ticket.resolved_at = _utc_now()
    if actor is not None:
        ticket.assigned_to_user_id = actor.id
    db.add(ticket)
    await db.flush()
    return ticket


async def resolve_ai_handoff_escalations_for_ticket(
    db: AsyncSession,
    *,
    ticket: SupportTicket,
    actor: User | None = None,
) -> None:
    metadata = _ticket_source_metadata(ticket)
    if metadata.get("source") != "ai_handoff":
        return

    session_id = _linked_session_uuid_from_ticket(ticket)
    if not session_id:
        return

    escalations = (
        await db.execute(
            select(Escalation)
            .options(selectinload(Escalation.conversation))
            .join(AIConversation, Escalation.conversation_id == AIConversation.id)
            .where(
                AIConversation.session_id == session_id,
                Escalation.status == "OPEN",
            )
            .order_by(Escalation.escalated_at.desc())
        )
    ).scalars().all()

    resolved_at = _utc_now()
    for escalation in escalations:
        escalation.status = "RESOLVED"
        escalation.resolved_at = resolved_at
        if actor is not None:
            escalation.escalated_to_user_id = actor.id
        db.add(escalation)

    await _close_support_session_once(db, session_id)
    await db.flush()


async def sync_vendor_ticket_to_support_ticket(
    db: AsyncSession,
    *,
    vendor: User,
    vendor_ticket: VendorSupportTicket,
    source: str | None = None,
    metadata_updates: dict[str, str | None] | None = None,
) -> SupportTicket:
    support_manager = await get_default_support_manager(db)
    existing = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(
                SupportTicket.notes.contains(
                    f"[meta:linked_vendor_ticket_id={vendor_ticket.id}]"
                )
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    visible_notes = None
    existing_metadata: dict[str, str] = {}
    if existing:
        existing_metadata, visible_notes = _split_ticket_notes(existing.notes)

    metadata = {
        **existing_metadata,
        "source": existing_metadata.get("source") or source or "vendor_portal",
        "linked_vendor_ticket_id": str(vendor_ticket.id),
        "linked_vendor_id": str(vendor.id),
        "linked_order_id": str(vendor_ticket.order_id) if vendor_ticket.order_id else None,
    }
    if source:
        metadata["source"] = source
    if metadata_updates:
        metadata.update(metadata_updates)
    vendor_name = (vendor.company_name or vendor.name or vendor.email or "Vendor").strip()

    ticket = existing or SupportTicket(reference_code=await _next_ticket_reference(db))
    ticket.title = vendor_ticket.subject.strip()
    ticket.description = vendor_ticket.description.strip()
    ticket.priority = _support_priority_from_vendor(vendor_ticket.priority)
    ticket.status = _support_status_from_vendor(vendor_ticket.status)
    ticket.category = "vendor_support"
    ticket.customer_name = vendor_name
    if support_manager:
        ticket.assigned_to_user_id = support_manager.id
    ticket.notes = _compose_ticket_notes(metadata=metadata, visible_notes=visible_notes)
    ticket.resolved_at = _utc_now() if ticket.status == "resolved" else None
    db.add(ticket)
    await db.flush()
    return ticket


async def sync_ai_handoff_ticket(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    user: User,
    reason: str,
    latest_user_message: str,
) -> SupportTicket:
    support_manager = await get_default_support_manager(db)
    existing = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(
                SupportTicket.notes.contains(
                    f"[meta:linked_session_id={session_id}]"
                )
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    visible_notes = None
    if existing:
        _, visible_notes = _split_ticket_notes(existing.notes)

    metadata = {
        "source": "ai_handoff",
        "linked_session_id": str(session_id),
        "linked_user_id": str(user.id),
        "requester_type": "Vendor"
        if getattr(getattr(user, "role", None), "name", None) == "VENDOR"
        else "Customer",
    }

    display_name = (user.name or user.email or "Customer").strip()
    title = f"AI Chat Handoff: {display_name}"
    description = (
        f"{reason.strip()}\n\nLatest user message:\n{latest_user_message.strip()}"
        if latest_user_message.strip()
        else reason.strip()
    )

    ticket = existing or SupportTicket(reference_code=await _next_ticket_reference(db))
    ticket.title = title
    ticket.description = description
    ticket.priority = _handoff_ticket_priority(reason)
    ticket.status = "new"
    ticket.category = "general"
    ticket.customer_name = display_name
    if support_manager:
        ticket.assigned_to_user_id = support_manager.id
    ticket.notes = _compose_ticket_notes(metadata=metadata, visible_notes=visible_notes)
    ticket.resolved_at = None
    db.add(ticket)
    await db.flush()
    return ticket
