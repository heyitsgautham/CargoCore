"""Support manager lookup, notifications, public contact submissions and support settings."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.logistics import LogisticsNotification
from app.models.support_contact import SupportContactSubmission
from app.models.support_ticket import SupportTicket
from app.models.user import Role, User
from app.schemas.ai import (
    ContactSubmissionCreatePublic,
    ContactSubmissionListResponse,
    ContactSubmissionReplyRequest,
    ContactSubmissionResponse,
    ContactSubmissionStats,
    ContactSubmissionUpdate,
    SupportSettings,
    SupportSettingsResponse,
)
from app.services.support.common import (
    SUPPORT_MANAGER_ROLE_NAME,
    SUPPORT_ROLE_NAMES,
    _contact_submission_response,
    _ensure_support_manager,
    _get_or_create_support_settings,
    _list_support_agents,
    _next_contact_reference,
    _normalize_contact_priority,
    _normalize_contact_status,
    _settings_to_response,
)
from app.utils.email import send_email, support_contact_reply_email_html


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
