"""Support chat sessions: listing, takeover, replies, escalation and enriched escalations."""

import uuid
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.order import Order
from app.models.user import User
from app.schemas.ai import (
    AgentReplyRequest,
    EscalationDetailItem,
    EscalationDetailListResponse,
    EscalationResponse,
    SupportConversationMessage,
    SupportSessionDetail,
    SupportSessionEscalateRequest,
    SupportSessionEscalationSummary,
    SupportSessionListItem,
    SupportSessionListResponse,
)
from app.services.support.analytics_format import _sentiment_label
from app.services.support.common import (
    HUMAN_ASSISTANT_INTENTS,
    SUPPORT_SESSION_CLOSED_INTENT,
    SUPPORT_SESSION_OWNER_ROLE_NAMES,
    TRACKING_CODE_PATTERN,
    _ensure_support_manager,
)
from app.services.support.ticket_sync import mark_ai_handoff_ticket_in_progress


async def _fetch_order_tracking_map(
    db: AsyncSession,
    user_ids: list[uuid.UUID],
) -> dict[uuid.UUID, str]:
    if not user_ids:
        return {}
    rows = (
        await db.execute(
            select(Order.customer_id, Order.tracking_code)
            .where(Order.customer_id.in_(user_ids))
            .order_by(Order.customer_id.asc(), Order.created_at.desc())
        )
    ).all()
    result: dict[uuid.UUID, str] = {}
    for customer_id, tracking_code in rows:
        result.setdefault(customer_id, tracking_code)
    return result


def _extract_tracking_code_from_messages(messages: list[AIConversation]) -> str | None:
    for message in reversed(messages):
        if isinstance(message.query_result, dict):
            tracking_code = message.query_result.get("linked_order_tracking_code")
            if tracking_code:
                return str(tracking_code).upper()
        match = TRACKING_CODE_PATTERN.search(message.message or "")
        if match:
            return match.group(0).upper()
    return None


def _message_author_name(message: AIConversation, owner: User | None) -> tuple[str, str]:
    if message.role == "user":
        return (owner.name if owner else "Customer", "customer")
    if message.author_user:
        return (message.author_user.name, "agent")
    if message.intent == "handover":
        return ("Support Manager", "agent")
    if message.intent == SUPPORT_SESSION_CLOSED_INTENT:
        return ("Support Manager", "agent")
    return ("Cargo-Core AI", "ai")


def _is_human_authored_support_message(message: AIConversation) -> bool:
    return bool(message.author_user_id) or message.intent == "agent_reply"


def _is_customer_support_owner(user: User | None) -> bool:
    role_name = getattr(getattr(user, "role", None), "name", None)
    return str(role_name or "").upper() in SUPPORT_SESSION_OWNER_ROLE_NAMES


def _is_linked_support_session(messages: list[AIConversation]) -> bool:
    return any(
        isinstance(message.query_result, dict) and message.query_result.get("linked_order_id")
        for message in messages
    )


def _escalation_for_session(
    session_id: uuid.UUID,
    escalations_by_session: dict[uuid.UUID, list[Escalation]],
) -> SupportSessionEscalationSummary | None:
    items = escalations_by_session.get(session_id, [])
    if not items:
        return None

    selected = next((item for item in items if item.status == "OPEN"), items[0])
    return SupportSessionEscalationSummary(
        id=selected.id,
        status=selected.status,
        reason=selected.reason,
        escalated_at=selected.escalated_at,
        resolved_at=selected.resolved_at,
        escalated_to_user_id=selected.escalated_to_user_id,
        assigned_agent_name=selected.assigned_agent.name if selected.assigned_agent else None,
    )


async def _load_support_session_items(
    db: AsyncSession,
    limit: int | None = 100,
) -> list[SupportSessionListItem]:
    summary_query = (
        select(
            AIConversation.session_id,
            AIConversation.user_id,
            func.min(AIConversation.created_at).label("first_message_at"),
            func.max(AIConversation.created_at).label("last_message_at"),
            func.count(AIConversation.id).label("message_count"),
        )
        .group_by(AIConversation.session_id, AIConversation.user_id)
        .order_by(func.max(AIConversation.created_at).desc())
    )
    if limit:
        summary_query = summary_query.limit(limit)

    summary_rows = (await db.execute(summary_query)).all()
    if not summary_rows:
        return []

    session_ids = [row.session_id for row in summary_rows]
    user_ids = list({row.user_id for row in summary_rows})

    users = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id.in_(user_ids))
        )
    ).scalars().all()
    users_by_id = {user.id: user for user in users}

    messages = (
        await db.execute(
            select(AIConversation)
            .options(selectinload(AIConversation.author_user))
            .where(AIConversation.session_id.in_(session_ids))
            .order_by(AIConversation.created_at.asc())
        )
    ).scalars().all()
    messages_by_session: dict[uuid.UUID, list[AIConversation]] = defaultdict(list)
    for message in messages:
        messages_by_session[message.session_id].append(message)

    escalations = (
        await db.execute(
            select(Escalation)
            .options(selectinload(Escalation.assigned_agent), selectinload(Escalation.conversation))
            .join(AIConversation, Escalation.conversation_id == AIConversation.id)
            .where(AIConversation.session_id.in_(session_ids))
            .order_by(Escalation.escalated_at.desc())
        )
    ).scalars().all()
    escalations_by_session: dict[uuid.UUID, list[Escalation]] = defaultdict(list)
    for escalation in escalations:
        if escalation.conversation:
            escalations_by_session[escalation.conversation.session_id].append(escalation)

    latest_order_map = await _fetch_order_tracking_map(db, user_ids)

    items: list[SupportSessionListItem] = []
    for row in summary_rows:
        owner = users_by_id.get(row.user_id)
        session_messages = messages_by_session.get(row.session_id, [])
        if not session_messages or not owner:
            continue
        if not _is_customer_support_owner(owner):
            continue
        if not _is_linked_support_session(session_messages):
            continue

        last_message = session_messages[-1]
        latest_user_message = next(
            (message for message in reversed(session_messages) if message.role == "user"),
            last_message,
        )
        human_agent_engaged = any(
            _is_human_authored_support_message(message) for message in session_messages
        )
        assigned_agent_name = next(
            (
                message.author_user.name
                for message in reversed(session_messages)
                if _is_human_authored_support_message(message) and message.author_user
            ),
            None,
        )
        escalation_summary = _escalation_for_session(row.session_id, escalations_by_session)
        needs_human_attention = bool(
            escalation_summary and escalation_summary.status == "OPEN"
        )
        if not assigned_agent_name and escalation_summary:
            assigned_agent_name = escalation_summary.assigned_agent_name

        items.append(
            SupportSessionListItem(
                session_id=row.session_id,
                user_id=owner.id,
                user_name=owner.name,
                user_email=owner.email,
                user_role=owner.role.name if owner.role else None,
                user_phone=owner.phone,
                first_message_at=row.first_message_at,
                last_message=last_message.message,
                last_message_role="agent"
                if last_message.intent in HUMAN_ASSISTANT_INTENTS
                else last_message.role,
                last_message_at=row.last_message_at,
                message_count=row.message_count,
                latest_order_tracking_code=_extract_tracking_code_from_messages(session_messages)
                or latest_order_map.get(owner.id),
                sentiment=await _sentiment_label(latest_user_message.message),
                human_agent_engaged=human_agent_engaged,
                assigned_agent_name=assigned_agent_name,
                needs_human_attention=needs_human_attention,
                attention_reason=escalation_summary.reason if needs_human_attention else None,
                escalation=escalation_summary,
            )
        )

    return items


async def _get_support_session_item(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> SupportSessionListItem:
    session_items = await _load_support_session_items(db, limit=None)
    session_item = next((item for item in session_items if item.session_id == session_id), None)
    if not session_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation session not found")
    return session_item


async def list_support_sessions(
    db: AsyncSession,
    search: str | None = None,
) -> SupportSessionListResponse:
    items = await _load_support_session_items(db)

    if search:
        query = search.strip().lower()
        items = [
            item
            for item in items
            if query in (item.user_name or "").lower()
            or query in (item.user_email or "").lower()
            or query in (item.last_message or "").lower()
            or query in (item.latest_order_tracking_code or "").lower()
        ]

    return SupportSessionListResponse(sessions=items)


async def get_support_session_detail(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> SupportSessionDetail:
    session_item = await _get_support_session_item(db, session_id)

    owner = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == session_item.user_id)
        )
    ).scalar_one()
    messages = (
        await db.execute(
            select(AIConversation)
            .options(selectinload(AIConversation.author_user))
            .where(AIConversation.session_id == session_id)
            .order_by(AIConversation.created_at.asc())
        )
    ).scalars().all()

    response_messages = []
    for message in messages:
        author_name, author_role = _message_author_name(message, owner)
        response_messages.append(
            SupportConversationMessage(
                id=message.id,
                role=message.role,
                message=message.message,
                intent=message.intent,
                created_at=message.created_at,
                author_name=author_name,
                author_role=author_role,
            )
        )

    return SupportSessionDetail(session=session_item, messages=response_messages)


async def _get_session_owner(db: AsyncSession, session_id: uuid.UUID) -> User:
    session_item = await _get_support_session_item(db, session_id)
    row = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == session_item.user_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation session not found")
    return row


async def take_over_support_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    agent: User,
) -> SupportSessionDetail:
    _ensure_support_manager(agent)
    owner = await _get_session_owner(db, session_id)
    # Only count an agent-authored handover as "already taken".
    # The bot's escalation-confirmation message also uses intent="handover"
    # but has author_user_id=None — that must NOT block the manager's take-over.
    already_taken = (
        await db.execute(
            select(AIConversation.id)
            .where(
                AIConversation.session_id == session_id,
                AIConversation.intent == "handover",
                AIConversation.author_user_id.isnot(None),
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    if already_taken is None:
        db.add(
            AIConversation(
                session_id=session_id,
                user_id=owner.id,
                author_user_id=agent.id,
                role="assistant",
                message=f"{agent.name} has taken over this conversation.",
                intent="handover",
            )
        )
        await db.flush()

    await mark_ai_handoff_ticket_in_progress(db, session_id=session_id, agent=agent)
    return await get_support_session_detail(db, session_id)


async def reply_to_support_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    agent: User,
    data: AgentReplyRequest,
) -> SupportSessionDetail:
    _ensure_support_manager(agent)
    owner = await _get_session_owner(db, session_id)
    db.add(
        AIConversation(
            session_id=session_id,
            user_id=owner.id,
            author_user_id=agent.id,
            role="assistant",
            message=data.message.strip(),
            intent="agent_reply",
        )
    )
    await db.flush()
    await mark_ai_handoff_ticket_in_progress(db, session_id=session_id, agent=agent)
    return await get_support_session_detail(db, session_id)


async def escalate_support_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    agent: User,
    data: SupportSessionEscalateRequest,
) -> EscalationResponse:
    _ensure_support_manager(agent)
    await _get_support_session_item(db, session_id)
    latest_message = (
        await db.execute(
            select(AIConversation)
            .where(AIConversation.session_id == session_id)
            .order_by(AIConversation.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not latest_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation session not found")

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
        conversation_id=latest_message.id,
        reason=data.reason.strip(),
        status="OPEN",
    )
    escalation.reason = data.reason.strip()
    escalation.escalated_to_user_id = agent.id
    db.add(escalation)
    await db.flush()
    await db.refresh(escalation)
    return EscalationResponse.model_validate(escalation)


# ── Enriched Escalations ──────────────────────────────────────────────────────

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
