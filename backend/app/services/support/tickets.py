"""Support tickets: AI handoff tickets, vendor ticket sync, CRUD and replies."""

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.order import DamageReport
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.models.vendor import VendorSupportReply, VendorSupportTicket
from app.schemas.ai import (
    AgentReplyRequest,
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketStats,
    TicketUpdate,
)
from app.services.support.common import (
    _ensure_support_manager,
    _list_support_agents,
    _utc_now,
)
from app.services.support.contacts import (
    create_user_notification,
    get_default_support_manager,
)
from app.services.support.ticket_helpers import (
    INBOUND_RESOLUTION_LABELS,
    TICKET_PRIORITY_VALUES,
    TICKET_STATUS_VALUES,
    _close_support_session_once,
    _compose_ticket_notes,
    _find_ai_handoff_ticket_for_session,
    _handoff_ticket_priority,
    _linked_order_tracking_map,
    _linked_order_uuid_from_ticket,
    _linked_session_uuid_from_ticket,
    _linked_vendor_ticket_map,
    _linked_vendor_ticket_uuid_from_ticket,
    _next_ticket_reference,
    _split_ticket_notes,
    _support_priority_from_vendor,
    _support_status_from_vendor,
    _ticket_response,
    _ticket_source_metadata,
    _vendor_priority_from_support,
    _vendor_status_from_support,
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


async def create_ticket(
    db: AsyncSession,
    data: TicketCreate,
    actor: User | None = None,
) -> TicketResponse:
    if actor is not None:
        _ensure_support_manager(actor)
    priority = (data.priority or "medium").strip().lower()
    if priority not in TICKET_PRIORITY_VALUES:
        raise HTTPException(status_code=400, detail="Invalid priority")
    category = (data.category or "general").strip().lower()

    ticket = SupportTicket(
        reference_code=await _next_ticket_reference(db),
        title=data.title.strip(),
        description=data.description.strip(),
        priority=priority,
        status="new",
        category=category,
        customer_name=(data.customer_name or "").strip() or None,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return _ticket_response(ticket)


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


async def list_tickets(db: AsyncSession) -> TicketListResponse:
    tickets = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .order_by(SupportTicket.created_at.desc())
        )
    ).scalars().all()

    stats = TicketStats(
        total=len(tickets),
        new=sum(1 for t in tickets if t.status == "new"),
        in_progress=sum(1 for t in tickets if t.status == "in_progress"),
        resolved=sum(1 for t in tickets if t.status == "resolved"),
        urgent=sum(1 for t in tickets if t.priority == "urgent"),
    )
    order_map = await _linked_order_tracking_map(db, tickets)
    vendor_ticket_map = await _linked_vendor_ticket_map(db, tickets)

    return TicketListResponse(
        tickets=[
            _ticket_response(
                t,
                order_tracking_code=order_map.get(_linked_order_uuid_from_ticket(t)),
                vendor_ticket=vendor_ticket_map.get(_linked_vendor_ticket_uuid_from_ticket(t)),
            )
            for t in tickets
        ],
        stats=stats,
        agents=await _list_support_agents(db),
    )


async def get_recovery_tickets_count(db: AsyncSession) -> dict:
    tickets = (
        await db.execute(
            select(SupportTicket).where(
                SupportTicket.customer_name == "AI Support Analytics",
                SupportTicket.status != "resolved",
            )
        )
    ).scalars().all()
    return {"count": len(tickets)}


async def update_ticket(
    db: AsyncSession, ticket_id: uuid.UUID, data: TicketUpdate, actor: User | None = None
) -> TicketResponse:
    if actor is not None:
        _ensure_support_manager(actor)
    ticket = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(SupportTicket.id == ticket_id)
        )
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    metadata, visible_notes = _split_ticket_notes(ticket.notes)
    source = metadata.get("source", "manual")
    current_resolution_action = (metadata.get("resolution_action") or "").strip().lower()
    should_resolve_linked_ai_handoff = False

    if data.status is not None:
        s = data.status.strip().lower()
        if s not in TICKET_STATUS_VALUES:
            raise HTTPException(status_code=400, detail="Invalid status")
        if source == "warehouse_inbound" and s == "resolved":
            requested_resolution = (
                data.resolution_action.strip().lower()
                if data.resolution_action is not None
                else current_resolution_action
            )
            if requested_resolution not in {"vendor_accept_move", "vendor_take_back"}:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Warehouse inbound tickets must be resolved with "
                        "Vendor Cleared For Move or Vendor Will Take Back."
                    ),
                )
        ticket.status = s
        ticket.resolved_at = _utc_now() if s == "resolved" else None
        should_resolve_linked_ai_handoff = source == "ai_handoff" and s == "resolved"
    if data.priority is not None:
        p = data.priority.strip().lower()
        if p not in TICKET_PRIORITY_VALUES:
            raise HTTPException(status_code=400, detail="Invalid priority")
        ticket.priority = p
    if data.category is not None:
        ticket.category = data.category.strip().lower()
    if data.notes is not None:
        visible_notes = data.notes
        ticket.notes = _compose_ticket_notes(
            metadata=metadata,
            visible_notes=data.notes,
        )
    if data.resolution_action is not None:
        resolution_action = data.resolution_action.strip().lower()
        if resolution_action not in INBOUND_RESOLUTION_LABELS:
            raise HTTPException(status_code=400, detail="Invalid resolution action")
        metadata["resolution_action"] = resolution_action
        ticket.notes = _compose_ticket_notes(
            metadata=metadata,
            visible_notes=visible_notes,
        )
        linked_damage_report_raw = metadata.get("linked_damage_report_id")
        if linked_damage_report_raw:
            try:
                linked_damage_report_id = uuid.UUID(linked_damage_report_raw)
            except ValueError:
                linked_damage_report_id = None
            if linked_damage_report_id:
                report = (
                    await db.execute(
                        select(DamageReport).where(DamageReport.id == linked_damage_report_id)
                    )
                ).scalar_one_or_none()
                if report:
                    report.status = (
                        "vendor_take_back"
                        if resolution_action == "vendor_take_back"
                        else "vendor_accept_move"
                    )
                    support_summary = INBOUND_RESOLUTION_LABELS[resolution_action]
                    if visible_notes and visible_notes.strip():
                        support_summary = f"{support_summary}\n{visible_notes.strip()}"
                    report.support_notes = support_summary
                    db.add(report)
    if "assigned_to_user_id" in data.model_fields_set:
        ticket.assigned_to_user_id = data.assigned_to_user_id

    linked_vendor_ticket_id_raw = _ticket_source_metadata(ticket).get("linked_vendor_ticket_id")
    vendor_ticket: VendorSupportTicket | None = None
    if linked_vendor_ticket_id_raw:
        try:
            linked_vendor_ticket_id = uuid.UUID(linked_vendor_ticket_id_raw)
        except ValueError:
            linked_vendor_ticket_id = None
        if linked_vendor_ticket_id:
            vendor_ticket = (
                await db.execute(
                    select(VendorSupportTicket)
                    .options(selectinload(VendorSupportTicket.replies))
                    .where(VendorSupportTicket.id == linked_vendor_ticket_id)
                )
            ).scalar_one_or_none()
            if vendor_ticket:
                vendor_ticket.status = _vendor_status_from_support(ticket.status)
                vendor_ticket.priority = _vendor_priority_from_support(ticket.priority)
                db.add(vendor_ticket)
                if data.resolution_action is not None:
                    linked_vendor_id_raw = _ticket_source_metadata(ticket).get("linked_vendor_id")
                    if linked_vendor_id_raw:
                        try:
                            linked_vendor_id = uuid.UUID(linked_vendor_id_raw)
                        except ValueError:
                            linked_vendor_id = None
                        if linked_vendor_id:
                            await create_user_notification(
                                db,
                                user_id=linked_vendor_id,
                                title="Inbound issue updated",
                                message=(
                                    f"{ticket.reference_code}: "
                                    f"{INBOUND_RESOLUTION_LABELS[data.resolution_action.strip().lower()]}"
                                ),
                                notification_type="info",
                            )

    if should_resolve_linked_ai_handoff:
        await resolve_ai_handoff_escalations_for_ticket(db, ticket=ticket, actor=actor)

    await db.flush()
    await db.refresh(ticket)
    if ticket.assigned_to_user_id is not None:
        await db.refresh(ticket, attribute_names=["assigned_to_user"])
    order_map = await _linked_order_tracking_map(db, [ticket])
    order_tracking_code = order_map.get(_linked_order_uuid_from_ticket(ticket))
    return _ticket_response(
        ticket,
        order_tracking_code=order_tracking_code,
        vendor_ticket=vendor_ticket,
    )


async def reply_to_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    data: AgentReplyRequest,
    actor: User,
) -> TicketResponse:
    _ensure_support_manager(actor)

    ticket = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(SupportTicket.id == ticket_id)
        )
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    linked_vendor_ticket_id = _linked_vendor_ticket_uuid_from_ticket(ticket)
    if not linked_vendor_ticket_id:
        raise HTTPException(
            status_code=400,
            detail="Only vendor-linked tickets support dashboard chat replies.",
        )

    vendor_ticket = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.id == linked_vendor_ticket_id)
        )
    ).scalar_one_or_none()
    if not vendor_ticket:
        raise HTTPException(status_code=404, detail="Linked vendor ticket not found")
    if ticket.status == "resolved" or vendor_ticket.status == "Resolved":
        raise HTTPException(
            status_code=409,
            detail="This vendor chat is closed because the ticket has been resolved.",
        )

    db.add(
        VendorSupportReply(
            ticket_id=vendor_ticket.id,
            from_name=f"Support Team ({actor.name})",
            message=data.message.strip(),
        )
    )

    if ticket.status == "new":
        ticket.status = "in_progress"

    vendor_ticket.priority = _vendor_priority_from_support(ticket.priority)
    vendor_ticket.status = _vendor_status_from_support(ticket.status)
    db.add(vendor_ticket)
    db.add(ticket)

    linked_vendor_id_raw = _ticket_source_metadata(ticket).get("linked_vendor_id")
    if linked_vendor_id_raw:
        try:
            linked_vendor_id = uuid.UUID(linked_vendor_id_raw)
        except ValueError:
            linked_vendor_id = None
        if linked_vendor_id:
            await create_user_notification(
                db,
                user_id=linked_vendor_id,
                title="Support replied to your inbound issue",
                message=f"{ticket.reference_code}: {data.message.strip()}",
                notification_type="info",
            )

    await db.flush()
    await db.refresh(ticket)
    await db.refresh(vendor_ticket, attribute_names=["replies"])
    order_map = await _linked_order_tracking_map(db, [ticket])
    return _ticket_response(
        ticket,
        order_tracking_code=order_map.get(_linked_order_uuid_from_ticket(ticket)),
        vendor_ticket=vendor_ticket,
    )


async def delete_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    actor: User | None = None,
) -> None:
    if actor is not None:
        _ensure_support_manager(actor)
    ticket = (
        await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if _ticket_source_metadata(ticket).get("source") in {"vendor_portal", "warehouse_inbound", "ai_handoff"}:
        raise HTTPException(
            status_code=400,
            detail="System-linked tickets cannot be deleted from the AI dashboard. Resolve them instead.",
        )
    await db.delete(ticket)
    await db.flush()
