"""The support dashboard: headline counts and the live activity feed."""

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.support_ticket import SupportTicket
from app.schemas.ai import (
    SupportDashboardFeedItem,
    SupportDashboardResponse,
    SupportDashboardStats,
)
from app.services.support.common import (
    _utc_now,
)
from app.services.support.contacts import list_contact_submissions
from app.services.support.sessions import (
    _load_support_session_items,
)


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
