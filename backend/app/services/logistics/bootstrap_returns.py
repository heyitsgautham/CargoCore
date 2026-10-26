"""Return cases for the logistics bootstrap: backfilling missing cases and mapping them for the dashboard."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsReturnCase,
)
from app.models.order import DamageReport, Order
from app.models.user import User
from app.models.warehouse import ReturnGrading
from app.schemas.logistics import (
    LogisticsReturnCaseItem,
)


async def backfill_return_cases(
    return_cases: Sequence[LogisticsReturnCase],
    db: AsyncSession,
    orders: Sequence[Order],
    users: Sequence[User],
    return_gradings: Sequence[ReturnGrading],
) -> Sequence[LogisticsReturnCase]:
    """Create return cases for damage reports and warehouse gradings that have none, newest first."""
    # Backfill: auto-create LogisticsReturnCase for any DamageReport not yet linked
    existing_ref_codes = {rc.reference_code for rc in return_cases}
    damage_reports = (await db.execute(select(DamageReport).order_by(DamageReport.created_at.desc()))).scalars().all()
    order_map = {o.id: o for o in orders}
    user_map = {u.id: u for u in users}
    new_cases = []
    for dr in damage_reports:
        if dr.reference_code not in existing_ref_codes:
            order_row = order_map.get(dr.order_id) if dr.order_id else None
            order_total = (order_row.total_amount or 0.0) if order_row else 0.0
            warehouse_id = order_row.warehouse_id if order_row else None
            user_row = user_map.get(dr.customer_id)
            customer_name = (user_row.name or user_row.email or str(dr.customer_id)) if user_row else str(dr.customer_id)
            new_case = LogisticsReturnCase(
                warehouse_id=warehouse_id,
                order_id=dr.order_id,
                reference_code=dr.reference_code,
                customer_name=customer_name,
                reason=(dr.description or "Damage reported")[:255],
                flow_type=getattr(dr, "flow_type", "photo_review") or "photo_review",
                condition="Reported",
                status="Pickup Requested" if (getattr(dr, "flow_type", "photo_review") == "pickup_inspection") else "Reported",
                original_price=order_total,
                refund_amount=0.0,
                images=dr.photos or [],
            )
            db.add(new_case)
            new_cases.append(new_case)

    # Backfill: warehouse/driver-side returns may create ReturnGrading records without
    # a LogisticsReturnCase entry. Surface them in Reverse Logistics so LM can still
    # see "Arrived at Warehouse" / "Physically Inspected" states.
    for grading in return_gradings:
        if not grading.rma_code or grading.rma_code in existing_ref_codes:
            continue

        order_row = order_map.get(grading.order_id) if grading.order_id else None
        user_row = user_map.get(order_row.customer_id) if order_row and order_row.customer_id else None
        customer_name = (
            user_row.name or user_row.email
            if user_row
            else (f"Order {order_row.tracking_code}" if order_row else "Warehouse Return")
        )

        if grading.status == "completed":
            derived_status = "Physically Inspected"
        elif grading.item_condition == "Awaiting Pickup":
            derived_status = "Pickup Scheduled"
        else:
            derived_status = "Arrived at Warehouse"

        new_case = LogisticsReturnCase(
            warehouse_id=grading.warehouse_id or (order_row.warehouse_id if order_row else None),
            order_id=grading.order_id,
            reference_code=grading.rma_code,
            customer_name=customer_name,
            reason=grading.condition_notes or "Warehouse return",
            flow_type="pickup_inspection",
            condition=grading.item_condition or "Pending Inspection",
            status=derived_status,
            original_price=(order_row.total_amount or 0.0) if order_row else 0.0,
            refund_amount=0.0,
            images=[],
        )
        db.add(new_case)
        new_cases.append(new_case)
        existing_ref_codes.add(grading.rma_code)

    if new_cases:
        await db.flush()
        return_cases = list(new_cases) + list(return_cases)
    return return_cases


async def credited_reference_codes(return_cases: Sequence[LogisticsReturnCase], db: AsyncSession) -> set[str]:
    """Reference codes already named in a DAMAGE_REFUND wallet transaction."""
    # Build set of reference codes that already have a DAMAGE_REFUND wallet transaction.
    from app.models.wallet import WalletTransaction
    _credited_ref_codes: set[str] = set()
    _reference_codes = {item.reference_code for item in return_cases if item.reference_code}
    if _reference_codes:
        _dmg_txns = (await db.execute(
            select(WalletTransaction.description).where(WalletTransaction.reason == "DAMAGE_REFUND")
        )).scalars().all()
        for _desc in _dmg_txns:
            description = _desc or ""
            for reference_code in _reference_codes:
                if reference_code in description:
                    _credited_ref_codes.add(reference_code)
    return _credited_ref_codes


def latest_completed_gradings(
    return_gradings: Sequence[ReturnGrading],
) -> tuple[dict[str, ReturnGrading], dict[UUID, ReturnGrading]]:
    """The newest completed grading per RMA code and per order. Gradings arrive newest first."""
    latest_completed_grading_by_rma: dict[str, ReturnGrading] = {}
    latest_completed_grading_by_order_id: dict[UUID, ReturnGrading] = {}
    for grading in return_gradings:
        if grading.status != "completed":
            continue
        if grading.rma_code and grading.rma_code not in latest_completed_grading_by_rma:
            latest_completed_grading_by_rma[grading.rma_code] = grading
        if grading.order_id and grading.order_id not in latest_completed_grading_by_order_id:
            latest_completed_grading_by_order_id[grading.order_id] = grading
    return latest_completed_grading_by_rma, latest_completed_grading_by_order_id


def _wm_completed_grading_for_case(
    item: LogisticsReturnCase,
    latest_completed_grading_by_rma: dict[str, ReturnGrading],
    latest_completed_grading_by_order_id: dict[UUID, ReturnGrading],
) -> ReturnGrading | None:
    if item.reference_code and item.reference_code in latest_completed_grading_by_rma:
        return latest_completed_grading_by_rma[item.reference_code]
    if item.order_id and item.order_id in latest_completed_grading_by_order_id:
        return latest_completed_grading_by_order_id[item.order_id]
    return None


def to_return_case_item(
    item: LogisticsReturnCase,
    latest_completed_grading_by_rma: dict[str, ReturnGrading],
    latest_completed_grading_by_order_id: dict[UUID, ReturnGrading],
    _credited_ref_codes: set[str],
) -> LogisticsReturnCaseItem:
    completed_grading = _wm_completed_grading_for_case(
        item, latest_completed_grading_by_rma, latest_completed_grading_by_order_id
    )
    is_physical_flow = getattr(item, "flow_type", None) == "pickup_inspection"
    normalized_status = item.status
    case_images = list(item.images or [])
    if completed_grading and completed_grading.damage_photo_url and completed_grading.damage_photo_url not in case_images:
        case_images.append(completed_grading.damage_photo_url)
    if not is_physical_flow and item.status in {"Inspected", "Physically Inspected"}:
        normalized_status = "Claims Reviewed"
    display_status = normalized_status
    if completed_grading and is_physical_flow and normalized_status in {"Arrived at Warehouse", "At Warehouse", "Inspected", "Physically Inspected"}:
        display_status = "Physically Inspected"
    return LogisticsReturnCaseItem(
        id=item.id,
        hub_id=item.warehouse_id,
        order_id=item.order_id,
        customer=item.customer_name,
        reason=item.reason,
        flow_type=getattr(item, "flow_type", None),
        condition=completed_grading.item_condition if (completed_grading and is_physical_flow) else item.condition,
        status=display_status,
        original_price=item.original_price,
        refund_amount=item.refund_amount,
        images=case_images,
        reference_code=item.reference_code,
        wallet_credited=item.reference_code in _credited_ref_codes,
        wm_disposition=completed_grading.disposition if (completed_grading and is_physical_flow) else None,
        wm_is_genuine=completed_grading.is_genuine if (completed_grading and is_physical_flow) else getattr(item, "wm_is_genuine", None),
        wm_recommended_outcome=completed_grading.recommended_outcome if (completed_grading and is_physical_flow) else getattr(item, "wm_recommended_outcome", None),
        wm_inspection_remarks=completed_grading.inspection_remarks if (completed_grading and is_physical_flow) else getattr(item, "wm_inspection_remarks", None),
        wm_graded_at=completed_grading.graded_at if (completed_grading and is_physical_flow) else None,
        wm_grader_name=completed_grading.grader.name if (completed_grading and is_physical_flow and completed_grading.grader) else None,
        transport_charge_amount=round(float(item.transport_charge_amount or 0.0), 2),
        transport_charge_wallet_collected=round(float(item.transport_charge_wallet_collected or 0.0), 2),
        transport_charge_pending_amount=round(float(item.transport_charge_pending_amount or 0.0), 2),
        transport_charge_status=item.transport_charge_status,
        transport_charge_applied_at=item.transport_charge_applied_at,
        is_urgent=bool(getattr(item, "is_urgent", False)),
        urgent_reason=getattr(item, "urgent_reason", None),
    )
