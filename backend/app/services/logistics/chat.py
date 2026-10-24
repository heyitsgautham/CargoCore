"""Logistics manager chat threads and dispatch contacts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsChatMessage,
    LogisticsChatThread,
)
from app.models.user import Role, User
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    DispatchContactItem,
    LogisticsChatMessageCreate,
    LogisticsChatMessageItem,
    LogisticsChatThreadCreate,
    LogisticsChatThreadItem,
    LogisticsChatThreadUpdate,
)
from app.services.logistics.bootstrap import build_bootstrap
from app.services.logistics.formatting import _now
from app.services.logistics.lookups import _build_thread_item, _get_chat_thread


async def list_chat_threads(db: AsyncSession) -> list[LogisticsChatThreadItem]:
    threads = (await db.execute(
        select(LogisticsChatThread).order_by(LogisticsChatThread.last_message_at.desc().nullslast())
    )).scalars().all()
    all_messages = (await db.execute(
        select(LogisticsChatMessage).order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()
    msgs_by_thread: dict[UUID, list[LogisticsChatMessage]] = {}
    for msg in all_messages:
        msgs_by_thread.setdefault(msg.thread_id, []).append(msg)
    return [_build_thread_item(t, msgs_by_thread.get(t.id, [])) for t in threads]


async def get_dispatch_contacts(db: AsyncSession) -> list[DispatchContactItem]:
    """Return all DRIVER + WAREHOUSE_MANAGER users, joined with any existing chat threads."""
    contactable_roles = ["DRIVER", "WAREHOUSE_MANAGER"]
    users = (await db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.name.in_(contactable_roles))
        .where(User.is_active.is_(True))
        .order_by(User.name.asc())
    )).scalars().all()

    threads = (await db.execute(select(LogisticsChatThread))).scalars().all()
    all_messages = (await db.execute(
        select(LogisticsChatMessage).order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()
    msgs_by_thread: dict = {}
    for msg in all_messages:
        msgs_by_thread.setdefault(msg.thread_id, []).append(msg)

    # Index threads by normalised name for matching
    thread_by_name: dict[str, LogisticsChatThread] = {t.name.strip().lower(): t for t in threads}

    # Also load roles for display
    roles_map: dict[UUID, str] = {}
    role_rows = (await db.execute(select(Role))).scalars().all()
    for r in role_rows:
        roles_map[r.id] = r.name

    result: list[DispatchContactItem] = []
    for user in users:
        # Driver threads are named "Driver: {name}" by the driver app — try that first
        thread = (
            thread_by_name.get(f"driver: {user.name.strip().lower()}")
            or thread_by_name.get(user.name.strip().lower())
        )
        thread_messages = []
        if thread:
            thread_messages = [
                LogisticsChatMessageItem(
                    id=m.id, text=m.text, sender=m.sender,
                    time=m.created_at.strftime("%I:%M %p"),
                )
                for m in msgs_by_thread.get(thread.id, [])
            ]
        result.append(DispatchContactItem(
            user_id=user.id,
            name=user.name,
            role=roles_map.get(user.role_id, "DRIVER"),
            phone=user.phone or None,
            email=user.email,
            thread_id=thread.id if thread else None,
            last_message=thread.last_message if thread else None,
            thread_status=thread.status if thread else "Offline",
            messages=thread_messages,
        ))
    return result


async def create_chat_thread(
    db: AsyncSession,
    data: LogisticsChatThreadCreate,
) -> LogisticsChatThreadItem:
    # Return existing thread if one with this name already exists (prevents duplicates)
    existing = (
        await db.execute(
            select(LogisticsChatThread)
            .where(LogisticsChatThread.name == data.name)
            .order_by(LogisticsChatThread.created_at.asc())
        )
    ).scalars().first()
    if existing:
        messages = (await db.execute(
            select(LogisticsChatMessage)
            .where(LogisticsChatMessage.thread_id == existing.id)
            .order_by(LogisticsChatMessage.created_at.asc())
        )).scalars().all()
        return _build_thread_item(existing, list(messages))

    thread = LogisticsChatThread(
        name=data.name,
        phone=data.phone,
        warehouse_id=data.warehouse_id,
        status="Online",
        muted=False,
        last_message=None,
        last_message_at=None,
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return _build_thread_item(thread, [])


async def delete_chat_thread(db: AsyncSession, thread_id: UUID) -> MessageResponse:
    thread = await _get_chat_thread(db, thread_id)
    await db.delete(thread)
    await db.commit()
    return MessageResponse(message="Chat thread deleted")


async def mute_chat_thread(
    db: AsyncSession,
    thread_id: UUID,
    data: LogisticsChatThreadUpdate,
) -> LogisticsChatThreadItem:
    thread = await _get_chat_thread(db, thread_id)
    thread.muted = data.muted
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    messages = (await db.execute(
        select(LogisticsChatMessage)
        .where(LogisticsChatMessage.thread_id == thread.id)
        .order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()
    return _build_thread_item(thread, list(messages))


async def add_chat_message(db: AsyncSession, thread_id: UUID, data: LogisticsChatMessageCreate) -> LogisticsChatThreadItem:
    thread = await _get_chat_thread(db, thread_id)
    message = LogisticsChatMessage(thread_id=thread.id, sender=data.sender, text=data.text)
    db.add(message)
    thread.last_message = data.text
    thread.last_message_at = _now()
    db.add(thread)
    await db.flush()
    bootstrap = await build_bootstrap(db)
    return next(item for item in bootstrap.chats if item.id == thread.id)
