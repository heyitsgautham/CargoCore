"""Keyword classifiers for staff chats: which warehouse, logistics or dispatcher shortcut answers a message."""

from app.models.user import User
from app.services.ai_chat.constants import (
    DISPATCHER_CONTEXTS,
    LOGISTIC_MANAGER_CONTEXTS,
    WAREHOUSE_CONTEXTS,
)
from app.services.ai_chat.intents import _role_name


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
