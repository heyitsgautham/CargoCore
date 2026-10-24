"""Support constants, settings, contact normalisation and shared support-desk lookups."""

import re
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_support_settings import AISupportSettings
from app.models.support_contact import SupportContactSubmission
from app.models.user import Role, User
from app.schemas.ai import (
    ContactSubmissionResponse,
    SupportAgentSummary,
    SupportIntegrationStatus,
    SupportSettings,
    SupportSettingsResponse,
)

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
