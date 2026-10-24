"""Limits, regex patterns, role contexts and per-role table allow lists for the AI chatbot."""

import re

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
