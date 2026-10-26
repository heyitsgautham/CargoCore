"""Support tickets: AI handoff tickets, vendor ticket sync, CRUD and replies."""

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

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
)
from app.services.support.ticket_helpers import (
    INBOUND_RESOLUTION_LABELS,
    TICKET_PRIORITY_VALUES,
    TICKET_STATUS_VALUES,
    _compose_ticket_notes,
    _linked_order_tracking_map,
    _linked_order_uuid_from_ticket,
    _linked_vendor_ticket_map,
    _linked_vendor_ticket_uuid_from_ticket,
    _next_ticket_reference,
    _split_ticket_notes,
    _ticket_response,
    _ticket_source_metadata,
    _vendor_priority_from_support,
    _vendor_status_from_support,
)
from app.services.support.ticket_sync import resolve_ai_handoff_escalations_for_ticket


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
