"""
ai_service.py
Core orchestration layer for the AI chatbot.

Handles: Gemini interaction, SQL validation & execution, conversation persistence.

Uses the new unified `google-genai` SDK with async client (`client.aio`).
"""
import json
import re
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from google.genai import types
from loguru import logger
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.inventory import InventoryItem, RestockRequest
from app.models.labour import Labourer
from app.models.logistics import (
    LogisticsAlert,
    LogisticsDailyStats,
    LogisticsDriverProfile,
    LogisticsReturnCase,
    LogisticsVehicle,
)
from app.models.order import DamageReport, Order
from app.models.user import User
from app.models.vendor import VendorRecurringRule, VendorSupportTicket
from app.models.wallet import WalletTransaction
from app.models.warehouse import (
    LoadingDock,
    PackingStation,
    ReturnGrading,
    Warehouse,
    WarehouseZoneMetrics,
)
from app.schemas.ai import (
    ChatResponse,
    ConversationHistory,
    ConversationMessage,
    SessionListItem,
    SessionListResponse,
)
from app.services.ai_knowledge import retrieve_knowledge, retrieve_knowledge_from_db
from app.services.finance_service import get_finance_summary
from app.services.sql_validator import SQLValidationError, validate_sql
from app.services.wallet_service import get_wallet_balance
from app.utils.gemini import (
    EXECUTE_SQL_TOOL,
    GEMINI_FLASH_MODEL,
    SYSTEM_INSTRUCTION,
    GeminiConfigError,
    generate_with_fallback,
    get_gemini_client,
)

# Maximum conversation messages to include in context window.
MAX_CONTEXT_MESSAGES = 20
TRACKING_CODE_PATTERN = re.compile(r"\bQC-[A-Z0-9]+\b", re.IGNORECASE)
SUPPORT_CHAT_CONTEXT = "support_chat"
SUPPORT_SESSION_CLOSED_INTENT = "support_session_closed"
SUPPORT_SESSION_CLOSED_MESSAGE = (
    "This human support session has been closed by the Support Manager. "
    "You can continue with AI help here, but to request human support again you need to start a fresh support chat."
)
HUMAN_HANDOFF_PATTERNS = (
    "human",
    "real person",
    "customer care",
    "customer support",
    "live agent",
    "support agent",
    "support executive",
    "representative",
    "talk to someone",
    "speak to someone",
    "call me",
    "call back",
)
HUMAN_HANDOFF_PHRASES = (
    "talk to human",
    "human agent",
    "connect support",
    "connect me to support",
    "connect me to a human",
    "i want human support",
    "i need human support",
    "i need a human",
    "i want a human",
    "not satisfied",
    "not happy with this",
    "this did not help",
    "this didn't help",
    "still not resolved",
    "need to escalate",
    "escalate this",
)
LEGAL_THREAT_PATTERNS = (
    "lawyer",
    "legal notice",
    "consumer court",
    "court",
    "police complaint",
    "sue",
    "lawsuit",
    "legal action",
)
SEVERE_NEGATIVE_SENTIMENT_PATTERNS = (
    "angry",
    "very angry",
    "frustrated",
    "very frustrated",
    "furious",
    "useless",
    "worst service",
    "terrible service",
    "pathetic",
    "unacceptable",
    "rude",
    "stupid",
    "idiot",
    "scam",
    "fraud",
    "cheat",
    "cheated",
    "hate this",
    "damn",
    "hell",
)

SELF_SERVICE_ROLES = {"VENDOR", "INDIVIDUAL"}
MIN_PROACTIVE_ESCALATION_TURNS = 3  # Minimum customer exchanges before sentiment-based handover fires
WAREHOUSE_CONTEXTS = {"warehouse_management", "smart_wms", "warehouse_ai"}
LOGISTIC_MANAGER_CONTEXTS = {"logistic_manager", "ai_intelligence", "logistics_intelligence"}
DISPATCHER_CONTEXTS = {"dispatcher", "smart_dispatcher", "dispatch_ai"}
SELF_SERVICE_ALLOWED_TABLES = {
    "orders",
    "order_items",
    "picked_items",
    "customer_quotes",
    "damage_reports",
    "users",
    "roles",
    "wallet_transactions",
    "vendor_recurring_rules",
    "vendor_support_tickets",
}
WAREHOUSE_MANAGER_ALLOWED_TABLES = {
    "warehouses",
    "orders",
    "order_items",
    "picked_items",
    "inventory_items",
    "inventory_movements",
    "restock_requests",
    "labourers",
    "users",
    "roles",
    "loading_docks",
    "packing_stations",
    "quality_checks",
    "return_gradings",
    "warehouse_zone_metrics",
    "logistics_return_cases",
    "logistics_alerts",
    "logistics_daily_stats",
    "logistics_driver_profiles",
    "logistics_vehicles",
    "logistics_transactions",
    "logistics_zones",
    "logistics_metrics",
    "logistics_chat_threads",
    "logistics_chat_messages",
    "logistics_escalations",
    "damage_reports",
}


def _safe_message_text(value: str | None, fallback: str) -> str:
    text_value = _sanitize_chat_text((value or "").strip())
    fallback_value = _sanitize_chat_text(fallback)
    return text_value if text_value else fallback_value


def _sanitize_chat_text(value: str) -> str:
    cleaned = (value or "").replace("**", "").replace("__", "").replace("`", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _extract_tracking_code(user_message: str) -> str | None:
    match = TRACKING_CODE_PATTERN.search(user_message or "")
    return match.group(0).upper() if match else None


def _format_money(amount: float) -> str:
    return f"INR {amount:,.2f}"


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _is_wallet_balance_question(msg: str) -> bool:
    return "wallet" in msg and any(
        key in msg
        for key in [
            "balance",
            "amount",
            "how much",
            "right now",
            "current",
            "available",
            "funds",
            "money",
            "credit",
        ]
    )


def _is_current_orders_question(msg: str, role: str) -> bool:
    phrases = [
        "current orders",
        "current shipments",
        "active orders",
        "active shipments",
        "pending orders",
        "pending shipments",
        "show current orders",
        "show current shipments",
        "list current orders",
        "list current shipments",
        "in-progress orders",
        "in-progress shipments",
        "unfulfilled orders",
        "unfulfilled shipments",
    ]
    if any(phrase in msg for phrase in phrases):
        return True
    return role == "VENDOR" and "current order" not in msg and "orders" in msg and "current" in msg


def _extract_order_status_filter(msg: str) -> tuple[str | None, set[str] | None]:
    status_definitions: list[tuple[str, set[str], list[str]]] = [
        ("in transit", {"IN_TRANSIT"}, ["in transit", "intransit", "on the way", "en route"]),
        ("delivered", {"DELIVERED", "CLOSED"}, ["delivered", "completed", "finished"]),
        ("cancelled", {"CANCELLED"}, ["cancelled", "canceled", "voided"]),
        ("confirmed", {"CONFIRMED"}, ["confirmed", "approved"]),
        ("assigned", {"ASSIGNED"}, ["assigned", "dispatched"]),
        ("pending", {"DRAFT", "CONFIRMED", "ASSIGNED"}, ["pending", "waiting", "not yet shipped"]),
    ]
    for label, statuses, tokens in status_definitions:
        if any(token in msg for token in tokens):
            return label, statuses
    return None, None


def _is_order_status_list_question(msg: str, role: str) -> bool:
    status_label, _ = _extract_order_status_filter(msg)
    if not status_label:
        return False

    order_terms = {"orders", "order", "my orders"}
    if role == "VENDOR":
        order_terms.update({"shipment", "shipments", "my shipments"})

    return any(term in msg for term in order_terms)


def _is_recurring_data_question(msg: str) -> bool:
    if "recurring" not in msg and "scheduled" not in msg:
        return False
    return any(
        key in msg
        for key in [
            "orders",
            "order",
            "shipments",
            "shipment",
            "list",
            "show",
            "what order",
            "which",
            "scheduled",
            "upcoming",
            "next run",
            "rules",
            "automated",
            "template",
        ]
    )


def _is_analytics_section_question(msg: str) -> bool:
    return "analytics" in msg and any(
        key in msg
        for key in ["what is", "what's", "section", "do", "mean", "shows", "show", "about", "explain", "purpose of"]
    )


def _is_support_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "need support",
            "support needed",
            "help me",
            "customer support",
            "support ticket",
            "support",
            "raise ticket",
            "contact support",
            "talk to human",
            "human agent",
            "connect support",
            "speak to someone",
            "agent",
            "representative",
            "assistance",
        ]
    )


def _is_knowledge_question(msg: str) -> bool:
    knowledge_starters = [
        "what is",
        "what are",
        "what does",
        "how does",
        "how do",
        "explain",
        "tell me about",
        "meaning of",
        "screen mean",
        "section mean",
        "define",
        "can you explain",
    ]
    knowledge_topics = [
        "refund",
        "damage report",
        "damage",
        "wallet",
        "analytics",
        "support",
        "recurring",
        "quote",
        "estimator",
        "bulk upload",
        "tracking",
        "screen",
        "section",
        "invoice",
        "billing",
        "payment",
        "dashboard",
        "geofencing",
        "payroll",
        "salary",
        "dues",
        "warehouse management",
        "user roles",
        "fleet",
        "rate governance",
        "reverse logistics",
        "reports",
        "communication",
        "recovery tickets",
        "comparative viewers",
        "ai intelligence",
        "api",
        "integration",
    ]
    return any(starter in msg for starter in knowledge_starters) or (
        any(topic in msg for topic in knowledge_topics)
        and any(token in msg for token in ["work", "works", "working", "mean", "means", "process"])
    )


def _is_refund_question(msg: str) -> bool:
    return "refund" in msg or "refunded" in msg or "money back" in msg


def _is_total_spend_question(msg: str) -> bool:
    spend_terms = [
        "spent",
        "spend",
        "spending",
        "amount spend",
        "amount spent",
        "total spend",
        "total spent",
        "expenditure",
        "total cost",
    ]
    scope_terms = [
        "total",
        "till now",
        "till date",
        "so far",
        "upto now",
        "up to now",
        "overall",
        "for orders",
        "for order",
        "for shipments",
        "for moves",
        "this month",
        "current month",
        "last month",
        "this year",
    ]
    return any(term in msg for term in spend_terms) and any(term in msg for term in scope_terms)


def _is_warehouse_chat_context(user: User, chat_context: str | None) -> bool:
    role = _role_name(user)
    return role == "WAREHOUSE_MANAGER" and (chat_context or "").strip().lower() in WAREHOUSE_CONTEXTS


def _is_warehouse_capacity_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "free space",
            "space left",
            "aisle",
            "zone",
            "capacity",
            "slotting",
            "layout",
            "capacity for",
        ]
    )


def _is_warehouse_staff_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "laborers",
            "labourers",
            "staff",
            "on-field",
            "on field",
            "available staff",
            "free staff",
            "reallocate",
            "roster",
            "who is free",
        ]
    )


def _is_warehouse_workload_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "workload",
            "predict",
            "prediction",
            "forecast",
            "tomorrow",
            "expected load",
            "schedule extra staff",
        ]
    )


def _is_warehouse_pending_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "pending orders",
            "orders pending",
            "pending action",
            "review orders",
            "what needs attention",
            "backlog",
            "queue",
        ]
    )


def _is_warehouse_returns_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "damage",
            "returns",
            "return grading",
            "refund",
            "visual damage",
            "damaged",
            "grading",
        ]
    )


def _is_warehouse_dock_question(msg: str) -> bool:
    return any(key in msg for key in ["dock", "loading dock", "truck", "bay"])


def _is_warehouse_inventory_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "inventory",
            "stock",
            "restock",
            "safety stock",
            "packing material",
            "packing materials",
            "sku",
        ]
    )


def _is_warehouse_overview_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "overview",
            "summary",
            "status",
            "what's happening",
            "whats happening",
            "dashboard",
            "warehouse now",
        ]
    )


def _is_logistic_manager_chat_context(user: User, chat_context: str | None) -> bool:
    role = _role_name(user)
    normalized = (chat_context or "").strip().lower()
    return role == "LOGISTIC_MANAGER" and (
        normalized in LOGISTIC_MANAGER_CONTEXTS or normalized == ""
    )


def _is_dispatcher_chat_context(user: User, chat_context: str | None) -> bool:
    role = _role_name(user)
    normalized = (chat_context or "").strip().lower()
    return role == "DISPATCHER" and normalized in DISPATCHER_CONTEXTS


def _is_logistics_driver_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "driver status",
            "current driver status",
            "drivers status",
            "driver report",
            "driver update",
            "active drivers",
            "available drivers",
            "driver coverage",
        ]
    )


def _is_logistics_fleet_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "fleet status",
            "vehicle status",
            "fleet & vehicle",
            "fleet readiness",
            "vehicle readiness",
            "vehicles available",
            "fleet health",
        ]
    )


def _is_logistics_inventory_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "inventory",
            "inventory levels",
            "stock levels",
            "low stock",
            "inventory pressure",
            "restock",
        ]
    )


def _is_logistics_returns_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "returns",
            "return",
            "rma",
            "refund",
            "damage cases",
            "returns summary",
        ]
    )


def _is_logistics_revenue_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "revenue",
            "finance",
            "financial",
            "payroll",
            "salary",
            "payout",
            "payouts",
            "due",
            "dues",
            "pending salary",
            "salary due",
            "pay due",
            "cod",
            "cash flow",
            "revenue forecast",
            "revenue trend",
            "expenses",
            "profit",
            "net profit",
        ]
    )


def _is_logistics_dashboard_question(msg: str) -> bool:
    return any(
        key in msg
        for key in [
            "dashboard",
            "dashboard overview",
            "overview",
            "network overview",
            "operations overview",
            "hub performance",
            "performance overview",
            "active alerts",
        ]
    )


def _is_human_handoff_request(msg: str) -> bool:
    if not msg:
        return False
    if any(phrase in msg for phrase in HUMAN_HANDOFF_PHRASES):
        return True
    return any(pattern in msg for pattern in HUMAN_HANDOFF_PATTERNS) and any(
        token in msg
        for token in [
            "want",
            "need",
            "connect",
            "speak",
            "talk",
            "reply",
            "call",
            "person",
            "someone",
            "manual",
        ]
    )


def _has_legal_threat(msg: str) -> bool:
    return any(pattern in msg for pattern in LEGAL_THREAT_PATTERNS)


def _has_severe_negative_sentiment(msg: str) -> bool:
    normalized = (msg or "").strip().lower()
    if not normalized:
        return False
    if any(
        re.search(rf"\b{re.escape(pattern)}\b", normalized)
        for pattern in SEVERE_NEGATIVE_SENTIMENT_PATTERNS
    ):
        return True
    return _support_health_score(normalized) <= 45


def _support_health_score(msg: str) -> int:
    """Keyword-based fallback health scorer (used when Gemini is unavailable)."""
    score = 100

    if not msg:
        return score

    penalties = {
        "not satisfied": 35,
        "not happy": 25,
        "did not help": 25,
        "didn't help": 25,
        "still not resolved": 30,
        "angry": 20,
        "frustrated": 20,
        "complaint": 15,
        "urgent": 10,
        "refund": 10,
        "delay": 10,
        "delayed": 10,
        "damaged": 15,
        "broken": 15,
        "issue": 8,
        "problem": 8,
    }
    for token, penalty in penalties.items():
        if token in msg:
            score -= penalty

    if _is_human_handoff_request(msg):
        score -= 45
    if _has_legal_threat(msg):
        score -= 60

    return max(0, min(100, score))


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
        client = get_gemini_client()
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


async def _list_current_self_service_orders(
    ro_db: AsyncSession,
    user: User,
    role: str,
) -> str:
    noun_plural = "shipments" if role == "VENDOR" else "orders"
    rows = (
        await ro_db.execute(
            select(Order)
            .where(
                Order.customer_id == user.id,
                func.upper(Order.status).notin_(["DELIVERED", "CANCELLED"]),
            )
            .order_by(Order.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    if not rows:
        return f"You do not have any active {noun_plural} right now."

    header = f"Here are your current {noun_plural}:"
    lines = [header]
    for order in rows:
        schedule = order.scheduled_at.isoformat() if order.scheduled_at else "Not scheduled yet"
        stage = order.warehouse_substatus or "N/A"
        lines.append(
            f"- {order.tracking_code}: {order.status} | Stage: {stage} | Scheduled: {schedule}"
        )
    return "\n".join(lines)


async def _list_self_service_orders_by_status(
    ro_db: AsyncSession,
    user: User,
    role: str,
    status_label: str,
    statuses: set[str],
) -> str:
    noun_plural = "shipments" if role == "VENDOR" else "orders"
    rows = (
        await ro_db.execute(
            select(Order)
            .where(
                Order.customer_id == user.id,
                func.upper(Order.status).in_(sorted(statuses)),
            )
            .order_by(Order.created_at.desc())
            .limit(10)
        )
    ).scalars().all()

    if not rows:
        return f"You do not have any {status_label} {noun_plural} right now."

    lines = [f"Here are your {status_label} {noun_plural}:"]
    for order in rows:
        schedule = order.scheduled_at.isoformat() if order.scheduled_at else "Not scheduled yet"
        stage = order.warehouse_substatus or "N/A"
        lines.append(
            f"- {order.tracking_code}: {order.status} | Stage: {stage} | Scheduled: {schedule}"
        )
    return "\n".join(lines)


async def _lookup_self_service_order(
    ro_db: AsyncSession,
    user: User,
    user_message: str,
) -> tuple[Order | None, str | None]:
    tracking_code = _extract_tracking_code(user_message)

    stmt = select(Order).where(Order.customer_id == user.id)
    if tracking_code:
        stmt = stmt.where(func.upper(Order.tracking_code) == tracking_code).limit(1)
    else:
        stmt = stmt.order_by(Order.created_at.desc()).limit(1)

    order = (await ro_db.execute(stmt)).scalar_one_or_none()
    return order, tracking_code


def _format_self_service_order_message(
    order: Order,
    role: str,
    tracking_code: str | None = None,
) -> str:
    noun = "shipment" if role == "VENDOR" else "order"
    heading = (
        f"Your {noun}: **{order.tracking_code}**"
        if tracking_code
        else f"Your latest {noun}: **{order.tracking_code}**"
    )
    eta = order.scheduled_at.isoformat() if order.scheduled_at else "Not scheduled yet"
    pickup_addr = order.pickup_addr or "N/A"
    delivery_addr = order.delivery_addr or "N/A"
    substatus = order.warehouse_substatus or "N/A"
    return (
        f"{heading}\n"
        f"- Status: {order.status}\n"
        f"- Warehouse stage: {substatus}\n"
        f"- Scheduled: {eta}\n"
        f"- Route: {pickup_addr} -> {delivery_addr}"
    )


async def _vendor_wallet_message(ro_db: AsyncSession, user: User) -> str:
    balance = round(await get_wallet_balance(ro_db, user.id), 2)
    rows = (
        await ro_db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.user_id == user.id)
            .order_by(WalletTransaction.created_at.desc())
            .limit(3)
        )
    ).scalars().all()
    lines = [f"Your wallet balance right now is **{_format_money(balance)}**."]
    if rows:
        lines.append("Recent wallet activity:")
        for tx in rows:
            lines.append(
                f"- {tx.transaction_kind}: {_format_money(float(tx.amount or 0.0))} for {tx.reason} on {tx.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
    else:
        lines.append("No wallet transactions found yet.")
    return "\n".join(lines)


async def _vendor_recurring_orders_message(ro_db: AsyncSession, user: User) -> str:
    rules = (
        await ro_db.execute(
            select(VendorRecurringRule)
            .where(VendorRecurringRule.vendor_id == user.id)
            .order_by(VendorRecurringRule.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    if not rules:
        return (
            "You do not have any recurring shipment schedules yet. "
            "Create one from the Recurring Orders section to automate repeat shipments."
        )

    lines = ["Here are your recurring shipment schedules:"]
    for rule in rules:
        status = "Active" if rule.active else "Paused"
        lines.append(
            f"- {rule.name}: {rule.frequency} | Next run: {rule.next_run} | Route: {rule.route} | {status}"
        )
    return "\n".join(lines)


async def _vendor_support_message(ro_db: AsyncSession, user: User) -> str:
    tickets = (
        await ro_db.execute(
            select(VendorSupportTicket)
            .where(VendorSupportTicket.vendor_id == user.id)
            .order_by(VendorSupportTicket.created_at.desc())
            .limit(3)
        )
    ).scalars().all()

    open_count = (
        await ro_db.execute(
            select(func.count())
            .select_from(VendorSupportTicket)
            .where(
                VendorSupportTicket.vendor_id == user.id,
                func.upper(VendorSupportTicket.status) != "RESOLVED",
            )
        )
    ).scalar_one()

    lines = [
        f"You currently have {int(open_count or 0)} open support ticket(s).",
    ]
    if tickets:
        latest = tickets[0]
        lines.append(
            f"Latest ticket: {latest.subject} | Status: {latest.status} | Priority: {latest.priority}"
        )
    else:
        lines.append("No support tickets have been raised yet.")
    lines.append("If you need further help, you can raise a new ticket from the Support Tickets tab.")
    return "\n".join(lines)


async def _vendor_analytics_message(ro_db: AsyncSession, user: User) -> str:
    orders = (
        await ro_db.execute(
            select(Order)
            .where(Order.customer_id == user.id)
            .order_by(Order.created_at.desc())
        )
    ).scalars().all()

    total = len(orders)
    delivered = sum(1 for order in orders if _normalize_text(order.status) == "delivered")
    cancelled = sum(1 for order in orders if _normalize_text(order.status) == "cancelled")
    active = sum(1 for order in orders if _normalize_text(order.status) not in {"delivered", "cancelled"})
    successful = max(total - cancelled, 0)
    success_rate = round((successful / total) * 100, 1) if total else 0.0
    avg_order_value = round(sum(float(order.total_amount or 0.0) for order in orders) / total, 2) if total else 0.0
    current_month = datetime.now(UTC).strftime("%Y-%m")
    monthly_spend = round(
        sum(float(order.total_amount or 0.0) for order in orders if order.created_at.strftime("%Y-%m") == current_month),
        2,
    )

    return (
        "The Analytics section shows your shipment trends and business performance, "
        "including monthly spend, active vs delivered shipments, success rate, and average order value.\n"
        f"Right now: total shipments **{total}**, active **{active}**, delivered **{delivered}**, "
        f"success rate **{success_rate}%**, average order value **{_format_money(avg_order_value)}**, "
        f"this month spend **{_format_money(monthly_spend)}**."
    )


async def _self_service_spend_message(ro_db: AsyncSession, user: User, role: str) -> str:
    orders = (
        await ro_db.execute(
            select(Order)
            .where(Order.customer_id == user.id)
            .order_by(Order.created_at.desc())
        )
    ).scalars().all()

    completed_orders = [
        order for order in orders
        if _normalize_text(order.payment_status) == "paid" or _normalize_text(order.status) == "delivered"
    ]
    total_spent = round(sum(float(order.total_amount or 0.0) for order in completed_orders), 2)
    current_month = datetime.now(UTC).strftime("%Y-%m")
    month_spent = round(
        sum(
            float(order.total_amount or 0.0)
            for order in completed_orders
            if order.created_at.strftime("%Y-%m") == current_month
        ),
        2,
    )
    noun_plural = "shipments" if role == "VENDOR" else "orders"

    if not completed_orders:
        return (
            f"You have not completed any paid {noun_plural} yet, so your total spend so far is "
            f"**{_format_money(0.0)}**."
        )

    latest = completed_orders[0]
    return (
        f"Your total spend so far is **{_format_money(total_spent)}** across **{len(completed_orders)}** completed {noun_plural}.\n"
        f"This month: **{_format_money(month_spent)}**.\n"
        f"Latest completed {'shipment' if role == 'VENDOR' else 'order'}: **{latest.tracking_code}** for **{_format_money(float(latest.total_amount or 0.0))}**."
    )


async def _self_service_refund_message(
    ro_db: AsyncSession,
    user: User,
    role: str,
    user_message: str,
) -> str:
    msg = _normalize_text(user_message)
    refund_rows = (
        await ro_db.execute(
            select(WalletTransaction, Order.tracking_code)
            .outerjoin(Order, Order.id == WalletTransaction.order_id)
            .where(
                WalletTransaction.user_id == user.id,
                WalletTransaction.reason.in_(["CANCELLATION_REFUND", "DAMAGE_REFUND"]),
            )
            .order_by(WalletTransaction.created_at.desc())
            .limit(10)
        )
    ).all()

    if role == "INDIVIDUAL" and ("damage" in msg or "claim" in msg):
        damage_rows = (
            await ro_db.execute(
                select(DamageReport.reference_code, LogisticsReturnCase.refund_amount, LogisticsReturnCase.status, Order.tracking_code)
                .select_from(DamageReport)
                .outerjoin(LogisticsReturnCase, LogisticsReturnCase.reference_code == DamageReport.reference_code)
                .outerjoin(Order, Order.id == DamageReport.order_id)
                .where(DamageReport.customer_id == user.id)
                .order_by(DamageReport.created_at.desc())
                .limit(10)
            )
        ).all()
        approved_damage = [row for row in damage_rows if float(row.refund_amount or 0.0) > 0]
        if not approved_damage:
            return (
                "You do not have any approved damage-report refunds yet. "
                "If a claim is approved, the refund will appear in your wallet history."
            )

        total_damage_refund = round(sum(float(row.refund_amount or 0.0) for row in approved_damage), 2)
        lines = [f"Your approved damage-report refunds total **{_format_money(total_damage_refund)}**."]
        for row in approved_damage[:5]:
            tracking_code = row.tracking_code or "No linked order"
            lines.append(
                f"- {tracking_code}: {_format_money(float(row.refund_amount or 0.0))} | Claim status: {row.status or 'N/A'}"
            )
        return "\n".join(lines)

    if not refund_rows:
        return "You do not have any wallet refunds recorded yet."

    total_refunds = round(sum(float(tx.amount or 0.0) for tx, _ in refund_rows), 2)
    lines = [f"Your total recorded refunds are **{_format_money(total_refunds)}**."]
    for tx, tracking_code in refund_rows[:5]:
        ref_label = tracking_code or "Wallet adjustment"
        lines.append(
            f"- {ref_label}: {_format_money(float(tx.amount or 0.0))} | {tx.reason} | {tx.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
    return "\n".join(lines)


async def _build_warehouse_snapshot(ro_db: AsyncSession, user: User) -> dict | None:
    warehouse_id = getattr(user, "warehouse_id", None)
    if not warehouse_id:
        return None

    warehouse = (
        await ro_db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    ).scalar_one_or_none()
    if not warehouse:
        return None

    status_rows = (
        await ro_db.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.warehouse_id == warehouse_id)
            .group_by(Order.status)
        )
    ).all()
    status_counts = {
        (status or "UNKNOWN").upper(): int(count or 0)
        for status, count in status_rows
    }

    substatus_rows = (
        await ro_db.execute(
            select(Order.warehouse_substatus, func.count(Order.id))
            .where(Order.warehouse_id == warehouse_id)
            .group_by(Order.warehouse_substatus)
        )
    ).all()
    substatus_counts = {
        (substatus or "NONE").upper(): int(count or 0)
        for substatus, count in substatus_rows
    }

    active_orders = sum(
        count
        for status, count in status_counts.items()
        if status not in {"DELIVERED", "CANCELLED", "CLOSED"}
    )
    pending_orders = (
        await ro_db.execute(
            select(func.count(Order.id))
            .where(
                Order.warehouse_id == warehouse_id,
                or_(
                    func.upper(Order.warehouse_substatus).in_(
                        ["AWAITING_INBOUND", "AWAITING_PICK", "PICKING", "PICKED", "PACKING", "QC_PASSED"]
                    ),
                    (
                        Order.warehouse_substatus.is_(None)
                        & func.upper(Order.status).in_(["CONFIRMED", "ASSIGNED"])
                    ),
                ),
            )
        )
    ).scalar_one()
    picking_orders = sum(
        substatus_counts.get(key, 0)
        for key in ["PICKING", "PICKED", "PACKING"]
    )
    ready_for_dispatch = sum(
        substatus_counts.get(key, 0)
        for key in ["PACKED", "QC_PASSED", "ON_DOCK", "DISPATCHED"]
    )
    in_transit_orders = status_counts.get("IN_TRANSIT", 0)
    delivered_orders = status_counts.get("DELIVERED", 0) + status_counts.get("CLOSED", 0)

    recent_orders = (
        await ro_db.execute(
            select(Order)
            .where(Order.warehouse_id == warehouse_id)
            .order_by(Order.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    labour_pairs = (
        await ro_db.execute(
            select(Labourer, Order, User.name)
            .outerjoin(User, Labourer.user_id == User.id)
            .outerjoin(Order, Labourer.assigned_order_id == Order.id)
            .where(Labourer.warehouse_id == warehouse_id)
            .order_by(Labourer.created_at.desc())
        )
    ).all()

    available_staff = 0
    assigned_staff = 0
    on_field_staff = 0
    off_duty_staff = 0
    available_names: list[str] = []
    on_field_names: list[str] = []
    for labourer, order, labour_name in labour_pairs:
        if not labourer.is_active:
            off_duty_staff += 1
            continue
        if order and _normalize_text(order.status) == "in_transit":
            on_field_staff += 1
            if labour_name and len(on_field_names) < 3:
                on_field_names.append(labour_name)
            continue
        if labourer.assigned_order_id:
            assigned_staff += 1
            continue
        available_staff += 1
        if labour_name and len(available_names) < 3:
            available_names.append(labour_name)

    total_staff = len(labour_pairs)

    dock_rows = (
        await ro_db.execute(
            select(LoadingDock, Order.tracking_code)
            .outerjoin(Order, LoadingDock.assigned_order_id == Order.id)
            .where(LoadingDock.warehouse_id == warehouse_id)
            .order_by(LoadingDock.dock_number.asc())
        )
    ).all()
    docks = [dock for dock, _ in dock_rows]
    free_docks = sum(1 for dock in docks if _normalize_text(dock.status) == "free")
    occupied_docks = sum(1 for dock in docks if _normalize_text(dock.status) == "occupied")
    maintenance_docks = sum(1 for dock in docks if _normalize_text(dock.status) == "maintenance")
    occupied_dock_labels = [
        f"Dock {dock.dock_number}{f' ({tracking_code})' if tracking_code else ''}"
        for dock, tracking_code in dock_rows
        if _normalize_text(dock.status) == "occupied"
    ][:3]

    packing_stations = (
        await ro_db.execute(
            select(PackingStation).where(PackingStation.warehouse_id == warehouse_id)
        )
    ).scalars().all()
    active_stations = sum(1 for station in packing_stations if _normalize_text(station.status) == "active")
    maintenance_stations = sum(
        1 for station in packing_stations if _normalize_text(station.status) == "maintenance"
    )

    low_stock_items = (
        await ro_db.execute(
            select(InventoryItem)
            .where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.quantity_on_hand <= InventoryItem.safety_stock,
            )
            .order_by(InventoryItem.quantity_on_hand.asc(), InventoryItem.name.asc())
            .limit(5)
        )
    ).scalars().all()
    total_inventory_units = (
        await ro_db.execute(
            select(func.coalesce(func.sum(InventoryItem.quantity_on_hand), 0))
            .where(InventoryItem.warehouse_id == warehouse_id)
        )
    ).scalar_one()
    pending_restocks = (
        await ro_db.execute(
            select(func.count(RestockRequest.id))
            .where(
                RestockRequest.warehouse_id == warehouse_id,
                func.upper(RestockRequest.status) == "PENDING",
            )
        )
    ).scalar_one()

    latest_metric_date = (
        await ro_db.execute(
            select(func.max(WarehouseZoneMetrics.metric_date))
            .where(WarehouseZoneMetrics.warehouse_id == warehouse_id)
        )
    ).scalar_one()
    zone_metrics = []
    if latest_metric_date:
        zone_metrics = (
            await ro_db.execute(
                select(WarehouseZoneMetrics)
                .where(
                    WarehouseZoneMetrics.warehouse_id == warehouse_id,
                    WarehouseZoneMetrics.metric_date == latest_metric_date,
                )
                .order_by(WarehouseZoneMetrics.zone_id.asc())
            )
        ).scalars().all()

    aisle_rows = (
        await ro_db.execute(
            select(
                InventoryItem.aisle,
                func.count(InventoryItem.id).label("sku_count"),
                func.coalesce(func.sum(InventoryItem.quantity_on_hand), 0).label("total_qty"),
            )
            .where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.aisle.is_not(None),
            )
            .group_by(InventoryItem.aisle)
        )
    ).all()

    free_space_label = "No aisle utilization data yet"
    busy_space_label = "No busy zone detected"
    if zone_metrics:
        freest_zone = min(zone_metrics, key=lambda row: row.capacity_used_pct or 0.0)
        busiest_zone = max(zone_metrics, key=lambda row: row.capacity_used_pct or 0.0)
        free_space_label = (
            f"Zone {freest_zone.zone_id} at {round(float(freest_zone.capacity_used_pct or 0.0), 1)}% utilized"
        )
        busy_space_label = (
            f"Zone {busiest_zone.zone_id} at {round(float(busiest_zone.capacity_used_pct or 0.0), 1)}% utilized"
        )
    elif aisle_rows:
        freest_aisle = min(aisle_rows, key=lambda row: int(row.total_qty or 0))
        busiest_aisle = max(aisle_rows, key=lambda row: int(row.total_qty or 0))
        free_space_label = f"Aisle {freest_aisle.aisle} with {int(freest_aisle.total_qty or 0)} units stored"
        busy_space_label = f"Aisle {busiest_aisle.aisle} with {int(busiest_aisle.total_qty or 0)} units stored"

    recent_returns = (
        await ro_db.execute(
            select(ReturnGrading)
            .where(ReturnGrading.warehouse_id == warehouse_id)
            .order_by(ReturnGrading.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    pending_returns = sum(1 for row in recent_returns if _normalize_text(row.status) != "completed")
    completed_returns = sum(1 for row in recent_returns if _normalize_text(row.status) == "completed")

    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    orders_last_week = (
        await ro_db.execute(
            select(func.count(Order.id))
            .where(
                Order.warehouse_id == warehouse_id,
                Order.created_at >= seven_days_ago,
            )
        )
    ).scalar_one()
    avg_daily_orders = round(float(orders_last_week or 0) / 7.0, 1)
    projected_orders = int(round(max(avg_daily_orders, float(active_orders or 0)) * 1.15))
    suggested_staff = max(1, int((max(projected_orders, pending_orders, 1) + 3) // 4))

    facts = [
        f"Warehouse name: {warehouse.name}",
        f"Warehouse capacity limit: {warehouse.capacity_limit or 0}",
        f"Active warehouse orders: {active_orders}",
        f"Orders awaiting warehouse action: {pending_orders}",
        f"Orders in picking or packing: {picking_orders}",
        f"Orders ready for dispatch: {ready_for_dispatch}",
        f"Orders already in transit from this warehouse: {in_transit_orders}",
        f"Available staff: {available_staff} out of {total_staff}",
        f"Assigned floor staff: {assigned_staff}",
        f"On-field staff: {on_field_staff}",
        f"Loading docks free: {free_docks} out of {len(docks)}",
        f"Packing stations active: {active_stations} out of {len(packing_stations)}",
        f"Low-stock SKUs: {len(low_stock_items)}",
        f"Pending restock requests: {int(pending_restocks or 0)}",
        f"Most free storage area: {free_space_label}",
        f"Most loaded storage area: {busy_space_label}",
        f"Pending return gradings in the latest batch: {pending_returns}",
        f"Completed return gradings in the latest batch: {completed_returns}",
        f"Average incoming orders per day over the last 7 days: {avg_daily_orders}",
        f"Projected tomorrow workload: {projected_orders}",
        f"Suggested active floor staff for tomorrow: {suggested_staff}",
    ]

    return {
        "warehouse": warehouse,
        "active_orders": active_orders,
        "pending_orders": pending_orders,
        "picking_orders": picking_orders,
        "ready_for_dispatch": ready_for_dispatch,
        "in_transit_orders": in_transit_orders,
        "delivered_orders": delivered_orders,
        "recent_orders": recent_orders,
        "available_staff": available_staff,
        "assigned_staff": assigned_staff,
        "on_field_staff": on_field_staff,
        "off_duty_staff": off_duty_staff,
        "total_staff": total_staff,
        "available_names": available_names,
        "on_field_names": on_field_names,
        "free_docks": free_docks,
        "occupied_docks": occupied_docks,
        "maintenance_docks": maintenance_docks,
        "total_docks": len(docks),
        "occupied_dock_labels": occupied_dock_labels,
        "active_stations": active_stations,
        "maintenance_stations": maintenance_stations,
        "total_stations": len(packing_stations),
        "low_stock_items": low_stock_items,
        "total_inventory_units": int(total_inventory_units or 0),
        "pending_restocks": int(pending_restocks or 0),
        "free_space_label": free_space_label,
        "busy_space_label": busy_space_label,
        "recent_returns": recent_returns,
        "pending_returns": pending_returns,
        "completed_returns": completed_returns,
        "avg_daily_orders": avg_daily_orders,
        "projected_orders": projected_orders,
        "suggested_staff": suggested_staff,
        "facts": facts,
    }


def _warehouse_overview_message(snapshot: dict) -> str:
    warehouse = snapshot["warehouse"]
    return (
        f"Warehouse **{warehouse.name}** snapshot:\n"
        f"- Active orders: **{snapshot['active_orders']}**\n"
        f"- Awaiting warehouse action: **{snapshot['pending_orders']}**\n"
        f"- Picking / packing now: **{snapshot['picking_orders']}**\n"
        f"- Ready for dispatch: **{snapshot['ready_for_dispatch']}**\n"
        f"- Staff available: **{snapshot['available_staff']}/{snapshot['total_staff']}**\n"
        f"- Free docks: **{snapshot['free_docks']}/{snapshot['total_docks']}**"
    )


def _warehouse_capacity_message(snapshot: dict) -> str:
    return (
        f"Best free space right now: **{snapshot['free_space_label']}**.\n"
        f"Most loaded area: **{snapshot['busy_space_label']}**.\n"
        f"Free docks: **{snapshot['free_docks']}/{snapshot['total_docks']}**. "
        f"Active orders on the warehouse floor: **{snapshot['active_orders']}**."
    )


def _warehouse_staff_message(snapshot: dict) -> str:
    available_line = ", ".join(snapshot["available_names"]) if snapshot["available_names"] else "No unassigned staff listed"
    on_field_line = ", ".join(snapshot["on_field_names"]) if snapshot["on_field_names"] else "No staff currently on field"
    return (
        f"Staff status right now:\n"
        f"- Available: **{snapshot['available_staff']}**\n"
        f"- Assigned on floor: **{snapshot['assigned_staff']}**\n"
        f"- On field: **{snapshot['on_field_staff']}**\n"
        f"- Off duty: **{snapshot['off_duty_staff']}**\n"
        f"- Available names: {available_line}\n"
        f"- On-field names: {on_field_line}"
    )


def _warehouse_workload_message(snapshot: dict) -> str:
    return (
        f"Tomorrow's workload forecast:\n"
        f"- 7-day average inbound volume: **{snapshot['avg_daily_orders']}** orders/day\n"
        f"- Current active pipeline: **{snapshot['active_orders']}** orders\n"
        f"- Projected tomorrow load: **{snapshot['projected_orders']}** orders\n"
        f"- Suggested active floor staff: **{snapshot['suggested_staff']}**\n"
        f"- Available now: **{snapshot['available_staff']}**"
    )


def _warehouse_pending_orders_message(snapshot: dict) -> str:
    lines = [
        f"Orders needing warehouse attention: **{snapshot['pending_orders']}**.",
        f"Picking / packing in progress: **{snapshot['picking_orders']}**. Ready for dispatch: **{snapshot['ready_for_dispatch']}**.",
    ]
    if snapshot["recent_orders"]:
        lines.append("Recent warehouse orders:")
        for order in snapshot["recent_orders"][:5]:
            lines.append(
                f"- {order.tracking_code}: {order.status} | Stage: {order.warehouse_substatus or 'N/A'}"
            )
    return "\n".join(lines)


def _warehouse_returns_message(snapshot: dict) -> str:
    lines = [
        f"Returns / damage snapshot: **{snapshot['pending_returns']}** pending gradings and **{snapshot['completed_returns']}** completed in the latest batch.",
    ]
    if snapshot["recent_returns"]:
        lines.append("Latest graded returns:")
        for grading in snapshot["recent_returns"][:5]:
            lines.append(
                f"- {grading.rma_code}: {grading.item_condition} -> {grading.disposition} | Status: {grading.status}"
            )
    else:
        lines.append("No recent return gradings found for this warehouse.")
    return "\n".join(lines)


def _warehouse_dock_message(snapshot: dict) -> str:
    lines = [
        f"Loading dock status: **{snapshot['free_docks']}** free, **{snapshot['occupied_docks']}** occupied, **{snapshot['maintenance_docks']}** under maintenance.",
    ]
    if snapshot["occupied_dock_labels"]:
        lines.append("Occupied docks:")
        lines.extend(f"- {label}" for label in snapshot["occupied_dock_labels"])
    else:
        lines.append("All tracked docks are currently free.")
    return "\n".join(lines)


def _warehouse_inventory_message(snapshot: dict) -> str:
    lines = [
        f"Inventory health: **{snapshot['total_inventory_units']}** units on hand, **{len(snapshot['low_stock_items'])}** low-stock SKUs, **{snapshot['pending_restocks']}** pending restock requests.",
    ]
    if snapshot["low_stock_items"]:
        lines.append("Most urgent low-stock items:")
        for item in snapshot["low_stock_items"]:
            lines.append(
                f"- {item.name} ({item.sku}): {item.quantity_on_hand} left vs safety stock {item.safety_stock}"
            )
    else:
        lines.append("No SKUs are currently below safety stock.")
    return "\n".join(lines)


async def _build_logistics_manager_snapshot(ro_db: AsyncSession) -> dict:
    finance_summary = await get_finance_summary(ro_db)

    drivers_result = await ro_db.execute(
        select(LogisticsDriverProfile, User.name, Warehouse.name)
        .join(User, User.id == LogisticsDriverProfile.user_id)
        .outerjoin(Warehouse, Warehouse.id == LogisticsDriverProfile.warehouse_id)
        .order_by(User.name.asc())
    )
    driver_rows = drivers_result.all()

    vehicles_result = await ro_db.execute(
        select(LogisticsVehicle, Warehouse.name, User.name)
        .outerjoin(Warehouse, Warehouse.id == LogisticsVehicle.warehouse_id)
        .outerjoin(User, User.id == LogisticsVehicle.assigned_driver_id)
        .order_by(LogisticsVehicle.code.asc())
    )
    vehicle_rows = vehicles_result.all()

    low_stock_result = await ro_db.execute(
        select(InventoryItem, Warehouse.name)
        .outerjoin(Warehouse, Warehouse.id == InventoryItem.warehouse_id)
        .where(InventoryItem.quantity_on_hand <= InventoryItem.safety_stock)
        .order_by((InventoryItem.safety_stock - InventoryItem.quantity_on_hand).desc(), InventoryItem.name.asc())
        .limit(5)
    )
    low_stock_rows = low_stock_result.all()

    pending_restocks = int(
        (
            await ro_db.execute(
                select(func.count(RestockRequest.id)).where(
                    RestockRequest.status.in_(["PENDING", "OPEN", "REQUESTED"])
                )
            )
        ).scalar_one()
        or 0
    )

    total_inventory_units = int(
        (
            await ro_db.execute(
                select(func.coalesce(func.sum(InventoryItem.quantity_on_hand), 0))
            )
        ).scalar_one()
        or 0
    )

    alerts_result = await ro_db.execute(
        select(LogisticsAlert, Warehouse.name)
        .outerjoin(Warehouse, Warehouse.id == LogisticsAlert.warehouse_id)
        .where(LogisticsAlert.is_active.is_(True))
        .order_by(LogisticsAlert.created_at.desc())
        .limit(5)
    )
    alert_rows = alerts_result.all()

    returns_result = await ro_db.execute(
        select(LogisticsReturnCase, Warehouse.name)
        .outerjoin(Warehouse, Warehouse.id == LogisticsReturnCase.warehouse_id)
        .order_by(LogisticsReturnCase.created_at.desc())
        .limit(5)
    )
    return_rows = returns_result.all()

    stats_result = await ro_db.execute(
        select(LogisticsDailyStats)
        .where(LogisticsDailyStats.warehouse_id.is_(None))
        .order_by(LogisticsDailyStats.stat_date.desc())
        .limit(7)
    )
    stats_rows = list(reversed(stats_result.scalars().all()))

    top_hubs_result = await ro_db.execute(
        select(Warehouse.name, LogisticsDailyStats.revenue, LogisticsDailyStats.orders_count)
        .join(Warehouse, Warehouse.id == LogisticsDailyStats.warehouse_id)
        .order_by(LogisticsDailyStats.stat_date.desc(), LogisticsDailyStats.revenue.desc())
        .limit(3)
    )
    top_hub_rows = top_hubs_result.all()

    pending_orders = int(
        (
            await ro_db.execute(
                select(func.count(Order.id)).where(
                    Order.status.in_(["DRAFT", "CONFIRMED", "ASSIGNED"])
                )
            )
        ).scalar_one()
        or 0
    )
    active_deliveries = int(
        (
            await ro_db.execute(
                select(func.count(Order.id)).where(Order.status == "IN_TRANSIT")
            )
        ).scalar_one()
        or 0
    )
    active_hubs = int(
        (
            await ro_db.execute(
                select(func.count(Warehouse.id)).where(Warehouse.is_active.is_(True))
            )
        ).scalar_one()
        or 0
    )

    driver_status_counts: dict[str, int] = {}
    for profile, _, _ in driver_rows:
        key = (profile.status or "unknown").strip().lower()
        driver_status_counts[key] = driver_status_counts.get(key, 0) + 1

    vehicle_status_counts: dict[str, int] = {}
    for vehicle, _, _ in vehicle_rows:
        key = (vehicle.status or "unknown").strip().lower()
        vehicle_status_counts[key] = vehicle_status_counts.get(key, 0) + 1

    revenue_by_day = finance_summary.get("revenue_by_day") or []
    today_revenue = float(stats_rows[-1].revenue) if stats_rows else float(revenue_by_day[-1].get("revenue", 0.0) if revenue_by_day else 0.0)
    seven_day_revenue = (
        round(sum(float(row.revenue or 0) for row in stats_rows), 2)
        if stats_rows
        else round(sum(float(item.get("revenue", 0.0) or 0.0) for item in revenue_by_day[-7:]), 2)
    )
    daily_average = round(seven_day_revenue / len(stats_rows), 2) if stats_rows else 0.0
    revenue_forecast = round(daily_average * 1.05, 2) if daily_average else 0.0
    active_alerts = len(alert_rows)
    open_returns = sum(1 for item, _ in return_rows if _normalize_text(item.status) not in {"completed", "closed", "approved"})
    total_expenses = float(finance_summary.get("total_expenses", 0.0) or 0.0)
    pending_cod = float(finance_summary.get("pending_cod", 0.0) or 0.0)
    total_payroll_due = float(finance_summary.get("total_payroll_due", 0.0) or 0.0)
    net_profit = float(finance_summary.get("net_profit", 0.0) or 0.0)

    facts = [
        f"Active hubs: {active_hubs}",
        f"Pending orders needing action: {pending_orders}",
        f"Active deliveries in transit: {active_deliveries}",
        f"Tracked drivers: {len(driver_rows)}",
        f"Tracked vehicles: {len(vehicle_rows)}",
        f"Active alerts: {active_alerts}",
        f"Open return or RMA cases in the latest batch: {open_returns}",
        f"Inventory units on hand: {total_inventory_units}",
        f"Pending restock requests: {pending_restocks}",
        f"Network revenue today: INR {today_revenue:,.2f}",
        f"Network 7 day revenue: INR {seven_day_revenue:,.2f}",
        f"Projected next-day revenue from trailing 7 day average: INR {revenue_forecast:,.2f}",
        f"Pending COD exposure: INR {pending_cod:,.2f}",
        f"Outstanding payroll due: INR {total_payroll_due:,.2f}",
        f"Total expenses: INR {total_expenses:,.2f}",
        f"Net profit: INR {net_profit:,.2f}",
    ]

    return {
        "finance_summary": finance_summary,
        "drivers": driver_rows,
        "vehicles": vehicle_rows,
        "low_stock_items": low_stock_rows,
        "pending_restocks": pending_restocks,
        "total_inventory_units": total_inventory_units,
        "alerts": alert_rows,
        "returns": return_rows,
        "stats": stats_rows,
        "top_hubs": top_hub_rows,
        "pending_orders": pending_orders,
        "active_deliveries": active_deliveries,
        "active_hubs": active_hubs,
        "driver_status_counts": driver_status_counts,
        "vehicle_status_counts": vehicle_status_counts,
        "today_revenue": today_revenue,
        "seven_day_revenue": seven_day_revenue,
        "revenue_forecast": revenue_forecast,
        "pending_cod": pending_cod,
        "total_payroll_due": total_payroll_due,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "facts": facts,
    }


def _logistics_dashboard_message(snapshot: dict) -> str:
    lines = [
        f"Network overview: **{snapshot['active_hubs']}** active hubs, **{snapshot['pending_orders']}** pending orders, **{snapshot['active_deliveries']}** deliveries in transit, and **{len(snapshot['alerts'])}** active alerts.",
        f"Live coverage: **{len(snapshot['drivers'])}** tracked drivers and **{len(snapshot['vehicles'])}** tracked vehicles across the network.",
        f"Revenue snapshot: **INR {snapshot['today_revenue']:,.2f}** today and **INR {snapshot['seven_day_revenue']:,.2f}** over the last 7 days.",
    ]
    if snapshot["top_hubs"]:
        lines.append("Top-performing hubs in the latest revenue snapshot:")
        for hub_name, revenue, orders_count in snapshot["top_hubs"][:3]:
            lines.append(f"- {hub_name}: INR {float(revenue or 0):,.2f} revenue from {int(orders_count or 0)} orders")
    if snapshot["alerts"]:
        alert, warehouse_name = snapshot["alerts"][0]
        lines.append(f"Most recent active alert: {alert.title} ({alert.severity}) at {warehouse_name or 'network scope'}")
    return "\n".join(lines)


def _logistics_driver_status_message(snapshot: dict) -> str:
    active = snapshot["driver_status_counts"].get("active", 0)
    idle = snapshot["driver_status_counts"].get("idle", 0)
    off_duty = snapshot["driver_status_counts"].get("off duty", 0) + snapshot["driver_status_counts"].get("offline", 0)
    lines = [
        f"Driver status snapshot: **{len(snapshot['drivers'])}** tracked drivers, **{active}** active, **{idle}** idle, and **{off_duty}** off duty/offline.",
    ]
    if snapshot["drivers"]:
        lines.append("Current driver highlights:")
        for profile, driver_name, warehouse_name in snapshot["drivers"][:5]:
            job = profile.current_job or "No active job"
            location = profile.current_location or (warehouse_name or "Location unavailable")
            lines.append(f"- {driver_name}: {profile.status} at {location} · Job: {job}")
    else:
        lines.append("No driver profiles are available right now.")
    return "\n".join(lines)


def _logistics_fleet_status_message(snapshot: dict) -> str:
    available = snapshot["vehicle_status_counts"].get("available", 0)
    active = snapshot["vehicle_status_counts"].get("active", 0)
    maintenance = snapshot["vehicle_status_counts"].get("maintenance", 0)
    lines = [
        f"Fleet status: **{len(snapshot['vehicles'])}** vehicles tracked, **{available}** available, **{active}** active, and **{maintenance}** in maintenance.",
    ]
    if snapshot["vehicles"]:
        lines.append("Vehicle highlights:")
        for vehicle, warehouse_name, driver_name in snapshot["vehicles"][:5]:
            driver_label = driver_name or "Unassigned"
            lines.append(
                f"- {vehicle.code}: {vehicle.status} · {vehicle.vehicle_type} · Driver: {driver_label} · Hub: {warehouse_name or 'Unassigned'}"
            )
    else:
        lines.append("No fleet vehicles are available right now.")
    return "\n".join(lines)


def _logistics_inventory_message(snapshot: dict) -> str:
    lines = [
        f"Inventory pressure: **{snapshot['total_inventory_units']}** units on hand, **{len(snapshot['low_stock_items'])}** urgent low-stock SKUs, and **{snapshot['pending_restocks']}** pending restock requests.",
    ]
    if snapshot["low_stock_items"]:
        lines.append("Most urgent low-stock items:")
        for item, warehouse_name in snapshot["low_stock_items"][:5]:
            lines.append(
                f"- {item.name} ({item.sku}) at {warehouse_name or 'Unknown hub'}: {item.quantity_on_hand} left vs safety stock {item.safety_stock}"
            )
    else:
        lines.append("No SKUs are currently below safety stock.")
    return "\n".join(lines)


def _logistics_returns_message(snapshot: dict) -> str:
    open_returns = sum(
        1 for item, _ in snapshot["returns"] if _normalize_text(item.status) not in {"completed", "closed", "approved"}
    )
    lines = [
        f"Returns and RMA snapshot: **{open_returns}** open cases in the latest batch and **{len(snapshot['returns'])}** recent cases reviewed.",
    ]
    if snapshot["returns"]:
        lines.append("Latest return cases:")
        for item, warehouse_name in snapshot["returns"][:5]:
            lines.append(
                f"- {item.reference_code}: {item.status} · {item.reason} · Refund INR {float(item.refund_amount or 0):,.2f} · Hub: {warehouse_name or 'Unknown'}"
            )
    else:
        lines.append("No recent return cases are available.")
    return "\n".join(lines)


def _logistics_revenue_message(snapshot: dict) -> str:
    lines = [
        f"Revenue outlook: **INR {snapshot['today_revenue']:,.2f}** booked today and **INR {snapshot['seven_day_revenue']:,.2f}** over the trailing 7 days.",
        f"Next-day forecast from the recent run-rate is **INR {snapshot['revenue_forecast']:,.2f}**.",
        f"Finance position: **INR {snapshot['total_expenses']:,.2f}** total expenses, **INR {snapshot['pending_cod']:,.2f}** pending COD, and **INR {snapshot['total_payroll_due']:,.2f}** payroll due.",
        f"Current net position is **INR {snapshot['net_profit']:,.2f}**.",
    ]
    if snapshot["stats"]:
        lines.append("Recent network revenue trend:")
        for row in snapshot["stats"][-5:]:
            lines.append(
                f"- {row.stat_date}: INR {float(row.revenue or 0):,.2f} revenue · {int(row.orders_count or 0)} orders"
            )
    else:
        lines.append("No network revenue history is available yet.")
    return "\n".join(lines)


async def _try_handle_logistic_manager_shortcuts(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    chat_context: str | None,
) -> ChatResponse | None:
    if not _is_logistic_manager_chat_context(user, chat_context):
        return None

    snapshot = await _build_logistics_manager_snapshot(ro_db)
    msg = (user_message or "").strip().lower()
    base_message = None

    if _is_logistics_driver_question(msg):
        base_message = _logistics_driver_status_message(snapshot)
    elif _is_logistics_fleet_question(msg):
        base_message = _logistics_fleet_status_message(snapshot)
    elif _is_logistics_inventory_question(msg):
        base_message = _logistics_inventory_message(snapshot)
    elif _is_logistics_returns_question(msg):
        base_message = _logistics_returns_message(snapshot)
    elif _is_logistics_revenue_question(msg):
        base_message = _logistics_revenue_message(snapshot)
    elif _is_logistics_dashboard_question(msg):
        base_message = _logistics_dashboard_message(snapshot)

    if not base_message:
        return None

    assistant_message = await _answer_with_grounded_ai(
        user=user,
        user_message=user_message,
        fallback_message=base_message,
        grounding_facts=snapshot["facts"] + [base_message],
    )
    await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
    await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent="db_query",
        sql_generated=None,
    )


async def _build_dispatcher_snapshot(ro_db: AsyncSession) -> dict:
    """Fetch live operational data for the dispatcher AI context."""

    # Orders needing driver assignment (released / confirmed, vehicle assigned, no driver yet)
    pending_dispatch_result = await ro_db.execute(
        select(Order)
        .where(
            Order.status.in_(["CONFIRMED", "ASSIGNED"]),
            Order.assigned_driver_id.is_(None),
            Order.assigned_vehicle_id.isnot(None),
        )
        .order_by(Order.created_at.asc())
        .limit(10)
    )
    pending_dispatch = list(pending_dispatch_result.scalars().all())

    # Active in-transit orders
    in_transit_result = await ro_db.execute(
        select(Order, User.name)
        .join(User, User.id == Order.assigned_driver_id, isouter=True)
        .where(Order.status == "IN_TRANSIT")
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    in_transit_rows = in_transit_result.all()

    # Driver availability
    driver_result = await ro_db.execute(
        select(LogisticsDriverProfile, User.name)
        .join(User, User.id == LogisticsDriverProfile.user_id)
        .order_by(User.name.asc())
    )
    driver_rows = driver_result.all()

    # Free drivers (Active status, no current job)
    free_drivers = [
        (profile, name)
        for profile, name in driver_rows
        if (profile.status or "").lower() == "active" and not profile.current_job
    ]

    # Vehicles
    vehicle_result = await ro_db.execute(
        select(LogisticsVehicle)
        .where(LogisticsVehicle.status == "Active")
        .order_by(LogisticsVehicle.code.asc())
        .limit(20)
    )
    active_vehicles = list(vehicle_result.scalars().all())

    # SLA at risk (orders past scheduled time, not yet delivered)
    now = datetime.now(UTC)
    sla_risk_result = await ro_db.execute(
        select(Order)
        .where(
            Order.status.in_(["CONFIRMED", "ASSIGNED", "IN_TRANSIT"]),
            Order.scheduled_at < now,
        )
        .order_by(Order.scheduled_at.asc())
        .limit(5)
    )
    sla_risk = list(sla_risk_result.scalars().all())

    # Today deliveries
    today_count = int(
        (
            await ro_db.execute(
                select(func.count(Order.id)).where(
                    Order.status == "DELIVERED",
                    func.date(Order.delivered_at) == func.current_date(),
                )
            )
        ).scalar_one()
        or 0
    )

    # Build facts list
    driver_status_counts: dict[str, int] = {}
    for profile, _ in driver_rows:
        key = (profile.status or "unknown").strip().lower()
        driver_status_counts[key] = driver_status_counts.get(key, 0) + 1

    facts = [
        f"Total drivers registered: {len(driver_rows)}",
        f"Free/available drivers right now: {len(free_drivers)}",
        f"Driver status breakdown: {', '.join(f'{k}: {v}' for k, v in driver_status_counts.items())}",
        f"Orders waiting for driver assignment: {len(pending_dispatch)}",
        f"Orders currently in transit: {len(in_transit_rows)}",
        f"Active vehicles available: {len(active_vehicles)}",
        f"SLA at risk (overdue): {len(sla_risk)}",
        f"Deliveries completed today: {today_count}",
    ]
    if free_drivers:
        facts.append("Free drivers: " + ", ".join(name for _, name in free_drivers[:5]))
    if pending_dispatch:
        facts.append(
            "Top pending orders needing drivers: "
            + ", ".join(
                f"{o.tracking_code or str(o.id)[:8]} ({o.pickup_addr or 'TBD'} → {o.delivery_addr or 'TBD'})"
                for o in pending_dispatch[:3]
            )
        )
    if sla_risk:
        facts.append(
            "SLA-at-risk orders: "
            + ", ".join(
                f"{o.tracking_code or str(o.id)[:8]} (scheduled {o.scheduled_at.strftime('%H:%M') if o.scheduled_at else 'N/A'})"
                for o in sla_risk[:3]
            )
        )

    return {
        "pending_dispatch": pending_dispatch,
        "in_transit_rows": in_transit_rows,
        "driver_rows": driver_rows,
        "free_drivers": free_drivers,
        "active_vehicles": active_vehicles,
        "sla_risk": sla_risk,
        "today_count": today_count,
        "driver_status_counts": driver_status_counts,
        "facts": facts,
    }


def _is_dispatcher_pending_question(msg: str) -> bool:
    return any(k in msg for k in ["pending order", "ready order", "waiting for driver", "need driver", "unassigned order", "released order", "dispatch queue"])


def _is_dispatcher_driver_question(msg: str) -> bool:
    return any(k in msg for k in ["driver", "who is free", "available driver", "best driver", "suggest driver", "free driver", "driver available", "driver status"])


def _is_dispatcher_fleet_question(msg: str) -> bool:
    return any(k in msg for k in ["vehicle", "fleet", "truck", "van", "lcv"])


def _is_dispatcher_in_transit_question(msg: str) -> bool:
    return any(k in msg for k in ["in transit", "active order", "on route", "in delivery", "currently delivering", "active delivery"])


def _is_dispatcher_sla_question(msg: str) -> bool:
    return any(k in msg for k in ["sla", "overdue", "late", "delay", "at risk", "behind schedule"])


def _dispatcher_pending_message(snapshot: dict) -> str:
    orders = snapshot["pending_dispatch"]
    if not orders:
        return "No orders are currently waiting for driver assignment. All released orders are covered."
    lines = [f"**{len(orders)} order(s)** waiting for driver assignment right now:"]
    for o in orders[:5]:
        lines.append(
            f"- **{o.tracking_code or str(o.id)[:8]}** | {o.pickup_addr or 'TBD'} → {o.delivery_addr or 'TBD'} | Created: {o.created_at.strftime('%d %b %H:%M') if o.created_at else 'N/A'}"
        )
    return "\n".join(lines)


def _dispatcher_driver_message(snapshot: dict) -> str:
    free = snapshot["free_drivers"]
    total = len(snapshot["driver_rows"])
    counts = snapshot["driver_status_counts"]
    lines = [
        f"**{total}** drivers registered. **{len(free)}** are currently free and available.",
        f"Status breakdown: {', '.join(f'{k.capitalize()}: {v}' for k, v in counts.items())}",
    ]
    if free:
        lines.append("Free drivers (best candidates for assignment):")
        for profile, name in free[:5]:
            lines.append(
                f"- **{name}** | Location: {profile.current_location or 'Unknown'} | Efficiency: {profile.efficiency_score}%"
            )
    else:
        lines.append("No drivers are currently free. All drivers are on jobs or off-shift.")
    pending = snapshot["pending_dispatch"]
    if pending and free:
        lines.append(
            f"\nTop match: assign **{free[0][1]}** to order **{pending[0].tracking_code or str(pending[0].id)[:8]}** "
            f"({pending[0].pickup_addr or 'TBD'} → {pending[0].delivery_addr or 'TBD'})."
        )
    return "\n".join(lines)


def _dispatcher_fleet_message(snapshot: dict) -> str:
    vehicles = snapshot["active_vehicles"]
    if not vehicles:
        return "No active vehicles found in the fleet right now."
    lines = [f"**{len(vehicles)}** active vehicles available:"]
    for v in vehicles[:8]:
        lines.append(
            f"- **{v.code}** ({v.vehicle_type}) | Plate: {v.license_plate or 'N/A'} | Status: {v.status}"
        )
    return "\n".join(lines)


def _dispatcher_in_transit_message(snapshot: dict) -> str:
    rows = snapshot["in_transit_rows"]
    if not rows:
        return "No orders are currently in transit."
    lines = [f"**{len(rows)}** order(s) currently in transit:"]
    for o, driver_name in rows[:5]:
        lines.append(
            f"- **{o.tracking_code or str(o.id)[:8]}** | Driver: {driver_name or 'Unassigned'} | {o.pickup_addr or 'TBD'} → {o.delivery_addr or 'TBD'}"
        )
    return "\n".join(lines)


def _dispatcher_sla_message(snapshot: dict) -> str:
    at_risk = snapshot["sla_risk"]
    today = snapshot["today_count"]
    lines = [f"Deliveries completed today: **{today}**."]
    if at_risk:
        lines.append(f"**{len(at_risk)}** order(s) are past their scheduled delivery window (SLA at risk):")
        for o in at_risk:
            lines.append(
                f"- **{o.tracking_code or str(o.id)[:8]}** | Status: {o.status} | Scheduled: {o.scheduled_at.strftime('%d %b %H:%M') if o.scheduled_at else 'N/A'}"
            )
    else:
        lines.append("No SLA breaches detected. All active orders are within their delivery windows.")
    return "\n".join(lines)


async def _try_handle_dispatcher_shortcuts(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    chat_context: str | None,
) -> "ChatResponse | None":
    if not _is_dispatcher_chat_context(user, chat_context):
        return None

    snapshot = await _build_dispatcher_snapshot(ro_db)
    msg = (user_message or "").strip().lower()
    base_message = None

    if _is_dispatcher_pending_question(msg):
        base_message = _dispatcher_pending_message(snapshot)
    elif _is_dispatcher_driver_question(msg):
        base_message = _dispatcher_driver_message(snapshot)
    elif _is_dispatcher_fleet_question(msg):
        base_message = _dispatcher_fleet_message(snapshot)
    elif _is_dispatcher_in_transit_question(msg):
        base_message = _dispatcher_in_transit_message(snapshot)
    elif _is_dispatcher_sla_question(msg):
        base_message = _dispatcher_sla_message(snapshot)

    if not base_message:
        return None

    assistant_message = await _answer_with_grounded_ai(
        user=user,
        user_message=user_message,
        fallback_message=base_message,
        grounding_facts=snapshot["facts"] + [base_message],
    )
    await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
    await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
    await db.commit()
    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent="db_query",
        sql_generated=None,
    )


async def _try_handle_warehouse_shortcuts(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    chat_context: str | None,
    snapshot: dict | None = None,
) -> ChatResponse | None:
    if not _is_warehouse_chat_context(user, chat_context):
        return None

    snapshot = snapshot or await _build_warehouse_snapshot(ro_db, user)
    if not snapshot:
        return None

    msg = (user_message or "").strip().lower()
    base_message = None
    intent = "general"

    if _is_warehouse_workload_question(msg):
        base_message = _warehouse_workload_message(snapshot)
    elif _is_warehouse_staff_question(msg):
        base_message = _warehouse_staff_message(snapshot)
    elif _is_warehouse_capacity_question(msg):
        base_message = _warehouse_capacity_message(snapshot)
    elif _is_warehouse_pending_question(msg):
        base_message = _warehouse_pending_orders_message(snapshot)
        intent = "db_query"
    elif _is_warehouse_returns_question(msg):
        base_message = _warehouse_returns_message(snapshot)
        intent = "db_query"
    elif _is_warehouse_dock_question(msg):
        base_message = _warehouse_dock_message(snapshot)
    elif _is_warehouse_inventory_question(msg):
        base_message = _warehouse_inventory_message(snapshot)
        intent = "db_query"
    elif _is_warehouse_overview_question(msg):
        base_message = _warehouse_overview_message(snapshot)

    if not base_message:
        return None

    assistant_message = await _answer_with_grounded_ai(
        user=user,
        user_message=user_message,
        fallback_message=base_message,
        grounding_facts=snapshot["facts"] + [base_message],
    )
    await _persist_message(db, session_id, user.id, "user", user_message, intent)
    await _persist_message(db, session_id, user.id, "assistant", assistant_message, intent)
    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent=intent,
        sql_generated=None,
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
        return shortcut

    # Deterministic dashboard help shortcuts for general product guidance.
    help_shortcut = await _try_handle_dashboard_help_shortcuts(
        db=db,
        user=user,
        session_id=session_id,
        user_message=effective_user_message,
        chat_context=chat_context,
    )
    if help_shortcut is not None:
        return help_shortcut

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


# ── Function Call Handler ─────────────────────────────────────────────────────


async def _handle_function_call(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    linked_order_meta: dict[str, str] | None,
    linked_order: Order | None,
    client,
    contents: list,
    response,
    function_call,
    system_instruction: str,
) -> ChatResponse:
    """
    Handle a Gemini function call (execute_sql_query).

    Validates the SQL, executes on read-only session, feeds results back to Gemini.
    Uses the new google-genai SDK pattern for multi-turn function calling.
    """
    fn_name = function_call.name
    fn_args = dict(function_call.args) if function_call.args else {}

    logger.info(f"Gemini function call: {fn_name}({fn_args})")

    if fn_name != "execute_sql_query":
        logger.warning(f"Unknown function call: {fn_name}")
        error_msg = "I tried to use an unknown tool. Let me try answering directly."
        await _persist_message(
            db,
            session_id,
            user.id,
            "user",
            user_message,
            "error",
            linked_order_meta=linked_order_meta,
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

    raw_sql = fn_args.get("sql_query", "")

    # ── Validate SQL ──────────────────────────────────────────────────────
    try:
        validated_sql = validate_sql(raw_sql)
    except SQLValidationError as e:
        logger.warning(f"SQL validation failed: {e} | SQL: {raw_sql}")
        # Build the function response with error and send back to Gemini
        error_result = {"error": f"Query rejected: {str(e)}"}
        try:
            # Append the model's function call + our error response, then re-call
            follow_up_contents = contents + [
                response.candidates[0].content,
                types.Content(
                    role="tool",
                    parts=[
                        types.Part.from_function_response(
                            name="execute_sql_query",
                            response=error_result,
                        )
                    ],
                ),
            ]
            follow_up = await generate_with_fallback(
                contents=follow_up_contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[EXECUTE_SQL_TOOL],
                ),
            )
            assistant_message = _safe_message_text(
                follow_up.text,
                "I could not format the validation error response. Please rephrase your request.",
            )
        except Exception:
            assistant_message = (
                f"I tried to query the database but the query was rejected: {str(e)}. "
                "Could you rephrase your question?"
            )

        await _persist_message(
            db, session_id, user.id, "user", user_message, "error",
            sql_generated=raw_sql,
            linked_order_meta=linked_order_meta,
        )
        await _persist_message(
            db, session_id, user.id, "assistant", assistant_message, "error",
            sql_generated=raw_sql,
            linked_order_meta=linked_order_meta,
        )
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="error",
            sql_generated=raw_sql,
            linked_order_id=linked_order.id if linked_order else None,
            linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
        )

    # ── Execute SQL on read-only session ──────────────────────────────────
    role_scoped_sql = validated_sql
    try:
        role_scoped_sql = _scope_sql_for_user(validated_sql, user)
    except SQLValidationError as e:
        logger.warning(f"Role scope validation failed: {e} | SQL: {validated_sql}")
        assistant_message = (
            "I can only access data for your own account in this assistant. "
            "Please ask using your own orders, shipments, or payments."
        )
        await _persist_message(
            db, session_id, user.id, "user", user_message, "error",
            sql_generated=validated_sql,
            linked_order_meta=linked_order_meta,
        )
        await _persist_message(
            db, session_id, user.id, "assistant", assistant_message, "error",
            sql_generated=validated_sql,
            linked_order_meta=linked_order_meta,
        )
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="error",
            sql_generated=validated_sql,
            linked_order_id=linked_order.id if linked_order else None,
            linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
        )

    try:
        result = await ro_db.execute(text(role_scoped_sql))
        rows = result.fetchall()
        columns = list(result.keys())

        # Serialize results to JSON-friendly format
        query_result = [dict(zip(columns, row)) for row in rows]

        # Convert non-serializable types (UUID, datetime, etc.)
        query_result = _make_json_serializable(query_result)

        logger.info(f"SQL executed successfully: {len(query_result)} rows returned")

    except Exception as e:
        logger.error(f"SQL execution error: {e} | SQL: {validated_sql}")
        error_result = {"error": f"Query execution failed: {str(e)}"}
        try:
            follow_up_contents = contents + [
                response.candidates[0].content,
                types.Content(
                    role="tool",
                    parts=[
                        types.Part.from_function_response(
                            name="execute_sql_query",
                            response=error_result,
                        )
                    ],
                ),
            ]
            follow_up = await generate_with_fallback(
                contents=follow_up_contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[EXECUTE_SQL_TOOL],
                ),
            )
            assistant_message = _safe_message_text(
                follow_up.text,
                "I could not run that data query due to a database mismatch, but I can still help. "
                "Try: 'Where is my latest order?', 'Show my dashboard summary', or 'What is my wallet balance?'."
            )
        except Exception:
            assistant_message = (
                "I tried to query the database but encountered an execution error. "
                "Could you rephrase your question?"
            )

        await _persist_message(
            db, session_id, user.id, "user", user_message, "error",
            sql_generated=role_scoped_sql,
            linked_order_meta=linked_order_meta,
        )
        await _persist_message(
            db, session_id, user.id, "assistant", assistant_message, "error",
            sql_generated=role_scoped_sql,
            linked_order_meta=linked_order_meta,
        )
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="error",
            sql_generated=role_scoped_sql,
            linked_order_id=linked_order.id if linked_order else None,
            linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
        )

    # ── Feed results back to Gemini ───────────────────────────────────────
    function_response_data = {
        "columns": columns,
        "row_count": len(query_result),
        "data": query_result,
    }

    try:
        # Build multi-turn: original contents + model's function call + our result
        follow_up_contents = contents + [
            response.candidates[0].content,
            types.Content(
                role="tool",
                parts=[
                    types.Part.from_function_response(
                        name="execute_sql_query",
                        response=function_response_data,
                    )
                ],
            ),
        ]
        follow_up = await generate_with_fallback(
            contents=follow_up_contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[EXECUTE_SQL_TOOL],
            ),
        )
        assistant_message = _safe_message_text(
            follow_up.text,
            _format_results_fallback(query_result, columns),
        )
    except Exception as e:
        logger.error(f"Gemini response error after function call: {e}")
        # Fallback: format results directly
        assistant_message = _format_results_fallback(query_result, columns)

    # ── Persist messages ──────────────────────────────────────────────────
    await _persist_message(
        db, session_id, user.id, "user", user_message, "db_query",
        sql_generated=role_scoped_sql, query_result=query_result,
        linked_order_meta=linked_order_meta,
    )
    await _persist_message(
        db, session_id, user.id, "assistant", assistant_message, "db_query",
        sql_generated=role_scoped_sql,
        linked_order_meta=linked_order_meta,
    )

    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent="db_query",
        sql_generated=role_scoped_sql,
        linked_order_id=linked_order.id if linked_order else None,
        linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
    )


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


async def _local_fallback_response(
    ro_db: AsyncSession,
    user: User,
    user_message: str,
    chat_context: str | None = None,
    warehouse_snapshot: dict | None = None,
) -> str | None:
    msg = (user_message or "").strip().lower()
    role = _role_name(user)
    noun = "shipment" if role == "VENDOR" else "order"

    # Greeting
    if msg in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}:
        first = user.name.split()[0] if user.name else "there"
        if _is_warehouse_chat_context(user, chat_context):
            return (
                f"Hi {first}! Ask me about queue pressure, staff availability, free space, docks, returns, or workload in your warehouse."
            )
        if role == "LOGISTIC_MANAGER":
            return (
                f"Hi {first}! Ask me about hub performance, driver status, fleet readiness, inventory pressure, alerts, returns, revenue, or network operations."
            )
        if role == "VENDOR":
            return f"Hi {first}! Ask me about your shipments, wallet balance, invoices, or anything about your account."
        return f"Hi {first}! Ask me about your orders, wallet balance, spending, or anything about your account."

    if _is_warehouse_chat_context(user, chat_context):
        snapshot = warehouse_snapshot or await _build_warehouse_snapshot(ro_db, user)
        if snapshot:
            if _is_warehouse_workload_question(msg):
                return _warehouse_workload_message(snapshot)
            if _is_warehouse_staff_question(msg):
                return _warehouse_staff_message(snapshot)
            if _is_warehouse_capacity_question(msg):
                return _warehouse_capacity_message(snapshot)
            if _is_warehouse_pending_question(msg):
                return _warehouse_pending_orders_message(snapshot)
            if _is_warehouse_returns_question(msg):
                return _warehouse_returns_message(snapshot)
            if _is_warehouse_dock_question(msg):
                return _warehouse_dock_message(snapshot)
            if _is_warehouse_inventory_question(msg):
                return _warehouse_inventory_message(snapshot)
            return _warehouse_overview_message(snapshot)

    if _is_logistic_manager_chat_context(user, chat_context):
        snapshot = await _build_logistics_manager_snapshot(ro_db)
        if _is_logistics_driver_question(msg):
            return _logistics_driver_status_message(snapshot)
        if _is_logistics_fleet_question(msg):
            return _logistics_fleet_status_message(snapshot)
        if _is_logistics_inventory_question(msg):
            return _logistics_inventory_message(snapshot)
        if _is_logistics_returns_question(msg):
            return _logistics_returns_message(snapshot)
        if _is_logistics_revenue_question(msg):
            return _logistics_revenue_message(snapshot)
        if _is_logistics_dashboard_question(msg):
            return _logistics_dashboard_message(snapshot)

    if _is_refund_question(msg):
        return await _self_service_refund_message(ro_db, user, role, user_message)

    if _is_knowledge_question(msg):
        knowledge_message = await _answer_from_retrieved_knowledge(ro_db, user, user_message)
        if knowledge_message:
            return knowledge_message

    if role == "VENDOR":
        if _is_wallet_balance_question(msg):
            return await _vendor_wallet_message(ro_db, user)
        if _is_analytics_section_question(msg):
            return await _vendor_analytics_message(ro_db, user)
        # Only fire the "raise a ticket" shortcut outside support_chat — inside support_chat
        # the AI should answer directly, not redirect to ticket creation.
        is_in_support_chat = (chat_context or "").strip().lower() == SUPPORT_CHAT_CONTEXT
        if not is_in_support_chat and _is_support_question(msg):
            return await _vendor_support_message(ro_db, user)
        if _is_recurring_data_question(msg):
            return await _vendor_recurring_orders_message(ro_db, user)

    if not _extract_tracking_code(user_message) and _is_order_status_list_question(msg, role):
        status_label, statuses = _extract_order_status_filter(msg)
        if status_label and statuses:
            return await _list_self_service_orders_by_status(
                ro_db=ro_db,
                user=user,
                role=role,
                status_label=status_label,
                statuses=statuses,
            )

    if _is_current_orders_question(msg, role):
        return await _list_current_self_service_orders(ro_db, user, role)

    # Tracking / order status
    order_keywords = ["where is my order", "where is my current order", "track my order", "order status",
                      "current order", "my shipment", "pending shipment", "show my shipment", "show my order",
                      "shipment status"]
    tracking_code = _extract_tracking_code(user_message)
    if tracking_code or any(k in msg for k in order_keywords):
        matched_order, requested_tracking_code = await _lookup_self_service_order(
            ro_db=ro_db,
            user=user,
            user_message=user_message,
        )
        if matched_order:
            return _format_self_service_order_message(
                matched_order,
                role=role,
                tracking_code=requested_tracking_code,
            )
        if requested_tracking_code:
            return f"I couldn't find {noun} **{requested_tracking_code}** in your account."
        return f"No {noun} found for your account yet."

    # Glossary questions — always answerable without AI
    if "bulk upload" in msg:
        return (
            "Bulk Upload lets you create many shipments at once by uploading a CSV or Excel file. "
            "Each row in the file represents one shipment with pickup, destination, and item details. "
            "Go to Bulk Upload in your dashboard to download the template and upload your file."
        )
    if any(k in msg for k in ["damage report", "what is damage"]):
        return (
            "A damage report is a record created when an item is found damaged during packing, transit, or delivery. "
            "It includes item details, remarks, and the stage where damage occurred."
        )
    if "analytics" in msg:
        if role == "LOGISTIC_MANAGER":
            return (
                "The logistics intelligence views show hub performance, revenue trends, fleet utilization, alert pressure, returns, and delivery outcomes across the network."
            )
        if role == "VENDOR":
            return (
                "The Analytics section shows monthly spend, shipment volume, success rate, "
                "and average order value for your vendor account."
            )
        return "The Analytics section shows booking volume, spend trends, and delivery outcomes for your account."
    if any(k in msg for k in ["what is quote", "what are quotes", "quote meaning", "quotation"]):
        return "A quote is the estimated cost shown before you confirm a booking, based on route, volume, labor, and packing."
    if "what is recurring" in msg or "what are recurring" in msg:
        return "Recurring shipments let you schedule automatic repeat deliveries on a weekly or monthly basis."
    if _is_wallet_balance_question(msg):
        return await _vendor_wallet_message(ro_db, user)
    if "wallet" in msg:
        return "Your wallet balance is shown in the header. You can top it up by clicking the balance amount. It is used to pay for orders automatically."
    if any(k in msg for k in ["how to track", "where to track", "tracking"]):
        return f"Track your {noun}s from the Orders/Shipments section in your dashboard. Click any {noun} to see live status updates."
    if any(k in msg for k in ["how to book", "book a move", "new booking", "create shipment"]):
        if role == "VENDOR":
            return "Go to Create Shipment in your vendor dashboard. Enter pickup, destination, cargo details, and confirm."
        return "Go to Book a Move in your dashboard. Enter pickup, destination, items, labor and packing options, then confirm."
    if "support" in msg:
        if role == "LOGISTIC_MANAGER":
            return (
                "Use Recovery Tickets, Communication, or escalation tools to coordinate follow-ups, exception handling, and human support across operations."
            )
        return (
            "Open the Help / Support section to raise a support ticket. "
            "You can describe shipment, invoice, or platform issues there."
        )

    # Generic fallback — role-aware
    if role == "VENDOR":
        return "I can answer questions about your shipments, wallet, invoices, spending history, and platform features. Ask me anything."
    if role == "LOGISTIC_MANAGER":
        return "I can answer questions about hub performance, driver and fleet status, inventory pressure, alerts, returns, revenue, and overall logistics operations."
    if role == "WAREHOUSE_MANAGER":
        return "I can answer questions about your warehouse operations, including queue pressure, staff availability, docks, returns, inventory pressure, and workload forecasts."
    if role == "DISPATCHER":
        return "I can answer questions about driver status, available drivers, pending orders, fleet vehicles, active trips, and SLA risk. Ask me anything."
    return "I can answer questions about your orders, wallet, spending history, quotes, and platform features. Ask me anything."


def _role_name(user: User) -> str:
    role = getattr(getattr(user, "role", None), "name", None)
    return str(role or "").upper()


def _extract_table_names_for_scope(sql: str) -> set[str]:
    pattern = r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    matches = re.findall(pattern, sql, re.IGNORECASE)
    tables: set[str] = set()
    for match in matches:
        name = match.lower().strip()
        if name not in {"select", "lateral", "unnest", "generate_series", "values"}:
            tables.add(name)
    return tables


def _contextualize_user_message(
    user_message: str,
    chat_context: str | None,
    warehouse_snapshot: dict | None = None,
    dispatcher_snapshot: dict | None = None,
    logistic_manager_snapshot: dict | None = None,
) -> str:
    normalized = (chat_context or "").strip().lower()

    if normalized in WAREHOUSE_CONTEXTS and warehouse_snapshot:
        snapshot_facts = warehouse_snapshot.get("facts", [])[:12]
        return (
            "Smart WMS context.\n"
            "Current warehouse grounding facts:\n"
            + "\n".join(f"- {fact}" for fact in snapshot_facts)
            + f"\n\nUser question: {user_message}"
        )

    if normalized in DISPATCHER_CONTEXTS and dispatcher_snapshot:
        snapshot_facts = dispatcher_snapshot.get("facts", [])[:10]
        return (
            "Smart Dispatcher context.\n"
            "Current dispatch grounding facts:\n"
            + "\n".join(f"- {fact}" for fact in snapshot_facts)
            + f"\n\nUser question: {user_message}"
        )

    if normalized in LOGISTIC_MANAGER_CONTEXTS and logistic_manager_snapshot:
        snapshot_facts = logistic_manager_snapshot.get("facts", [])[:16]
        return (
            "Reports & Command Center context.\n"
            "Live network operational grounding facts:\n"
            + "\n".join(f"- {fact}" for fact in snapshot_facts)
            + f"\n\nUser question: {user_message}"
        )

    return user_message


def _support_chat_order_snapshot(order: "Order") -> str:
    """Build a concise order fact-sheet to inject into the support chat system prompt."""
    status = (order.status or "UNKNOWN").upper()
    substatus = (order.warehouse_substatus or "").upper()
    scheduled = ""
    if order.scheduled_at:
        try:
            scheduled = f"Scheduled for: {order.scheduled_at.strftime('%d %b %Y %H:%M UTC')}\n"
        except Exception:
            pass
    driver_line = (
        f"Driver assigned: YES (assigned_driver_id={order.assigned_driver_id})\n"
        if order.assigned_driver_id
        else "Driver assigned: NOT YET\n"
    )
    payment = (order.payment_status or "UNKNOWN").upper()
    payment_mode = (order.payment_mode or "UNKNOWN").upper()
    total = f"INR {order.total_amount:,.2f}" if order.total_amount else "N/A"
    return (
        "== ACTIVE SUPPORT ORDER SNAPSHOT ==\n"
        f"Tracking code: {order.tracking_code or 'N/A'}\n"
        f"Order type: {(order.order_type or 'STANDARD').upper()}\n"
        f"Status: {status}{f' / {substatus}' if substatus else ''}\n"
        f"Pickup: {order.pickup_addr or 'N/A'}\n"
        f"Delivery: {order.delivery_addr or 'N/A'}\n"
        f"{scheduled}"
        f"{driver_line}"
        f"Payment mode: {payment_mode} | Payment status: {payment}\n"
        f"Total amount: {total}\n"
    )


def _system_instruction_for_user(
    user: User,
    chat_context: str | None = None,
    db_settings=None,  # AISupportSettings | None
    linked_order=None,  # Order | None — injected only in support_chat context
) -> str:
    role = _role_name(user)
    # Use admin-configured system prompt if available, otherwise fall back to
    # the hardcoded SYSTEM_INSTRUCTION in gemini.py
    base = (
        db_settings.system_prompt
        if db_settings and db_settings.system_prompt
        else SYSTEM_INSTRUCTION
    )
    # Prepend tone instruction so the LLM adopts the right personality
    if db_settings and db_settings.tone:
        tone_line = f"== COMMUNICATION TONE ==\nAlways respond in a {db_settings.tone} manner.\n\n"
        base = tone_line + base
    if db_settings and getattr(db_settings, "language_mode", None):
        base = (
            f"== LANGUAGE MODE ==\nFollow this response language policy: {db_settings.language_mode}.\n\n"
            + base
        )

    user_id = str(user.id)
    name = user.name or "User"
    is_support_chat = (chat_context or "").strip().lower() == SUPPORT_CHAT_CONTEXT

    if role == "INDIVIDUAL":
        base_section = (
            f"{base}\n\n"
            "== CURRENT SESSION CONTEXT ==\n"
            f"User name: {name}\n"
            f"User role: INDIVIDUAL (personal move customer)\n"
            f"User ID: {user_id}\n\n"
            "== DATA ACCESS RULES ==\n"
            "You are in self-service mode for this individual customer.\n"
            "The server automatically scopes all SQL to this user — write queries using real table names and the WHERE clause is injected.\n"
            "Allowed tables: orders, order_items, customer_quotes, damage_reports, wallet_transactions, users, vendor_recurring_rules, vendor_support_tickets.\n"
            "Do NOT query inventory, drivers, vehicles, or logistics operational tables.\n\n"
            "== WHAT YOU CAN ANSWER ==\n"
            "- Order status and tracking: query orders table\n"
            "- Recent bookings: SELECT tracking_code, status, pickup_addr, delivery_addr, total_amount, created_at FROM orders ORDER BY created_at DESC LIMIT 10\n"
            "- Wallet balance: SELECT SUM(CASE WHEN transaction_kind='CREDIT' THEN amount ELSE -amount END) FROM wallet_transactions\n"
            "- Transaction history: SELECT transaction_kind, reason, amount, description, created_at FROM wallet_transactions ORDER BY created_at DESC LIMIT 20\n"
            "- Total spent: SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE status='DELIVERED'\n"
            "- Quotes: SELECT * FROM customer_quotes ORDER BY created_at DESC\n"
            "- How-to platform questions: answer directly without SQL\n\n"
            "== RAIL GUARDS ==\n"
            "Refuse other users' data: say 'I can only show your own account data.'\n"
            "Refuse global metrics: say 'That is only available to operations managers.'\n"
            "Refuse non-logistics topics: say 'I am your Cargo-Core move assistant. Ask me about bookings, tracking, wallet, or account details.'\n"
            "Never expose password_hash.\n"
        )
        if is_support_chat:
            order_snapshot = _support_chat_order_snapshot(linked_order) if linked_order else ""
            return (
                base_section
                + "\n"
                + (order_snapshot + "\n" if order_snapshot else "")
                + "== SUPPORT CHAT MODE — AUTONOMOUS RESOLUTION FIRST ==\n"
                "You are in a DEDICATED CUSTOMER SUPPORT SESSION. Your primary goal is to fully resolve the customer's concern without involving a human agent.\n"
                "Always try to answer using live DB data before saying you cannot help.\n\n"
                "RESOLUTION PLAYBOOK — handle these autonomously:\n"
                "- 'Where is my order / order status' → Query orders for current status + substatus. Give a clear, human-friendly answer.\n"
                "- 'When will it arrive / ETA' → Check scheduled_at and status. If IN_TRANSIT, say driver is on the way with scheduled time. If PENDING/ASSIGNED, explain processing stage.\n"
                "- 'My address is wrong' → If status is PENDING/CONFIRMED, explain they can update it from the app's order detail page. If IN_TRANSIT, tell them it is too late to change automatically and a support manager will be notified.\n"
                "- 'I want to reschedule' → If not yet IN_TRANSIT, guide them to the reschedule option in the app. If IN_TRANSIT, acknowledge and say a support manager will contact them.\n"
                "- 'Payment / invoice / receipt' → Query payment_status and payment_mode. Explain status. Tell them receipts are available in order history.\n"
                "- 'Refund request' → Query order status and payment_status. Explain: delivered orders qualify for a refund review within 48 hours; submit via the Refund Center section of the app.\n"
                "- 'Damage complaint' → Query damage_reports for this order. Acknowledge the issue. Explain: file a damage report via the app if not already done; it goes to the logistics manager for review.\n"
                "- 'Add extra helper / change service' → Explain this can be requested by messaging via the chat; note any changes to the order may affect the final amount.\n"
                "- General how-to or feature questions → Answer directly from your knowledge of the Cargo-Core platform.\n\n"
                "== ESCALATION RAIL GUARD ==\n"
                "ONLY suggest talking to a human agent when:\n"
                "1. The customer has a billing dispute or charge that requires manager override.\n"
                "2. The customer has made a legal complaint or threatens legal action.\n"
                "3. A physical emergency or safety concern is reported.\n"
                "4. The customer explicitly requests human support AFTER you have already tried to resolve the issue.\n"
                "5. The data is missing or a system error prevents you from answering.\n"
                "DO NOT escalate for: tracking questions, ETA questions, payment status questions, receipt requests, address-change enquiries, reschedule requests, refund information, or general how-to questions.\n"
            )
        return base_section

    if role == "VENDOR":
        base_section = (
            f"{base}\n\n"
            "== CURRENT SESSION CONTEXT ==\n"
            f"User name: {name}\n"
            f"User role: VENDOR (commercial shipper)\n"
            f"User ID: {user_id}\n\n"
            "== DATA ACCESS RULES ==\n"
            "You are in self-service mode for this vendor.\n"
            "The server automatically scopes all SQL to this vendor — write queries using real table names and the WHERE clause is injected.\n"
            "Allowed tables: orders, order_items, customer_quotes, damage_reports, wallet_transactions, users.\n"
            "Do NOT query inventory, drivers, vehicles, or logistics operational tables.\n\n"
            "== WHAT YOU CAN ANSWER ==\n"
            "- Pending shipments: SELECT tracking_code, status, pickup_addr, delivery_addr, total_amount, created_at FROM orders WHERE status IN ('PENDING','CONFIRMED','ASSIGNED') ORDER BY created_at DESC\n"
            "- All shipments: SELECT tracking_code, status, pickup_addr, delivery_addr, total_amount, created_at FROM orders ORDER BY created_at DESC LIMIT 10\n"
            "- Wallet balance: SELECT SUM(CASE WHEN transaction_kind='CREDIT' THEN amount ELSE -amount END) FROM wallet_transactions\n"
            "- Transaction history: SELECT transaction_kind, reason, amount, description, created_at FROM wallet_transactions ORDER BY created_at DESC LIMIT 20\n"
            "- Monthly spend: SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE created_at >= date_trunc('month', now())\n"
            "- Overdue invoices: SELECT tracking_code, total_amount, created_at FROM orders WHERE payment_status='PENDING' AND status='DELIVERED'\n"
            "- Recurring schedules: SELECT name, frequency, route, next_run, active FROM vendor_recurring_rules ORDER BY created_at DESC LIMIT 10\n"
            "- Support tickets: SELECT subject, status, priority, created_at FROM vendor_support_tickets ORDER BY created_at DESC LIMIT 10\n"
            "- Bulk upload meaning: answer directly — it means uploading many shipments at once via CSV/Excel file\n"
            "- How-to platform questions: answer directly without SQL\n"
            "- General greetings or casual messages: respond conversationally and helpfully, ask what you can assist with\n\n"
            "== CRITICAL ANTI-DEFLECTION RULES ==\n"
            "NEVER respond to a vendor query by telling them to raise a support ticket. This is a direct-answer chat interface.\n"
            "- If data is available: query it and present the result clearly.\n"
            "- If data is empty: say so directly (e.g., 'You have no overdue invoices right now.').\n"
            "- If a question is greeting/general: respond warmly and ask how you can help.\n"
            "- NEVER say 'please raise a ticket', 'contact support', or 'use the Support section' as your primary response.\n\n"
            "== RAIL GUARDS ==\n"
            "Refuse other users' data: say 'I can only show your own account data.'\n"
            "Refuse global metrics: say 'Company-wide analytics are only available to operations managers.'\n"
            "Refuse non-logistics topics: say 'I am your Cargo-Core vendor assistant. Ask me about shipments, tracking, invoices, or wallet.'\n"
            "Never expose password_hash.\n"
        )
        if is_support_chat:
            order_snapshot = _support_chat_order_snapshot(linked_order) if linked_order else ""
            return (
                base_section
                + "\n"
                + (order_snapshot + "\n" if order_snapshot else "")
                + "== SUPPORT CHAT MODE — AUTONOMOUS RESOLUTION FIRST ==\n"
                "You are in a DEDICATED VENDOR SUPPORT SESSION. Your PRIMARY goal is to ANSWER the vendor's question directly using DB data.\n"
                "ALWAYS try to answer using live DB data first. NEVER deflect by saying 'raise a ticket' or 'use the Support section'.\n\n"
                "RESOLUTION PLAYBOOK — handle all of these autonomously:\n"
                "- Greetings / 'hey' / 'hello' → Respond warmly: 'Hello! I am your Cargo-Core AI assistant. How can I help you today?'\n"
                "- 'Do I have overdue invoices?' → Query: SELECT tracking_code, total_amount, created_at FROM orders WHERE payment_status='PENDING' AND status='DELIVERED'. Report findings directly.\n"
                "- 'Where is my shipment / status' → Query orders for current status + substatus. Give a specific, factual answer with tracking code.\n"
                "- 'ETA / delivery estimate' → Check scheduled_at and status. If IN_TRANSIT, confirm driver is dispatched with scheduled time. If PENDING/ASSIGNED, explain the processing stage.\n"
                "- 'Payment pending / invoice overdue' → Query payment_status and payment_mode. Explain the payment cycle and when it will clear.\n"
                "- 'I want to cancel a shipment' → If PENDING/CONFIRMED, explain the cancellation is possible via the app's shipment detail page.\n"
                "- 'Address correction' → If not yet IN_TRANSIT, guide them to edit via the app. If IN_TRANSIT, acknowledge urgency and say a support manager will be informed.\n"
                "- 'Damage / loss claim' → Query damage_reports. Explain the claim process: file via app → logistics manager review → refund/replacement decision within 3-5 business days.\n"
                "- 'Recurring schedule question' → Query vendor_recurring_rules. Give the current schedule status and next run date.\n"
                "- 'Refund / wallet credit' → Query wallet_transactions and order status. Explain refund eligibility and expected credit timeline.\n"
                "- 'Bulk upload / CSV feature' → Explain directly: upload multiple shipments at once via the Vendor portal Bulk Upload section.\n"
                "- 'What can you do?' or general questions → Explain your capabilities as the AI assistant.\n"
                "- General how-to or feature questions → Answer directly from your knowledge of the Cargo-Core platform.\n\n"
                "== ESCALATION RAIL GUARD ==\n"
                "ONLY suggest talking to a human agent when:\n"
                "1. The vendor disputes a charge or payment that requires a manager override.\n"
                "2. The vendor makes a legal complaint or threatens legal action.\n"
                "3. A shipment emergency (security breach, driver unresponsive, critical cargo at risk) is reported.\n"
                "4. The vendor explicitly requests human support AFTER you have already tried to resolve the issue.\n"
                "5. The data is missing or a system error prevents you from answering.\n"
                "DO NOT escalate for: tracking questions, ETA questions, payment status questions, invoice enquiries, address-change requests, recurring schedule questions, or general how-to questions.\n"
            )
        return base_section

    if role == "WAREHOUSE_MANAGER":
        warehouse_id = str(getattr(user, "warehouse_id", "") or "")
        warehouse_mode = (chat_context or "").strip().lower() in WAREHOUSE_CONTEXTS
        mode_note = (
            "You are serving the Smart WMS warehouse assistant. "
            "Answer from the current warehouse only. The server automatically scopes warehouse SQL to this manager's warehouse.\n"
            if warehouse_mode
            else "You are serving a warehouse manager. Keep answers focused on the manager's assigned warehouse.\n"
        )
        return (
            f"{base}\n\n"
            "== CURRENT SESSION CONTEXT ==\n"
            f"User name: {name}\n"
            "User role: WAREHOUSE_MANAGER\n"
            f"User ID: {user_id}\n"
            f"Assigned warehouse ID: {warehouse_id}\n\n"
            "== DATA ACCESS RULES ==\n"
            f"{mode_note}"
            "Use real operational tables such as warehouses, orders, inventory_items, labourers, loading_docks, "
            "packing_stations, return_gradings, warehouse_zone_metrics, logistics_return_cases, logistics_alerts, "
            "logistics_daily_stats, logistics_driver_profiles, and logistics_vehicles.\n"
            "Do NOT answer with customer wallet/spending help text in this mode.\n"
            "When discussing recommendations, ground them in live counts, zones, staff, or queue state.\n\n"
            "== WHAT YOU CAN ANSWER ==\n"
            "- Warehouse overview, congestion, and picking backlog\n"
            "- Free space / aisle or zone utilization\n"
            "- Staff availability, on-field staff, and reallocation suggestions\n"
            "- Dock availability and dispatch readiness\n"
            "- Returns, damage grading, and restock pressure\n"
            "- Tomorrow workload forecast using recent operational volume\n\n"
            "== RAIL GUARDS ==\n"
            "Stay inside the assigned warehouse unless the user explicitly has broader logistics-manager permissions.\n"
            "Do not expose unrelated warehouses or other roles' personal financial data.\n"
            "Never expose password_hash.\n"
        )

    if role == "LOGISTIC_MANAGER":
        logistics_mode = (chat_context or "").strip().lower() in LOGISTIC_MANAGER_CONTEXTS
        mode_note = (
            "You are serving Cargo-Core AI Intelligence for a logistics manager. "
            "Answer with cross-hub operational insight, management actions, and notable exceptions.\n"
            if logistics_mode
            else "You are serving a logistics manager with network-wide operational visibility.\n"
        )
        return (
            f"{base}\n\n"
            "== CURRENT SESSION CONTEXT ==\n"
            f"User name: {name}\n"
            "User role: LOGISTIC_MANAGER\n"
            f"User ID: {user_id}\n"
            "Access scope: Network-wide logistics, warehouse, fleet, finance, returns, and alert operations.\n\n"
            "== DATA ACCESS RULES ==\n"
            f"{mode_note}"
            "Use live operational tables such as warehouses, orders, inventory_items, labourers, loading_docks, "
            "packing_stations, return_gradings, warehouse_zone_metrics, logistics_return_cases, logistics_alerts, "
            "logistics_daily_stats, logistics_driver_profiles, logistics_vehicles, logistics_transactions, "
            "logistics_zones, logistics_metrics, logistics_notifications, logistics_tasks, logistics_chat_threads, "
            "logistics_chat_messages, and logistics_escalations.\n"
            "Prioritize answers about hub performance, fleet readiness, driver coverage, warehouse bottlenecks, "
            "inventory pressure, returns, alerts, revenue, COD exposure, and service risk.\n"
            "Do NOT answer like a customer, vendor, or warehouse self-service assistant.\n"
            "When summarizing, call out top performers, at-risk hubs, unusual trends, and recommended next actions.\n\n"
            "== WHAT YOU CAN ANSWER ==\n"
            "- Dashboard overviews and cross-hub comparisons\n"
            "- Driver status, fleet utilization, and vehicle readiness\n"
            "- Inventory levels, warehouse pressure, and dock readiness\n"
            "- Active alerts, returns/RMA, and exception handling\n"
            "- Revenue trends, COD exposure, and operational finance questions\n"
            "- User, role, and cross-functional operations questions\n\n"
            "== RAIL GUARDS ==\n"
            "Keep answers focused on logistics management and operational decision-making.\n"
            "Do not pretend this is a customer wallet or vendor invoice assistant.\n"
            "Never expose password_hash.\n"
        )

    if role == "DISPATCHER":
        return (
            f"{base}\n\n"
            "== CURRENT SESSION CONTEXT ==\n"
            f"User name: {name}\n"
            f"User role: DISPATCHER\n"
            f"User ID: {user_id}\n\n"
            "== YOUR JOB ==\n"
            "You are serving the AI Dispatch Agent for a logistics dispatcher. "
            "Your job is to help the dispatcher manage drivers, assign orders, monitor fleet status, and optimize routes.\n"
            "Do NOT answer with customer wallet, spending, or personal order tracking — that is not relevant here.\n\n"
            "== WHAT YOU CAN ANSWER ==\n"
            "- Driver status: SELECT u.name, ldp.status, ldp.current_location, ldp.current_job FROM logistics_driver_profiles ldp JOIN users u ON u.id = ldp.user_id\n"
            "- Available drivers: SELECT u.name, ldp.status, ldp.current_location FROM logistics_driver_profiles ldp JOIN users u ON u.id = ldp.user_id WHERE ldp.status = 'Active'\n"
            "- Pending orders (need driver): SELECT tracking_code, pickup_addr, delivery_addr, status, created_at FROM orders WHERE status = 'CONFIRMED' AND assigned_driver_id IS NULL ORDER BY created_at ASC LIMIT 20\n"
            "- Active orders (on trip): SELECT o.tracking_code, o.pickup_addr, o.delivery_addr, u.name as driver FROM orders o JOIN users u ON u.id = o.assigned_driver_id WHERE o.status = 'IN_TRANSIT'\n"
            "- Fleet vehicles: SELECT code, license_plate, type, status FROM logistics_vehicles ORDER BY status\n"
            "- Overloaded drivers (many assignments): SELECT u.name, COUNT(o.id) as order_count FROM orders o JOIN users u ON u.id = o.assigned_driver_id WHERE o.status IN ('ASSIGNED','IN_TRANSIT') GROUP BY u.name ORDER BY order_count DESC\n"
            "- SLA at risk: SELECT tracking_code, scheduled_at, status, pickup_addr FROM orders WHERE status IN ('CONFIRMED','ASSIGNED') AND scheduled_at < now() ORDER BY scheduled_at ASC LIMIT 10\n"
            "- Today deliveries: SELECT COUNT(*) FROM orders WHERE status = 'DELIVERED' AND delivered_at::date = CURRENT_DATE\n\n"
            "== RAIL GUARDS ==\n"
            "Do NOT answer about customer wallets, personal spending, or vendor invoices — say 'That is customer data, not available in the dispatch view.'\n"
            "Stay focused on fleet, drivers, orders, and routing.\n"
            "Never expose password_hash.\n"
        )

    # Staff / manager roles — full access
    return (
        f"{base}\n\n"
        "== CURRENT SESSION CONTEXT ==\n"
        f"User name: {name}\n"
        f"User role: {role}\n"
        f"User ID: {user_id}\n"
        "Access level: Full operational access. You may query any table in the schema.\n"
    )


def _scope_sql_for_user(sql: str, user: User) -> str:
    role = _role_name(user)
    if role == "WAREHOUSE_MANAGER":
        warehouse_id = str(getattr(user, "warehouse_id", "") or "")
        user_id = str(user.id)
        if not warehouse_id:
            raise SQLValidationError("This warehouse manager account is not linked to a warehouse.")

        tables = _extract_table_names_for_scope(sql)
        disallowed = tables - WAREHOUSE_MANAGER_ALLOWED_TABLES
        if disallowed:
            raise SQLValidationError(
                "Warehouse manager AI access is limited to current-warehouse operational data. "
                f"Disallowed table(s): {sorted(disallowed)}"
            )

        scoped_sources = {
            "warehouses": f"(SELECT * FROM warehouses WHERE id = '{warehouse_id}'::uuid)",
            "orders": f"(SELECT * FROM orders WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "order_items": (
                "(SELECT oi.* FROM order_items oi "
                "JOIN orders o ON o.id = oi.order_id "
                f"WHERE o.warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "picked_items": (
                "(SELECT pi.* FROM picked_items pi "
                "JOIN orders o ON o.id = pi.order_id "
                f"WHERE o.warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "inventory_items": f"(SELECT * FROM inventory_items WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "inventory_movements": (
                "(SELECT im.* FROM inventory_movements im "
                "JOIN inventory_items ii ON ii.id = im.item_id "
                f"WHERE ii.warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "restock_requests": f"(SELECT * FROM restock_requests WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "labourers": f"(SELECT * FROM labourers WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "users": (
                "(SELECT * FROM users "
                f"WHERE warehouse_id = '{warehouse_id}'::uuid OR id = '{user_id}'::uuid)"
            ),
            "loading_docks": f"(SELECT * FROM loading_docks WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "packing_stations": f"(SELECT * FROM packing_stations WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "quality_checks": f"(SELECT * FROM quality_checks WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "return_gradings": f"(SELECT * FROM return_gradings WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "warehouse_zone_metrics": (
                f"(SELECT * FROM warehouse_zone_metrics WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_return_cases": (
                f"(SELECT * FROM logistics_return_cases WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_alerts": f"(SELECT * FROM logistics_alerts WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "logistics_daily_stats": (
                f"(SELECT * FROM logistics_daily_stats WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_driver_profiles": (
                f"(SELECT * FROM logistics_driver_profiles WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_vehicles": (
                f"(SELECT * FROM logistics_vehicles WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_transactions": (
                f"(SELECT * FROM logistics_transactions WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_zones": f"(SELECT * FROM logistics_zones WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "logistics_metrics": f"(SELECT * FROM logistics_metrics WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "logistics_chat_threads": (
                f"(SELECT * FROM logistics_chat_threads WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_chat_messages": (
                "(SELECT m.* FROM logistics_chat_messages m "
                "JOIN logistics_chat_threads t ON t.id = m.thread_id "
                f"WHERE t.warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_escalations": (
                f"(SELECT * FROM logistics_escalations WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "damage_reports": (
                "(SELECT dr.* FROM damage_reports dr "
                "JOIN orders o ON o.id = dr.order_id "
                f"WHERE o.warehouse_id = '{warehouse_id}'::uuid)"
            ),
        }

        scoped_sql = _normalize_common_sql_aliases(sql)
        for table, subquery in scoped_sources.items():
            pattern = rf"(?i)\b(FROM|JOIN)\s+{table}\b"
            scoped_sql = re.sub(
                pattern,
                lambda m, sq=subquery: f"{m.group(1)} {sq} {table}",
                scoped_sql,
            )
        return scoped_sql

    if role not in SELF_SERVICE_ROLES:
        return sql

    tables = _extract_table_names_for_scope(sql)
    disallowed = tables - SELF_SERVICE_ALLOWED_TABLES
    if disallowed:
        raise SQLValidationError(
            "This account can only access personal shipment/payment data. "
            f"Disallowed table(s): {sorted(disallowed)}"
        )

    user_id = str(user.id)
    scoped_sources = {
        "orders": (
            "(SELECT * FROM orders WHERE customer_id = "
            f"'{user_id}'::uuid)"
        ),
        "order_items": (
            "(SELECT oi.* FROM order_items oi "
            "JOIN orders o ON o.id = oi.order_id "
            f"WHERE o.customer_id = '{user_id}'::uuid)"
        ),
        "picked_items": (
            "(SELECT pi.* FROM picked_items pi "
            "JOIN orders o ON o.id = pi.order_id "
            f"WHERE o.customer_id = '{user_id}'::uuid)"
        ),
        "customer_quotes": (
            "(SELECT * FROM customer_quotes WHERE customer_id = "
            f"'{user_id}'::uuid)"
        ),
        "damage_reports": (
            "(SELECT dr.* FROM damage_reports dr "
            "JOIN orders o ON o.id = dr.order_id "
            f"WHERE o.customer_id = '{user_id}'::uuid)"
        ),
        "users": (
            "(SELECT * FROM users WHERE id = "
            f"'{user_id}'::uuid)"
        ),
        "wallet_transactions": (
            "(SELECT * FROM wallet_transactions WHERE user_id = "
            f"'{user_id}'::uuid)"
        ),
        "vendor_recurring_rules": (
            "(SELECT * FROM vendor_recurring_rules WHERE vendor_id = "
            f"'{user_id}'::uuid)"
        ),
        "vendor_support_tickets": (
            "(SELECT * FROM vendor_support_tickets WHERE vendor_id = "
            f"'{user_id}'::uuid)"
        ),
    }

    scoped_sql = _normalize_common_sql_aliases(sql)
    for table, subquery in scoped_sources.items():
        pattern = rf"(?i)\b(FROM|JOIN)\s+{table}\b"
        scoped_sql = re.sub(
            pattern,
            lambda m, sq=subquery, t=table: f"{m.group(1)} {sq} {t}",
            scoped_sql,
        )

    return scoped_sql


def _normalize_common_sql_aliases(sql: str) -> str:
    normalized = sql
    replacements = {
        "customer_name": "customer_id",
        "customer_phone": "customer_id",
        "order_date": "created_at",
        "pickup_address": "pickup_addr",
        "delivery_address": "delivery_addr",
        "base_cost": "base_amount",
        "labor_cost": "labor_amount",
    }
    for old, new in replacements.items():
        normalized = re.sub(rf"(?i)\b{old}\b", new, normalized)
    return normalized


def _make_json_serializable(data: list[dict]) -> list[dict]:
    """Convert non-JSON-serializable types to strings."""
    serialized = []
    for row in data:
        clean_row = {}
        for key, value in row.items():
            if isinstance(value, (datetime,)):
                clean_row[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                clean_row[key] = str(value)
            elif isinstance(value, Decimal):
                # Convert Decimal to float (or int if it's a whole number)
                clean_row[key] = int(value) if value == value.to_integral_value() else float(value)
            elif isinstance(value, bytes):
                clean_row[key] = value.decode("utf-8", errors="replace")
            else:
                clean_row[key] = value
        serialized.append(clean_row)
    return serialized


def _format_results_fallback(results: list[dict], columns: list[str]) -> str:
    """Format query results as a readable string when Gemini fails to respond."""
    if not results:
        return "The query returned no results."

    if len(results) == 1 and len(columns) == 1:
        # Single value (e.g., COUNT)
        val = list(results[0].values())[0]
        return f"Result: {val}"

    # Simple table format
    lines = [f"Query returned {len(results)} row(s):"]
    lines.append(" | ".join(columns))
    lines.append("-" * (len(" | ".join(columns))))
    for row in results[:20]:  # Cap display at 20 rows
        lines.append(" | ".join(str(row.get(c, "")) for c in columns))

    if len(results) > 20:
        lines.append(f"... and {len(results) - 20} more rows")

    return "\n".join(lines)


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
