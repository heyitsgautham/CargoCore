"""Self-service and dashboard-help shortcut answers."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.ai import (
    ChatResponse,
)
from app.services.ai_chat.constants import SELF_SERVICE_ROLES, SUPPORT_CHAT_CONTEXT
from app.services.ai_chat.conversations import (
    _create_human_handoff_response,
    _persist_message,
)
from app.services.ai_chat.intents import (
    _extract_order_status_filter,
    _extract_tracking_code,
    _is_analytics_section_question,
    _is_current_orders_question,
    _is_human_handoff_request,
    _is_knowledge_question,
    _is_order_status_list_question,
    _is_recurring_data_question,
    _is_refund_question,
    _is_support_question,
    _is_total_spend_question,
    _is_wallet_balance_question,
    _role_name,
)
from app.services.ai_chat.self_service import (
    _format_self_service_order_message,
    _list_current_self_service_orders,
    _list_self_service_orders_by_status,
    _lookup_self_service_order,
    _self_service_refund_message,
    _self_service_spend_message,
    _vendor_analytics_message,
    _vendor_recurring_orders_message,
    _vendor_support_message,
    _vendor_wallet_message,
)
from app.services.ai_chat.staff_intents import _is_warehouse_chat_context
from app.services.ai_chat.support_handoff import (
    _answer_from_retrieved_knowledge,
    _answer_with_grounded_ai,
)


async def _try_handle_self_service_shortcuts(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    chat_context: str | None = None,
) -> ChatResponse | None:
    """
    Only intercept the single most time-critical shortcut: exact current-order
    tracking phrases. Everything else (wallet, summary, spending, shipments…)
    goes to Gemini so it can run a real SQL query and return accurate data.
    """
    role = _role_name(user)
    if role not in SELF_SERVICE_ROLES:
        return None

    msg = (user_message or "").strip().lower()

    if _is_refund_question(msg):
        base_message = await _self_service_refund_message(ro_db, user, role, user_message)
        assistant_message = await _answer_with_grounded_ai(
            user=user,
            user_message=user_message,
            fallback_message=base_message,
            grounding_facts=[base_message],
        )
        await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
        await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="db_query",
            sql_generated=None,
        )

    if _is_total_spend_question(msg):
        base_message = await _self_service_spend_message(ro_db, user, role)
        assistant_message = await _answer_with_grounded_ai(
            user=user,
            user_message=user_message,
            fallback_message=base_message,
            grounding_facts=[base_message],
        )
        await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
        await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="db_query",
            sql_generated=None,
        )

    if _is_wallet_balance_question(msg):
        base_message = await _vendor_wallet_message(ro_db, user)
        assistant_message = await _answer_with_grounded_ai(
            user=user,
            user_message=user_message,
            fallback_message=base_message,
            grounding_facts=[base_message],
        )
        await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
        await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="db_query",
            sql_generated=None,
        )

    if role == "VENDOR":
        if _is_analytics_section_question(msg):
            base_message = await _vendor_analytics_message(ro_db, user)
            assistant_message = await _answer_with_grounded_ai(
                user=user,
                user_message=user_message,
                fallback_message=base_message,
                grounding_facts=[base_message],
            )
            await _persist_message(db, session_id, user.id, "user", user_message, "general")
            await _persist_message(db, session_id, user.id, "assistant", assistant_message, "general")
            return ChatResponse(
                session_id=session_id,
                message=assistant_message,
                intent="general",
                sql_generated=None,
            )

        # Skip the "raise a ticket" shortcut when already inside support_chat — the
        # user is already talking to AI support, so let Gemini answer their real question
        # instead of short-circuiting with a generic "please raise a ticket" response.
        is_in_support_chat = (chat_context or "").strip().lower() == SUPPORT_CHAT_CONTEXT
        if not is_in_support_chat and _is_support_question(msg):
            base_message = await _vendor_support_message(ro_db, user)
            assistant_message = await _answer_with_grounded_ai(
                user=user,
                user_message=user_message,
                fallback_message=base_message,
                grounding_facts=[base_message],
            )
            await _persist_message(db, session_id, user.id, "user", user_message, "general")
            await _persist_message(db, session_id, user.id, "assistant", assistant_message, "general")
            return ChatResponse(
                session_id=session_id,
                message=assistant_message,
                intent="general",
                sql_generated=None,
            )

        if _is_recurring_data_question(msg):
            base_message = await _vendor_recurring_orders_message(ro_db, user)
            assistant_message = await _answer_with_grounded_ai(
                user=user,
                user_message=user_message,
                fallback_message=base_message,
                grounding_facts=[base_message],
            )
            await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
            await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
            return ChatResponse(
                session_id=session_id,
                message=assistant_message,
                intent="db_query",
                sql_generated=None,
            )

    if not _extract_tracking_code(user_message) and _is_order_status_list_question(msg, role):
        status_label, statuses = _extract_order_status_filter(msg)
        if status_label and statuses:
            base_message = await _list_self_service_orders_by_status(
                ro_db=ro_db,
                user=user,
                role=role,
                status_label=status_label,
                statuses=statuses,
            )
            assistant_message = await _answer_with_grounded_ai(
                user=user,
                user_message=user_message,
                fallback_message=base_message,
                grounding_facts=[base_message],
            )
            await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
            await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
            return ChatResponse(
                session_id=session_id,
                message=assistant_message,
                intent="db_query",
                sql_generated=None,
            )

    if _is_current_orders_question(msg, role):
        base_message = await _list_current_self_service_orders(ro_db, user, role)
        assistant_message = await _answer_with_grounded_ai(
            user=user,
            user_message=user_message,
            fallback_message=base_message,
            grounding_facts=[base_message],
        )
        await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
        await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="db_query",
            sql_generated=None,
        )

    # Fast-path: "where is my order" style — query DB directly, no Gemini call needed.
    order_keywords = [
        "where is my order",
        "where is my current order",
        "track my order",
        "my latest order",
        "current order status",
        "shipment status",
    ]
    tracking_code = _extract_tracking_code(user_message)
    if tracking_code or any(k in msg for k in order_keywords):
        matched_order, requested_tracking_code = await _lookup_self_service_order(
            ro_db=ro_db,
            user=user,
            user_message=user_message,
        )

        if not matched_order:
            noun = "shipment" if role == "VENDOR" else "order"
            if requested_tracking_code:
                assistant_message = (
                    f"I couldn't find {noun} **{requested_tracking_code}** in your account. "
                    f"Please double-check the tracking code and try again."
                )
            else:
                assistant_message = (
                    f"No {noun} found for your account yet. "
                    f"You can create a new {'shipment' if role == 'VENDOR' else 'booking'} from your dashboard."
                )
        else:
            base_message = _format_self_service_order_message(
                matched_order,
                role=role,
                tracking_code=requested_tracking_code,
            )
            assistant_message = await _answer_with_grounded_ai(
                user=user,
                user_message=user_message,
                fallback_message=base_message,
                grounding_facts=[base_message],
            )

        await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
        await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="db_query",
            sql_generated=None,
        )

    # All other data questions (wallet, spending, invoices, summaries, etc.)
    # fall through to Gemini with full DB access and user-scoped SQL.
    return None


async def _try_handle_dashboard_help_shortcuts(
    db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    chat_context: str | None = None,
) -> ChatResponse | None:
    """
    Only intercept messages that are pure UI-navigation/glossary questions
    that never need real data. Everything else falls through to Gemini so it
    can query the DB and return the user's actual data.
    """
    msg = (user_message or "").strip().lower()
    role = _role_name(user)

    if not msg:
        return None

    if _is_knowledge_question(msg):
        assistant_message = await _answer_from_retrieved_knowledge(db, user, user_message)
        if assistant_message:
            await _persist_message(db, session_id, user.id, "user", user_message, "general")
            await _persist_message(db, session_id, user.id, "assistant", assistant_message, "general")
            return ChatResponse(session_id=session_id, message=assistant_message, intent="general", sql_generated=None)

    # ── Greetings — pure pleasantries, no data needed ─────────────────
    if msg in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "sup", "yo"}:
        first = user.name.split()[0] if user.name else "there"
        if _is_warehouse_chat_context(user, chat_context):
            assistant_message = (
                f"Hi {first}! I'm your Smart WMS assistant. Ask me about warehouse capacity, queue pressure, staff availability, docks, returns, or tomorrow's workload."
            )
        elif role == "LOGISTIC_MANAGER":
            assistant_message = (
                f"Hi {first}! I'm your Cargo-Core AI Intelligence assistant. "
                "Ask me about hub performance, driver status, fleet readiness, inventory pressure, alerts, returns, revenue, or network operations."
            )
        elif role == "VENDOR":
            assistant_message = (
                f"Hi {first}! I'm your Cargo-Core vendor assistant. "
                "Ask me about your shipments, wallet balance, transaction history, invoices, or anything about your account."
            )
        elif role == "INDIVIDUAL":
            assistant_message = (
                f"Hi {first}! I'm your Cargo-Core move assistant. "
                "Ask me about your orders, wallet balance, spending history, booking help, or anything about your account."
            )
        else:
            assistant_message = (
                "Hi! I'm your Cargo-Core assistant. Ask me about orders, tracking, wallet, revenue, operations, or platform features."
            )
        await _persist_message(db, session_id, user.id, "user", user_message, "greeting")
        await _persist_message(db, session_id, user.id, "assistant", assistant_message, "greeting")
        return ChatResponse(session_id=session_id, message=assistant_message, intent="greeting", sql_generated=None)

    # ── Capabilities question — what can the AI do ─────────────────────
    if msg in {"what can you do", "help", "how can you help", "what do you know"} or msg.startswith("what can you"):
        if _is_warehouse_chat_context(user, chat_context):
            assistant_message = (
                "I can answer questions about your assigned warehouse using live operational data:\n"
                "- Queue pressure, picking backlog, and dispatch readiness\n"
                "- Free space by aisle/zone and dock availability\n"
                "- Labour availability, on-field staff, and staffing suggestions\n"
                "- Low-stock SKUs, restock pressure, and packing activity\n"
                "- Return grading, damage handling, and workload forecasts\n\n"
                "Ask naturally and I'll ground the answer in your current warehouse state."
            )
        elif role == "LOGISTIC_MANAGER":
            assistant_message = (
                "I can help with live logistics-management questions across your network:\n"
                "- Dashboard overview, hub comparisons, and active alerts\n"
                "- Driver status, fleet utilization, and vehicle readiness\n"
                "- Inventory pressure, dock status, and warehouse bottlenecks\n"
                "- Returns, RMA flow, and service-risk hotspots\n"
                "- Revenue trends, COD exposure, and operational performance\n"
                "- User, role, and cross-functional operations questions\n\n"
                "Ask naturally and I'll answer with live operational data whenever needed."
            )
        elif role == "VENDOR":
            assistant_message = (
                "I can answer questions about **your account** by querying the live database:\n"
                "- Your shipments (pending, active, delivered, cancelled)\n"
                "- Your wallet balance and full transaction history\n"
                "- How much you've spent (this month, total, per shipment)\n"
                "- Your unpaid or overdue invoices\n"
                "- Your damage reports\n"
                "- How to create shipments, bulk uploads, or recurring schedules\n\n"
                "Just ask naturally — I'll fetch real data for you."
            )
        elif role == "INDIVIDUAL":
            assistant_message = (
                "I can answer questions about **your account** by querying the live database:\n"
                "- Your orders (latest, active, delivered, cancelled)\n"
                "- Your wallet balance and transaction history\n"
                "- How much you've spent on moves\n"
                "- Your move quotes and estimates\n"
                "- Your damage reports\n"
                "- How to book a move or use the AI Spatial Estimator\n\n"
                "Just ask naturally — I'll fetch real data for you."
            )
        else:
            assistant_message = (
                "I can query live database data: orders, drivers, vehicles, inventory, revenue, "
                "wallets, logistics metrics, and more. Ask me anything about Cargo-Core operations."
            )
        await _persist_message(db, session_id, user.id, "user", user_message, "general")
        await _persist_message(db, session_id, user.id, "assistant", assistant_message, "general")
        return ChatResponse(session_id=session_id, message=assistant_message, intent="general", sql_generated=None)

    # ── Human handoff ──────────────────────────────────────────────────
    if _is_human_handoff_request(msg):
        return await _create_human_handoff_response(
            db=db,
            session_id=session_id,
            user=user,
            user_message=user_message,
            reason="Customer requested a human support reply.",
        )

    # Everything else (orders, wallet, tracking, spending, invoices, bookings...)
    # falls through to Gemini so it can use execute_sql_query with real data.
    return None
