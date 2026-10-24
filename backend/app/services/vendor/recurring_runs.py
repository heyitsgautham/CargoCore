"""Turning recurring rules into orders on schedule, with optional wallet auto-debit."""

import json
import uuid
from datetime import UTC, date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.user import User
from app.models.vendor import (
    VendorRecurringRule,
)
from app.services.vendor.recurring_estimate import (
    _normalize_uuid,
    _resolve_recurring_pickup_origin,
    _resolve_recurring_warehouse,
    _road_route_distance_km,
    _safe_float,
)
from app.services.vendor.shipments import _is_active_vendor_owner


def _rule_run_marker(rule_id: uuid.UUID, run_iso: str) -> str:
    return f"RECURRING_RULE:{rule_id}|RUN:{run_iso}"


async def _has_materialized_rule_run(
    db: AsyncSession,
    *,
    rule_id: uuid.UUID,
    run_iso: str,
) -> bool:
    marker = _rule_run_marker(rule_id, run_iso)
    row = (
        await db.execute(
            select(Order.id).where(Order.delivery_notes.ilike(f"%{marker}%")).limit(1)
        )
    ).scalar_one_or_none()
    return row is not None


async def _materialize_rule_run_order(
    db: AsyncSession,
    *,
    rule: VendorRecurringRule,
    owner: User,
    run_iso: str,
) -> bool:
    if await _has_materialized_rule_run(db, rule_id=rule.id, run_iso=run_iso):
        return False

    details = _parse_rule_details(rule.details)
    hub_id = _normalize_uuid(details.get("hubId"))
    hub_name = (details.get("hub") or "Vendor Hub").strip()
    destination = (details.get("destinationAddress") or "Destination").strip()
    cargo = (details.get("cargo") or rule.description or "Recurring cargo").strip()
    drop_time = details.get("dropOffTime")
    dest_lat = _safe_float(details.get("destinationLat"))
    dest_lon = _safe_float(details.get("destinationLon"))

    target_warehouse, _ = await _resolve_recurring_warehouse(
        db,
        hub_id=hub_id,
        hub_name=hub_name,
        fallback_to_first=True,
    )
    if target_warehouse is None:
        return False
    target_warehouse_id = target_warehouse.id

    # ── Compute pricing from distance ──────────────────────────────────────
    base_amount = 0.0
    total_amount = 0.0
    if dest_lat is not None and dest_lon is not None and target_warehouse_id:
        pickup_lat, pickup_lng, _, _ = await _resolve_recurring_pickup_origin(
            db,
            warehouse=target_warehouse,
        )
        if pickup_lat is not None and pickup_lng is not None:
            from app.routers.rates import _load as _load_rates
            rate_cfg = _load_rates()
            base_fee = float(rate_cfg.get("baseBookingFee", 220))
            per_km = float(rate_cfg.get("perKmRate", 12))
            dist_km, _ = await _road_route_distance_km(
                pickup_lat,
                pickup_lng,
                dest_lat,
                dest_lon,
            )
            base_amount = round(base_fee, 2)
            distance_cost = round(dist_km * per_km, 2)
            total_amount = round(base_fee + distance_cost, 2)

    marker = _rule_run_marker(rule.id, run_iso)
    order = Order(
        tracking_code=_tracking_code(),
        order_type="VENDOR",
        status="CONFIRMED",
        warehouse_substatus="AWAITING_INBOUND",
        customer_id=owner.id,
        warehouse_id=target_warehouse_id,
        pickup_addr=target_warehouse.name or hub_name,
        pickup_type="hub",
        delivery_addr=destination,
        delivery_lat=dest_lat,
        delivery_lng=dest_lon,
        cargo_type=cargo,
        vehicle_type="Mini Truck",
        labor_count=0,
        base_amount=base_amount,
        vehicle_amount=0.0,
        labor_amount=0.0,
        materials_amount=0.0,
        packing_amount=0.0,
        platform_fee=0.0,
        tax_amount=0.0,
        total_amount=total_amount,
        payment_mode="invoice",
        payment_status="pending",
        scheduled_at=_scheduled_datetime(run_iso, drop_time),
        delivery_notes=marker,
    )
    db.add(order)
    return True


def _tracking_code() -> str:
    return f"QC-{uuid.uuid4().hex[:10].upper()}"


def _parse_rule_details(details: str) -> dict:
    try:
        parsed = json.loads(details)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}


def _is_auto_debit_enabled(details: dict) -> bool:
    value = details.get("autoDebitEnabled", False)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return False


def _parse_rule_marker(delivery_notes: str | None) -> tuple[uuid.UUID | None, str | None]:
    if not delivery_notes:
        return None, None
    marker = str(delivery_notes)
    if "RECURRING_RULE:" not in marker or "|RUN:" not in marker:
        return None, None
    try:
        tail = marker.split("RECURRING_RULE:", 1)[1]
        rule_raw, run_iso = tail.split("|RUN:", 1)
        rule_id = uuid.UUID(rule_raw.strip())
        run = run_iso.splitlines()[0].strip()
        return rule_id, run
    except Exception:
        return None, None


def _append_auto_debit_event(
    order: Order,
    *,
    run_iso: str,
    event_type: str,
    message: str,
) -> None:
    now_iso = datetime.now(UTC).isoformat(timespec="seconds")
    event_line = f"AUTODEBIT_EVENT|RUN:{run_iso}|TYPE:{event_type}|TS:{now_iso}|MSG:{message}"
    existing = str(order.delivery_notes or "")
    marker = f"|RUN:{run_iso}|TYPE:{event_type}|"
    if marker in existing:
        return
    order.delivery_notes = f"{existing}\n{event_line}".strip()


async def _auto_debit_order_if_eligible(
    db: AsyncSession,
    *,
    order: Order,
    owner: User,
    rule: VendorRecurringRule,
    run_iso: str,
    trigger: str,
) -> tuple[bool, str]:
    if (order.payment_mode or "").lower() != "invoice":
        return False, ""
    if order.payment_status == "paid":
        return False, ""

    outstanding = max(float(order.total_amount or 0.0) - float(order.paid_amount or 0.0), 0.0)
    if outstanding <= 0:
        return False, ""

    details = _parse_rule_details(rule.details)
    if not _is_auto_debit_enabled(details):
        _append_auto_debit_event(
            order,
            run_iso=run_iso,
            event_type="SKIPPED_DISABLED",
            message="Recurring auto-debit is disabled",
        )
        db.add(order)
        return False, "Recurring auto-debit is disabled for this schedule"

    # Scheduled auto-debit must happen only on the exact scheduled day.
    if trigger == "scheduled":
        today = datetime.now(UTC).date()
        scheduled_day = order.scheduled_at.date() if order.scheduled_at else None
        if scheduled_day is None:
            try:
                scheduled_day = date.fromisoformat(run_iso)
            except Exception:
                scheduled_day = None
        if scheduled_day != today:
            return False, ""

    from app.services import wallet_service

    try:
        payment = await wallet_service.apply_wallet_payment(
            db,
            order=order,
            user=owner,
            amount=outstanding,
            allow_negative=True,
        )
        if float(payment.remaining_wallet_balance or 0.0) < 0:
            debt = abs(float(payment.remaining_wallet_balance or 0.0))
            _append_auto_debit_event(
                order,
                run_iso=run_iso,
                event_type="DEBT",
                message=f"Wallet balance is negative by INR {debt:.2f}. Please top up to clear dues.",
            )
            db.add(order)
            return True, "Auto-debit completed. Wallet is now negative; please top up"

        _append_auto_debit_event(
            order,
            run_iso=run_iso,
            event_type="SUCCESS",
            message="Debited from wallet",
        )
        db.add(order)
        return True, "Auto-debit completed from vendor wallet"
    except HTTPException as exc:
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            detail = exc.detail or "Auto-debit skipped"
            if "insufficient wallet balance" in str(detail).lower():
                _append_auto_debit_event(
                    order,
                    run_iso=run_iso,
                    event_type="SKIPPED_LOW_BALANCE",
                    message="Insufficient wallet balance",
                )
                db.add(order)
            return False, exc.detail or "Auto-debit skipped"
        raise


async def auto_debit_recurring_order_if_eligible(
    db: AsyncSession,
    *,
    order: Order,
    trigger: str,
) -> tuple[bool, str]:
    """Attempt wallet auto-debit for a recurring order.

    trigger:
    - "scheduled": run by scheduler on due date only
    - "arrived": run when warehouse marks goods arrived (can be before scheduled date)
    """
    rule_id, run_iso = _parse_rule_marker(order.delivery_notes)
    if not rule_id or not run_iso:
        return False, ""

    rule = (
        await db.execute(select(VendorRecurringRule).where(VendorRecurringRule.id == rule_id))
    ).scalar_one_or_none()
    if not rule:
        return False, ""

    owner = (
        await db.execute(select(User).where(User.id == order.customer_id))
    ).scalar_one_or_none()
    if not owner:
        return False, ""

    return await _auto_debit_order_if_eligible(
        db,
        order=order,
        owner=owner,
        rule=rule,
        run_iso=run_iso,
        trigger=trigger,
    )


def _next_run_for_frequency(current_due: date, frequency: str) -> date:
    label = (frequency or "").strip().lower()
    if label == "daily":
        return current_due + timedelta(days=1)
    if label == "bi-weekly":
        return current_due + timedelta(days=14)
    if label == "1st of month":
        year = current_due.year + (1 if current_due.month == 12 else 0)
        month = 1 if current_due.month == 12 else current_due.month + 1
        return date(year, month, 1)
    if label == "15th of month":
        year = current_due.year + (1 if current_due.month == 12 else 0)
        month = 1 if current_due.month == 12 else current_due.month + 1
        return date(year, month, 15)

    weekday_map = {
        "every monday": 0,
        "every tuesday": 1,
        "every wednesday": 2,
        "every thursday": 3,
        "every friday": 4,
        "every saturday": 5,
        "every sunday": 6,
    }
    target = weekday_map.get(label)
    if target is not None:
        days_ahead = (target - current_due.weekday()) % 7
        return current_due + timedelta(days=days_ahead or 7)

    # Fallback to weekly cadence for unknown labels.
    return current_due + timedelta(days=7)


def _scheduled_datetime(next_run: str, drop_off_time: str | None) -> datetime | None:
    try:
        run_day = date.fromisoformat(next_run)
    except Exception:
        return None
    hh, mm = 9, 0
    if drop_off_time:
        try:
            parts = drop_off_time.split(":")
            hh = int(parts[0])
            mm = int(parts[1])
        except Exception:
            pass
    return datetime.combine(run_day, time(hour=hh, minute=mm, tzinfo=UTC))


async def run_due_recurring_rules(
    db: AsyncSession,
    *,
    vendor_id: uuid.UUID | None = None,
) -> int:
    today = datetime.now(UTC).date()
    stmt = select(VendorRecurringRule).where(VendorRecurringRule.active.is_(True))
    if vendor_id:
        stmt = stmt.where(VendorRecurringRule.vendor_id == vendor_id)

    rules = (
        await db.execute(
            stmt.order_by(VendorRecurringRule.created_at.asc()).with_for_update(skip_locked=True)
        )
    ).scalars().all()
    if not rules:
        return 0

    vendor_ids = {rule.vendor_id for rule in rules}
    users = (
        await db.execute(select(User).where(User.id.in_(vendor_ids), User.is_active.is_(True)))
    ).scalars().all()
    user_by_id = {user.id: user for user in users}

    created = 0
    for rule in rules:
        try:
            due = date.fromisoformat(rule.next_run)
        except Exception:
            continue

        if due > today:
            continue

        owner = user_by_id.get(rule.vendor_id)
        if not _is_active_vendor_owner(owner):
            continue

        run_iso = rule.next_run

        was_created = await _materialize_rule_run_order(
            db,
            rule=rule,
            owner=owner,
            run_iso=run_iso,
        )

        marker = _rule_run_marker(rule.id, run_iso)
        run_order = (
            await db.execute(
                select(Order).where(
                    Order.customer_id == owner.id,
                    Order.delivery_notes.ilike(f"%{marker}%"),
                ).order_by(Order.created_at.desc())
            )
        ).scalars().first()
        if run_order:
            await _auto_debit_order_if_eligible(
                db,
                order=run_order,
                owner=owner,
                rule=rule,
                run_iso=run_iso,
                trigger="scheduled",
            )

        next_due = _next_run_for_frequency(due, rule.frequency)
        rule.next_run = next_due.isoformat()
        db.add(rule)
        if was_created:
            created += 1

    if created:
        await db.flush()
    return created


async def ensure_upcoming_recurring_orders(
    db: AsyncSession,
    *,
    vendor_id: uuid.UUID | None = None,
) -> int:
    stmt = select(VendorRecurringRule).where(VendorRecurringRule.active.is_(True))
    if vendor_id:
        stmt = stmt.where(VendorRecurringRule.vendor_id == vendor_id)
    rules = (await db.execute(stmt.order_by(VendorRecurringRule.created_at.asc()))).scalars().all()
    if not rules:
        return 0

    vendor_ids = {rule.vendor_id for rule in rules}
    users = (
        await db.execute(select(User).where(User.id.in_(vendor_ids), User.is_active.is_(True)))
    ).scalars().all()
    user_by_id = {user.id: user for user in users}

    today = datetime.now(UTC).date()
    cutoff = today + timedelta(days=1)  # only materialize 1 day before the scheduled run

    created = 0
    for rule in rules:
        owner = user_by_id.get(rule.vendor_id)
        if not _is_active_vendor_owner(owner):
            continue
        try:
            next_run_date = date.fromisoformat(rule.next_run)
        except Exception:
            continue
        # Do not create the order until 1 day before its run date
        if next_run_date > cutoff:
            continue
        if await _materialize_rule_run_order(db, rule=rule, owner=owner, run_iso=rule.next_run):
            created += 1

    if created:
        await db.flush()
    return created
