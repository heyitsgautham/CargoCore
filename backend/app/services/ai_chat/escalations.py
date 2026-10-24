"""Escalating, listing and resolving AI conversations."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.services.ai_chat.constants import (
    SUPPORT_SESSION_CLOSED_INTENT,
    SUPPORT_SESSION_CLOSED_MESSAGE,
)

# ── Escalation Functions ───────────────────────────────────────────────────────


async def escalate_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    reason: str,
) -> Escalation:
    """
    Escalate an AI conversation to a human agent.

    Verifies the conversation belongs to the requesting user before creating
    the escalation record.
    """
    result = await db.execute(
        select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise ValueError("Conversation not found or you don't have access to it.")

    from app.services import ai_support_service

    support_manager = await ai_support_service.get_default_support_manager(db)
    escalation = Escalation(
        conversation_id=conversation_id,
        reason=reason,
        status="OPEN",
        escalated_to_user_id=support_manager.id if support_manager else None,
    )
    db.add(escalation)
    await db.flush()
    return escalation


async def list_escalations(
    db: AsyncSession,
    status_filter: str | None = None,
) -> list[Escalation]:
    """List escalations, optionally filtered by status (OPEN / RESOLVED)."""
    query = select(Escalation).order_by(Escalation.escalated_at.desc())
    if status_filter:
        query = query.where(Escalation.status == status_filter.upper())
    result = await db.execute(query)
    return list(result.scalars().all())


async def resolve_escalation(
    db: AsyncSession,
    escalation_id: uuid.UUID,
) -> Escalation:
    """Mark an escalation as RESOLVED and set resolved_at to now."""

    result = await db.execute(
        select(Escalation)
        .options(selectinload(Escalation.conversation))
        .where(Escalation.id == escalation_id)
    )
    escalation = result.scalar_one_or_none()
    if escalation is None:
        raise ValueError("Escalation not found.")

    was_resolved = escalation.status == "RESOLVED"
    escalation.status = "RESOLVED"
    escalation.resolved_at = datetime.now(UTC)

    conversation = escalation.conversation
    if conversation and not was_resolved:
        linked_order_meta = None
        if isinstance(conversation.query_result, dict) and conversation.query_result.get("linked_order_id"):
            linked_order_meta = {
                "linked_order_id": str(conversation.query_result.get("linked_order_id")),
                "linked_order_tracking_code": str(conversation.query_result.get("linked_order_tracking_code") or ""),
            }
        db.add(
            AIConversation(
                session_id=conversation.session_id,
                user_id=conversation.user_id,
                role="assistant",
                message=SUPPORT_SESSION_CLOSED_MESSAGE,
                intent=SUPPORT_SESSION_CLOSED_INTENT,
                query_result=linked_order_meta,
            )
        )
        from app.services import ai_support_service

        await ai_support_service.resolve_ai_handoff_ticket_for_session(
            db=db,
            session_id=conversation.session_id,
        )
    await db.flush()
    return escalation
