import re
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.config import get_settings
from app.models.ai_config import AIKnowledgeArticle
from app.models.ai_conversation import AIConversation
from app.models.ai_support_settings import AISupportSettings
from app.models.escalation import Escalation
from app.models.logistics import LogisticsNotification, LogisticsReturnCase
from app.models.order import DamageReport, Order
from app.models.support_contact import SupportContactSubmission
from app.models.support_ticket import SupportTicket
from app.models.user import Role, User
from app.models.vendor import VendorSupportReply, VendorSupportTicket
from app.schemas.ai import (
    AgentReplyRequest,
    ContactSubmissionCreatePublic,
    ContactSubmissionListResponse,
    ContactSubmissionReplyRequest,
    ContactSubmissionResponse,
    ContactSubmissionStats,
    ContactSubmissionUpdate,
    CustomerHistoryResponse,
    EscalationDetailItem,
    EscalationDetailListResponse,
    EscalationResponse,
    SupportAgentSummary,
    SupportAnalyticsEscalationReason,
    SupportAnalyticsInsight,
    SupportAnalyticsInsightExecutionResponse,
    SupportAnalyticsMetric,
    SupportAnalyticsResolutionChart,
    SupportAnalyticsResponse,
    SupportAnalyticsSentimentChart,
    SupportConversationMessage,
    SupportDamageReportCreate,
    SupportDamageReportItem,
    SupportDamageReportListResponse,
    SupportDamageReportNotesUpdate,
    SupportDamageReportStats,
    SupportDashboardFeedItem,
    SupportDashboardResponse,
    SupportDashboardStats,
    SupportIntegrationStatus,
    SupportMessageCreate,
    SupportMessageItem,
    SupportRefundCaseItem,
    SupportRefundCaseListResponse,
    SupportRefundCaseStats,
    SupportRefundCaseUrgentUpdate,
    SupportSessionDetail,
    SupportSessionEscalateRequest,
    SupportSessionEscalationSummary,
    SupportSessionListItem,
    SupportSessionListResponse,
    SupportSettings,
    SupportSettingsResponse,
    TicketCreate,
    TicketListResponse,
    TicketReplyItem,
    TicketResponse,
    TicketStats,
    TicketUpdate,
)
from app.utils.email import send_email, support_contact_reply_email_html
from app.utils.gemini import GEMINI_FLASH_MODEL, get_gemini_client

SUPPORT_ROLE_NAMES = ("LOGISTIC_MANAGER", "AI_AGENT", "AI_SUPPORT", "CUSTOMER_SUPPORT")
SUPPORT_MANAGER_ROLE_NAME = "LOGISTIC_MANAGER"
SUPPORT_SESSION_OWNER_ROLE_NAMES = {"INDIVIDUAL", "VENDOR"}
HUMAN_ASSISTANT_INTENTS = {"agent_reply", "handover"}
TRACKING_CODE_PATTERN = re.compile(r"\b[A-Z]{2,6}-[A-Z0-9]{3,}\b", re.IGNORECASE)
SUPPORT_SESSION_CLOSED_INTENT = "support_session_closed"
SUPPORT_SESSION_CLOSED_MESSAGE = (
    "This human support session has been closed by the Support Manager. "
    "You can continue with AI help here, but to request human support again you need to start a fresh support chat."
)

NEGATIVE_KEYWORDS = {
    "refund",
    "delay",
    "delayed",
    "late",
    "lawyer",
    "legal",
    "angry",
    "frustrated",
    "complaint",
    "damaged",
    "broken",
    "stuck",
    "issue",
    "problem",
    "urgent",
}

POSITIVE_KEYWORDS = {
    "thanks",
    "thank you",
    "resolved",
    "great",
    "good",
    "perfect",
}

CONTACT_STATUS_VALUES = {"new", "in_progress", "resolved"}
CONTACT_PRIORITY_VALUES = {"low", "medium", "high", "urgent"}
APP_SETTINGS = get_settings()


def _utc_now() -> datetime:
    return datetime.now(UTC)


DEFAULT_SUPPORT_SYSTEM_PROMPT = """You are the primary autonomous support agent for Cargo-Core Logistics.
Your operational priorities are:
1. De-escalate angry customers with empathy.
2. Adhere strictly to approved SOPs and policy documents.
3. Automatically process low-risk actions only when policy permits.
4. Transfer to a human supervisor if legal threats are detected or confidence drops.

Always communicate cleanly, concisely, and handle order references securely."""


ANALYTICS_RANGES = {"24H", "7D", "30D", "90D"}
SENTIMENT_SCORES = {"Positive": 92.0, "Neutral": 74.0, "Negative": 38.0}
ANALYTICS_HOURLY_RATE = 500.0
ANALYTICS_MINUTES_SAVED_PER_AI_RESOLUTION = 6.0
ANALYTICS_INSIGHT_RECOMMENDATIONS = {
    "optimize_refund_playbooks": {
        "category": "refund",
        "priority": "high",
        "action_steps": [
            "Review and update refund approval macros in the CS tool",
            "Identify top refund dispute patterns from the last 30 days",
            "Coordinate with finance team to clarify refund eligibility rules",
            "Audit any automated refund rejection messages for tone and accuracy",
        ],
    },
    "stabilize_delivery_comms": {
        "category": "logistics",
        "priority": "urgent",
        "action_steps": [
            "Audit driver checkpoint update frequency for all active routes",
            "Verify automated SMS/email delivery notifications are firing at each stage",
            "Review last 7 days of late-delivery complaints and identify repeat routes or drivers",
            "Brief dispatchers to enforce proactive customer update policy",
            "Check if any delivery notification templates are outdated or misconfigured",
        ],
    },
    "clear_contact_backlog": {
        "category": "general",
        "priority": "medium",
        "action_steps": [
            "Triage all open contact form submissions and assign to agents",
            "Escalate any requests older than 48 hours to senior support",
            "Review urgent tickets and prioritise resolution order",
            "Set up an auto-acknowledgement for new contact submissions",
        ],
    },
    "fast_track_damage_reviews": {
        "category": "damage",
        "priority": "high",
        "action_steps": [
            "Review all pending damage reports and approve or reject within 24 hours",
            "Identify repeat damage patterns by route, driver, or package type",
            "Coordinate with warehouse to check packing quality for flagged items",
            "Ensure all damage claim customers have received an acknowledgement",
        ],
    },
}


def _normalize_analytics_range(value: str | None) -> str:
    normalized = (value or "7D").strip().upper()
    if normalized not in ANALYTICS_RANGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analytics range must be one of: 24H, 7D, 30D, 90D",
        )
    return normalized


def _analytics_bucket_starts(range_name: str, now: datetime) -> list[datetime]:
    current = now.astimezone(UTC)
    if range_name == "24H":
        end = current.replace(minute=0, second=0, microsecond=0)
        return [end - timedelta(hours=index) for index in range(23, -1, -1)]
    if range_name == "7D":
        end = current.replace(hour=0, minute=0, second=0, microsecond=0)
        return [end - timedelta(days=index) for index in range(6, -1, -1)]
    if range_name == "30D":
        end = current.replace(hour=0, minute=0, second=0, microsecond=0)
        return [end - timedelta(days=index) for index in range(29, -1, -1)]

    week_start = (current - timedelta(days=current.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return [week_start - timedelta(weeks=index) for index in range(12, -1, -1)]


def _next_analytics_window_start(range_name: str, bucket_start: datetime) -> datetime:
    if range_name == "24H":
        return bucket_start + timedelta(hours=1)
    if range_name in {"7D", "30D"}:
        return bucket_start + timedelta(days=1)
    return bucket_start + timedelta(weeks=1)


def _analytics_label(range_name: str, bucket_start: datetime) -> str:
    if range_name == "24H":
        return bucket_start.strftime("%H:%M")
    if range_name == "7D":
        return bucket_start.strftime("%a")
    return bucket_start.strftime("%d %b")


def _bucket_for_datetime(value: datetime, range_name: str) -> datetime:
    current = value.astimezone(UTC)
    if range_name == "24H":
        return current.replace(minute=0, second=0, microsecond=0)
    if range_name in {"7D", "30D"}:
        return current.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = current - timedelta(days=current.weekday())
    return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)


def _percent_delta(current: float, previous: float) -> float:
    if previous <= 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100


def _format_count(value: float) -> str:
    return f"{int(round(value)):,}"


def _format_currency(value: float) -> str:
    if value >= 1000:
        return f"₹{value / 1000:.1f}k"
    return f"₹{value:.0f}"


def _format_duration_seconds(value: float) -> str:
    if value <= 0:
        return "0s"
    if value >= 60:
        return f"{int(round(value / 60))}m"
    return f"{int(round(value))}s"


def _trend_descriptor(
    current: float,
    previous: float,
    previous_label: str,
    *,
    formatter,
    inverse: bool = False,
) -> tuple[str, str]:
    delta = current - previous
    if abs(delta) < 0.01:
        return (f"Flat vs previous {previous_label}", "neutral")

    improved = delta < 0 if inverse else delta > 0
    if previous > 0 and not inverse:
        magnitude = abs(_percent_delta(current, previous))
        message = f"{'+' if improved else '-'}{magnitude:.1f}% vs previous {previous_label}"
    else:
        message = f"{'-' if delta < 0 else '+'}{formatter(abs(delta))} vs previous {previous_label}"
    return (message, "positive" if improved else "negative")


def _escalation_reason_label(reason: str | None) -> str:
    normalized = (reason or "").lower()
    if any(keyword in normalized for keyword in ("refund", "billing", "charge", "payment")):
        return "Refund Dispute"
    if any(keyword in normalized for keyword in ("delay", "late", "delivery", "tracking", "shipment")):
        return "Late Delivery"
    if any(keyword in normalized for keyword in ("damage", "damaged", "broken", "missing")):
        return "Damaged Item"
    if any(keyword in normalized for keyword in ("driver", "rude", "conduct", "behavior", "behaviour")):
        return "Driver Conduct"
    return "Other"


def _analytics_ticket_marker(insight_id: str) -> str:
    return f"[analytics:{insight_id}]"


def _extract_analytics_ticket_marker(notes: str | None) -> str | None:
    match = re.search(r"\[analytics:([a-z0-9_-]+)\]", notes or "", flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1)


def _build_analytics_insights(
    *,
    top_reason_label: str,
    top_reason_pct: int,
    negative_sessions: int,
    total_sessions: int,
    open_contact_forms: int,
    urgent_tickets: int,
    under_review_damage_reports: int,
    executed_insight_ids: set[str],
) -> list[SupportAnalyticsInsight]:
    insights: list[SupportAnalyticsInsight] = []
    negative_ratio = (negative_sessions / total_sessions) if total_sessions else 0

    if top_reason_label == "Refund Dispute" and top_reason_pct >= 20:
        insights.append(
            SupportAnalyticsInsight(
                id="optimize_refund_playbooks",
                icon="rule_settings",
                title="Optimize Refund Playbooks",
                text=(
                    f"{top_reason_pct}% of escalations in this window were tied to refund disputes."
                    " Queue a support follow-up so the team can tighten refund macros and automation rules."
                ),
                tone="purple",
                action_label="Create Follow-up Ticket",
                executed="optimize_refund_playbooks" in executed_insight_ids,
            )
        )

    if (
        top_reason_label == "Late Delivery"
        or negative_ratio >= 0.3
        or top_reason_pct >= 20
    ):
        insights.append(
            SupportAnalyticsInsight(
                id="stabilize_delivery_comms",
                icon="notifications_active",
                title="Stabilize Delivery Communications",
                text=(
                    f"{negative_sessions} of {total_sessions} recent conversations show negative sentiment,"
                    " and delivery-related escalations remain a leading driver."
                    " Open a logistics follow-up so proactive updates can be improved."
                ),
                tone="blue" if negative_ratio < 0.4 else "red",
                action_label="Open Recovery Ticket",
                executed="stabilize_delivery_comms" in executed_insight_ids,
            )
        )

    if open_contact_forms > 0 or urgent_tickets > 0:
        insights.append(
            SupportAnalyticsInsight(
                id="clear_contact_backlog",
                icon="inbox_customize",
                title="Clear Contact Backlog",
                text=(
                    f"{open_contact_forms} open contact requests and {urgent_tickets} urgent support tickets"
                    " still need attention. Create a queue review task so the team can rebalance work."
                ),
                tone="amber",
                action_label="Create Queue Review Ticket",
                executed="clear_contact_backlog" in executed_insight_ids,
            )
        )

    if under_review_damage_reports > 0:
        insights.append(
            SupportAnalyticsInsight(
                id="fast_track_damage_reviews",
                icon="inventory_2",
                title="Fast-Track Damage Reviews",
                text=(
                    f"{under_review_damage_reports} damage reports are still under review."
                    " Open a dedicated follow-up so support and operations can shorten resolution time."
                ),
                tone="green",
                action_label="Open Damage Review Task",
                executed="fast_track_damage_reviews" in executed_insight_ids,
            )
        )

    if not insights:
        insights.append(
            SupportAnalyticsInsight(
                id="clear_contact_backlog",
                icon="insights",
                title="Maintain Current Support Quality",
                text=(
                    "No major risk spike was detected in this window."
                    " Create a lightweight review ticket if you want the team to document what is working well."
                ),
                tone="blue",
                action_label="Create Review Ticket",
                executed="clear_contact_backlog" in executed_insight_ids,
            )
        )

    deduped: list[SupportAnalyticsInsight] = []
    seen: set[str] = set()
    for insight in insights:
        if insight.id in seen:
            continue
        seen.add(insight.id)
        deduped.append(insight)
    return deduped[:4]


def _keyword_sentiment_label(text: str | None) -> str:
    """Keyword-based fallback — used when Gemini is unavailable."""
    normalized = (text or "").lower()
    negative_hits = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in normalized)
    positive_hits = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in normalized)
    if negative_hits >= 2:
        return "Negative"
    if positive_hits > negative_hits:
        return "Positive"
    return "Neutral"


# Simple in-process cache so repeated polls for the same message text
# don't fire a new Gemini call.  Evicts oldest half when it fills up.
_SENTIMENT_CACHE: dict[str, str] = {}
_SENTIMENT_CACHE_MAX = 500


async def _sentiment_label(text: str | None) -> str:
    """Use Gemini Flash to classify message sentiment as Positive, Neutral, or Negative.

    Falls back to keyword matching if Gemini is unavailable or returns an
    unexpected value.
    """
    if not text or not text.strip():
        return "Neutral"

    cache_key = text[:500]
    if cache_key in _SENTIMENT_CACHE:
        return _SENTIMENT_CACHE[cache_key]

    label = "Neutral"
    try:
        client = get_gemini_client()
        prompt = (
            "Classify the sentiment of this customer support message as exactly one of: "
            "Positive, Neutral, or Negative.\n"
            "Reply with ONLY that single word — no punctuation, no explanation.\n\n"
            f"Message: {text[:300]}"
        )
        response = await client.aio.models.generate_content(
            model=GEMINI_FLASH_MODEL,
            contents=prompt,
        )
        raw = (response.text or "").strip().strip(".").capitalize()
        if raw in ("Positive", "Neutral", "Negative"):
            label = raw
        else:
            label = _keyword_sentiment_label(text)
    except Exception:
        label = _keyword_sentiment_label(text)

    if len(_SENTIMENT_CACHE) >= _SENTIMENT_CACHE_MAX:
        keys = list(_SENTIMENT_CACHE.keys())
        for k in keys[: _SENTIMENT_CACHE_MAX // 2]:
            del _SENTIMENT_CACHE[k]
    _SENTIMENT_CACHE[cache_key] = label
    return label


def _analytics_sentiment_label(text: str | None) -> str:
    """Fast local sentiment for dashboard aggregation.

    The analytics endpoint may score many messages at once, so it should never
    block on an external LLM call just to render charts.
    """
    if not text or not text.strip():
        return "Neutral"

    cache_key = f"analytics:{text[:500]}"
    if cache_key in _SENTIMENT_CACHE:
        return _SENTIMENT_CACHE[cache_key]

    label = _keyword_sentiment_label(text)
    if len(_SENTIMENT_CACHE) >= _SENTIMENT_CACHE_MAX:
        keys = list(_SENTIMENT_CACHE.keys())
        for k in keys[: _SENTIMENT_CACHE_MAX // 2]:
            del _SENTIMENT_CACHE[k]
    _SENTIMENT_CACHE[cache_key] = label
    return label


def _normalize_contact_status(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized not in CONTACT_STATUS_VALUES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be one of: new, in_progress, resolved",
        )
    return normalized


def _normalize_contact_priority(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized not in CONTACT_PRIORITY_VALUES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Priority must be one of: low, medium, high, urgent",
        )
    return normalized


def _ensure_support_manager(user: User) -> None:
    role_name = getattr(getattr(user, "role", None), "name", None)
    if role_name not in SUPPORT_ROLE_NAMES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only support staff can manually handle customer conversations and linked tickets.",
        )


def _support_integrations() -> list[SupportIntegrationStatus]:
    gemini_connected = bool(APP_SETTINGS.gemini_api_key)
    return [
        SupportIntegrationStatus(
            provider="gemini",
            label="Google Gemini",
            description="Primary reasoning engine used by the current backend chat service",
            connected=gemini_connected,
            connection_source="server_env",
            status_note="Configured via backend environment variables"
            if gemini_connected
            else "No GEMINI_API_KEY is configured on the backend",
            editable=False,
        ),
        SupportIntegrationStatus(
            provider="anthropic",
            label="Anthropic Claude",
            description="Secondary provider slot reserved for future failover or comparison routing",
            connected=False,
            connection_source="not_configured",
            status_note="Provider wiring is not implemented in the backend yet",
            editable=False,
        ),
    ]


def _settings_to_response(item: AISupportSettings) -> SupportSettingsResponse:
    return SupportSettingsResponse(
        settings=SupportSettings(
            tone=item.tone,
            language_mode=item.language_mode,
            sentiment_threshold=item.sentiment_threshold,
            refund_limit_inr=item.refund_limit_inr,
            system_prompt=item.system_prompt,
            autonomous_replies=item.autonomous_replies,
            legal_threat_detection=item.legal_threat_detection,
            real_time_sentiment_analysis=item.real_time_sentiment_analysis,
            proactive_human_handover=item.proactive_human_handover,
        ),
        integrations=_support_integrations(),
        updated_at=item.updated_at,
        autonomous_reply_guidance=(
            "Autonomous replies can be enabled as a policy control, but they should only be trusted for"
            " customer-facing decisions when the knowledge base, retrieval layer, and escalation guardrails"
            " are grounded in approved documents."
        ),
        rag_recommended=True,
    )


async def _get_or_create_support_settings(db: AsyncSession) -> AISupportSettings:
    settings_row = (
        await db.execute(
            select(AISupportSettings).order_by(AISupportSettings.created_at.asc()).limit(1)
        )
    ).scalar_one_or_none()
    if settings_row:
        return settings_row

    settings_row = AISupportSettings(
        tone="Friendly & Empathetic",
        language_mode="Auto-Detect (Multilingual)",
        sentiment_threshold=80,
        refund_limit_inr=5000,
        system_prompt=DEFAULT_SUPPORT_SYSTEM_PROMPT,
        autonomous_replies=True,
        legal_threat_detection=True,
        real_time_sentiment_analysis=True,
        proactive_human_handover=True,
    )
    db.add(settings_row)
    await db.flush()
    await db.refresh(settings_row)
    return settings_row


async def _next_contact_reference(db: AsyncSession) -> str:
    latest = (
        await db.execute(
            select(SupportContactSubmission.reference_code)
            .order_by(SupportContactSubmission.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if not latest:
        return "CF-001"

    match = re.search(r"(\d+)$", latest)
    next_number = int(match.group(1)) + 1 if match else 1
    return f"CF-{next_number:03d}"


def _contact_submission_response(item: SupportContactSubmission) -> ContactSubmissionResponse:
    return ContactSubmissionResponse(
        id=item.id,
        reference_code=item.reference_code,
        name=item.name,
        email=item.email,
        phone=item.phone,
        subject=item.subject,
        category=item.category,
        message=item.message,
        priority=item.priority,
        status=item.status,
        notes=item.notes,
        assigned_to_user_id=item.assigned_to_user_id,
        assigned_agent_name=item.assigned_to_user.name if item.assigned_to_user else None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _list_support_agents(db: AsyncSession) -> list[SupportAgentSummary]:
    rows = (
        await db.execute(
            select(User)
            .join(Role, User.role_id == Role.id)
            .where(Role.name.in_(SUPPORT_ROLE_NAMES))
            .order_by(User.name.asc())
        )
    ).scalars().all()
    return [SupportAgentSummary(id=row.id, name=row.name, email=row.email) for row in rows]


async def get_default_support_manager(db: AsyncSession) -> User | None:
    return (
        await db.execute(
            select(User)
            .join(Role, User.role_id == Role.id)
            .where(
                Role.name == SUPPORT_MANAGER_ROLE_NAME,
                User.is_active.is_(True),
            )
            .order_by(User.created_at.asc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def create_user_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    title: str,
    message: str,
    notification_type: str = "info",
) -> None:
    db.add(
        LogisticsNotification(
            title=title,
            message=message,
            type=notification_type,
            target_user_id=user_id,
            is_read=False,
        )
    )


async def notify_support_manager_about_ticket(
    db: AsyncSession,
    *,
    ticket: SupportTicket,
    source: str | None = None,
) -> None:
    support_manager = await get_default_support_manager(db)
    if not support_manager:
        return

    title = "Warehouse inbound issue" if source == "warehouse_inbound" else "Support ticket update"
    await create_user_notification(
        db,
        user_id=support_manager.id,
        title=title,
        message=f"{ticket.reference_code}: {ticket.title}",
        notification_type="warning" if source == "warehouse_inbound" else "info",
    )


async def create_public_contact_submission(
    db: AsyncSession,
    data: ContactSubmissionCreatePublic,
) -> ContactSubmissionResponse:
    submission = SupportContactSubmission(
        reference_code=await _next_contact_reference(db),
        name=data.name.strip(),
        email=data.email.strip().lower(),
        phone=(data.phone or "").strip() or None,
        subject=data.subject.strip(),
        category=(data.category or "general").strip().lower(),
        message=data.message.strip(),
        priority=_normalize_contact_priority(data.priority) or "medium",
        status="new",
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)
    return _contact_submission_response(submission)


async def get_support_settings(
    db: AsyncSession,
) -> SupportSettingsResponse:
    settings_row = await _get_or_create_support_settings(db)
    return _settings_to_response(settings_row)


async def update_support_settings(
    db: AsyncSession,
    user: User,
    data: SupportSettings,
) -> SupportSettingsResponse:
    settings_row = await _get_or_create_support_settings(db)
    settings_row.tone = data.tone.strip()
    settings_row.language_mode = data.language_mode.strip()
    settings_row.sentiment_threshold = data.sentiment_threshold
    settings_row.refund_limit_inr = data.refund_limit_inr
    settings_row.system_prompt = data.system_prompt.strip()
    settings_row.autonomous_replies = data.autonomous_replies
    settings_row.legal_threat_detection = data.legal_threat_detection
    settings_row.real_time_sentiment_analysis = data.real_time_sentiment_analysis
    settings_row.proactive_human_handover = data.proactive_human_handover
    settings_row.updated_by_user_id = user.id
    await db.flush()
    await db.refresh(settings_row)
    return _settings_to_response(settings_row)


async def list_contact_submissions(
    db: AsyncSession,
    limit: int | None = None,
) -> ContactSubmissionListResponse:
    query = (
        select(SupportContactSubmission)
        .options(joinedload(SupportContactSubmission.assigned_to_user))
        .order_by(SupportContactSubmission.created_at.desc())
    )
    if limit:
        query = query.limit(limit)

    submissions = (await db.execute(query)).scalars().all()

    stats = ContactSubmissionStats(
        total=int(
            (
                await db.execute(
                    select(func.count()).select_from(SupportContactSubmission)
                )
            ).scalar_one()
        ),
        new=int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(SupportContactSubmission)
                    .where(SupportContactSubmission.status == "new")
                )
            ).scalar_one()
        ),
        in_progress=int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(SupportContactSubmission)
                    .where(SupportContactSubmission.status == "in_progress")
                )
            ).scalar_one()
        ),
        resolved=int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(SupportContactSubmission)
                    .where(SupportContactSubmission.status == "resolved")
                )
            ).scalar_one()
        ),
        urgent=int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(SupportContactSubmission)
                    .where(SupportContactSubmission.priority == "urgent")
                )
            ).scalar_one()
        ),
    )

    return ContactSubmissionListResponse(
        submissions=[_contact_submission_response(item) for item in submissions],
        stats=stats,
        agents=await _list_support_agents(db),
    )


async def update_contact_submission(
    db: AsyncSession,
    submission_id: uuid.UUID,
    data: ContactSubmissionUpdate,
) -> ContactSubmissionResponse:
    submission = (
        await db.execute(
            select(SupportContactSubmission)
            .options(joinedload(SupportContactSubmission.assigned_to_user))
            .where(SupportContactSubmission.id == submission_id)
        )
    ).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact submission not found")

    status_value = _normalize_contact_status(data.status)
    priority_value = _normalize_contact_priority(data.priority)

    if status_value is not None:
        submission.status = status_value
    if priority_value is not None:
        submission.priority = priority_value
    if "assigned_to_user_id" in data.model_fields_set:
        if data.assigned_to_user_id:
            agent = (
                await db.execute(
                    select(User)
                    .join(Role, User.role_id == Role.id)
                    .where(
                        User.id == data.assigned_to_user_id,
                        Role.name.in_(SUPPORT_ROLE_NAMES),
                    )
                )
            ).scalar_one_or_none()
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned user must be a support-capable user",
                )
        submission.assigned_to_user_id = data.assigned_to_user_id
    if data.notes is not None:
        submission.notes = (data.notes or "").strip() or None

    await db.flush()
    await db.refresh(submission, attribute_names=["assigned_to_user"])
    return _contact_submission_response(submission)


async def reply_to_contact_submission(
    db: AsyncSession,
    submission_id: uuid.UUID,
    data: ContactSubmissionReplyRequest,
    actor: User,
) -> ContactSubmissionResponse:
    _ensure_support_manager(actor)

    submission = (
        await db.execute(
            select(SupportContactSubmission)
            .options(joinedload(SupportContactSubmission.assigned_to_user))
            .where(SupportContactSubmission.id == submission_id)
        )
    ).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact submission not found")

    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reply message is required")

    subject = f"Re: {submission.subject} [{submission.reference_code}]"
    sent = await send_email(
        submission.email,
        subject,
        support_contact_reply_email_html(
            customer_name=submission.name,
            reference_code=submission.reference_code,
            original_subject=submission.subject,
            reply_message=message,
            support_agent_name=actor.name or "Cargo Core Support",
        ),
    )
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reply email could not be sent. Please verify SMTP settings and try again.",
        )

    submission.status = "resolved"
    submission.assigned_to_user_id = actor.id

    await db.flush()
    await db.refresh(submission, attribute_names=["assigned_to_user"])
    return _contact_submission_response(submission)


async def delete_contact_submission(
    db: AsyncSession,
    submission_id: uuid.UUID,
) -> None:
    submission = (
        await db.execute(
            select(SupportContactSubmission).where(SupportContactSubmission.id == submission_id)
        )
    ).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact submission not found")
    await db.delete(submission)
    await db.flush()


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


async def get_support_dashboard(
    db: AsyncSession,
) -> SupportDashboardResponse:
    all_session_items = await _load_support_session_items(db, limit=None)
    contact_list = await list_contact_submissions(db, limit=5)

    now = _utc_now()
    day_start = now - timedelta(days=1)
    support_session_ids = [item.session_id for item in all_session_items]

    total_sessions = len(all_session_items)
    active_sessions = sum(1 for item in all_session_items if item.last_message_at >= day_start)
    human_engaged_sessions = sum(1 for item in all_session_items if item.human_agent_engaged)
    sessions_needing_human = sum(1 for item in all_session_items if item.needs_human_attention)
    open_escalations = sum(
        1
        for item in all_session_items
        if item.escalation and item.escalation.status == "OPEN"
    )
    if support_session_ids:
        user_messages_today = int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(AIConversation)
                    .where(
                        AIConversation.session_id.in_(support_session_ids),
                        AIConversation.role == "user",
                        AIConversation.created_at >= day_start,
                    )
                )
            ).scalar_one()
        )
        assistant_messages_today = int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(AIConversation)
                    .where(
                        AIConversation.session_id.in_(support_session_ids),
                        AIConversation.role == "assistant",
                        AIConversation.created_at >= day_start,
                    )
                )
            ).scalar_one()
        )
    else:
        user_messages_today = 0
        assistant_messages_today = 0

    priority_sessions = sorted(
        all_session_items,
        key=lambda item: (
            0 if item.needs_human_attention else 1,
            0 if item.sentiment == "Negative" else 1,
            -item.last_message_at.timestamp(),
        ),
    )[:5]

    if support_session_ids:
        recent_user_messages = (
            await db.execute(
                select(AIConversation)
                .options(selectinload(AIConversation.user))
                .where(
                    AIConversation.session_id.in_(support_session_ids),
                    AIConversation.role == "user",
                )
                .order_by(AIConversation.created_at.desc())
                .limit(5)
            )
        ).scalars().all()
        recent_escalations = (
            await db.execute(
                select(Escalation)
                .options(selectinload(Escalation.assigned_agent), selectinload(Escalation.conversation))
                .join(AIConversation, Escalation.conversation_id == AIConversation.id)
                .where(AIConversation.session_id.in_(support_session_ids))
                .order_by(Escalation.escalated_at.desc())
                .limit(5)
            )
        ).scalars().all()
    else:
        recent_user_messages = []
        recent_escalations = []
    recent_tickets = (
        await db.execute(
            select(SupportTicket)
            .order_by(SupportTicket.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    activity_feed: list[SupportDashboardFeedItem] = []
    for submission in contact_list.submissions:
        activity_feed.append(
            SupportDashboardFeedItem(
                id=f"contact-{submission.id}",
                type="contact_submission",
                title=f"Contact form from {submission.name}",
                description=submission.subject,
                created_at=submission.created_at,
            )
        )
    for message in recent_user_messages:
        activity_feed.append(
            SupportDashboardFeedItem(
                id=f"chat-{message.id}",
                type="live_message",
                title=f"New live message from {message.user.name if message.user else 'Customer'}",
                description=message.message[:120],
                created_at=message.created_at,
            )
        )
    for escalation in recent_escalations:
        activity_feed.append(
            SupportDashboardFeedItem(
                id=f"escalation-{escalation.id}",
                type="escalation",
                title="Conversation escalated",
                description=escalation.reason,
                created_at=escalation.escalated_at,
            )
        )
    for ticket in recent_tickets:
        activity_feed.append(
            SupportDashboardFeedItem(
                id=f"ticket-{ticket.id}",
                type="ticket",
                title=f"New ticket {ticket.reference_code}",
                description=ticket.title,
                created_at=ticket.created_at,
            )
        )
    activity_feed.sort(key=lambda item: item.created_at, reverse=True)

    return SupportDashboardResponse(
        stats=SupportDashboardStats(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            human_engaged_sessions=human_engaged_sessions,
            sessions_needing_human=sessions_needing_human,
            open_escalations=open_escalations,
            open_contact_forms=contact_list.stats.new + contact_list.stats.in_progress,
            new_contact_forms=contact_list.stats.new,
            resolved_contact_forms=contact_list.stats.resolved,
            user_messages_today=user_messages_today,
            assistant_messages_today=assistant_messages_today,
        ),
        priority_sessions=priority_sessions,
        recent_contact_submissions=contact_list.submissions,
        activity_feed=activity_feed[:10],
    )


async def _build_support_analytics(
    db: AsyncSession,
    time_range: str,
) -> SupportAnalyticsResponse:
    range_name = _normalize_analytics_range(time_range)
    now = _utc_now()
    bucket_starts = _analytics_bucket_starts(range_name, now)
    current_start = bucket_starts[0]
    current_end = _next_analytics_window_start(range_name, bucket_starts[-1])
    previous_start = current_start - (current_end - current_start)

    messages = (
        await db.execute(
            select(AIConversation)
            .where(AIConversation.created_at >= previous_start)
            .order_by(AIConversation.session_id.asc(), AIConversation.created_at.asc())
        )
    ).scalars().all()

    sessions_by_id: dict[uuid.UUID, dict] = {}
    for message in messages:
        session = sessions_by_id.setdefault(
            message.session_id,
            {
                "session_id": message.session_id,
                "created_at": message.created_at,
                "last_message_at": message.created_at,
                "first_user_at": None,
                "first_response_at": None,
                "latest_user_sentiment": "Neutral",
                "has_human": False,
                "has_ai_reply": False,
            },
        )
        session["created_at"] = min(session["created_at"], message.created_at)
        session["last_message_at"] = max(session["last_message_at"], message.created_at)
        if message.role == "user":
            session["first_user_at"] = session["first_user_at"] or message.created_at
            session["latest_user_sentiment"] = _analytics_sentiment_label(message.message)
        if message.role == "assistant":
            session["first_response_at"] = session["first_response_at"] or message.created_at
            if _is_human_authored_support_message(message):
                session["has_human"] = True
            else:
                session["has_ai_reply"] = True

    session_ids = list(sessions_by_id.keys())
    escalations: list[Escalation] = []
    if session_ids:
        escalations = (
            await db.execute(
                select(Escalation)
                .options(selectinload(Escalation.conversation))
                .join(AIConversation, Escalation.conversation_id == AIConversation.id)
                .where(AIConversation.session_id.in_(session_ids))
                .order_by(Escalation.escalated_at.asc())
            )
        ).scalars().all()

    escalations_by_session: dict[uuid.UUID, list[Escalation]] = defaultdict(list)
    for escalation in escalations:
        if escalation.conversation:
            escalations_by_session[escalation.conversation.session_id].append(escalation)

    def _session_in_window(session: dict, start: datetime, end: datetime) -> bool:
        return start <= session["last_message_at"] < end

    current_sessions = [
        session for session in sessions_by_id.values() if _session_in_window(session, current_start, current_end)
    ]
    previous_sessions = [
        session for session in sessions_by_id.values() if _session_in_window(session, previous_start, current_start)
    ]

    def _is_ai_resolved(session: dict) -> bool:
        session_escalations = escalations_by_session.get(session["session_id"], [])
        has_escalation = any(item.status in {"OPEN", "RESOLVED"} for item in session_escalations)
        return session["has_ai_reply"] and not session["has_human"] and not has_escalation

    current_ai_resolved = sum(1 for session in current_sessions if _is_ai_resolved(session))
    previous_ai_resolved = sum(1 for session in previous_sessions if _is_ai_resolved(session))

    current_resolution_rate = (current_ai_resolved / len(current_sessions) * 100) if current_sessions else 0.0
    previous_resolution_rate = (previous_ai_resolved / len(previous_sessions) * 100) if previous_sessions else 0.0

    def _avg_handle_time(sessions: list[dict]) -> float:
        durations = []
        for session in sessions:
            if session["first_user_at"] and session["first_response_at"]:
                durations.append((session["first_response_at"] - session["first_user_at"]).total_seconds())
        if not durations:
            return 0.0
        return sum(durations) / len(durations)

    current_handle_time = _avg_handle_time(current_sessions)
    previous_handle_time = _avg_handle_time(previous_sessions)

    current_savings = current_ai_resolved * (ANALYTICS_MINUTES_SAVED_PER_AI_RESOLUTION / 60) * ANALYTICS_HOURLY_RATE
    previous_savings = previous_ai_resolved * (ANALYTICS_MINUTES_SAVED_PER_AI_RESOLUTION / 60) * ANALYTICS_HOURLY_RATE

    conversation_trend, conversation_direction = _trend_descriptor(
        len(current_sessions),
        len(previous_sessions),
        range_name,
        formatter=_format_count,
    )
    resolution_trend, resolution_direction = _trend_descriptor(
        current_resolution_rate,
        previous_resolution_rate,
        range_name,
        formatter=lambda value: f"{value:.1f} pts",
    )
    handle_trend, handle_direction = _trend_descriptor(
        current_handle_time,
        previous_handle_time,
        range_name,
        formatter=_format_duration_seconds,
        inverse=True,
    )
    savings_trend, savings_direction = _trend_descriptor(
        current_savings,
        previous_savings,
        range_name,
        formatter=_format_currency,
    )

    metrics = [
        SupportAnalyticsMetric(
            id="conversations",
            label="Conversations",
            icon="forum",
            value=float(len(current_sessions)),
            formatted_value=_format_count(len(current_sessions)),
            trend=conversation_trend,
            trend_direction=conversation_direction,
        ),
        SupportAnalyticsMetric(
            id="ai_resolution",
            label="AI Resolution",
            icon="smart_toy",
            value=round(current_resolution_rate, 1),
            formatted_value=f"{current_resolution_rate:.1f}%",
            trend=resolution_trend,
            trend_direction=resolution_direction,
        ),
        SupportAnalyticsMetric(
            id="avg_handle_time",
            label="Avg Handle Time",
            icon="timer",
            value=round(current_handle_time, 1),
            formatted_value=_format_duration_seconds(current_handle_time),
            trend=handle_trend,
            trend_direction=handle_direction,
        ),
        SupportAnalyticsMetric(
            id="estimated_savings",
            label="Est. Savings",
            icon="savings",
            value=round(current_savings, 2),
            formatted_value=_format_currency(current_savings),
            trend=savings_trend,
            trend_direction=savings_direction,
        ),
    ]

    bucket_index = {bucket: index for index, bucket in enumerate(bucket_starts)}
    resolution_ai = [0 for _ in bucket_starts]
    resolution_escalated = [0 for _ in bucket_starts]
    sentiment_ai_scores: list[list[float]] = [[] for _ in bucket_starts]
    sentiment_human_scores: list[list[float]] = [[] for _ in bucket_starts]

    for session in current_sessions:
        bucket = _bucket_for_datetime(session["last_message_at"], range_name)
        index = bucket_index.get(bucket)
        if index is None:
            continue
        if _is_ai_resolved(session):
            resolution_ai[index] += 1

        score = SENTIMENT_SCORES.get(session["latest_user_sentiment"], SENTIMENT_SCORES["Neutral"])
        if session["has_human"]:
            sentiment_human_scores[index].append(score)
        else:
            sentiment_ai_scores[index].append(score)

    current_escalations = [
        escalation
        for escalation in escalations
        if current_start <= escalation.escalated_at < current_end
    ]
    for escalation in current_escalations:
        bucket = _bucket_for_datetime(escalation.escalated_at, range_name)
        index = bucket_index.get(bucket)
        if index is not None:
            resolution_escalated[index] += 1

    reason_counts: dict[str, int] = defaultdict(int)
    for escalation in current_escalations:
        reason_counts[_escalation_reason_label(escalation.reason)] += 1

    ordered_reason_labels = [
        "Refund Dispute",
        "Late Delivery",
        "Damaged Item",
        "Driver Conduct",
        "Other",
    ]
    total_reason_count = max(1, sum(reason_counts.values()))
    escalation_reasons = [
        SupportAnalyticsEscalationReason(
            label=label,
            count=reason_counts.get(label, 0),
            pct=int(round((reason_counts.get(label, 0) / total_reason_count) * 100)),
        )
        for label in ordered_reason_labels
    ]

    tickets = (
        await db.execute(
            select(SupportTicket).order_by(SupportTicket.created_at.desc())
        )
    ).scalars().all()
    executed_insight_ids = {
        marker
        for ticket in tickets
        if ticket.status != "resolved"
        for marker in [_extract_analytics_ticket_marker(ticket.notes)]
        if marker
    }
    urgent_tickets = sum(
        1
        for ticket in tickets
        if ticket.priority == "urgent" and ticket.status != "resolved"
    )

    open_contact_forms = int(
        (
            await db.execute(
                select(func.count())
                .select_from(SupportContactSubmission)
                .where(SupportContactSubmission.status.in_(("new", "in_progress")))
            )
        ).scalar_one()
    )
    under_review_damage_reports = int(
        (
            await db.execute(
                select(func.count())
                .select_from(DamageReport)
                .where(DamageReport.status.in_(("under_review", "Under Review")))
            )
        ).scalar_one()
    )

    top_reason = max(escalation_reasons, key=lambda item: item.count, default=None)
    negative_sessions = sum(1 for session in current_sessions if session["latest_user_sentiment"] == "Negative")
    insights = _build_analytics_insights(
        top_reason_label=top_reason.label if top_reason else "Other",
        top_reason_pct=top_reason.pct if top_reason else 0,
        negative_sessions=negative_sessions,
        total_sessions=len(current_sessions),
        open_contact_forms=open_contact_forms,
        urgent_tickets=urgent_tickets,
        under_review_damage_reports=under_review_damage_reports,
        executed_insight_ids=executed_insight_ids,
    )

    return SupportAnalyticsResponse(
        range=range_name,
        generated_at=now,
        metrics=metrics,
        resolution_chart=SupportAnalyticsResolutionChart(
            labels=[_analytics_label(range_name, bucket) for bucket in bucket_starts],
            ai_resolved=resolution_ai,
            human_escalated=resolution_escalated,
        ),
        escalation_reasons=escalation_reasons,
        sentiment_chart=SupportAnalyticsSentimentChart(
            labels=[_analytics_label(range_name, bucket) for bucket in bucket_starts],
            ai_handled=[
                round(sum(scores) / len(scores), 1) if scores else 0.0
                for scores in sentiment_ai_scores
            ],
            human_handled=[
                round(sum(scores) / len(scores), 1) if scores else 0.0
                for scores in sentiment_human_scores
            ],
        ),
        insights=insights,
    )


async def get_support_analytics(
    db: AsyncSession,
    time_range: str = "7D",
) -> SupportAnalyticsResponse:
    return await _build_support_analytics(db=db, time_range=time_range)


async def execute_support_analytics_insight(
    db: AsyncSession,
    insight_id: str,
    time_range: str = "7D",
) -> SupportAnalyticsInsightExecutionResponse:
    analytics = await _build_support_analytics(db=db, time_range=time_range)
    selected_insight = next((item for item in analytics.insights if item.id == insight_id), None)
    if not selected_insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analytics insight not found")

    marker = _analytics_ticket_marker(insight_id)
    existing_ticket = (
        await db.execute(
            select(SupportTicket)
            .where(
                SupportTicket.notes.is_not(None),
                SupportTicket.status != "resolved",
            )
            .order_by(SupportTicket.created_at.desc())
        )
    ).scalars().all()
    for ticket in existing_ticket:
        if marker in (ticket.notes or ""):
            return SupportAnalyticsInsightExecutionResponse(
                insight_id=insight_id,
                ticket_id=ticket.id,
                ticket_reference_code=ticket.reference_code,
                message="A follow-up ticket already exists for this analytics insight.",
            )

    config = ANALYTICS_INSIGHT_RECOMMENDATIONS.get(
        insight_id,
        {"category": "general", "priority": "medium"},
    )
    action_steps = config.get("action_steps", [])
    steps_encoded = "||".join(action_steps)
    ticket = SupportTicket(
        reference_code=await _next_ticket_reference(db),
        title=selected_insight.title,
        description=selected_insight.text,
        priority=config["priority"],
        status="new",
        category=config["category"],
        customer_name="AI Support Analytics",
        notes=(
            f"[meta:source=ai_analytics]\n"
            f"[meta:lm_steps={steps_encoded}]\n"
            f"{marker} Created from support analytics for range {analytics.range}."
        ),
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return SupportAnalyticsInsightExecutionResponse(
        insight_id=insight_id,
        ticket_id=ticket.id,
        ticket_reference_code=ticket.reference_code,
        message="Follow-up ticket created from the analytics insight.",
    )


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


# ── Support Tickets ───────────────────────────────────────────────────────────

TICKET_STATUS_VALUES = {"new", "in_progress", "resolved"}
TICKET_PRIORITY_VALUES = {"low", "medium", "high", "urgent"}
TICKET_SOURCE_LABELS = {
    "manual": "Manual",
    "vendor_portal": "Vendor Portal",
    "warehouse_inbound": "Warehouse Inbound",
    "ai_handoff": "AI Chat Handoff",
    "ai_analytics": "AI Analytics",
}
TICKET_NOTE_META_PATTERN = re.compile(r"^\[meta:(?P<key>[a-z_]+)=(?P<value>.*)\]$")
INBOUND_RESOLUTION_LABELS = {
    "pending_review": "Pending Review",
    "vendor_accept_move": "Vendor Cleared For Move",
    "vendor_take_back": "Vendor Will Take Back",
}


def _vendor_ticket_display_code(ticket_id: uuid.UUID) -> str:
    return f"TK-{str(ticket_id).split('-')[0].upper()}"


def _support_status_from_vendor(status_value: str | None) -> str:
    mapping = {
        "open": "new",
        "in progress": "in_progress",
        "resolved": "resolved",
    }
    return mapping.get((status_value or "").strip().lower(), "new")


def _vendor_status_from_support(status_value: str | None) -> str:
    mapping = {
        "new": "Open",
        "in_progress": "In Progress",
        "resolved": "Resolved",
    }
    return mapping.get((status_value or "").strip().lower(), "Open")


def _support_priority_from_vendor(priority_value: str | None) -> str:
    normalized = (priority_value or "medium").strip().lower()
    return normalized if normalized in TICKET_PRIORITY_VALUES else "medium"


def _vendor_priority_from_support(priority_value: str | None) -> str:
    normalized = _support_priority_from_vendor(priority_value)
    return normalized.title()


def _handoff_ticket_priority(reason: str | None) -> str:
    text = (reason or "").strip().lower()
    if "legal" in text:
        return "urgent"
    if text:
        return "high"
    return "medium"


def _split_ticket_notes(raw_notes: str | None) -> tuple[dict[str, str], str | None]:
    metadata: dict[str, str] = {}
    visible_lines: list[str] = []

    for raw_line in (raw_notes or "").splitlines():
        line = raw_line.strip()
        match = TICKET_NOTE_META_PATTERN.match(line)
        if match:
            metadata[match.group("key")] = match.group("value")
            continue
        visible_lines.append(raw_line)

    visible_notes = "\n".join(visible_lines).strip() or None
    return metadata, visible_notes


def _compose_ticket_notes(
    *,
    metadata: dict[str, str | None],
    visible_notes: str | None = None,
) -> str | None:
    meta_lines = [
        f"[meta:{key}={value}]"
        for key, value in metadata.items()
        if value is not None and str(value).strip()
    ]
    clean_notes = (visible_notes or "").strip()
    if clean_notes:
        meta_lines.append(clean_notes)
    return "\n".join(meta_lines) if meta_lines else None


def _ticket_source_metadata(ticket: SupportTicket) -> dict[str, str]:
    metadata, _ = _split_ticket_notes(ticket.notes)
    return metadata


def _linked_vendor_ticket_uuid_from_ticket(ticket: SupportTicket) -> uuid.UUID | None:
    vendor_ticket_id_raw = _ticket_source_metadata(ticket).get("linked_vendor_ticket_id")
    if not vendor_ticket_id_raw:
        return None
    try:
        return uuid.UUID(vendor_ticket_id_raw)
    except ValueError:
        return None


def _linked_order_uuid_from_ticket(ticket: SupportTicket) -> uuid.UUID | None:
    order_id_raw = _ticket_source_metadata(ticket).get("linked_order_id")
    if not order_id_raw:
        return None
    try:
        return uuid.UUID(order_id_raw)
    except ValueError:
        return None


def _linked_session_uuid_from_ticket(ticket: SupportTicket) -> uuid.UUID | None:
    session_id_raw = _ticket_source_metadata(ticket).get("linked_session_id")
    if not session_id_raw:
        return None
    try:
        return uuid.UUID(session_id_raw)
    except ValueError:
        return None


async def _linked_order_tracking_map(
    db: AsyncSession,
    tickets: list[SupportTicket],
) -> dict[uuid.UUID, str]:
    order_ids: set[uuid.UUID] = set()
    for ticket in tickets:
        order_id = _linked_order_uuid_from_ticket(ticket)
        if order_id:
            order_ids.add(order_id)

    if not order_ids:
        return {}

    rows = (
        await db.execute(
            select(Order.id, Order.tracking_code).where(Order.id.in_(order_ids))
        )
    ).all()
    return {row.id: row.tracking_code for row in rows}


async def _linked_vendor_ticket_map(
    db: AsyncSession,
    tickets: list[SupportTicket],
) -> dict[uuid.UUID, VendorSupportTicket]:
    vendor_ticket_ids: set[uuid.UUID] = set()
    for ticket in tickets:
        vendor_ticket_id = _linked_vendor_ticket_uuid_from_ticket(ticket)
        if vendor_ticket_id:
            vendor_ticket_ids.add(vendor_ticket_id)

    if not vendor_ticket_ids:
        return {}

    rows = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.id.in_(vendor_ticket_ids))
        )
    ).scalars().all()
    return {row.id: row for row in rows}


def _ticket_response(
    t: SupportTicket,
    *,
    order_tracking_code: str | None = None,
    vendor_ticket: VendorSupportTicket | None = None,
) -> TicketResponse:
    metadata, visible_notes = _split_ticket_notes(t.notes)
    source = metadata.get("source", "manual")
    linked_vendor_ticket_id: uuid.UUID | None = None
    linked_order_id: uuid.UUID | None = None
    linked_damage_report_id: uuid.UUID | None = None

    try:
        linked_vendor_ticket_id = (
            uuid.UUID(metadata["linked_vendor_ticket_id"])
            if metadata.get("linked_vendor_ticket_id")
            else None
        )
    except ValueError:
        linked_vendor_ticket_id = None

    try:
        linked_order_id = (
            uuid.UUID(metadata["linked_order_id"])
            if metadata.get("linked_order_id")
            else None
        )
    except ValueError:
        linked_order_id = None

    try:
        linked_damage_report_id = (
            uuid.UUID(metadata["linked_damage_report_id"])
            if metadata.get("linked_damage_report_id")
            else None
        )
    except ValueError:
        linked_damage_report_id = None

    resolution_action = metadata.get("resolution_action")
    issue_type = metadata.get("issue_type")

    return TicketResponse(
        id=t.id,
        reference_code=t.reference_code,
        title=t.title,
        description=t.description,
        priority=t.priority,
        status=t.status,
        category=t.category,
        customer_name=t.customer_name,
        notes=visible_notes,
        assigned_to_user_id=t.assigned_to_user_id,
        assigned_agent_name=t.assigned_to_user.name if t.assigned_to_user else None,
        created_at=t.created_at,
        updated_at=t.updated_at,
        resolved_at=t.resolved_at,
        source=source,
        source_label=TICKET_SOURCE_LABELS.get(source, source.replace("_", " ").title()),
        requester_type=(
            "Vendor"
            if source == "vendor_portal"
            else "Warehouse / Vendor"
            if source == "warehouse_inbound"
            else metadata.get("requester_type", "Customer")
            if source == "ai_handoff"
            else None
        ),
        issue_type=issue_type,
        resolution_action=resolution_action,
        resolution_label=INBOUND_RESOLUTION_LABELS.get(resolution_action),
        linked_vendor_ticket_id=linked_vendor_ticket_id,
        linked_vendor_ticket_code=(
            _vendor_ticket_display_code(linked_vendor_ticket_id)
            if linked_vendor_ticket_id
            else None
        ),
        linked_damage_report_id=linked_damage_report_id,
        linked_order_id=linked_order_id,
        linked_order_tracking_code=order_tracking_code,
        linked_vendor_replies=[
            TicketReplyItem(
                from_name=reply.from_name,
                message=reply.message,
                created_at=reply.created_at,
            )
            for reply in ((vendor_ticket.replies if vendor_ticket else []) or [])
        ],
        can_delete=source not in {"vendor_portal", "warehouse_inbound", "ai_handoff"},
        lm_action_steps=[
            s.strip()
            for s in metadata.get("lm_steps", "").split("||")
            if s.strip()
        ],
    )


async def _next_ticket_reference(db: AsyncSession) -> str:
    latest = (
        await db.execute(
            select(SupportTicket.reference_code)
            .order_by(SupportTicket.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not latest:
        return "TK-001"
    match = re.search(r"(\d+)$", latest)
    next_number = int(match.group(1)) + 1 if match else 1
    return f"TK-{next_number:03d}"


async def _find_ai_handoff_ticket_for_session(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> SupportTicket | None:
    return (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(
                SupportTicket.notes.contains("[meta:source=ai_handoff]"),
                SupportTicket.notes.contains(f"[meta:linked_session_id={session_id}]"),
            )
            .order_by(SupportTicket.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def _close_support_session_once(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> None:
    already_closed = (
        await db.execute(
            select(AIConversation.id)
            .where(
                AIConversation.session_id == session_id,
                AIConversation.intent == SUPPORT_SESSION_CLOSED_INTENT,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if already_closed:
        return

    messages = (
        await db.execute(
            select(AIConversation)
            .where(AIConversation.session_id == session_id)
            .order_by(AIConversation.created_at.desc())
        )
    ).scalars().all()
    if not messages:
        return

    linked_order_meta = None
    for message in messages:
        if isinstance(message.query_result, dict) and message.query_result.get("linked_order_id"):
            linked_order_meta = {
                "linked_order_id": str(message.query_result.get("linked_order_id")),
                "linked_order_tracking_code": str(
                    message.query_result.get("linked_order_tracking_code") or ""
                ),
            }
            break

    db.add(
        AIConversation(
            session_id=session_id,
            user_id=messages[0].user_id,
            role="assistant",
            message=SUPPORT_SESSION_CLOSED_MESSAGE,
            intent=SUPPORT_SESSION_CLOSED_INTENT,
            query_result=linked_order_meta,
        )
    )


async def mark_ai_handoff_ticket_in_progress(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    agent: User | None = None,
) -> None:
    ticket = await _find_ai_handoff_ticket_for_session(db, session_id)
    if not ticket or ticket.status == "resolved":
        return
    if ticket.status == "new":
        ticket.status = "in_progress"
    if agent is not None:
        ticket.assigned_to_user_id = agent.id
    db.add(ticket)
    await db.flush()


async def resolve_ai_handoff_ticket_for_session(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    actor: User | None = None,
) -> SupportTicket | None:
    ticket = await _find_ai_handoff_ticket_for_session(db, session_id)
    if not ticket:
        return None
    if ticket.status != "resolved":
        ticket.status = "resolved"
        ticket.resolved_at = _utc_now()
    if actor is not None:
        ticket.assigned_to_user_id = actor.id
    db.add(ticket)
    await db.flush()
    return ticket


async def resolve_ai_handoff_escalations_for_ticket(
    db: AsyncSession,
    *,
    ticket: SupportTicket,
    actor: User | None = None,
) -> None:
    metadata = _ticket_source_metadata(ticket)
    if metadata.get("source") != "ai_handoff":
        return

    session_id = _linked_session_uuid_from_ticket(ticket)
    if not session_id:
        return

    escalations = (
        await db.execute(
            select(Escalation)
            .options(selectinload(Escalation.conversation))
            .join(AIConversation, Escalation.conversation_id == AIConversation.id)
            .where(
                AIConversation.session_id == session_id,
                Escalation.status == "OPEN",
            )
            .order_by(Escalation.escalated_at.desc())
        )
    ).scalars().all()

    resolved_at = _utc_now()
    for escalation in escalations:
        escalation.status = "RESOLVED"
        escalation.resolved_at = resolved_at
        if actor is not None:
            escalation.escalated_to_user_id = actor.id
        db.add(escalation)

    await _close_support_session_once(db, session_id)
    await db.flush()


async def create_ticket(
    db: AsyncSession,
    data: TicketCreate,
    actor: User | None = None,
) -> TicketResponse:
    if actor is not None:
        _ensure_support_manager(actor)
    priority = (data.priority or "medium").strip().lower()
    if priority not in TICKET_PRIORITY_VALUES:
        raise HTTPException(status_code=400, detail="Invalid priority")
    category = (data.category or "general").strip().lower()

    ticket = SupportTicket(
        reference_code=await _next_ticket_reference(db),
        title=data.title.strip(),
        description=data.description.strip(),
        priority=priority,
        status="new",
        category=category,
        customer_name=(data.customer_name or "").strip() or None,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return _ticket_response(ticket)


async def sync_vendor_ticket_to_support_ticket(
    db: AsyncSession,
    *,
    vendor: User,
    vendor_ticket: VendorSupportTicket,
    source: str | None = None,
    metadata_updates: dict[str, str | None] | None = None,
) -> SupportTicket:
    support_manager = await get_default_support_manager(db)
    existing = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(
                SupportTicket.notes.contains(
                    f"[meta:linked_vendor_ticket_id={vendor_ticket.id}]"
                )
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    visible_notes = None
    existing_metadata: dict[str, str] = {}
    if existing:
        existing_metadata, visible_notes = _split_ticket_notes(existing.notes)

    metadata = {
        **existing_metadata,
        "source": existing_metadata.get("source") or source or "vendor_portal",
        "linked_vendor_ticket_id": str(vendor_ticket.id),
        "linked_vendor_id": str(vendor.id),
        "linked_order_id": str(vendor_ticket.order_id) if vendor_ticket.order_id else None,
    }
    if source:
        metadata["source"] = source
    if metadata_updates:
        metadata.update(metadata_updates)
    vendor_name = (vendor.company_name or vendor.name or vendor.email or "Vendor").strip()

    ticket = existing or SupportTicket(reference_code=await _next_ticket_reference(db))
    ticket.title = vendor_ticket.subject.strip()
    ticket.description = vendor_ticket.description.strip()
    ticket.priority = _support_priority_from_vendor(vendor_ticket.priority)
    ticket.status = _support_status_from_vendor(vendor_ticket.status)
    ticket.category = "vendor_support"
    ticket.customer_name = vendor_name
    if support_manager:
        ticket.assigned_to_user_id = support_manager.id
    ticket.notes = _compose_ticket_notes(metadata=metadata, visible_notes=visible_notes)
    ticket.resolved_at = _utc_now() if ticket.status == "resolved" else None
    db.add(ticket)
    await db.flush()
    return ticket


async def sync_ai_handoff_ticket(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    user: User,
    reason: str,
    latest_user_message: str,
) -> SupportTicket:
    support_manager = await get_default_support_manager(db)
    existing = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(
                SupportTicket.notes.contains(
                    f"[meta:linked_session_id={session_id}]"
                )
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    visible_notes = None
    if existing:
        _, visible_notes = _split_ticket_notes(existing.notes)

    metadata = {
        "source": "ai_handoff",
        "linked_session_id": str(session_id),
        "linked_user_id": str(user.id),
        "requester_type": "Vendor"
        if getattr(getattr(user, "role", None), "name", None) == "VENDOR"
        else "Customer",
    }

    display_name = (user.name or user.email or "Customer").strip()
    title = f"AI Chat Handoff: {display_name}"
    description = (
        f"{reason.strip()}\n\nLatest user message:\n{latest_user_message.strip()}"
        if latest_user_message.strip()
        else reason.strip()
    )

    ticket = existing or SupportTicket(reference_code=await _next_ticket_reference(db))
    ticket.title = title
    ticket.description = description
    ticket.priority = _handoff_ticket_priority(reason)
    ticket.status = "new"
    ticket.category = "general"
    ticket.customer_name = display_name
    if support_manager:
        ticket.assigned_to_user_id = support_manager.id
    ticket.notes = _compose_ticket_notes(metadata=metadata, visible_notes=visible_notes)
    ticket.resolved_at = None
    db.add(ticket)
    await db.flush()
    return ticket


async def list_tickets(db: AsyncSession) -> TicketListResponse:
    tickets = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .order_by(SupportTicket.created_at.desc())
        )
    ).scalars().all()

    stats = TicketStats(
        total=len(tickets),
        new=sum(1 for t in tickets if t.status == "new"),
        in_progress=sum(1 for t in tickets if t.status == "in_progress"),
        resolved=sum(1 for t in tickets if t.status == "resolved"),
        urgent=sum(1 for t in tickets if t.priority == "urgent"),
    )
    order_map = await _linked_order_tracking_map(db, tickets)
    vendor_ticket_map = await _linked_vendor_ticket_map(db, tickets)

    return TicketListResponse(
        tickets=[
            _ticket_response(
                t,
                order_tracking_code=order_map.get(_linked_order_uuid_from_ticket(t)),
                vendor_ticket=vendor_ticket_map.get(_linked_vendor_ticket_uuid_from_ticket(t)),
            )
            for t in tickets
        ],
        stats=stats,
        agents=await _list_support_agents(db),
    )


async def get_recovery_tickets_count(db: AsyncSession) -> dict:
    tickets = (
        await db.execute(
            select(SupportTicket).where(
                SupportTicket.customer_name == "AI Support Analytics",
                SupportTicket.status != "resolved",
            )
        )
    ).scalars().all()
    return {"count": len(tickets)}


async def update_ticket(
    db: AsyncSession, ticket_id: uuid.UUID, data: TicketUpdate, actor: User | None = None
) -> TicketResponse:
    if actor is not None:
        _ensure_support_manager(actor)
    ticket = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(SupportTicket.id == ticket_id)
        )
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    metadata, visible_notes = _split_ticket_notes(ticket.notes)
    source = metadata.get("source", "manual")
    current_resolution_action = (metadata.get("resolution_action") or "").strip().lower()
    should_resolve_linked_ai_handoff = False

    if data.status is not None:
        s = data.status.strip().lower()
        if s not in TICKET_STATUS_VALUES:
            raise HTTPException(status_code=400, detail="Invalid status")
        if source == "warehouse_inbound" and s == "resolved":
            requested_resolution = (
                data.resolution_action.strip().lower()
                if data.resolution_action is not None
                else current_resolution_action
            )
            if requested_resolution not in {"vendor_accept_move", "vendor_take_back"}:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Warehouse inbound tickets must be resolved with "
                        "Vendor Cleared For Move or Vendor Will Take Back."
                    ),
                )
        ticket.status = s
        ticket.resolved_at = _utc_now() if s == "resolved" else None
        should_resolve_linked_ai_handoff = source == "ai_handoff" and s == "resolved"
    if data.priority is not None:
        p = data.priority.strip().lower()
        if p not in TICKET_PRIORITY_VALUES:
            raise HTTPException(status_code=400, detail="Invalid priority")
        ticket.priority = p
    if data.category is not None:
        ticket.category = data.category.strip().lower()
    if data.notes is not None:
        visible_notes = data.notes
        ticket.notes = _compose_ticket_notes(
            metadata=metadata,
            visible_notes=data.notes,
        )
    if data.resolution_action is not None:
        resolution_action = data.resolution_action.strip().lower()
        if resolution_action not in INBOUND_RESOLUTION_LABELS:
            raise HTTPException(status_code=400, detail="Invalid resolution action")
        metadata["resolution_action"] = resolution_action
        ticket.notes = _compose_ticket_notes(
            metadata=metadata,
            visible_notes=visible_notes,
        )
        linked_damage_report_raw = metadata.get("linked_damage_report_id")
        if linked_damage_report_raw:
            try:
                linked_damage_report_id = uuid.UUID(linked_damage_report_raw)
            except ValueError:
                linked_damage_report_id = None
            if linked_damage_report_id:
                report = (
                    await db.execute(
                        select(DamageReport).where(DamageReport.id == linked_damage_report_id)
                    )
                ).scalar_one_or_none()
                if report:
                    report.status = (
                        "vendor_take_back"
                        if resolution_action == "vendor_take_back"
                        else "vendor_accept_move"
                    )
                    support_summary = INBOUND_RESOLUTION_LABELS[resolution_action]
                    if visible_notes and visible_notes.strip():
                        support_summary = f"{support_summary}\n{visible_notes.strip()}"
                    report.support_notes = support_summary
                    db.add(report)
    if "assigned_to_user_id" in data.model_fields_set:
        ticket.assigned_to_user_id = data.assigned_to_user_id

    linked_vendor_ticket_id_raw = _ticket_source_metadata(ticket).get("linked_vendor_ticket_id")
    vendor_ticket: VendorSupportTicket | None = None
    if linked_vendor_ticket_id_raw:
        try:
            linked_vendor_ticket_id = uuid.UUID(linked_vendor_ticket_id_raw)
        except ValueError:
            linked_vendor_ticket_id = None
        if linked_vendor_ticket_id:
            vendor_ticket = (
                await db.execute(
                    select(VendorSupportTicket)
                    .options(selectinload(VendorSupportTicket.replies))
                    .where(VendorSupportTicket.id == linked_vendor_ticket_id)
                )
            ).scalar_one_or_none()
            if vendor_ticket:
                vendor_ticket.status = _vendor_status_from_support(ticket.status)
                vendor_ticket.priority = _vendor_priority_from_support(ticket.priority)
                db.add(vendor_ticket)
                if data.resolution_action is not None:
                    linked_vendor_id_raw = _ticket_source_metadata(ticket).get("linked_vendor_id")
                    if linked_vendor_id_raw:
                        try:
                            linked_vendor_id = uuid.UUID(linked_vendor_id_raw)
                        except ValueError:
                            linked_vendor_id = None
                        if linked_vendor_id:
                            await create_user_notification(
                                db,
                                user_id=linked_vendor_id,
                                title="Inbound issue updated",
                                message=(
                                    f"{ticket.reference_code}: "
                                    f"{INBOUND_RESOLUTION_LABELS[data.resolution_action.strip().lower()]}"
                                ),
                                notification_type="info",
                            )

    if should_resolve_linked_ai_handoff:
        await resolve_ai_handoff_escalations_for_ticket(db, ticket=ticket, actor=actor)

    await db.flush()
    await db.refresh(ticket)
    if ticket.assigned_to_user_id is not None:
        await db.refresh(ticket, attribute_names=["assigned_to_user"])
    order_map = await _linked_order_tracking_map(db, [ticket])
    order_tracking_code = order_map.get(_linked_order_uuid_from_ticket(ticket))
    return _ticket_response(
        ticket,
        order_tracking_code=order_tracking_code,
        vendor_ticket=vendor_ticket,
    )


async def reply_to_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    data: AgentReplyRequest,
    actor: User,
) -> TicketResponse:
    _ensure_support_manager(actor)

    ticket = (
        await db.execute(
            select(SupportTicket)
            .options(joinedload(SupportTicket.assigned_to_user))
            .where(SupportTicket.id == ticket_id)
        )
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    linked_vendor_ticket_id = _linked_vendor_ticket_uuid_from_ticket(ticket)
    if not linked_vendor_ticket_id:
        raise HTTPException(
            status_code=400,
            detail="Only vendor-linked tickets support dashboard chat replies.",
        )

    vendor_ticket = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.id == linked_vendor_ticket_id)
        )
    ).scalar_one_or_none()
    if not vendor_ticket:
        raise HTTPException(status_code=404, detail="Linked vendor ticket not found")
    if ticket.status == "resolved" or vendor_ticket.status == "Resolved":
        raise HTTPException(
            status_code=409,
            detail="This vendor chat is closed because the ticket has been resolved.",
        )

    db.add(
        VendorSupportReply(
            ticket_id=vendor_ticket.id,
            from_name=f"Support Team ({actor.name})",
            message=data.message.strip(),
        )
    )

    if ticket.status == "new":
        ticket.status = "in_progress"

    vendor_ticket.priority = _vendor_priority_from_support(ticket.priority)
    vendor_ticket.status = _vendor_status_from_support(ticket.status)
    db.add(vendor_ticket)
    db.add(ticket)

    linked_vendor_id_raw = _ticket_source_metadata(ticket).get("linked_vendor_id")
    if linked_vendor_id_raw:
        try:
            linked_vendor_id = uuid.UUID(linked_vendor_id_raw)
        except ValueError:
            linked_vendor_id = None
        if linked_vendor_id:
            await create_user_notification(
                db,
                user_id=linked_vendor_id,
                title="Support replied to your inbound issue",
                message=f"{ticket.reference_code}: {data.message.strip()}",
                notification_type="info",
            )

    await db.flush()
    await db.refresh(ticket)
    await db.refresh(vendor_ticket, attribute_names=["replies"])
    order_map = await _linked_order_tracking_map(db, [ticket])
    return _ticket_response(
        ticket,
        order_tracking_code=order_map.get(_linked_order_uuid_from_ticket(ticket)),
        vendor_ticket=vendor_ticket,
    )


async def delete_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    actor: User | None = None,
) -> None:
    if actor is not None:
        _ensure_support_manager(actor)
    ticket = (
        await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if _ticket_source_metadata(ticket).get("source") in {"vendor_portal", "warehouse_inbound", "ai_handoff"}:
        raise HTTPException(
            status_code=400,
            detail="System-linked tickets cannot be deleted from the AI dashboard. Resolve them instead.",
        )
    await db.delete(ticket)
    await db.flush()


# ── AI Support — Damage Reports ───────────────────────────────────────────────

async def _latest_sentiment_for_users(
    db: AsyncSession,
    user_ids: list[uuid.UUID],
) -> dict[uuid.UUID, str]:
    """Return {user_id: sentiment} for the latest user message in ai_conversations."""
    if not user_ids:
        return {}
    rows = (
        await db.execute(
            select(AIConversation.user_id, AIConversation.message)
            .where(
                AIConversation.user_id.in_(user_ids),
                AIConversation.role == "user",
            )
            .order_by(AIConversation.user_id.asc(), AIConversation.created_at.desc())
        )
    ).all()
    result: dict[uuid.UUID, str] = {}
    for user_id, message in rows:
        if user_id not in result:
            result[user_id] = await _sentiment_label(message)
    return result


def _parse_support_messages(raw: list[dict] | None) -> list[SupportMessageItem]:
    result = []
    for m in (raw or []):
        try:
            result.append(SupportMessageItem(
                text=m.get("text", ""),
                sent_by=m.get("sent_by", "Support Agent"),
                sent_at=m.get("sent_at", ""),
            ))
        except Exception:
            pass
    return result


def _support_damage_report_item(
    report: DamageReport,
    user: User,
    order_tracking_code: str | None,
    sentiment: str | None,
) -> SupportDamageReportItem:
    return SupportDamageReportItem(
        id=report.id,
        reference_code=report.reference_code,
        customer_id=report.customer_id,
        customer_name=user.name,
        customer_email=user.email,
        order_id=report.order_id,
        order_tracking_code=order_tracking_code,
        description=report.description,
        photos=list(report.photos or []),
        flow_type=report.flow_type,
        status=report.status,
        support_notes=report.support_notes,
        support_messages=_parse_support_messages(getattr(report, "support_messages", None)),
        sentiment=sentiment,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


async def list_support_damage_reports(
    db: AsyncSession,
) -> SupportDamageReportListResponse:
    reports = (
        await db.execute(
            select(DamageReport)
            .options(joinedload(DamageReport.customer))
            .order_by(DamageReport.created_at.desc())
        )
    ).scalars().all()

    # Gather order tracking codes
    order_ids = [r.order_id for r in reports if r.order_id]
    order_map: dict[uuid.UUID, str] = {}
    if order_ids:
        order_rows = (
            await db.execute(
                select(Order.id, Order.tracking_code).where(Order.id.in_(order_ids))
            )
        ).all()
        order_map = {row.id: row.tracking_code for row in order_rows}

    # Gather sentiments
    user_ids = list({r.customer_id for r in reports})
    sentiment_map = await _latest_sentiment_for_users(db, user_ids)

    items = [
        _support_damage_report_item(
            report=r,
            user=r.customer,
            order_tracking_code=order_map.get(r.order_id) if r.order_id else None,
            sentiment=sentiment_map.get(r.customer_id),
        )
        for r in reports
        if r.customer
    ]

    stats = SupportDamageReportStats(
        total=len(items),
        reported=sum(1 for i in items if i.status == "reported"),
        photo_review=sum(1 for i in items if i.flow_type == "photo_review"),
        pickup_inspection=sum(1 for i in items if i.flow_type == "pickup_inspection"),
        under_review=sum(1 for i in items if i.status in ("under_review", "Under Review")),
    )
    return SupportDamageReportListResponse(reports=items, stats=stats)


async def create_support_damage_report(
    db: AsyncSession,
    data: SupportDamageReportCreate,
) -> SupportDamageReportItem:
    """Support creates a damage report on a customer's behalf."""
    customer = (
        await db.execute(
            select(User).options(selectinload(User.role)).where(User.id == data.customer_id)
        )
    ).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    order_tracking_code: str | None = None
    if data.order_id:
        order_row = (
            await db.execute(select(Order.tracking_code).where(Order.id == data.order_id))
        ).scalar_one_or_none()
        order_tracking_code = order_row

    flow_type = data.flow_type if data.flow_type in {"photo_review", "pickup_inspection"} else "photo_review"

    import uuid as _uuid
    report = DamageReport(
        reference_code=f"DMG-{_uuid.uuid4().hex[:6].upper()}",
        customer_id=data.customer_id,
        order_id=data.order_id,
        description=data.description.strip(),
        photos=[],
        flow_type=flow_type,
        status="reported",
        qr_code=f"QR-{_uuid.uuid4().hex[:8].upper()}",
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    return _support_damage_report_item(
        report=report,
        user=customer,
        order_tracking_code=order_tracking_code,
        sentiment=None,
    )


async def update_damage_report_notes(
    db: AsyncSession,
    report_id: uuid.UUID,
    data: SupportDamageReportNotesUpdate,
) -> SupportDamageReportItem:
    report = (
        await db.execute(
            select(DamageReport)
            .options(joinedload(DamageReport.customer))
            .where(DamageReport.id == report_id)
        )
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Damage report not found")

    report.support_notes = (data.support_notes or "").strip() or None
    await db.flush()

    order_tracking_code: str | None = None
    if report.order_id:
        order_tracking_code = (
            await db.execute(select(Order.tracking_code).where(Order.id == report.order_id))
        ).scalar_one_or_none()

    sentiment_map = await _latest_sentiment_for_users(db, [report.customer_id])
    return _support_damage_report_item(
        report=report,
        user=report.customer,
        order_tracking_code=order_tracking_code,
        sentiment=sentiment_map.get(report.customer_id),
    )


async def send_support_message(
    db: AsyncSession,
    report_id: uuid.UUID,
    data: SupportMessageCreate,
    agent: User,
) -> SupportDamageReportItem:
    """Append a message to a damage report's support_messages log AND push
    it into the customer's AI chat session so they see it in their chat UI."""
    report = (
        await db.execute(
            select(DamageReport)
            .options(joinedload(DamageReport.customer))
            .where(DamageReport.id == report_id)
        )
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Damage report not found")

    text = data.text.strip()
    now = _utc_now()

    new_message = {
        "text": text,
        "sent_by": agent.name or data.sent_by,
        "sent_at": now.isoformat(),
    }
    current = list(report.support_messages or [])
    current.append(new_message)
    # Reassign to mark the column dirty for SQLAlchemy
    from sqlalchemy.orm.attributes import flag_modified
    report.support_messages = current
    flag_modified(report, "support_messages")

    # ── Mirror the message into the customer's AI chat session ──────────────
    # Find the customer's most recent session_id (reuse it so the thread stays
    # in one place). If the customer has never chatted, create a new session.
    latest_session_id: uuid.UUID | None = (
        await db.execute(
            select(AIConversation.session_id)
            .where(AIConversation.user_id == report.customer_id)
            .order_by(AIConversation.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    chat_session_id = latest_session_id or uuid.uuid4()

    ref = report.reference_code
    chat_text = f"[Support — {ref}] {text}"

    db.add(
        AIConversation(
            session_id=chat_session_id,
            user_id=report.customer_id,
            author_user_id=agent.id,
            role="assistant",
            message=chat_text,
            intent="support_message",
        )
    )

    await db.flush()

    order_tracking_code: str | None = None
    if report.order_id:
        order_tracking_code = (
            await db.execute(select(Order.tracking_code).where(Order.id == report.order_id))
        ).scalar_one_or_none()

    sentiment_map = await _latest_sentiment_for_users(db, [report.customer_id])
    return _support_damage_report_item(
        report=report,
        user=report.customer,
        order_tracking_code=order_tracking_code,
        sentiment=sentiment_map.get(report.customer_id),
    )


# ── AI Support — Refund Center ────────────────────────────────────────────────

async def list_support_refund_cases(
    db: AsyncSession,
) -> SupportRefundCaseListResponse:
    cases = (
        await db.execute(
            select(LogisticsReturnCase).order_by(LogisticsReturnCase.created_at.desc())
        )
    ).scalars().all()

    # Resolve customer_id via order_id → orders.customer_id
    order_ids = [c.order_id for c in cases if c.order_id]
    customer_id_map: dict[uuid.UUID, uuid.UUID] = {}
    if order_ids:
        rows = (
            await db.execute(
                select(Order.id, Order.customer_id).where(Order.id.in_(order_ids))
            )
        ).all()
        customer_id_map = {row.id: row.customer_id for row in rows}

    user_ids = list(set(customer_id_map.values()))
    sentiment_map = await _latest_sentiment_for_users(db, user_ids)

    items = [
        SupportRefundCaseItem(
            id=c.id,
            reference_code=c.reference_code,
            customer_name=c.customer_name,
            customer_id=customer_id_map.get(c.order_id) if c.order_id else None,
            order_id=c.order_id,
            original_price=c.original_price,
            refund_amount=c.refund_amount,
            status=c.status,
            flow_type=getattr(c, "flow_type", "photo_review") or "photo_review",
            is_urgent=bool(c.is_urgent),
            urgent_reason=c.urgent_reason,
            support_notes=c.support_notes,
            sentiment=sentiment_map.get(customer_id_map.get(c.order_id)) if c.order_id else None,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cases
    ]

    total_refunded = sum(i.refund_amount for i in items if i.status in ("Claimed", "Refunded", "Closed"))
    pending = sum(1 for i in items if i.status in ("Pending", "Under Review", "Claims Reviewed", "Physically Inspected"))
    urgent = sum(1 for i in items if i.is_urgent)

    return SupportRefundCaseListResponse(
        cases=items,
        stats=SupportRefundCaseStats(
            total_refunded_value=round(total_refunded, 2),
            pending_decision=pending,
            urgent_count=urgent,
        ),
    )


async def flag_refund_case_urgent(
    db: AsyncSession,
    case_id: uuid.UUID,
    data: SupportRefundCaseUrgentUpdate,
) -> SupportRefundCaseItem:
    case = (
        await db.execute(
            select(LogisticsReturnCase).where(LogisticsReturnCase.id == case_id)
        )
    ).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return case not found")

    case.is_urgent = data.is_urgent
    case.urgent_reason = (data.urgent_reason or "").strip() or None
    await db.flush()

    customer_id: uuid.UUID | None = None
    if case.order_id:
        customer_id = (
            await db.execute(select(Order.customer_id).where(Order.id == case.order_id))
        ).scalar_one_or_none()

    sentiment_map = await _latest_sentiment_for_users(db, [customer_id] if customer_id else [])
    return SupportRefundCaseItem(
        id=case.id,
        reference_code=case.reference_code,
        customer_name=case.customer_name,
        customer_id=customer_id,
        order_id=case.order_id,
        original_price=case.original_price,
        refund_amount=case.refund_amount,
        status=case.status,
        flow_type=getattr(case, "flow_type", "photo_review") or "photo_review",
        is_urgent=bool(case.is_urgent),
        urgent_reason=case.urgent_reason,
        support_notes=case.support_notes,
        sentiment=sentiment_map.get(customer_id) if customer_id else None,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


# ── AI Support — Customer History ─────────────────────────────────────────────

async def get_customer_history(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> CustomerHistoryResponse:
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    total_orders = int(
        (
            await db.execute(
                select(func.count()).select_from(Order).where(Order.customer_id == user_id)
            )
        ).scalar_one()
    )
    damage_reports_count = int(
        (
            await db.execute(
                select(func.count()).select_from(DamageReport).where(DamageReport.customer_id == user_id)
            )
        ).scalar_one()
    )
    escalations_count = int(
        (
            await db.execute(
                select(func.count(func.distinct(AIConversation.session_id)))
                .join(Escalation, Escalation.conversation_id == AIConversation.id)
                .where(AIConversation.user_id == user_id)
            )
        ).scalar_one()
    )

    # Latest sentiment from most recent user message
    latest_msg = (
        await db.execute(
            select(AIConversation.message)
            .where(AIConversation.user_id == user_id, AIConversation.role == "user")
            .order_by(AIConversation.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    last_sentiment = await _sentiment_label(latest_msg) if latest_msg else None

    return CustomerHistoryResponse(
        total_orders=total_orders,
        damage_reports_count=damage_reports_count,
        escalations_count=escalations_count,
        last_sentiment=last_sentiment,
    )


# ── AI System Settings ────────────────────────────────────────────────────────

# ── Knowledge Base CRUD ───────────────────────────────────────────────────────

from app.schemas.ai_config import (  # noqa: E402
    KnowledgeArticleCreate,
    KnowledgeArticleListResponse,
    KnowledgeArticleResponse,
    KnowledgeArticleUpdate,
)


def _article_to_schema(a: AIKnowledgeArticle) -> KnowledgeArticleResponse:
    return KnowledgeArticleResponse(
        id=a.id,
        audience=a.audience,
        title=a.title,
        keywords=list(a.keywords or []),
        content=a.content,
        category=a.category,
        article_type=a.article_type,
        is_active=a.is_active,
        likes=a.likes,
        author_initials=a.author_initials,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def _get_initials(name: str) -> str:
    parts = (name or "").split()
    if not parts:
        return "??"
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else parts[0][-1])).upper()


def _slugify(title: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:80]


async def list_knowledge_articles(
    db: AsyncSession,
    active_only: bool = True,
    audience: str | None = None,
) -> KnowledgeArticleListResponse:
    q = select(AIKnowledgeArticle)
    if active_only:
        q = q.where(AIKnowledgeArticle.is_active.is_(True))
    if audience:
        q = q.where(
            (AIKnowledgeArticle.audience == audience)
            | (AIKnowledgeArticle.audience == "ALL")
        )
    q = q.order_by(AIKnowledgeArticle.likes.desc(), AIKnowledgeArticle.title)
    rows = list((await db.execute(q)).scalars().all())
    return KnowledgeArticleListResponse(
        articles=[_article_to_schema(r) for r in rows],
        total=len(rows),
    )


async def get_knowledge_article_by_id(
    db: AsyncSession, article_id: str
) -> KnowledgeArticleResponse | None:
    row = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    return _article_to_schema(row) if row else None


async def create_knowledge_article(
    db: AsyncSession, data: KnowledgeArticleCreate, actor: User
) -> KnowledgeArticleResponse:
    import uuid as _uuid

    article_id = data.id or _slugify(data.title)
    existing = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    if existing:
        article_id = f"{article_id}_{_uuid.uuid4().hex[:6]}"

    row = AIKnowledgeArticle(
        id=article_id,
        audience=data.audience,
        title=data.title,
        keywords=data.keywords or [],
        content=data.content,
        category=data.category,
        article_type=data.article_type,
        is_active=True,
        likes=0,
        author_initials=_get_initials(actor.name),
        updated_by_user_id=actor.id,
    )
    db.add(row)
    await db.flush()
    return _article_to_schema(row)


async def update_knowledge_article(
    db: AsyncSession, article_id: str, data: KnowledgeArticleUpdate, actor: User
) -> KnowledgeArticleResponse | None:
    row = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    if not row:
        return None

    if data.title is not None:
        row.title = data.title
    if data.audience is not None:
        row.audience = data.audience
    if data.keywords is not None:
        row.keywords = data.keywords
    if data.content is not None:
        row.content = data.content
    if data.category is not None:
        row.category = data.category
    if data.article_type is not None:
        row.article_type = data.article_type
    if data.is_active is not None:
        row.is_active = data.is_active

    row.updated_by_user_id = actor.id
    row.updated_at = datetime.now(UTC)
    await db.flush()
    return _article_to_schema(row)


async def delete_knowledge_article(db: AsyncSession, article_id: str) -> bool:
    row = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    if not row:
        return False
    await db.delete(row)
    await db.flush()
    return True


async def like_knowledge_article(
    db: AsyncSession, article_id: str
) -> KnowledgeArticleResponse | None:
    row = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    if not row:
        return None
    row.likes += 1
    await db.flush()
    return _article_to_schema(row)
