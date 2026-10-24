"""
Lightweight knowledge retrieval for AI help answers.

Retrieval priority:
  1. DB articles from ai_knowledge_articles (managed via the Knowledge Base dashboard)
  2. Hardcoded KNOWLEDGE_BASE tuple (fallback when DB is empty or unavailable)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class KnowledgeEntry:
    id: str
    audience: str  # ALL | VENDOR | INDIVIDUAL
    title: str
    keywords: tuple[str, ...]
    content: str


KNOWLEDGE_BASE: tuple[KnowledgeEntry, ...] = (
    KnowledgeEntry(
        id="logistic_dashboard",
        audience="LOGISTIC_MANAGER",
        title="Logistics Dashboard",
        keywords=("dashboard", "logistics dashboard", "dashboard overview", "control tower", "hub performance"),
        content=(
            "The Logistics Dashboard is the control-tower summary for a Logistics Manager. "
            "It highlights active deliveries, pending operational load, alert pressure, SLA trend, revenue movement, "
            "and top-performing or at-risk hubs so the manager can decide where attention is needed first."
        ),
    ),
    KnowledgeEntry(
        id="logistic_warehouse_management",
        audience="LOGISTIC_MANAGER",
        title="Warehouse Management",
        keywords=("warehouse management", "warehouse mgmt", "warehouse section", "hub capacity", "warehouse operations"),
        content=(
            "Warehouse Management gives the Logistics Manager a cross-hub view of capacity, operational throughput, "
            "inventory pressure, dispatch readiness, and warehouse-specific execution bottlenecks."
        ),
    ),
    KnowledgeEntry(
        id="logistic_user_roles",
        audience="LOGISTIC_MANAGER",
        title="User & Roles",
        keywords=("user & roles", "user roles", "roles", "permissions", "staff access", "user management"),
        content=(
            "User & Roles is where the Logistics Manager reviews operational staff accounts, access permissions, "
            "approval status, role assignments, and platform access for teams such as warehouse managers, dispatchers, drivers, and support staff."
        ),
    ),
    KnowledgeEntry(
        id="logistic_fleet_drivers",
        audience="LOGISTIC_MANAGER",
        title="Fleet & Drivers",
        keywords=("fleet & drivers", "fleet drivers", "driver section", "vehicle section", "fleet management"),
        content=(
            "Fleet & Drivers tracks driver availability, assignment coverage, vehicle readiness, maintenance pressure, "
            "and fleet execution so the manager can spot idle capacity, shortages, or reliability issues."
        ),
    ),
    KnowledgeEntry(
        id="logistic_geofencing",
        audience="LOGISTIC_MANAGER",
        title="Geofencing",
        keywords=("geofencing", "geofence", "zones", "location rules", "route boundaries"),
        content=(
            "Geofencing manages logistics zones, route boundaries, compliance areas, and location-based triggers. "
            "It helps the manager supervise operational coverage and respond to deviations or exceptions."
        ),
    ),
    KnowledgeEntry(
        id="logistic_finance_payroll",
        audience="LOGISTIC_MANAGER",
        title="Finance & Payroll",
        keywords=("finance", "finance payroll", "finance & payroll", "payroll", "salary", "dues", "payouts", "cod"),
        content=(
            "Finance & Payroll tracks revenue, expenses, pending COD, refunds, payroll liability, and payout execution. "
            "It helps the Logistics Manager monitor financial health, salary due state, and operational cash exposure."
        ),
    ),
    KnowledgeEntry(
        id="logistic_rate_governance",
        audience="LOGISTIC_MANAGER",
        title="Rate Governance",
        keywords=("rate governance", "pricing", "quote control", "discounts", "commercial guardrails"),
        content=(
            "Rate Governance is used to supervise pricing rules, discounts, margin protection, and quote consistency across logistics operations."
        ),
    ),
    KnowledgeEntry(
        id="logistic_reverse_logistics",
        audience="LOGISTIC_MANAGER",
        title="Reverse Logistics",
        keywords=("reverse logistics", "returns", "rma", "refund flow", "return management"),
        content=(
            "Reverse Logistics manages returns, RMA workflow, recovery actions, pickups, inspections, and refund-linked exception handling for returned or failed shipments."
        ),
    ),
    KnowledgeEntry(
        id="logistic_reports",
        audience="LOGISTIC_MANAGER",
        title="Reports",
        keywords=("reports", "analytics reports", "reporting", "trends", "performance reports"),
        content=(
            "Reports is the analytics view for operational trends, hub performance, financial movement, returns, workforce patterns, and other decision-support summaries over time."
        ),
    ),
    KnowledgeEntry(
        id="logistic_ai_intelligence",
        audience="LOGISTIC_MANAGER",
        title="AI Intelligence",
        keywords=("ai intelligence", "logistics ai", "ai section", "assistant section", "what is ai intelligence"),
        content=(
            "AI Intelligence is the Logistics Manager assistant layer. "
            "It should explain dashboard modules, answer cross-functional operational questions, and use live logistics data when the question needs current values."
        ),
    ),
    KnowledgeEntry(
        id="logistic_recovery_tickets",
        audience="LOGISTIC_MANAGER",
        title="Recovery Tickets",
        keywords=("recovery tickets", "tickets", "exception tickets", "recovery queue"),
        content=(
            "Recovery Tickets is the exception-handling queue for unresolved operational cases, high-priority follow-ups, and customer-impact issues that need active recovery."
        ),
    ),
    KnowledgeEntry(
        id="logistic_communication",
        audience="LOGISTIC_MANAGER",
        title="Communication",
        keywords=("communication", "coordination", "messages", "team communication", "approvals"),
        content=(
            "Communication is the manager coordination center for approvals, follow-ups, escalation messaging, and cross-team operational updates."
        ),
    ),
    KnowledgeEntry(
        id="logistic_comparative_viewers",
        audience="LOGISTIC_MANAGER",
        title="Comparative Viewers",
        keywords=("comparative viewers", "compare hubs", "comparison view", "side by side"),
        content=(
            "Comparative Viewers lets the Logistics Manager compare hubs or operational slices side by side so performance gaps, imbalances, and bottlenecks become easier to spot."
        ),
    ),
    KnowledgeEntry(
        id="vendor_analytics",
        audience="VENDOR",
        title="Vendor Analytics",
        keywords=("analytics", "analytics section", "shipment analytics", "performance", "success rate"),
        content=(
            "The Vendor Analytics section summarizes shipment trends and business performance. "
            "It focuses on monthly spend, shipment volume, success rate, active versus delivered shipments, "
            "and average order value for the vendor account."
        ),
    ),
    KnowledgeEntry(
        id="vendor_recurring",
        audience="VENDOR",
        title="Recurring Orders",
        keywords=("recurring", "recurring orders", "recurring shipments", "schedule", "auto debit"),
        content=(
            "Recurring Orders let vendors template repeat shipment routes on a schedule such as weekly or monthly. "
            "Each recurring rule stores the route, frequency, details, next run date, and whether it is active. "
            "Recurring auto-debit works through wallet balance, so sufficient wallet funds are needed before the scheduled run."
        ),
    ),
    KnowledgeEntry(
        id="vendor_wallet",
        audience="VENDOR",
        title="Vendor Wallet",
        keywords=("wallet", "wallet balance", "credit balance", "top up", "wallet top up"),
        content=(
            "The Vendor Wallet stores usable credit for shipment payments and refunds. "
            "The wallet screen shows current balance, total credits, total debits, and recent transaction history. "
            "Refunds from eligible cancelled paid shipments are credited back to the wallet after applicable fees."
        ),
    ),
    KnowledgeEntry(
        id="vendor_support",
        audience="VENDOR",
        title="Vendor Support",
        keywords=("support", "support section", "ticket", "help", "contact support"),
        content=(
            "The Vendor Support area is for raising tickets about shipments, invoices, API usage, or platform issues. "
            "Tickets carry subject, description, priority, replies, and status so vendors can track follow-up from the support team."
        ),
    ),
    KnowledgeEntry(
        id="vendor_bulk_upload",
        audience="VENDOR",
        title="Bulk Upload",
        keywords=("bulk upload", "csv", "excel", "many shipments", "multiple shipments"),
        content=(
            "Bulk Upload lets vendors create many shipments in one step by uploading a CSV or spreadsheet-like file. "
            "Each row represents one shipment and is reviewed before final submission."
        ),
    ),
    KnowledgeEntry(
        id="individual_damage_report",
        audience="INDIVIDUAL",
        title="Damage Reports",
        keywords=("damage report", "damage", "claims", "refund for damage", "damage refund"),
        content=(
            "The Damage Report flow is used when items are damaged during packing, transit, or delivery. "
            "A report captures description, photos, linked order, and claim-review status. "
            "If a refund is approved, the customer sees the refund reflected through wallet credits or the related claim outcome."
        ),
    ),
    KnowledgeEntry(
        id="individual_wallet",
        audience="INDIVIDUAL",
        title="Customer Wallet",
        keywords=("wallet", "wallet balance", "refund", "cancellation refund", "wallet transactions"),
        content=(
            "The customer wallet shows current balance, credits, debits, and transaction history. "
            "Refunds from eligible cancelled orders are credited back to the wallet after applicable cancellation fees."
        ),
    ),
    KnowledgeEntry(
        id="individual_quotes",
        audience="INDIVIDUAL",
        title="Quotes",
        keywords=("quote", "quotes", "quotation", "estimate", "price estimate"),
        content=(
            "Quotes are estimated move costs shown before booking. "
            "They are based on route, labor, packing, materials, and vehicle requirements, and can later be converted into orders."
        ),
    ),
    KnowledgeEntry(
        id="individual_estimator",
        audience="INDIVIDUAL",
        title="AI Spatial Estimator",
        keywords=("spatial estimator", "estimator", "ai estimator", "room photo", "image estimate"),
        content=(
            "The AI Spatial Estimator analyzes room or goods photos to estimate visible items, packing needs, labor, vehicle recommendation, and a rough base cost."
        ),
    ),
    KnowledgeEntry(
        id="tracking_general",
        audience="ALL",
        title="Tracking",
        keywords=("tracking", "track order", "track shipment", "where to track", "live status"),
        content=(
            "Tracking shows order or shipment progress, warehouse stage, route, and status updates. "
            "Users can open their order or shipment list and drill into a specific tracking code for detailed status."
        ),
    ),
    KnowledgeEntry(
        id="refund_policy_general",
        audience="ALL",
        title="Refund Policy",
        keywords=("refund policy", "refund", "refunds", "cancel refund", "refund rules"),
        content=(
            "Refund outcomes depend on the order event and applicable charges. "
            "For cancellations, eligible paid amounts can be credited back to wallet after cancellation fees. "
            "For damage claims, refund handling depends on claim review and the recorded claim outcome."
        ),
    ),
)


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) > 1}


async def retrieve_knowledge_from_db(
    query: str, audience: str, db: AsyncSession, limit: int = 3
) -> list[KnowledgeEntry]:
    """
    Retrieve relevant knowledge entries from the DB.
    Returns empty list if the table is empty or query fails — caller falls back
    to the hardcoded KNOWLEDGE_BASE.
    """
    try:
        from sqlalchemy import select

        from app.models.ai_config import AIKnowledgeArticle

        rows = (
            await db.execute(
                select(AIKnowledgeArticle).where(
                    AIKnowledgeArticle.is_active.is_(True),
                    (AIKnowledgeArticle.audience == audience)
                    | (AIKnowledgeArticle.audience == "ALL"),
                )
            )
        ).scalars().all()

        if not rows:
            return []

        # Build transient KnowledgeEntry objects so the scoring logic is reused
        entries = [
            KnowledgeEntry(
                id=r.id,
                audience=r.audience,
                title=r.title,
                keywords=tuple(r.keywords or []),
                content=r.content,
            )
            for r in rows
        ]
        return _score_and_rank(query, audience, entries, limit)
    except Exception:
        return []


def _score_and_rank(
    query: str, audience: str, entries: list[KnowledgeEntry], limit: int
) -> list[KnowledgeEntry]:
    query_lower = (query or "").strip().lower()
    if not query_lower:
        return []
    query_tokens = _tokenize(query_lower)
    scored: list[tuple[int, KnowledgeEntry]] = []
    for entry in entries:
        if entry.audience not in {"ALL", audience}:
            continue
        score = 0
        if entry.title.lower() in query_lower:
            score += 8
        for keyword in entry.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in query_lower:
                score += 6 if " " in keyword_lower else 3
            score += len(query_tokens & _tokenize(keyword_lower))
        score += min(len(query_tokens & _tokenize(entry.content)), 4)
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in scored[:limit]]


def retrieve_knowledge(query: str, audience: str, limit: int = 3) -> list[KnowledgeEntry]:
    """Synchronous fallback using the hardcoded KNOWLEDGE_BASE tuple."""
    return _score_and_rank(query, audience, list(KNOWLEDGE_BASE), limit)
