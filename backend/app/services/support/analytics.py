"""Support analytics for a time range, and acting on an analytics insight."""

import uuid
from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.order import DamageReport
from app.models.support_contact import SupportContactSubmission
from app.models.support_ticket import SupportTicket
from app.schemas.ai import (
    SupportAnalyticsEscalationReason,
    SupportAnalyticsInsightExecutionResponse,
    SupportAnalyticsMetric,
    SupportAnalyticsResolutionChart,
    SupportAnalyticsResponse,
    SupportAnalyticsSentimentChart,
)
from app.services.support.analytics_format import (
    _analytics_bucket_starts,
    _analytics_label,
    _analytics_sentiment_label,
    _analytics_ticket_marker,
    _bucket_for_datetime,
    _build_analytics_insights,
    _escalation_reason_label,
    _extract_analytics_ticket_marker,
    _format_count,
    _format_currency,
    _format_duration_seconds,
    _next_analytics_window_start,
    _normalize_analytics_range,
    _trend_descriptor,
)
from app.services.support.common import (
    ANALYTICS_HOURLY_RATE,
    ANALYTICS_INSIGHT_RECOMMENDATIONS,
    ANALYTICS_MINUTES_SAVED_PER_AI_RESOLUTION,
    SENTIMENT_SCORES,
    _utc_now,
)
from app.services.support.sessions import (
    _is_human_authored_support_message,
)
from app.services.support.ticket_helpers import _next_ticket_reference


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
