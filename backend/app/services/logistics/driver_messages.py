"""Driver chat with dispatch and the manager, audit log and cash-out requests."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.logistics import (
    LogisticsChatMessage,
    LogisticsChatThread,
    LogisticsTransaction,
    LogisticsVehicle,
)
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    DriverAuditEventItem,
    DriverCashoutRequest,
    DriverDispatchMessageCreate,
    DriverDispatchThreadItem,
)
from app.services.logistics.driver_context import (
    _get_driver_orders,
    _get_driver_profile,
)
from app.services.logistics.formatting import (
    _coerce_utc,
    _is_active_order,
    _is_completed_order,
    _now,
    _shift_code,
)

# ── Driver Dispatch Chat ───────────────────────────────────────────────────────

_DISPATCHER_SENDERS = {"dispatcher", "dispatch", "system", "me"}
_MANAGER_SENDERS = {"manager", "logistics manager", "system", "me"}


async def _find_driver_thread(db: AsyncSession, user: User):
    """Find the driver's dispatch thread, checking both naming conventions."""
    for name in (f"Driver: {user.name}", user.name):
        thread = (
            await db.execute(
                select(LogisticsChatThread)
                .options(selectinload(LogisticsChatThread.messages))
                .where(LogisticsChatThread.name == name)
                .order_by(LogisticsChatThread.created_at.asc())
            )
        ).scalars().first()
        if thread:
            return thread
    return None


async def _find_driver_manager_thread(db: AsyncSession, user: User):
    """Find the driver's Logistics Manager thread, keeping it separate from dispatch."""
    for name in (f"LM Driver: {user.name}", f"Manager: {user.name}"):
        thread = (
            await db.execute(
                select(LogisticsChatThread)
                .options(selectinload(LogisticsChatThread.messages))
                .where(LogisticsChatThread.name == name)
                .order_by(LogisticsChatThread.created_at.asc())
            )
        ).scalars().first()
        if thread:
            return thread
    return None


async def get_driver_dispatch_thread(
    db: AsyncSession,
    user: User,
) -> DriverDispatchThreadItem:
    thread = await _find_driver_thread(db, user)

    if not thread:
        thread = LogisticsChatThread(
            name=f"Driver: {user.name}",
            status="Online",
            warehouse_id=user.warehouse_id,
        )
        db.add(thread)
        await db.flush()
        welcome = LogisticsChatMessage(
            thread_id=thread.id,
            sender="Dispatcher",
            text=f"Dispatch channel ready for {user.name}. How can I help?",
        )
        db.add(welcome)
        await db.flush()
        thread = (
            await db.execute(
                select(LogisticsChatThread)
                .options(selectinload(LogisticsChatThread.messages))
                .where(LogisticsChatThread.id == thread.id)
            )
        ).scalars().first()
        await db.commit()

    messages = [
        {
            "id": str(msg.id),
            "text": msg.text,
            "fromDriver": msg.sender.lower() not in _DISPATCHER_SENDERS,
            "time": msg.created_at.strftime("%H:%M"),
        }
        for msg in thread.messages
    ]
    return DriverDispatchThreadItem(thread_id=str(thread.id), messages=messages)


async def add_driver_dispatch_message(
    db: AsyncSession,
    user: User,
    data: DriverDispatchMessageCreate,
) -> DriverDispatchThreadItem:
    thread = await _find_driver_thread(db, user)

    if not thread:
        thread = LogisticsChatThread(
            name=f"Driver: {user.name}",
            status="Online",
            warehouse_id=user.warehouse_id,
        )
        db.add(thread)
        await db.flush()

    # Truncate sender to fit the String(30) DB column
    sender_name = (user.name or "Driver")[:30]
    msg = LogisticsChatMessage(
        thread_id=thread.id,
        sender=sender_name,
        text=data.text,
    )
    thread.last_message = data.text
    thread.last_message_at = _now()
    db.add(msg)
    db.add(thread)
    await db.commit()

    # Fetch messages directly to avoid SQLAlchemy identity-map cache returning stale data
    all_messages = (await db.execute(
        select(LogisticsChatMessage)
        .where(LogisticsChatMessage.thread_id == thread.id)
        .order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()

    messages = [
        {
            "id": str(m.id),
            "text": m.text,
            "fromDriver": m.sender.lower() not in _DISPATCHER_SENDERS,
            "time": m.created_at.strftime("%H:%M"),
        }
        for m in all_messages
    ]
    return DriverDispatchThreadItem(thread_id=str(thread.id), messages=messages)


async def get_driver_manager_thread(
    db: AsyncSession,
    user: User,
) -> DriverDispatchThreadItem:
    thread = await _find_driver_manager_thread(db, user)

    if not thread:
        thread = LogisticsChatThread(
            name=f"LM Driver: {user.name}",
            status="Online",
            warehouse_id=user.warehouse_id,
        )
        db.add(thread)
        await db.flush()
        welcome = LogisticsChatMessage(
            thread_id=thread.id,
            sender="Logistics Manager",
            text=f"Manager channel ready for {user.name}. Reach out if you need operational support.",
        )
        db.add(welcome)
        await db.flush()
        thread = (
            await db.execute(
                select(LogisticsChatThread)
                .options(selectinload(LogisticsChatThread.messages))
                .where(LogisticsChatThread.id == thread.id)
            )
        ).scalars().first()
        await db.commit()

    messages = [
        {
            "id": str(msg.id),
            "text": msg.text,
            "fromDriver": msg.sender.lower() not in _MANAGER_SENDERS,
            "time": msg.created_at.strftime("%H:%M"),
        }
        for msg in thread.messages
    ]
    return DriverDispatchThreadItem(thread_id=str(thread.id), messages=messages)


async def add_driver_manager_message(
    db: AsyncSession,
    user: User,
    data: DriverDispatchMessageCreate,
) -> DriverDispatchThreadItem:
    thread = await _find_driver_manager_thread(db, user)

    if not thread:
        thread = LogisticsChatThread(
            name=f"LM Driver: {user.name}",
            status="Online",
            warehouse_id=user.warehouse_id,
        )
        db.add(thread)
        await db.flush()

    sender_name = (user.name or "Driver")[:30]
    msg = LogisticsChatMessage(
        thread_id=thread.id,
        sender=sender_name,
        text=data.text,
    )
    thread.last_message = data.text
    thread.last_message_at = _now()
    db.add(msg)
    db.add(thread)
    await db.commit()

    all_messages = (await db.execute(
        select(LogisticsChatMessage)
        .where(LogisticsChatMessage.thread_id == thread.id)
        .order_by(LogisticsChatMessage.created_at.asc())
    )).scalars().all()

    messages = [
        {
            "id": str(m.id),
            "text": m.text,
            "fromDriver": m.sender.lower() not in _MANAGER_SENDERS,
            "time": m.created_at.strftime("%H:%M"),
        }
        for m in all_messages
    ]
    return DriverDispatchThreadItem(thread_id=str(thread.id), messages=messages)


# ── Driver Audit Log ───────────────────────────────────────────────────────────

async def get_driver_audit_log(
    db: AsyncSession,
    user: User,
) -> list[DriverAuditEventItem]:
    profile = await _get_driver_profile(db, user)
    vehicles = (
        await db.execute(
            select(LogisticsVehicle).where(LogisticsVehicle.assigned_driver_id == user.id)
        )
    ).scalars().all()
    orders = await _get_driver_orders(db, user)

    events: list[DriverAuditEventItem] = []
    event_id = 1

    def _fmt(dt: datetime | None) -> str:
        if not dt:
            return "—"
        local = _coerce_utc(dt)
        return local.strftime("%H:%M")

    shift_started = _coerce_utc(user.last_login) if profile.status.lower() != "off-duty" else None
    if shift_started:
        events.append(DriverAuditEventItem(
            id=str(event_id),
            icon="login",
            color="text-primary",
            action=f"Shift Started — {user.name}",
            detail=f"RBAC: DRIVER · Shift code {_shift_code(user, shift_started)}",
            time=_fmt(shift_started),
        ))
        event_id += 1

    for v in vehicles:
        events.append(DriverAuditEventItem(
            id=str(event_id),
            icon="directions_car",
            color="text-accent-blue",
            action="Vehicle Bound",
            detail=f"{v.code} · {v.license_plate or 'No plate'}",
            time=_fmt(v.updated_at),
        ))
        event_id += 1

    for order in orders:
        if _is_completed_order(order):
            events.append(DriverAuditEventItem(
                id=str(event_id),
                icon="verified",
                color="text-primary",
                action=f"Delivery Completed — {order.tracking_code}",
                detail=f"Order {order.tracking_code} · POD recorded",
                time=_fmt(order.updated_at),
            ))
            event_id += 1
        elif _is_active_order(order):
            events.append(DriverAuditEventItem(
                id=str(event_id),
                icon="place",
                color="text-accent-purple",
                action=f"Stop Active — {order.tracking_code}",
                detail=f"Order in progress · {order.status}",
                time=_fmt(order.updated_at),
            ))
            event_id += 1

    events.sort(key=lambda e: e.time)
    return events


# ── Driver Cashout ─────────────────────────────────────────────────────────────

async def request_driver_cashout(
    db: AsyncSession,
    user: User,
    data: DriverCashoutRequest,
) -> MessageResponse:
    profile = await _get_driver_profile(db, user)
    warehouse_id = user.warehouse_id or profile.warehouse_id

    tx_code = f"CASHOUT-{str(user.id)[:8].upper()}-{int(_now().timestamp())}"
    tx = LogisticsTransaction(
        warehouse_id=warehouse_id,
        transaction_code=tx_code,
        description=f"Driver cashout — {user.name}",
        transaction_type="DRIVER_CASHOUT",
        amount=-abs(data.amount),
        status="Pending",
        metadata_json={
            "driver_id": str(user.id),
            "driver_name": user.name,
            "requested_at": _now().isoformat(),
        },
    )
    db.add(tx)
    await db.commit()
    return MessageResponse(message=f"Cashout of ₹{data.amount:.0f} requested successfully")
