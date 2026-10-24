"""Conversation history, message persistence, linked-order metadata, handoff responses and intent labels."""

import uuid

from google.genai import types
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.order import Order
from app.models.user import User
from app.schemas.ai import (
    ChatResponse,
    ConversationHistory,
    ConversationMessage,
    SessionListItem,
    SessionListResponse,
)
from app.services.ai_chat.constants import (
    MAX_CONTEXT_MESSAGES,
    SUPPORT_SESSION_CLOSED_INTENT,
    SUPPORT_SESSION_CLOSED_MESSAGE,
)
from app.services.ai_chat.intents import _safe_message_text

# ── Conversation History ──────────────────────────────────────────────────────


async def get_conversation_history(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ConversationHistory:
    """Get all messages for a conversation session."""
    result = await db.execute(
        select(AIConversation)
        .where(
            AIConversation.session_id == session_id,
            AIConversation.user_id == user_id,
        )
        .order_by(AIConversation.created_at.asc())
    )
    messages = result.scalars().all()

    return ConversationHistory(
        session_id=session_id,
        messages=[
            ConversationMessage(
                role=msg.role,
                message=msg.message,
                intent=msg.intent,
                sql_generated=msg.sql_generated,
                created_at=msg.created_at,
            )
            for msg in messages
        ],
    )


async def get_user_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> SessionListResponse:
    """List all conversation sessions for a user, most recent first."""
    # Subquery: get last message and count per session
    result = await db.execute(
        select(
            AIConversation.session_id,
            func.max(AIConversation.message).label("last_message"),
            func.count(AIConversation.id).label("message_count"),
            func.min(AIConversation.created_at).label("created_at"),
        )
        .where(AIConversation.user_id == user_id)
        .group_by(AIConversation.session_id)
        .order_by(func.max(AIConversation.created_at).desc())
    )
    rows = result.all()

    return SessionListResponse(
        sessions=[
            SessionListItem(
                session_id=row.session_id,
                last_message=row.last_message[:100] if row.last_message else "",
                message_count=row.message_count,
                created_at=row.created_at,
            )
            for row in rows
        ]
    )


# ── Private Helpers ───────────────────────────────────────────────────────────


async def _load_conversation_history(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[AIConversation]:
    """Load recent conversation messages for context."""
    result = await db.execute(
        select(AIConversation)
        .where(
            AIConversation.session_id == session_id,
            AIConversation.user_id == user_id,
        )
        .order_by(AIConversation.created_at.desc())
        .limit(MAX_CONTEXT_MESSAGES)
    )
    messages = list(result.scalars().all())
    messages.reverse()  # Oldest first for context
    return messages


def _build_gemini_history(messages: list[AIConversation]) -> list[types.Content]:
    """Convert stored messages to Gemini history format."""
    history: list[types.Content] = []
    for msg in messages:
        gemini_role = "user" if msg.role == "user" else "model"
        history.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=msg.message)],
            )
        )
    return history


async def _persist_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str,
    message: str | None,
    intent: str | None = None,
    sql_generated: str | None = None,
    query_result: list | dict | None = None,
    linked_order_meta: dict[str, str] | None = None,
) -> AIConversation:
    """Save a message to the ai_conversations table."""
    message = _safe_message_text(message, "[empty message]")
    if linked_order_meta:
        if isinstance(query_result, dict):
            query_result = {**linked_order_meta, **query_result}
        elif query_result is None:
            query_result = dict(linked_order_meta)
    conversation = AIConversation(
        session_id=session_id,
        user_id=user_id,
        role=role,
        message=message,
        intent=intent,
        sql_generated=sql_generated,
        query_result=query_result,
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def _create_human_handoff_response(
    db: AsyncSession,
    session_id: uuid.UUID,
    user: User,
    user_message: str,
    reason: str,
    linked_order: Order | None = None,
) -> ChatResponse:
    assistant_message = (
        "I have flagged this conversation for human support. "
        "A support agent can now pick it up from the AI Support dashboard, and they can reply to you in this same chat."
    )

    linked_order_meta = _linked_order_metadata(linked_order)
    await _persist_message(
        db,
        session_id,
        user.id,
        "user",
        user_message,
        "handover",
        linked_order_meta=linked_order_meta,
    )
    assistant_row = await _persist_message(
        db,
        session_id,
        user.id,
        "assistant",
        assistant_message,
        "handover",
        linked_order_meta=linked_order_meta,
    )

    existing = (
        await db.execute(
            select(Escalation)
            .join(AIConversation, Escalation.conversation_id == AIConversation.id)
            .where(
                AIConversation.session_id == session_id,
                Escalation.status == "OPEN",
            )
            .order_by(Escalation.escalated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    escalation = existing or Escalation(
        conversation_id=assistant_row.id,
        reason=reason,
        status="OPEN",
    )
    from app.services import ai_support_service

    support_manager = await ai_support_service.get_default_support_manager(db)
    escalation.conversation_id = assistant_row.id
    escalation.reason = reason
    escalation.resolved_at = None
    escalation.escalated_to_user_id = support_manager.id if support_manager else None
    db.add(escalation)
    await db.flush()

    await ai_support_service.sync_ai_handoff_ticket(
        db=db,
        session_id=session_id,
        user=user,
        reason=reason,
        latest_user_message=user_message,
    )

    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent="handover",
        sql_generated=None,
        requires_human=True,
        human_handoff_reason=reason,
        linked_order_id=linked_order.id if linked_order else None,
        linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
    )


async def _create_closed_handoff_response(
    db: AsyncSession,
    session_id: uuid.UUID,
    user: User,
    user_message: str,
    linked_order: Order | None = None,
) -> ChatResponse:
    linked_order_meta = _linked_order_metadata(linked_order)
    await _persist_message(
        db,
        session_id,
        user.id,
        "user",
        user_message,
        SUPPORT_SESSION_CLOSED_INTENT,
        linked_order_meta=linked_order_meta,
    )
    await _persist_message(
        db,
        session_id,
        user.id,
        "assistant",
        SUPPORT_SESSION_CLOSED_MESSAGE,
        SUPPORT_SESSION_CLOSED_INTENT,
        linked_order_meta=linked_order_meta,
    )
    return ChatResponse(
        session_id=session_id,
        message=SUPPORT_SESSION_CLOSED_MESSAGE,
        intent=SUPPORT_SESSION_CLOSED_INTENT,
        sql_generated=None,
        requires_human=False,
        human_handoff_reason=None,
        human_handoff_locked=True,
        linked_order_id=linked_order.id if linked_order else None,
        linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
    )


def _classify_intent(user_message: str, assistant_message: str) -> str:
    """Simple heuristic intent classification for non-DB responses."""
    msg_lower = user_message.lower().strip()

    greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
    if any(msg_lower.startswith(g) for g in greetings):
        return "greeting"

    return "general"


def _linked_order_metadata(order: Order | None) -> dict[str, str] | None:
    if not order:
        return None
    return {
        "linked_order_id": str(order.id),
        "linked_order_tracking_code": order.tracking_code,
    }


def _linked_order_metadata_from_history(messages: list[AIConversation]) -> dict[str, str] | None:
    for message in reversed(messages):
        if isinstance(message.query_result, dict) and message.query_result.get("linked_order_id"):
            return {
                "linked_order_id": str(message.query_result.get("linked_order_id")),
                "linked_order_tracking_code": str(message.query_result.get("linked_order_tracking_code") or ""),
            }
    return None


def _message_for_linked_support_order(user_message: str, order: Order) -> str:
    return f"For support help about order {order.tracking_code}, {user_message}"
