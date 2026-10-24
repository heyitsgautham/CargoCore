"""Manager meetings with optional Daily.co rooms."""

from __future__ import annotations

import re
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.logistics import (
    LogisticsMeeting,
)
from app.models.user import Role, User
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    LogisticsMeetingCreate,
    LogisticsMeetingItem,
    LogisticsMeetingParticipantItem,
    LogisticsMeetingUpdate,
)

_SUPPORTED_MEETING_TYPES = {"gmeet", "zoom", "jitsi", "other"}
_TIME_LABEL_RE = re.compile(r"^\d{2}:\d{2}$")


def _normalize_meeting_type(value: str | None) -> str:
    normalized = (value or "other").strip().lower()
    return normalized if normalized in _SUPPORTED_MEETING_TYPES else "other"


def _normalize_meeting_link(value: str | None) -> str:
    trimmed = (value or "").strip()
    if not trimmed:
        return ""
    if re.match(r"^https?://", trimmed, re.IGNORECASE):
        return trimmed
    if re.match(r"^(meet\.google\.com|meet\.jit\.si|[\w-]+\.zoom\.(us|com)|zoom\.us|zoom\.com)", trimmed, re.IGNORECASE):
        return f"https://{trimmed}"
    return trimmed


async def _create_daily_room(topic: str) -> str:
    settings = get_settings()
    if not settings.daily_api_key:
        raise HTTPException(status_code=500, detail="Daily.co API key not configured")

    slug = re.sub(r"[^a-z0-9-]", "", topic.lower().replace(" ", "-"))[:30].strip("-")
    import secrets
    room_name = f"logistics-{slug}-{secrets.token_hex(3)}"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://api.daily.co/v1/rooms",
            headers={"Authorization": f"Bearer {settings.daily_api_key}"},
            json={"name": room_name, "privacy": "public", "properties": {"enable_prejoin_ui": False}},
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="Failed to create Daily.co room")

    return resp.json()["url"]


def _validate_meeting_time_range(start_time: str, end_time: str) -> None:
    if not _TIME_LABEL_RE.match(start_time) or not _TIME_LABEL_RE.match(end_time):
        raise HTTPException(status_code=400, detail="Meeting time must use HH:MM format")
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="Meeting end time must be after start time")


async def _normalize_meeting_participants(
    db: AsyncSession,
    participant_ids: list[UUID] | None,
    creator_id: UUID,
) -> list[str]:
    candidate_ids: list[UUID] = []
    seen: set[str] = set()

    for raw_id in [*(participant_ids or []), creator_id]:
        normalized = str(raw_id)
        if normalized in seen:
            continue
        seen.add(normalized)
        candidate_ids.append(raw_id)

    if not candidate_ids:
        return [str(creator_id)]

    existing_ids = (
        await db.execute(select(User.id).where(User.id.in_(candidate_ids)))
    ).scalars().all()
    existing_lookup = {str(item) for item in existing_ids}

    normalized_ids = [str(item) for item in candidate_ids if str(item) in existing_lookup]
    if str(creator_id) not in normalized_ids:
        normalized_ids.append(str(creator_id))
    return normalized_ids


def _meeting_to_item(meeting: LogisticsMeeting) -> LogisticsMeetingItem:
    participants: list[UUID] = []
    for participant_id in meeting.participant_ids or []:
        try:
            participants.append(UUID(str(participant_id)))
        except (TypeError, ValueError):
            continue

    return LogisticsMeetingItem(
        id=meeting.id,
        topic=meeting.topic,
        description=meeting.description or "",
        meeting_type=_normalize_meeting_type(meeting.meeting_type),
        link=meeting.meeting_link,
        date=meeting.meeting_date,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        participants=participants,
        created_by_id=meeting.created_by_id,
        warehouse_id=meeting.warehouse_id,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


async def _get_meeting_for_user(db: AsyncSession, meeting_id: UUID, current_user: User) -> LogisticsMeeting:
    meeting = (
        await db.execute(
            select(LogisticsMeeting).where(
                LogisticsMeeting.id == meeting_id,
                or_(
                    LogisticsMeeting.created_by_id == current_user.id,
                    LogisticsMeeting.participant_ids.contains([str(current_user.id)]),
                ),
            )
        )
    ).scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


def _ensure_meeting_owner(meeting: LogisticsMeeting, current_user: User) -> None:
    if meeting.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the meeting creator can modify this meeting")


async def list_meetings(db: AsyncSession, current_user: User) -> list[LogisticsMeetingItem]:
    meetings = (
        await db.execute(
            select(LogisticsMeeting)
            .where(
                or_(
                    LogisticsMeeting.created_by_id == current_user.id,
                    LogisticsMeeting.participant_ids.contains([str(current_user.id)]),
                )
            )
            .order_by(LogisticsMeeting.meeting_date.asc(), LogisticsMeeting.start_time.asc(), LogisticsMeeting.created_at.asc())
        )
    ).scalars().all()
    return [_meeting_to_item(meeting) for meeting in meetings]


async def list_meeting_participants(db: AsyncSession, current_user: User) -> list[LogisticsMeetingParticipantItem]:
    query = (
        select(User)
        .options(selectinload(User.role))
        .where(User.is_active == True)
    )

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "LOGISTIC_MANAGER":
        query = query.where(User.role.has(Role.name.in_(["LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER"])))
    elif role_name in {"WAREHOUSE_MANAGER", "DISPATCHER"}:
        scoped_warehouse_id = current_user.warehouse_id
        query = query.where(
            or_(
                User.role.has(Role.name == "LOGISTIC_MANAGER"),
                and_(
                    User.warehouse_id == scoped_warehouse_id,
                    User.role.has(Role.name.in_(["WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER"])),
                ),
            )
        )

    users = (await db.execute(query.order_by(User.name.asc()))).scalars().all()

    return [
        LogisticsMeetingParticipantItem(
            id=user.id,
            name=user.name,
            role=user.role.name.replace("_", " ").title() if user.role else "User",
            hub_id=user.warehouse_id,
        )
        for user in users
    ]


async def create_meeting(db: AsyncSession, data: LogisticsMeetingCreate, current_user: User) -> LogisticsMeetingItem:
    _validate_meeting_time_range(data.start_time, data.end_time)
    participant_ids = await _normalize_meeting_participants(db, data.participants, current_user.id)

    meeting = LogisticsMeeting(
        topic=data.topic.strip(),
        description=data.description.strip() if data.description else "",
        meeting_type=_normalize_meeting_type(data.meeting_type),
        meeting_link=_normalize_meeting_link(data.link),
        meeting_date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        participant_ids=participant_ids,
        created_by_id=current_user.id,
        warehouse_id=current_user.warehouse_id,
    )
    db.add(meeting)
    await db.flush()
    await db.refresh(meeting)
    return _meeting_to_item(meeting)


async def update_meeting(
    db: AsyncSession,
    meeting_id: UUID,
    data: LogisticsMeetingUpdate,
    current_user: User,
) -> LogisticsMeetingItem:
    meeting = await _get_meeting_for_user(db, meeting_id, current_user)
    _ensure_meeting_owner(meeting, current_user)

    updates = data.model_dump(exclude_unset=True)
    next_start = updates.get("start_time", meeting.start_time)
    next_end = updates.get("end_time", meeting.end_time)
    _validate_meeting_time_range(next_start, next_end)

    if "topic" in updates and updates["topic"] is not None:
        meeting.topic = updates["topic"].strip()
    if "description" in updates and updates["description"] is not None:
        meeting.description = updates["description"].strip()
    if "meeting_type" in updates and updates["meeting_type"] is not None:
        meeting.meeting_type = _normalize_meeting_type(updates["meeting_type"])
    if "link" in updates and updates["link"] is not None:
        meeting.meeting_link = _normalize_meeting_link(updates["link"])
    if "date" in updates and updates["date"] is not None:
        meeting.meeting_date = updates["date"]
    if "start_time" in updates and updates["start_time"] is not None:
        meeting.start_time = updates["start_time"]
    if "end_time" in updates and updates["end_time"] is not None:
        meeting.end_time = updates["end_time"]
    if "participants" in updates:
        meeting.participant_ids = await _normalize_meeting_participants(db, updates["participants"], current_user.id)

    db.add(meeting)
    await db.flush()
    await db.refresh(meeting)
    return _meeting_to_item(meeting)


async def delete_meeting(db: AsyncSession, meeting_id: UUID, current_user: User) -> MessageResponse:
    meeting = await _get_meeting_for_user(db, meeting_id, current_user)
    _ensure_meeting_owner(meeting, current_user)
    await db.delete(meeting)
    await db.flush()
    return MessageResponse(message="Meeting deleted")
