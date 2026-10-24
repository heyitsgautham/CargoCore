import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.logistics import LogisticsReturnCase, LogisticsTransaction
from app.models.order import Order

_RATES_PATH = Path(__file__).resolve().parent.parent.parent / "rates_config.json"
_DEFAULT_TRANSPORT_CHARGE = 500.0


def _now() -> datetime:
    return datetime.now(UTC)


def _round_amount(value: float) -> float:
    return round(float(value or 0.0), 2)


def _load_transport_charge_amount() -> float:
    try:
        with open(_RATES_PATH, encoding="utf-8") as fh:
            payload = json.load(fh)
        return _round_amount(payload.get("minimumCharge", _DEFAULT_TRANSPORT_CHARGE))
    except Exception:
        return _DEFAULT_TRANSPORT_CHARGE


def _derive_transport_charge_status(case: LogisticsReturnCase) -> str | None:
    total = _round_amount(case.transport_charge_amount)
    wallet_collected = _round_amount(case.transport_charge_wallet_collected)
    pending = _round_amount(case.transport_charge_pending_amount)

    if total <= 0:
        return None
    if pending <= 0:
        if wallet_collected >= total:
            return "Collected from Wallet"
        return "Collected"
    if case.transport_charge_order_id:
        return "Attached to Next Order"
    if wallet_collected > 0:
        return "Partially Collected"
    return "Pending Next Order"


async def get_unattached_pending_transport_charge_total(db: AsyncSession, user_id: UUID) -> float:
    original_order = aliased(Order)
    result = await db.execute(
        select(func.coalesce(func.sum(LogisticsReturnCase.transport_charge_pending_amount), 0.0))
        .join(original_order, original_order.id == LogisticsReturnCase.order_id)
        .where(
            original_order.customer_id == user_id,
            LogisticsReturnCase.transport_charge_pending_amount > 0,
            LogisticsReturnCase.transport_charge_order_id.is_(None),
        )
    )
    return _round_amount(result.scalar_one() or 0.0)


async def apply_rejected_claim_transport_charge(
    db: AsyncSession,
    *,
    case: LogisticsReturnCase,
    customer_id: UUID,
) -> float:
    existing_total = _round_amount(case.transport_charge_amount)
    existing_pending = _round_amount(case.transport_charge_pending_amount)
    existing_wallet = _round_amount(case.transport_charge_wallet_collected)
    if existing_total > 0 or existing_pending > 0 or existing_wallet > 0:
        case.transport_charge_status = _derive_transport_charge_status(case)
        db.add(case)
        await db.flush()
        return existing_total

    charge_amount = _load_transport_charge_amount()
    wallet_applied = 0.0

    if charge_amount > 0:
        from app.services.finance_service import _gen_ref, _upsert_daily_stats
        from app.services.wallet_service import (
            _record_wallet_transaction,
            get_wallet_balance,
        )

        wallet_balance = await get_wallet_balance(db, customer_id)
        wallet_applied = min(wallet_balance, charge_amount)

        if wallet_applied > 0:
            await _record_wallet_transaction(
                db,
                user_id=customer_id,
                order_id=case.order_id,
                transaction_kind="DEBIT",
                reason="RETURN_TRANSPORT_CHARGE",
                amount=wallet_applied,
                description=f"Transport charge recovered for rejected claim {case.reference_code}",
            )

            db.add(
                LogisticsTransaction(
                    warehouse_id=case.warehouse_id,
                    transaction_code=_gen_ref("RTC"),
                    description=f"Rejected claim transport charge {case.reference_code} recovered from wallet",
                    transaction_type="REVENUE_RETURN_CHARGE",
                    amount=wallet_applied,
                    status="Completed",
                    metadata_json={
                        "reference_code": case.reference_code,
                        "order_id": str(case.order_id) if case.order_id else None,
                        "customer_id": str(customer_id),
                        "collection_source": "WALLET_DIRECT",
                    },
                )
            )
            await _upsert_daily_stats(db, delta_revenue=wallet_applied)
            if case.warehouse_id:
                await _upsert_daily_stats(db, delta_revenue=wallet_applied, warehouse_id=case.warehouse_id)

    case.transport_charge_amount = charge_amount
    case.transport_charge_wallet_collected = wallet_applied
    case.transport_charge_pending_amount = _round_amount(charge_amount - wallet_applied)
    case.transport_charge_order_id = None
    case.transport_charge_applied_at = _now()
    case.transport_charge_status = _derive_transport_charge_status(case)
    db.add(case)
    await db.flush()
    return charge_amount


async def attach_pending_transport_charges_to_order(db: AsyncSession, order: Order) -> float:
    original_order = aliased(Order)
    pending_cases = (
        await db.execute(
            select(LogisticsReturnCase)
            .join(original_order, original_order.id == LogisticsReturnCase.order_id)
            .where(
                original_order.customer_id == order.customer_id,
                LogisticsReturnCase.transport_charge_pending_amount > 0,
                LogisticsReturnCase.transport_charge_order_id.is_(None),
            )
            .order_by(
                LogisticsReturnCase.transport_charge_applied_at.asc().nulls_last(),
                LogisticsReturnCase.created_at.asc(),
            )
        )
    ).scalars().all()

    attached_total = 0.0
    for case in pending_cases:
        attached_total += _round_amount(case.transport_charge_pending_amount)
        case.transport_charge_order_id = order.id
        case.transport_charge_status = _derive_transport_charge_status(case)
        db.add(case)

    order.carry_forward_charge_amount = _round_amount(attached_total)
    order.carry_forward_charge_paid_amount = _round_amount(order.carry_forward_charge_paid_amount)
    db.add(order)
    await db.flush()
    return order.carry_forward_charge_amount


async def settle_transport_charges_from_order_payment(
    db: AsyncSession,
    *,
    order: Order,
    payment_amount: float,
    collection_source: str,
) -> float:
    payment_amount = _round_amount(payment_amount)
    carry_remaining = _round_amount(order.carry_forward_charge_amount - order.carry_forward_charge_paid_amount)
    applied_amount = min(payment_amount, max(carry_remaining, 0.0))
    if applied_amount <= 0:
        return 0.0

    order.carry_forward_charge_paid_amount = _round_amount(order.carry_forward_charge_paid_amount + applied_amount)
    db.add(order)

    pending_cases = (
        await db.execute(
            select(LogisticsReturnCase)
            .where(
                LogisticsReturnCase.transport_charge_order_id == order.id,
                LogisticsReturnCase.transport_charge_pending_amount > 0,
            )
            .order_by(
                LogisticsReturnCase.transport_charge_applied_at.asc().nulls_last(),
                LogisticsReturnCase.created_at.asc(),
            )
        )
    ).scalars().all()

    remaining = applied_amount
    for case in pending_cases:
        if remaining <= 0:
            break
        settle_amount = min(_round_amount(case.transport_charge_pending_amount), remaining)
        if settle_amount <= 0:
            continue
        case.transport_charge_pending_amount = _round_amount(case.transport_charge_pending_amount - settle_amount)
        case.transport_charge_status = _derive_transport_charge_status(case)
        db.add(case)
        remaining = _round_amount(remaining - settle_amount)

    if collection_source == "ORDER_WALLET":
        from app.services.finance_service import _gen_ref, _upsert_daily_stats

        db.add(
            LogisticsTransaction(
                warehouse_id=order.warehouse_id,
                transaction_code=_gen_ref("RTC"),
                description=f"Carry-forward transport charge collected on {order.tracking_code} via wallet",
                transaction_type="REVENUE_RETURN_CHARGE",
                amount=applied_amount,
                status="Completed",
                metadata_json={
                    "order_id": str(order.id),
                    "tracking_code": order.tracking_code,
                    "collection_source": collection_source,
                },
            )
        )
        await _upsert_daily_stats(db, delta_revenue=applied_amount)
        if order.warehouse_id:
            await _upsert_daily_stats(db, delta_revenue=applied_amount, warehouse_id=order.warehouse_id)

    await db.flush()
    return applied_amount


async def release_attached_transport_charges(db: AsyncSession, order: Order) -> None:
    attached_cases = (
        await db.execute(
            select(LogisticsReturnCase).where(
                LogisticsReturnCase.transport_charge_order_id == order.id,
                LogisticsReturnCase.transport_charge_pending_amount > 0,
            )
        )
    ).scalars().all()

    for case in attached_cases:
        case.transport_charge_order_id = None
        case.transport_charge_status = _derive_transport_charge_status(case)
        db.add(case)

    await db.flush()
