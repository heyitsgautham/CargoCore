"""The main chat entry point that routes a message to shortcuts, handoff or Gemini."""

import uuid

from google.genai import types
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_conversation import AIConversation
from app.models.order import Order
from app.models.user import User
from app.schemas.ai import (
    ChatResponse,
)
from app.services.ai_chat.constants import SELF_SERVICE_ROLES, SUPPORT_CHAT_CONTEXT
from app.services.ai_chat.conversations import (
    _build_gemini_history,
    _classify_intent,
    _create_closed_handoff_response,
    _create_human_handoff_response,
    _linked_order_metadata,
    _load_conversation_history,
    _message_for_linked_support_order,
    _persist_message,
)
from app.services.ai_chat.dispatcher_answers import (
    _build_dispatcher_snapshot,
    _try_handle_dispatcher_shortcuts,
)
from app.services.ai_chat.fallback import (
    _contextualize_user_message,
    _local_fallback_response,
)
from app.services.ai_chat.function_calls import _handle_function_call
from app.services.ai_chat.intents import (
    _has_legal_threat,
    _has_severe_negative_sentiment,
    _is_dispatcher_chat_context,
    _is_human_handoff_request,
    _is_logistic_manager_chat_context,
    _is_warehouse_chat_context,
    _role_name,
    _safe_message_text,
)
from app.services.ai_chat.logistics_answers import (
    _build_logistics_manager_snapshot,
    _try_handle_logistic_manager_shortcuts,
)
from app.services.ai_chat.prompts import _system_instruction_for_user
from app.services.ai_chat.shortcuts import (
    _try_handle_dashboard_help_shortcuts,
    _try_handle_self_service_shortcuts,
)
from app.services.ai_chat.support_handoff import (
    _handoff_reason_for_message,
    _session_has_active_human_agent,
    _session_has_resolved_handoff,
    _validate_support_chat_order,
)
from app.services.ai_chat.warehouse_answers import (
    _build_warehouse_snapshot,
    _try_handle_warehouse_shortcuts,
)
from app.utils.gemini import (
    EXECUTE_SQL_TOOL,
    GeminiConfigError,
    generate_with_fallback,
    get_gemini_client,
)

# ── Main Chat Endpoint ────────────────────────────────────────────────────────


async def chat(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID | None,
    user_message: str,
    chat_context: str | None = None,
    order_id: uuid.UUID | None = None,
) -> ChatResponse:
    """
    Process a user message through the AI chatbot pipeline.

    1. Load conversation history for context
    2. Send to Gemini with tools
    3. If Gemini calls execute_sql_query → validate → execute on ro_db → feed back
    4. Persist messages to ai_conversations
    5. Return response
    """
    # Generate new session ID if starting a new conversation
    if session_id is None:
        session_id = uuid.uuid4()

    linked_order: Order | None = None
    linked_order_meta: dict[str, str] | None = None
    effective_user_message = user_message
    if chat_context == SUPPORT_CHAT_CONTEXT and _role_name(user) in SELF_SERVICE_ROLES:
        linked_order = await _validate_support_chat_order(
            db=db,
            user=user,
            session_id=session_id,
            order_id=order_id,
        )
        linked_order_meta = _linked_order_metadata(linked_order)
        if linked_order is not None:
            effective_user_message = _message_for_linked_support_order(user_message, linked_order)

    # ── Early handoff guard ────────────────────────────────────────────────────
    # Must run BEFORE shortcuts because _message_for_linked_support_order injects
    # the tracking code into effective_user_message, which causes _extract_tracking_code
    # inside the shortcuts to match and return order details instead of escalating.
    # We use the raw user_message here so the tracking code injection can't interfere.
    msg = (user_message or "").strip().lower()
    if chat_context == SUPPORT_CHAT_CONTEXT and _role_name(user) in SELF_SERVICE_ROLES:
        if _is_human_handoff_request(msg) or _has_legal_threat(msg) or _has_severe_negative_sentiment(msg):
            from sqlalchemy import select as _selectEarly

            from app.models.ai_support_settings import (
                AISupportSettings as _AISupportSettingsEarly,
            )
            _early_settings = (
                await db.execute(_selectEarly(_AISupportSettingsEarly).limit(1))
            ).scalar_one_or_none()
            if await _session_has_resolved_handoff(db, session_id, user.id):
                return await _create_closed_handoff_response(
                    db=db,
                    session_id=session_id,
                    user=user,
                    user_message=user_message,
                    linked_order=linked_order,
                )
            handoff_reason_early = await _handoff_reason_for_message(msg, _early_settings)
            if handoff_reason_early:
                return await _create_human_handoff_response(
                    db=db,
                    session_id=session_id,
                    user=user,
                    user_message=user_message,
                    reason=handoff_reason_early,
                    linked_order=linked_order,
                )

    # ── Human-agent takeover guard ─────────────────────────────────────────────
    # Once a support agent has replied, all subsequent customer messages must be
    # saved but the AI must NOT generate a response — the human agent is in control.
    if (
        chat_context == SUPPORT_CHAT_CONTEXT
        and _role_name(user) in SELF_SERVICE_ROLES
        and session_id is not None
        and await _session_has_active_human_agent(db, session_id)
    ):
        await _persist_message(
            db,
            session_id,
            user.id,
            "user",
            user_message,
            intent="support_message",
            linked_order_meta=linked_order_meta,
        )
        await db.commit()
        return ChatResponse(
            session_id=session_id,
            message="Your message has been sent to the support agent. Please wait for their reply.",
            intent="agent_waiting",
            sql_generated=None,
            linked_order_id=order_id,
        )

    warehouse_snapshot = None
    if _is_warehouse_chat_context(user, chat_context):
        warehouse_snapshot = await _build_warehouse_snapshot(ro_db, user)

    dispatcher_snapshot = None
    if _is_dispatcher_chat_context(user, chat_context):
        dispatcher_snapshot = await _build_dispatcher_snapshot(ro_db)

    logistic_manager_snapshot = None
    if _is_logistic_manager_chat_context(user, chat_context):
        logistic_manager_snapshot = await _build_logistics_manager_snapshot(ro_db)

    warehouse_shortcut = await _try_handle_warehouse_shortcuts(
        db=db,
        ro_db=ro_db,
        user=user,
        session_id=session_id,
        user_message=effective_user_message,
        chat_context=chat_context,
        snapshot=warehouse_snapshot,
    )
    if warehouse_shortcut is not None:
        return warehouse_shortcut

    logistic_manager_shortcut = await _try_handle_logistic_manager_shortcuts(
        db=db,
        ro_db=ro_db,
        user=user,
        session_id=session_id,
        user_message=effective_user_message,
        chat_context=chat_context,
    )
    if logistic_manager_shortcut is not None:
        return logistic_manager_shortcut

    dispatcher_shortcut = await _try_handle_dispatcher_shortcuts(
        db=db,
        ro_db=ro_db,
        user=user,
        session_id=session_id,
        user_message=effective_user_message,
        chat_context=chat_context,
    )
    if dispatcher_shortcut is not None:
        return dispatcher_shortcut

    # Deterministic shortcuts for common self-service questions.
    shortcut = await _try_handle_self_service_shortcuts(
        db=db,
        ro_db=ro_db,
        user=user,
        session_id=session_id,
        user_message=effective_user_message,
        chat_context=chat_context,
    )
    if shortcut is not None:
        return await _attach_linked_order(db, shortcut, session_id, linked_order_meta)

    # Deterministic dashboard help shortcuts for general product guidance.
    help_shortcut = await _try_handle_dashboard_help_shortcuts(
        db=db,
        user=user,
        session_id=session_id,
        user_message=effective_user_message,
        chat_context=chat_context,
    )
    if help_shortcut is not None:
        return await _attach_linked_order(db, help_shortcut, session_id, linked_order_meta)

    # ── Step 1: Load conversation history ─────────────────────────────────
    history = await _load_conversation_history(db, session_id, user.id)
    gemini_history = _build_gemini_history(history)
    _conversation_turns = sum(1 for m in history if m.role == "user")

    # ── Step 2: Load admin-configured settings (tone, system prompt, etc.) ─
    from sqlalchemy import select as _select

    from app.models.ai_support_settings import AISupportSettings as _AISupportSettings
    _db_settings = (
        await db.execute(_select(_AISupportSettings).limit(1))
    ).scalar_one_or_none()

    if (
        chat_context == SUPPORT_CHAT_CONTEXT
        and _role_name(user) in SELF_SERVICE_ROLES
        and await _session_has_resolved_handoff(db, session_id, user.id)
    ):
        resolved_handoff_reason = await _handoff_reason_for_message(msg, _db_settings, _conversation_turns)
        if resolved_handoff_reason:
            return await _create_closed_handoff_response(
                db=db,
                session_id=session_id,
                user=user,
                user_message=user_message,
                linked_order=linked_order,
            )

    handoff_reason = await _handoff_reason_for_message(msg, _db_settings, _conversation_turns)
    if handoff_reason:
        return await _create_human_handoff_response(
            db=db,
            session_id=session_id,
            user=user,
            user_message=user_message,
            reason=handoff_reason,
            linked_order=linked_order,
        )

    if (
        _role_name(user) in SELF_SERVICE_ROLES
        and _db_settings
        and not getattr(_db_settings, "autonomous_replies", True)
    ):
        return await _create_human_handoff_response(
            db=db,
            session_id=session_id,
            user=user,
            user_message=user_message,
            reason="Autonomous replies are currently disabled, so a human support agent will continue this conversation.",
            linked_order=linked_order,
        )

    # ── Step 3: Call Gemini ───────────────────────────────────────────────
    system_instruction = _system_instruction_for_user(
        user, chat_context=chat_context, db_settings=_db_settings,
        linked_order=linked_order,
    )

    try:
        client = get_gemini_client()
    except GeminiConfigError as e:
        logger.error(f"Gemini not configured: {e}")
        # Persist user message even on error
        await _persist_message(
            db,
            session_id,
            user.id,
            "user",
            user_message,
            "error",
            linked_order_meta=linked_order_meta,
        )
        error_msg = "AI service is not configured. Please contact your administrator."
        await _persist_message(
            db,
            session_id,
            user.id,
            "assistant",
            error_msg,
            "error",
            linked_order_meta=linked_order_meta,
        )
        return ChatResponse(
            session_id=session_id,
            message=error_msg,
            intent="error",
            sql_generated=None,
            requires_human=False,
            human_handoff_reason=None,
            linked_order_id=linked_order.id if linked_order else None,
            linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
        )

    try:
        # Build contents: history + new user message
        contents = gemini_history + [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=_contextualize_user_message(effective_user_message, chat_context, warehouse_snapshot, dispatcher_snapshot, logistic_manager_snapshot))],
            )
        ]

        # Call Gemini (Pro→Flash fallback) with function-calling disabled (we handle it manually)
        response = await generate_with_fallback(
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[EXECUTE_SQL_TOOL],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True,
                ),
            ),
        )
    except Exception as e:
        logger.error(f"Gemini API error: {type(e).__name__}: {e}")
        await _persist_message(
            db,
            session_id,
            user.id,
            "user",
            user_message,
            "error",
            linked_order_meta=linked_order_meta,
        )
        fallback_msg = await _local_fallback_response(
            ro_db=ro_db,
            user=user,
            user_message=effective_user_message,
            chat_context=chat_context,
            warehouse_snapshot=warehouse_snapshot,
        )
        error_msg = _safe_message_text(
            fallback_msg,
            "AI is temporarily unavailable. Please try again shortly.",
        )
        await _persist_message(
            db,
            session_id,
            user.id,
            "assistant",
            error_msg,
            "error",
            linked_order_meta=linked_order_meta,
        )
        return ChatResponse(
            session_id=session_id,
            message=error_msg,
            intent="error",
            sql_generated=None,
            requires_human=False,
            human_handoff_reason=None,
            linked_order_id=linked_order.id if linked_order else None,
            linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
        )

    # ── Step 3: Check if Gemini wants to call a function ──────────────────
    if response.function_calls:
        function_call = response.function_calls[0]
        return await _handle_function_call(
            db=db,
            ro_db=ro_db,
            user=user,
            session_id=session_id,
            user_message=user_message,
            linked_order_meta=linked_order_meta,
            linked_order=linked_order,
            client=client,
            contents=contents,
            response=response,
            function_call=function_call,
            system_instruction=system_instruction,
        )

    # ── Step 4: Plain text response (general query) ──────────────────────
    assistant_message = _safe_message_text(
        response.text,
        "I could not generate a response this time. Please try rephrasing your question.",
    )
    intent = _classify_intent(user_message, assistant_message)

    # Persist both messages
    await _persist_message(
        db,
        session_id,
        user.id,
        "user",
        user_message,
        intent,
        linked_order_meta=linked_order_meta,
    )
    await _persist_message(
        db,
        session_id,
        user.id,
        "assistant",
        assistant_message,
        intent,
        linked_order_meta=linked_order_meta,
    )

    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent=intent,
        sql_generated=None,
        requires_human=False,
        human_handoff_reason=None,
        linked_order_id=linked_order.id if linked_order else None,
        linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
    )


async def _attach_linked_order(
    db: AsyncSession,
    response: ChatResponse,
    session_id: uuid.UUID,
    linked_order_meta: dict[str, str] | None,
) -> ChatResponse:
    """Tag a shortcut answer with the order the support chat is about.

    The shortcuts persist their messages without the linked order, and the
    support desk only lists sessions whose messages carry one, so an
    order-linked chat answered by a shortcut never reached an agent.
    """
    if not linked_order_meta:
        return response
    rows = (
        await db.execute(select(AIConversation).where(AIConversation.session_id == session_id))
    ).scalars().all()
    for row in rows:
        if row.query_result is None:
            row.query_result = dict(linked_order_meta)
        elif isinstance(row.query_result, dict) and not row.query_result.get("linked_order_id"):
            row.query_result = {**linked_order_meta, **row.query_result}
    await db.flush()
    return response.model_copy(
        update={
            "linked_order_id": uuid.UUID(linked_order_meta["linked_order_id"]),
            "linked_order_tracking_code": linked_order_meta["linked_order_tracking_code"],
        }
    )
