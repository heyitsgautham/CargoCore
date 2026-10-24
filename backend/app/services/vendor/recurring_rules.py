"""Creating, updating, toggling and deleting recurring rules."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.user import User
from app.models.vendor import (
    VendorRecurringRule,
)
from app.schemas.vendor import (
    VendorRecurringRuleCreate,
    VendorRecurringRuleResponse,
)
from app.services.vendor.recurring_runs import (
    _auto_debit_order_if_eligible,
    _materialize_rule_run_order,
    _rule_run_marker,
    ensure_upcoming_recurring_orders,
    run_due_recurring_rules,
)
from app.services.vendor.shipments import _ensure_vendor


async def list_recurring_rules(db: AsyncSession, user: User) -> list[VendorRecurringRuleResponse]:
    _ensure_vendor(user)
    due_created = await run_due_recurring_rules(db, vendor_id=user.id)
    if due_created:
        await db.commit()
    upcoming_created = await ensure_upcoming_recurring_orders(db, vendor_id=user.id)
    if upcoming_created:
        await db.commit()
    rows = (
        await db.execute(
            select(VendorRecurringRule)
            .where(VendorRecurringRule.vendor_id == user.id)
            .order_by(VendorRecurringRule.created_at.desc())
        )
    ).scalars().all()
    return [VendorRecurringRuleResponse.model_validate(row) for row in rows]

def _compact_route(route: str) -> str:
    route = route.strip()
    return route if len(route) <= 255 else route[:252].rstrip() + "..."


async def create_recurring_rule(
    db: AsyncSession, user: User, data: VendorRecurringRuleCreate
) -> VendorRecurringRuleResponse:
    _ensure_vendor(user)
    rule = VendorRecurringRule(
        vendor_id=user.id,
        name=data.name,
        description=data.description,
        frequency=data.frequency,
        route=_compact_route(data.route),
        details=data.details,
        next_run=data.next_run,
        active=data.active,
    )
    db.add(rule)
    await db.flush()
    await _materialize_rule_run_order(db, rule=rule, owner=user, run_iso=rule.next_run)
    marker = _rule_run_marker(rule.id, rule.next_run)
    run_order = (
        await db.execute(
            select(Order).where(
                Order.customer_id == user.id,
                Order.delivery_notes.ilike(f"%{marker}%"),
            ).order_by(Order.created_at.desc())
        )
    ).scalars().first()
    if run_order:
        await _auto_debit_order_if_eligible(
            db,
            order=run_order,
            owner=user,
            rule=rule,
            run_iso=rule.next_run,
            trigger="scheduled",
        )
    await db.flush()
    await db.refresh(rule)
    return VendorRecurringRuleResponse.model_validate(rule)


async def update_recurring_rule(
    db: AsyncSession, user: User, rule_id: uuid.UUID, data: VendorRecurringRuleCreate
) -> VendorRecurringRuleResponse:
    _ensure_vendor(user)
    rule = (
        await db.execute(
            select(VendorRecurringRule).where(
                VendorRecurringRule.id == rule_id,
                VendorRecurringRule.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring rule not found")
    rule.name = data.name
    rule.description = data.description
    rule.frequency = data.frequency
    rule.route = _compact_route(data.route)
    rule.details = data.details
    rule.next_run = data.next_run
    rule.active = data.active
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return VendorRecurringRuleResponse.model_validate(rule)


async def toggle_recurring_rule(
    db: AsyncSession, user: User, rule_id: uuid.UUID
) -> VendorRecurringRuleResponse:
    _ensure_vendor(user)
    rule = (
        await db.execute(
            select(VendorRecurringRule).where(
                VendorRecurringRule.id == rule_id,
                VendorRecurringRule.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring rule not found")
    rule.active = not rule.active

    if not rule.active:
        # Cancel any pending materialized orders for this rule so they don't linger in Warehouse Inbound
        marker = f"RECURRING_RULE:{rule.id}|RUN:"
        pending_orders = (
            await db.execute(
                select(Order).where(
                    Order.customer_id == user.id,
                    Order.delivery_notes.contains(marker),
                    Order.status.notin_(["DELIVERED", "CANCELLED", "CLOSED"]),
                    Order.warehouse_substatus == "AWAITING_INBOUND",
                )
            )
        ).scalars().all()

        for order in pending_orders:
            order.status = "CANCELLED"
            order.cancel_reason = "Recurring schedule paused by vendor"
            db.add(order)

    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return VendorRecurringRuleResponse.model_validate(rule)


async def delete_recurring_rule(db: AsyncSession, user: User, rule_id: uuid.UUID) -> None:
    _ensure_vendor(user)
    rule = (
        await db.execute(
            select(VendorRecurringRule).where(
                VendorRecurringRule.id == rule_id,
                VendorRecurringRule.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring rule not found")
    
    # Cancel any pending materialized orders for this rule so they don't linger in Warehouse Inbound
    marker = f"RECURRING_RULE:{rule.id}|RUN:"
    pending_orders = (
        await db.execute(
            select(Order).where(
                Order.customer_id == user.id,
                Order.delivery_notes.contains(marker),
                Order.status.notin_(["DELIVERED", "CANCELLED", "CLOSED"]),
                Order.warehouse_substatus == "AWAITING_INBOUND",
            )
        )
    ).scalars().all()

    for order in pending_orders:
        order.status = "CANCELLED"
        order.cancel_reason = "Recurring schedule deleted by vendor"
        db.add(order)

    await db.delete(rule)
