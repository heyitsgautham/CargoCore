"""Damage reports, refund cases and customer history for support agents."""

import contextlib
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.logistics import LogisticsReturnCase
from app.models.order import DamageReport, Order
from app.models.user import User
from app.schemas.ai import (
    CustomerHistoryResponse,
    SupportDamageReportCreate,
    SupportDamageReportItem,
    SupportDamageReportListResponse,
    SupportDamageReportNotesUpdate,
    SupportDamageReportStats,
    SupportMessageCreate,
    SupportMessageItem,
    SupportRefundCaseItem,
    SupportRefundCaseListResponse,
    SupportRefundCaseStats,
    SupportRefundCaseUrgentUpdate,
)
from app.services.support.analytics_format import _sentiment_label
from app.services.support.common import _utc_now

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
        with contextlib.suppress(Exception):
            result.append(SupportMessageItem(
                text=m.get("text", ""),
                sent_by=m.get("sent_by", "Support Agent"),
                sent_at=m.get("sent_at", ""),
            ))
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
