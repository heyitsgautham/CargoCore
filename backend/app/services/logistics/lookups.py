"""Shared get-or-404 lookups for roles, users, vehicles, zones, return cases and chat threads."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.logistics import (
    LogisticsChatMessage,
    LogisticsChatThread,
    LogisticsReturnCase,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.user import Role, User
from app.models.warehouse import ReturnGrading
from app.schemas.logistics import (
    LogisticsChatMessageItem,
    LogisticsChatThreadItem,
    LogisticsReturnCaseItem,
)
from app.services.logistics.formatting import _fmt_relative
from app.utils.hashing import hash_password
from app.utils.username import generate_unique_username


async def _get_role(db: AsyncSession, name: str) -> Role:
    role = (await db.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
    if not role:
        raise RuntimeError(f"Required role missing: {name}")
    return role


async def _get_or_create_user(
    db: AsyncSession,
    *,
    role_name: str,
    email: str,
    name: str,
    username: str | None = None,
    warehouse_id: UUID | None = None,
    phone: str | None = None,
) -> User:
    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    role = await _get_role(db, role_name)
    if existing:
        existing.name = name
        if not existing.username:
            existing.username = await generate_unique_username(db, username or email.split("@")[0], exclude_user_id=existing.id)
        existing.role_id = role.id
        existing.warehouse_id = warehouse_id
        existing.phone = phone
        existing.is_active = True
        db.add(existing)
        await db.flush()
        return existing

    user = User(
        name=name,
        username=await generate_unique_username(db, username or email.split("@")[0]),
        email=email,
        phone=phone,
        address="",
        password_hash=hash_password("12345678"),
        role_id=role.id,
        warehouse_id=warehouse_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def _get_vehicle(db: AsyncSession, vehicle_id: UUID) -> LogisticsVehicle:
    vehicle = (await db.execute(select(LogisticsVehicle).where(LogisticsVehicle.id == vehicle_id))).scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


async def _get_zone(db: AsyncSession, zone_id: UUID) -> LogisticsZone:
    zone = (await db.execute(select(LogisticsZone).where(LogisticsZone.id == zone_id))).scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone


async def _get_return_case(db: AsyncSession, case_id: UUID) -> LogisticsReturnCase:
    case = (await db.execute(select(LogisticsReturnCase).where(LogisticsReturnCase.id == case_id))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return case not found")
    return case


async def _get_completed_return_grading(
    db: AsyncSession,
    case: LogisticsReturnCase,
) -> ReturnGrading | None:
    query = (
        select(ReturnGrading)
        .options(selectinload(ReturnGrading.grader))
        .where(ReturnGrading.status == "completed")
        .order_by(ReturnGrading.graded_at.desc(), ReturnGrading.created_at.desc())
    )
    if case.reference_code:
        grading = (
            await db.execute(query.where(ReturnGrading.rma_code == case.reference_code).limit(1))
        ).scalar_one_or_none()
        if grading:
            return grading
    if case.order_id:
        grading = (
            await db.execute(query.where(ReturnGrading.order_id == case.order_id).limit(1))
        ).scalar_one_or_none()
        if grading:
            return grading
    return None


async def _wallet_refund_credited(db: AsyncSession, reference_code: str | None) -> bool:
    if not reference_code:
        return False
    from app.models.wallet import WalletTransaction

    credited = (
        await db.execute(
            select(WalletTransaction.id).where(
                WalletTransaction.reason == "DAMAGE_REFUND",
                WalletTransaction.description.contains(reference_code),
            )
        )
    ).scalar_one_or_none()
    return bool(credited)


async def _build_return_case_item(
    db: AsyncSession,
    case: LogisticsReturnCase,
    completed_grading: ReturnGrading | None = None,
    wallet_credited: bool | None = None,
) -> LogisticsReturnCaseItem:
    grading = completed_grading if completed_grading is not None else await _get_completed_return_grading(db, case)
    credited = wallet_credited if wallet_credited is not None else await _wallet_refund_credited(db, case.reference_code)
    is_physical_flow = getattr(case, "flow_type", None) == "pickup_inspection"
    normalized_status = case.status
    case_images = list(case.images or [])
    if grading and grading.damage_photo_url and grading.damage_photo_url not in case_images:
        case_images.append(grading.damage_photo_url)
    if not is_physical_flow and case.status in {"Inspected", "Physically Inspected"}:
        normalized_status = "Claims Reviewed"
    display_status = normalized_status
    if grading and is_physical_flow and normalized_status in {"Arrived at Warehouse", "At Warehouse", "Inspected", "Physically Inspected"}:
        display_status = "Physically Inspected"

    return LogisticsReturnCaseItem(
        id=case.id,
        hub_id=case.warehouse_id,
        order_id=case.order_id,
        customer=case.customer_name,
        reason=case.reason,
        flow_type=getattr(case, "flow_type", None),
        condition=grading.item_condition if (grading and is_physical_flow) else case.condition,
        status=display_status,
        original_price=case.original_price,
        refund_amount=case.refund_amount,
        images=case_images,
        reference_code=case.reference_code,
        wallet_credited=credited,
        wm_disposition=grading.disposition if (grading and is_physical_flow) else None,
        wm_is_genuine=grading.is_genuine if (grading and is_physical_flow) else getattr(case, "wm_is_genuine", None),
        wm_recommended_outcome=grading.recommended_outcome if (grading and is_physical_flow) else getattr(case, "wm_recommended_outcome", None),
        wm_inspection_remarks=grading.inspection_remarks if (grading and is_physical_flow) else getattr(case, "wm_inspection_remarks", None),
        wm_graded_at=grading.graded_at if (grading and is_physical_flow) else None,
        wm_grader_name=grading.grader.name if (grading and is_physical_flow and grading.grader) else None,
        transport_charge_amount=round(float(case.transport_charge_amount or 0.0), 2),
        transport_charge_wallet_collected=round(float(case.transport_charge_wallet_collected or 0.0), 2),
        transport_charge_pending_amount=round(float(case.transport_charge_pending_amount or 0.0), 2),
        transport_charge_status=case.transport_charge_status,
        transport_charge_applied_at=case.transport_charge_applied_at,
        is_urgent=bool(getattr(case, "is_urgent", False)),
        urgent_reason=getattr(case, "urgent_reason", None),
    )


async def _get_chat_thread(db: AsyncSession, thread_id: UUID) -> LogisticsChatThread:
    thread = (await db.execute(select(LogisticsChatThread).where(LogisticsChatThread.id == thread_id))).scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat thread not found")
    return thread


def _build_thread_item(thread: LogisticsChatThread, messages: list[LogisticsChatMessage]) -> LogisticsChatThreadItem:
    return LogisticsChatThreadItem(
        id=thread.id,
        hub_id=thread.warehouse_id,
        name=thread.name,
        time=_fmt_relative(thread.last_message_at),
        last_message=thread.last_message,
        status=thread.status,
        phone=thread.phone,
        muted=thread.muted,
        messages=[
            LogisticsChatMessageItem(
                id=msg.id,
                text=msg.text,
                sender=msg.sender,
                time=msg.created_at.strftime("%I:%M %p"),
            )
            for msg in sorted(messages, key=lambda m: m.created_at)
        ],
    )
