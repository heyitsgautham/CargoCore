"""Ticket status and priority mapping, note metadata, links to vendor tickets and sessions, and ticket responses."""

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.ai_conversation import AIConversation
from app.models.order import Order
from app.models.support_ticket import SupportTicket
from app.models.vendor import VendorSupportTicket
from app.schemas.ai import (
    TicketReplyItem,
    TicketResponse,
)
from app.services.support.common import (
    SUPPORT_SESSION_CLOSED_INTENT,
    SUPPORT_SESSION_CLOSED_MESSAGE,
)

# ── Support Tickets ───────────────────────────────────────────────────────────

TICKET_STATUS_VALUES = {"new", "in_progress", "resolved"}
TICKET_PRIORITY_VALUES = {"low", "medium", "high", "urgent"}
TICKET_SOURCE_LABELS = {
    "manual": "Manual",
    "vendor_portal": "Vendor Portal",
    "warehouse_inbound": "Warehouse Inbound",
    "ai_handoff": "AI Chat Handoff",
    "ai_analytics": "AI Analytics",
}
TICKET_NOTE_META_PATTERN = re.compile(r"^\[meta:(?P<key>[a-z_]+)=(?P<value>.*)\]$")
INBOUND_RESOLUTION_LABELS = {
    "pending_review": "Pending Review",
    "vendor_accept_move": "Vendor Cleared For Move",
    "vendor_take_back": "Vendor Will Take Back",
}


def _vendor_ticket_display_code(ticket_id: uuid.UUID) -> str:
    return f"TK-{str(ticket_id).split('-')[0].upper()}"


def _support_status_from_vendor(status_value: str | None) -> str:
    mapping = {
        "open": "new",
        "in progress": "in_progress",
        "resolved": "resolved",
    }
    return mapping.get((status_value or "").strip().lower(), "new")


def _vendor_status_from_support(status_value: str | None) -> str:
    mapping = {
        "new": "Open",
        "in_progress": "In Progress",
        "resolved": "Resolved",
    }
    return mapping.get((status_value or "").strip().lower(), "Open")


def _support_priority_from_vendor(priority_value: str | None) -> str:
    normalized = (priority_value or "medium").strip().lower()
    return normalized if normalized in TICKET_PRIORITY_VALUES else "medium"


def _vendor_priority_from_support(priority_value: str | None) -> str:
    normalized = _support_priority_from_vendor(priority_value)
    return normalized.title()


def _handoff_ticket_priority(reason: str | None) -> str:
    text = (reason or "").strip().lower()
    if "legal" in text:
        return "urgent"
    if text:
        return "high"
    return "medium"


def _split_ticket_notes(raw_notes: str | None) -> tuple[dict[str, str], str | None]:
    metadata: dict[str, str] = {}
    visible_lines: list[str] = []

    for raw_line in (raw_notes or "").splitlines():
        line = raw_line.strip()
        match = TICKET_NOTE_META_PATTERN.match(line)
        if match:
            metadata[match.group("key")] = match.group("value")
            continue
        visible_lines.append(raw_line)

    visible_notes = "\n".join(visible_lines).strip() or None
    return metadata, visible_notes


def _compose_ticket_notes(
    *,
    metadata: dict[str, str | None],
    visible_notes: str | None = None,
) -> str | None:
    meta_lines = [
        f"[meta:{key}={value}]"
        for key, value in metadata.items()
        if value is not None and str(value).strip()
    ]
    clean_notes = (visible_notes or "").strip()
    if clean_notes:
        meta_lines.append(clean_notes)
    return "\n".join(meta_lines) if meta_lines else None


def _ticket_source_metadata(ticket: SupportTicket) -> dict[str, str]:
    metadata, _ = _split_ticket_notes(ticket.notes)
    return metadata


def _linked_vendor_ticket_uuid_from_ticket(ticket: SupportTicket) -> uuid.UUID | None:
    vendor_ticket_id_raw = _ticket_source_metadata(ticket).get("linked_vendor_ticket_id")
    if not vendor_ticket_id_raw:
        return None
    try:
        return uuid.UUID(vendor_ticket_id_raw)
    except ValueError:
        return None


def _linked_order_uuid_from_ticket(ticket: SupportTicket) -> uuid.UUID | None:
    order_id_raw = _ticket_source_metadata(ticket).get("linked_order_id")
    if not order_id_raw:
        return None
    try:
        return uuid.UUID(order_id_raw)
    except ValueError:
        return None


def _linked_session_uuid_from_ticket(ticket: SupportTicket) -> uuid.UUID | None:
    session_id_raw = _ticket_source_metadata(ticket).get("linked_session_id")
    if not session_id_raw:
        return None
    try:
        return uuid.UUID(session_id_raw)
    except ValueError:
        return None


async def _linked_order_tracking_map(
    db: AsyncSession,
    tickets: list[SupportTicket],
) -> dict[uuid.UUID, str]:
    order_ids: set[uuid.UUID] = set()
    for ticket in tickets:
        order_id = _linked_order_uuid_from_ticket(ticket)
        if order_id:
            order_ids.add(order_id)

    if not order_ids:
        return {}

    rows = (
        await db.execute(
            select(Order.id, Order.tracking_code).where(Order.id.in_(order_ids))
        )
    ).all()
    return {row.id: row.tracking_code for row in rows}


async def _linked_vendor_ticket_map(
    db: AsyncSession,
    tickets: list[SupportTicket],
) -> dict[uuid.UUID, VendorSupportTicket]:
    vendor_ticket_ids: set[uuid.UUID] = set()
    for ticket in tickets:
        vendor_ticket_id = _linked_vendor_ticket_uuid_from_ticket(ticket)
        if vendor_ticket_id:
            vendor_ticket_ids.add(vendor_ticket_id)

    if not vendor_ticket_ids:
        return {}

    rows = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.id.in_(vendor_ticket_ids))
        )
    ).scalars().all()
    return {row.id: row for row in rows}


def _ticket_response(
    t: SupportTicket,
    *,
    order_tracking_code: str | None = None,
    vendor_ticket: VendorSupportTicket | None = None,
) -> TicketResponse:
    metadata, visible_notes = _split_ticket_notes(t.notes)
    source = metadata.get("source", "manual")
    linked_vendor_ticket_id: uuid.UUID | None = None
    linked_order_id: uuid.UUID | None = None
    linked_damage_report_id: uuid.UUID | None = None

    try:
        linked_vendor_ticket_id = (
            uuid.UUID(metadata["linked_vendor_ticket_id"])
            if metadata.get("linked_vendor_ticket_id")
            else None
        )
    except ValueError:
        linked_vendor_ticket_id = None

    try:
        linked_order_id = (
            uuid.UUID(metadata["linked_order_id"])
            if metadata.get("linked_order_id")
            else None
        )
    except ValueError:
        linked_order_id = None

    try:
        linked_damage_report_id = (
            uuid.UUID(metadata["linked_damage_report_id"])
            if metadata.get("linked_damage_report_id")
            else None
        )
    except ValueError:
        linked_damage_report_id = None

    resolution_action = metadata.get("resolution_action")
    issue_type = metadata.get("issue_type")

    return TicketResponse(
        id=t.id,
        reference_code=t.reference_code,
        title=t.title,
        description=t.description,
        priority=t.priority,
        status=t.status,
        category=t.category,
        customer_name=t.customer_name,
        notes=visible_notes,
        assigned_to_user_id=t.assigned_to_user_id,
        assigned_agent_name=t.assigned_to_user.name if t.assigned_to_user else None,
        created_at=t.created_at,
        updated_at=t.updated_at,
        resolved_at=t.resolved_at,
        source=source,
        source_label=TICKET_SOURCE_LABELS.get(source, source.replace("_", " ").title()),
        requester_type=(
            "Vendor"
            if source == "vendor_portal"
            else "Warehouse / Vendor"
            if source == "warehouse_inbound"
            else metadata.get("requester_type", "Customer")
            if source == "ai_handoff"
            else None
        ),
        issue_type=issue_type,
        resolution_action=resolution_action,
        resolution_label=INBOUND_RESOLUTION_LABELS.get(resolution_action),
        linked_vendor_ticket_id=linked_vendor_ticket_id,
        linked_vendor_ticket_code=(
            _vendor_ticket_display_code(linked_vendor_ticket_id)
            if linked_vendor_ticket_id
            else None
        ),
        linked_damage_report_id=linked_damage_report_id,
        linked_order_id=linked_order_id,
        linked_order_tracking_code=order_tracking_code,
        linked_vendor_replies=[
            TicketReplyItem(
                from_name=reply.from_name,
                message=reply.message,
                created_at=reply.created_at,
            )
            for reply in ((vendor_ticket.replies if vendor_ticket else []) or [])
        ],
        can_delete=source not in {"vendor_portal", "warehouse_inbound", "ai_handoff"},
        lm_action_steps=[
            s.strip()
            for s in metadata.get("lm_steps", "").split("||")
            if s.strip()
        ],
    )


async def _next_ticket_reference(db: AsyncSession) -> str:
    latest = (
        await db.execute(
            select(SupportTicket.reference_code)
            .order_by(SupportTicket.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not latest:
        return "TK-001"
    match = re.search(r"(\d+)$", latest)
    next_number = int(match.group(1)) + 1 if match else 1
    return f"TK-{next_number:03d}"


async def _find_ai_handoff_ticket_for_session(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> SupportTicket | None:
    return (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(
                SupportTicket.notes.contains("[meta:source=ai_handoff]"),
                SupportTicket.notes.contains(f"[meta:linked_session_id={session_id}]"),
            )
            .order_by(SupportTicket.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def _close_support_session_once(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> None:
    already_closed = (
        await db.execute(
            select(AIConversation.id)
            .where(
                AIConversation.session_id == session_id,
                AIConversation.intent == SUPPORT_SESSION_CLOSED_INTENT,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if already_closed:
        return

    messages = (
        await db.execute(
            select(AIConversation)
            .where(AIConversation.session_id == session_id)
            .order_by(AIConversation.created_at.desc())
        )
    ).scalars().all()
    if not messages:
        return

    linked_order_meta = None
    for message in messages:
        if isinstance(message.query_result, dict) and message.query_result.get("linked_order_id"):
            linked_order_meta = {
                "linked_order_id": str(message.query_result.get("linked_order_id")),
                "linked_order_tracking_code": str(
                    message.query_result.get("linked_order_tracking_code") or ""
                ),
            }
            break

    db.add(
        AIConversation(
            session_id=session_id,
            user_id=messages[0].user_id,
            role="assistant",
            message=SUPPORT_SESSION_CLOSED_MESSAGE,
            intent=SUPPORT_SESSION_CLOSED_INTENT,
            query_result=linked_order_meta,
        )
    )
