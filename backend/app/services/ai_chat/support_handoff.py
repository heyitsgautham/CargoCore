"""Gemini health scoring, human handoff checks and grounded or knowledge-base answers."""

import json
import re
import uuid

from fastapi import HTTPException
from google.genai import types
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.order import Order
from app.models.user import User
from app.services.ai_chat.constants import MIN_PROACTIVE_ESCALATION_TURNS
from app.services.ai_chat.conversations import (
    _linked_order_metadata_from_history,
    _load_conversation_history,
)
from app.services.ai_chat.intents import (
    _has_legal_threat,
    _has_severe_negative_sentiment,
    _is_human_handoff_request,
    _normalize_text,
    _role_name,
    _safe_message_text,
    _support_health_score,
)
from app.services.ai_knowledge import retrieve_knowledge, retrieve_knowledge_from_db
from app.utils.gemini import (
    GEMINI_FLASH_MODEL,
    GeminiConfigError,
    generate_with_fallback,
    get_gemini_client,
)


async def _gemini_support_health_score(msg: str) -> int:
    """Use Gemini Flash to assess how distressed a customer message is (0–100).

    100 = very satisfied / happy.  0 = extremely angry or threatening.
    Falls back to keyword-based _support_health_score() on any error.
    """
    if not msg or not msg.strip():
        return 100
    try:
        client = get_gemini_client()
        prompt = (
            "You are a customer support sentiment analyzer for a logistics platform.\n"
            "Given the customer message below, return a JSON object with a single key:\n"
            '  "score": integer from 0 to 100 '
            "(100 = very satisfied/happy, 0 = extremely angry or making threats)\n\n"
            "Consider: anger, frustration, legal threats, urgency, and overall tone.\n"
            "Reply with ONLY valid JSON — no markdown, no explanation.\n\n"
            f"Message: {msg[:400]}"
        )
        response = await client.aio.models.generate_content(
            model=GEMINI_FLASH_MODEL,
            contents=prompt,
        )
        raw = (response.text or "").strip()
        # Strip markdown code fences if Gemini wraps the JSON
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        score = int(data.get("score", 100))
        return max(0, min(100, score))
    except Exception:
        logger.warning("Gemini health score failed, falling back to keyword scorer")
        return _support_health_score(msg)


async def _handoff_reason_for_message(
    msg: str,
    db_settings=None,
    conversation_turns: int = 0,
) -> str | None:
    if _has_legal_threat(msg):
        return "Legal escalation risk detected. Human support is required."
    if _is_human_handoff_request(msg):
        return "Customer requested a human support reply."
    if _has_severe_negative_sentiment(msg):
        return "Severe negative customer sentiment detected. Human support is required."
    if (
        db_settings
        and getattr(db_settings, "proactive_human_handover", False)
        and conversation_turns >= MIN_PROACTIVE_ESCALATION_TURNS
        and await _gemini_support_health_score(msg) < int(getattr(db_settings, "sentiment_threshold", 80) or 80)
    ):
        return (
            f"The AI was unable to resolve this issue after {conversation_turns} exchanges "
            "and the customer's sentiment remains negative. A human support agent will take over."
        )
    return None


async def _session_has_active_human_agent(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> bool:
    """Return True if a support agent has already taken over this session
    (i.e. there is at least one agent-authored reply in the conversation).
    When True, the AI must NOT generate a response — only the human agent speaks."""
    result = (
        await db.execute(
            select(AIConversation.id)
            .where(
                AIConversation.session_id == session_id,
                AIConversation.intent.in_(["agent_reply", "support_message"]),
                AIConversation.author_user_id.isnot(None),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    return result is not None


async def _session_has_resolved_handoff(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    resolved = (
        await db.execute(
            select(Escalation.id)
            .join(AIConversation, Escalation.conversation_id == AIConversation.id)
            .where(
                AIConversation.session_id == session_id,
                AIConversation.user_id == user_id,
                Escalation.status == "RESOLVED",
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    return resolved is not None


async def _validate_support_chat_order(
    db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    order_id: uuid.UUID | None,
) -> Order | None:
    if order_id is None:
        return None

    order = (
        await db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.customer_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Selected order was not found for this account.")

    normalized_status = _normalize_text(order.status)
    if normalized_status in {"delivered", "closed", "cancelled"}:
        raise HTTPException(
            status_code=400,
            detail="Support chat is only available for active orders or shipments.",
        )

    history = await _load_conversation_history(db, session_id, user.id)
    existing_meta = _linked_order_metadata_from_history(history)
    if existing_meta and existing_meta.get("linked_order_id") and existing_meta["linked_order_id"] != str(order.id):
        raise HTTPException(
            status_code=400,
            detail="This support session is already linked to another order. Start a fresh chat to switch orders.",
        )

    return order


async def _answer_with_grounded_ai(
    user: User,
    user_message: str,
    fallback_message: str,
    grounding_facts: list[str] | None = None,
) -> str:
    facts = [fact.strip() for fact in (grounding_facts or []) if str(fact).strip()]
    if not facts:
        facts = [fallback_message]

    try:
        get_gemini_client()  # fail fast when Gemini is not configured
    except GeminiConfigError:
        return fallback_message

    prompt = (
        f"User role: {_role_name(user)}\n"
        f"User asked: {user_message}\n\n"
        "Grounding facts:\n"
        + "\n".join(f"- {fact}" for fact in facts)
        + "\n\nWrite a concise, helpful answer for the user using only these facts."
    )

    try:
        response = await generate_with_fallback(
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a Cargo-Core assistant. Use only the provided grounding facts. "
                    "Do not invent values, records, or features. Keep the answer concise and natural. "
                    "Do not use markdown formatting like **bold**, bullets with markdown symbols, or code fences."
                ),
                temperature=0.2,
            ),
        )
        return _safe_message_text(response.text, fallback_message)
    except Exception as e:
        logger.warning(f"Grounded AI reply failed: {type(e).__name__}: {e}")
        return fallback_message


async def _answer_from_retrieved_knowledge(
    db: AsyncSession,
    user: User,
    user_message: str,
) -> str | None:
    audience = _role_name(user)
    entries = await retrieve_knowledge_from_db(user_message, audience, db)
    if not entries:
        entries = retrieve_knowledge(user_message, audience)
    if not entries:
        return None

    fallback_message = "\n".join(
        [entries[0].content] + [f"Related: {entry.content}" for entry in entries[1:]]
    )
    facts = [f"{entry.title}: {entry.content}" for entry in entries]
    return await _answer_with_grounded_ai(
        user=user,
        user_message=user_message,
        fallback_message=fallback_message,
        grounding_facts=facts,
    )
