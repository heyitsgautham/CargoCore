"""Keyword classifiers that decide which shortcut answers a chat message, plus the support health score."""

import re

from app.models.user import User
from app.services.ai_chat.constants import (
    HUMAN_HANDOFF_PATTERNS,
    HUMAN_HANDOFF_PHRASES,
    LEGAL_THREAT_PATTERNS,
    SEVERE_NEGATIVE_SENTIMENT_PATTERNS,
    TRACKING_CODE_PATTERN,
)


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


def _role_name(user: User) -> str:
    role = getattr(getattr(user, "role", None), "name", None)
    return str(role or "").upper()
