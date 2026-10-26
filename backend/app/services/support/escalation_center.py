"""The escalation center list: open and resolved escalations with their customer, order and ticket."""

import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.user import User
from app.schemas.ai import (
    EscalationDetailItem,
    EscalationDetailListResponse,
)
from app.services.support.analytics_format import _sentiment_label
from app.services.support.sessions import (
    _extract_tracking_code_from_messages,
    _fetch_order_tracking_map,
)


async def list_enriched_escalations(
    db: AsyncSession,
    status_filter: str | None = None,
) -> EscalationDetailListResponse:
    query = (
        select(Escalation)
        .options(
            selectinload(Escalation.conversation).selectinload(AIConversation.user).selectinload(User.role),
            selectinload(Escalation.assigned_agent),
        )
        .order_by(Escalation.escalated_at.desc())
    )
    if status_filter:
        query = query.where(Escalation.status == status_filter.upper())

    escalations = (await db.execute(query)).scalars().all()

    # Collect session_ids for order lookup
    session_ids = [e.conversation.session_id for e in escalations if e.conversation]
    user_ids = list({e.conversation.user_id for e in escalations if e.conversation})
    order_map = await _fetch_order_tracking_map(db, user_ids)

    # Compute sentiment per session from all messages in that session
    session_messages_map: dict[uuid.UUID, list[AIConversation]] = defaultdict(list)
    if session_ids:
        msgs = (
            await db.execute(
                select(AIConversation)
                .where(AIConversation.session_id.in_(session_ids), AIConversation.role == "user")
                .order_by(AIConversation.created_at.asc())
            )
        ).scalars().all()
        for m in msgs:
            session_messages_map[m.session_id].append(m)

    items: list[EscalationDetailItem] = []
    for esc in escalations:
        conv = esc.conversation
        if not conv:
            continue
        owner = conv.user
        if not owner:
            continue
        session_text = " ".join(m.message or "" for m in session_messages_map.get(conv.session_id, []))
        items.append(
            EscalationDetailItem(
                id=esc.id,
                conversation_id=conv.id,
                session_id=conv.session_id,
                reason=esc.reason,
                status=esc.status,
                escalated_at=esc.escalated_at,
                resolved_at=esc.resolved_at,
                customer_name=owner.name,
                customer_email=owner.email,
                customer_role=owner.role.name if owner.role else None,
                latest_order_tracking_code=(
                    _extract_tracking_code_from_messages(session_messages_map.get(conv.session_id, []))
                    or order_map.get(owner.id)
                ),
                sentiment=await _sentiment_label(session_text),
                assigned_agent_name=esc.assigned_agent.name if esc.assigned_agent else None,
            )
        )

    open_count = sum(1 for i in items if i.status == "OPEN")
    resolved_count = sum(1 for i in items if i.status == "RESOLVED")
    return EscalationDetailListResponse(
        escalations=items,
        open_count=open_count,
        resolved_count=resolved_count,
    )
