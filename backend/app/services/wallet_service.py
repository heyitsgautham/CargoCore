import random
import string
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.payment import OrderPayment
from app.models.user import User
from app.models.wallet import WalletTransaction

WALLET_PAYMENT_MODE = "WALLET"
REFUND_PAYMENT_MODE = "REFUND"


def _wallet_ref(prefix: str) -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"{prefix}-{suffix}"


async def get_wallet_balance(db: AsyncSession, user_id: UUID) -> float:
    result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (WalletTransaction.transaction_kind == "CREDIT", WalletTransaction.amount),
                        else_=-WalletTransaction.amount,
                    )
                ),
                0.0,
            )
        ).where(WalletTransaction.user_id == user_id)
    )
    return float(result.scalar_one() or 0.0)


async def get_wallet_summary(db: AsyncSession, user: User):
    balance = await get_wallet_balance(db, user.id)
    from app.services.return_charge_service import (
        get_unattached_pending_transport_charge_total,
    )
    pending_transport_charge = await get_unattached_pending_transport_charge_total(db, user.id)

    totals = await db.execute(
        select(
            func.coalesce(
                func.sum(case((WalletTransaction.transaction_kind == "CREDIT", WalletTransaction.amount), else_=0.0)),
                0.0,
            ),
            func.coalesce(
                func.sum(case((WalletTransaction.transaction_kind == "DEBIT", WalletTransaction.amount), else_=0.0)),
                0.0,
            ),
        ).where(WalletTransaction.user_id == user.id)
    )
    total_credits, total_debits = totals.one()

    rows = (
        await db.execute(
            select(WalletTransaction, Order.tracking_code)
            .outerjoin(Order, Order.id == WalletTransaction.order_id)
            .where(WalletTransaction.user_id == user.id)
            .order_by(WalletTransaction.created_at.desc())
            .limit(20)
        )
    ).all()

    from app.schemas.wallet import WalletSummary, WalletTransactionRecord

    return WalletSummary(
        balance=round(balance, 2),
        total_credits=round(float(total_credits or 0.0), 2),
        total_debits=round(float(total_debits or 0.0), 2),
        pending_transport_charge=round(pending_transport_charge, 2),
        transactions=[
            WalletTransactionRecord(
                id=tx.id,
                order_id=tx.order_id,
                tracking_code=tracking_code,
                transaction_kind=tx.transaction_kind,
                reason=tx.reason,
                amount=round(float(tx.amount or 0.0), 2),
                description=tx.description,
                created_at=tx.created_at,
            )
            for tx, tracking_code in rows
        ],
    )


async def _record_wallet_transaction(
    db: AsyncSession,
    *,
    user_id: UUID,
    amount: float,
    transaction_kind: str,
    reason: str,
    description: str,
    order_id: UUID | None = None,
) -> WalletTransaction:
    tx = WalletTransaction(
        user_id=user_id,
        order_id=order_id,
        transaction_kind=transaction_kind,
        reason=reason,
        amount=round(float(amount), 2),
        description=description,
    )
    db.add(tx)
    await db.flush()
    return tx


async def top_up_wallet(
    db: AsyncSession,
    *,
    user: User,
    amount: float,
):
    amount = round(float(amount or 0), 2)
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Top-up amount must be greater than zero")

    await _record_wallet_transaction(
        db,
        user_id=user.id,
        order_id=None,
        transaction_kind="CREDIT",
        reason="WALLET_TOPUP",
        amount=amount,
        description="Wallet top-up",
    )

    from app.schemas.wallet import WalletTopUpResponse

    return WalletTopUpResponse(
        added_amount=amount,
        balance=round(await get_wallet_balance(db, user.id), 2),
    )


async def apply_wallet_payment(
    db: AsyncSession,
    *,
    order: Order,
    user: User,
    amount: float | None = None,
    allow_negative: bool = False,
):
    if order.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    outstanding = max(float(order.total_amount or 0.0) - float(order.paid_amount or 0.0), 0.0)
    if outstanding <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is already fully paid")

    available = float(await get_wallet_balance(db, user.id) or 0.0)
    requested = float(amount) if amount else outstanding
    applied = min(requested, outstanding)

    if not allow_negative:
        applied = min(applied, available)

    if applied <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient Cargo Core Wallet balance. Available: ₹{available:.2f}, Required: ₹{requested:.2f}. Please top up your wallet and try again.",
        )

    await _record_wallet_transaction(
        db,
        user_id=user.id,
        order_id=order.id,
        transaction_kind="DEBIT",
        reason="ORDER_PAYMENT",
        amount=applied,
        description=f"Wallet payment applied to {order.tracking_code}",
    )

    db.add(
        OrderPayment(
            order_id=order.id,
            payment_ref=_wallet_ref("WLT"),
            payment_mode=WALLET_PAYMENT_MODE,
            payment_method="Internal Wallet",
            amount=applied,
            status="completed",
            notes="Wallet credit applied",
        )
    )

    order.paid_amount = float(order.paid_amount or 0.0) + applied
    order.payment_status = "paid" if order.paid_amount >= order.total_amount else "partial"
    db.add(order)

    from app.services.return_charge_service import (
        settle_transport_charges_from_order_payment,
    )
    await settle_transport_charges_from_order_payment(
        db,
        order=order,
        payment_amount=applied,
        collection_source="ORDER_WALLET",
    )

    # ── Record in Finance: create a REVENUE_WALLET LogisticsTransaction so
    #    wallet bookings appear in the Finance overview table and MTD revenue. ──
    from app.models.logistics import LogisticsTransaction
    from app.services.finance_service import _gen_ref, _upsert_daily_stats

    db.add(
        LogisticsTransaction(
            warehouse_id=order.warehouse_id,
            transaction_code=_gen_ref("WLT"),
            description=f"Wallet payment - Order {order.tracking_code}",
            transaction_type="REVENUE_WALLET",
            amount=applied,
            status="Completed",
            metadata_json={
                "order_id": str(order.id),
                "tracking_code": order.tracking_code,
                "payment_mode": "WALLET",
                "payment_method": "Internal Wallet",
                "customer_id": str(user.id),
            },
        )
    )
    await _upsert_daily_stats(db, delta_revenue=applied)
    if order.warehouse_id:
        await _upsert_daily_stats(db, delta_revenue=applied, warehouse_id=order.warehouse_id)

    await db.flush()

    from app.schemas.wallet import WalletPaymentResponse

    return WalletPaymentResponse(
        order_id=order.id,
        tracking_code=order.tracking_code,
        applied_amount=round(applied, 2),
        remaining_wallet_balance=round(await get_wallet_balance(db, user.id), 2),
        paid_amount=round(float(order.paid_amount or 0.0), 2),
        payment_status=order.payment_status,
    )


async def backfill_wallet_debits(db: AsyncSession, user: User) -> int:
    """
    For legacy wallet payments that went through /pay (ONLINE mode) instead of /wallet-pay,
    create missing DEBIT WalletTransaction rows so they appear in the wallet history.
    Returns the number of rows created.
    """
    from sqlalchemy import func as _func

    from app.models.order import Order
    from app.models.payment import OrderPayment

    # Find OrderPayment rows for this user's orders where the payment method was
    # a wallet (e.g. 'Cargo Core Wallet') but payment_mode was NOT 'WALLET'
    # (those would already have been handled by apply_wallet_payment).
    subq = (
        select(WalletTransaction.order_id)
        .where(
            WalletTransaction.user_id == user.id,
            WalletTransaction.transaction_kind == "DEBIT",
            WalletTransaction.reason == "ORDER_PAYMENT",
        )
    )

    rows = (
        await db.execute(
            select(OrderPayment, Order.tracking_code)
            .join(Order, Order.id == OrderPayment.order_id)
            .where(
                Order.customer_id == user.id,
                OrderPayment.status == "completed",
                OrderPayment.amount > 0,
                OrderPayment.payment_mode != "WALLET",
                _func.lower(OrderPayment.payment_method).contains("wallet"),
                OrderPayment.order_id.notin_(subq),
            )
        )
    ).all()

    created = 0
    for pmt, tracking_code in rows:
        await _record_wallet_transaction(
            db,
            user_id=user.id,
            order_id=pmt.order_id,
            transaction_kind="DEBIT",
            reason="ORDER_PAYMENT",
            amount=float(pmt.amount),
            description=f"Wallet payment applied to {tracking_code or pmt.order_id}",
        )
        created += 1

    if created:
        await db.flush()
    return created


async def credit_cancellation_refund(
    db: AsyncSession,
    *,
    order: Order,
    refund_amount: float,
    fee_amount: float,
) -> float:
    total_paid = float(order.paid_amount or 0.0)
    # Clamp refund to what was actually paid (if recorded). If paid_amount is 0 (legacy/inferred
    # payment), allow the full requested refund_amount through so the wallet is credited.
    if total_paid > 0:
        refund_amount = round(min(refund_amount, total_paid), 2)
    else:
        refund_amount = round(refund_amount, 2)

    if refund_amount <= 0:
        return 0.0

    payment_rows = (
        await db.execute(
            select(OrderPayment).where(
                OrderPayment.order_id == order.id,
                OrderPayment.status == "completed",
            )
        )
    ).scalars().all()

    wallet_paid = sum(float(row.amount or 0.0) for row in payment_rows if row.payment_mode == WALLET_PAYMENT_MODE and row.amount > 0)
    external_paid = sum(
        float(row.amount or 0.0)
        for row in payment_rows
        if row.payment_mode not in {WALLET_PAYMENT_MODE, REFUND_PAYMENT_MODE} and row.amount > 0
    )

    # Always credit the wallet with the full refund amount
    await _record_wallet_transaction(
        db,
        user_id=order.customer_id,
        order_id=order.id,
        transaction_kind="CREDIT",
        reason="CANCELLATION_REFUND",
        amount=refund_amount,
        description=f"Cancellation refund for {order.tracking_code}",
    )

    # Only create OrderPayment reversal rows when there are matching payment records
    if external_paid > 0:
        wallet_restore = min(wallet_paid, refund_amount)
        external_refund = max(refund_amount - wallet_restore, 0.0)
        if external_refund > 0:
            refund_entry_amount = round(min(external_refund, external_paid), 2)
            db.add(
                OrderPayment(
                    order_id=order.id,
                    payment_ref=_wallet_ref("RFD"),
                    payment_mode=REFUND_PAYMENT_MODE,
                    payment_method="Wallet Credit",
                    amount=-refund_entry_amount,
                    status="completed",
                    notes=f"Cancellation refund credited to wallet after fee INR {round(fee_amount, 2)}",
                )
            )

            # Create a LogisticsTransaction reversal so the Logistics Manager
            # transaction history reflects the revenue being returned to the customer.
            from app.models.logistics import LogisticsTransaction
            from app.services.finance_service import _gen_ref, _upsert_daily_stats

            db.add(
                LogisticsTransaction(
                    transaction_code=_gen_ref("RFD"),
                    description=f"Cancellation refund for {order.tracking_code} - INR {refund_entry_amount} returned to customer wallet",
                    transaction_type="REVENUE_REFUND",
                    amount=-refund_entry_amount,   # negative = revenue reversal
                    status="Completed",
                    metadata_json={
                        "order_id": str(order.id),
                        "tracking_code": order.tracking_code,
                        "cancellation_fee": round(fee_amount, 2),
                        "refund_amount": refund_entry_amount,
                    },
                )
            )

            # Decrement daily stats revenue by the refunded amount
            await _upsert_daily_stats(db, delta_revenue=-refund_entry_amount)
    else:
        # No recorded payment rows — the refund was inferred from payment_status='paid'.
        # Still record a logistics transaction reversal for accounting accuracy.
        from app.models.logistics import LogisticsTransaction
        from app.services.finance_service import _gen_ref, _upsert_daily_stats

        db.add(
            LogisticsTransaction(
                transaction_code=_gen_ref("RFD"),
                description=f"Cancellation refund for {order.tracking_code} - INR {round(refund_amount, 2)} returned to customer wallet",
                transaction_type="REVENUE_REFUND",
                amount=-round(refund_amount, 2),
                status="Completed",
                metadata_json={
                    "order_id": str(order.id),
                    "tracking_code": order.tracking_code,
                    "cancellation_fee": round(fee_amount, 2),
                    "refund_amount": round(refund_amount, 2),
                },
            )
        )
        await _upsert_daily_stats(db, delta_revenue=-round(refund_amount, 2))

    order.paid_amount = max(total_paid - refund_amount, 0.0)
    if order.paid_amount <= 0:
        order.payment_status = "refunded"
    else:
        order.payment_status = "partially_refunded"
    db.add(order)
    await db.flush()
    return refund_amount


async def credit_return_refund(
    db: AsyncSession,
    *,
    customer_id: UUID,
    order_id: UUID | None,
    refund_amount: float,
    reference_code: str,
    warehouse_id: UUID | None = None,
) -> bool:
    """Credit customer wallet for an approved damage/return case and debit finance revenue.
    Returns True if credited, False if already issued (idempotent)."""
    if refund_amount <= 0:
        return False

    # Idempotency check — don't double-credit the same return case
    existing = (await db.execute(
        select(WalletTransaction).where(
            WalletTransaction.user_id == customer_id,
            WalletTransaction.reason == "DAMAGE_REFUND",
            WalletTransaction.description.contains(reference_code),
        )
    )).scalar_one_or_none()
    if existing:
        return False

    # 1. Credit customer wallet
    await _record_wallet_transaction(
        db,
        user_id=customer_id,
        order_id=order_id,
        transaction_kind="CREDIT",
        reason="DAMAGE_REFUND",
        amount=refund_amount,
        description=f"Damage/return refund approved for {reference_code}",
    )

    # 2. LogisticsTransaction — negative amount = revenue reversal visible in Finance & Payroll
    from app.models.logistics import LogisticsTransaction
    from app.services.finance_service import _gen_ref, _upsert_daily_stats

    db.add(
        LogisticsTransaction(
            warehouse_id=warehouse_id,
            transaction_code=_gen_ref("DMG"),
            description=f"Damage return refund {reference_code} — ₹{refund_amount} credited to customer wallet",
            transaction_type="REVENUE_REFUND",
            amount=-refund_amount,
            status="Completed",
            metadata_json={
                "reference_code": reference_code,
                "order_id": str(order_id) if order_id else None,
                "refund_amount": refund_amount,
            },
        )
    )

    # 3. Debit daily stats (global + warehouse-scoped if available)
    await _upsert_daily_stats(db, delta_revenue=-refund_amount)
    if warehouse_id:
        await _upsert_daily_stats(db, delta_revenue=-refund_amount, warehouse_id=warehouse_id)
    return True
