"""Lookups, status rules and inbound ticket helpers shared by the warehouse operations."""

import re
import uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.models.warehouse import (
    QualityCheck,
    Warehouse,
)
from app.schemas.warehouse_operations import (
    WAREHOUSE_SUBSTATUS_TRANSITIONS,
    WAREHOUSE_SUBSTATUSES,
    InboundReceivePlanResponse,
    InboundReceivePlanShipment,
    QualityCheckResponse,
)

# ======================
# Helper Functions
# ======================

async def _get_warehouse(db: AsyncSession, warehouse_id: UUID) -> Warehouse:
    result = await db.execute(
        select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.is_active.is_(True))
    )
    warehouse = result.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return warehouse


async def _get_order(db: AsyncSession, order_id: UUID) -> Order:
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def _is_active_inbound_supplier(vendor: User | None) -> bool:
    return bool(vendor and getattr(vendor, "is_active", False))


def _validate_substatus_transition(current: str | None, target: str) -> None:
    if target not in WAREHOUSE_SUBSTATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid warehouse substatus: {target}"
        )

    if current is None:
        # Allow initial transition to AWAITING_INBOUND (vendor) or AWAITING_PICK (individual)
        if target not in {"AWAITING_INBOUND", "AWAITING_PICK", "ON_HOLD"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Initial substatus must be AWAITING_INBOUND or AWAITING_PICK, got {target}"
            )
        return

    allowed = WAREHOUSE_SUBSTATUS_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {current} to {target}. Allowed: {allowed}"
        )


def _to_quality_check_response(qc: QualityCheck) -> QualityCheckResponse:
    performer_name = qc.performer.name if qc.performer else None

    return QualityCheckResponse(
        id=qc.id,
        order_id=qc.order_id,
        warehouse_id=qc.warehouse_id,
        goods_correct=qc.goods_correct,
        count_correct=qc.count_correct,
        packaging_verified=qc.packaging_verified,
        labor_assigned=qc.labor_assigned,
        weight_verified=qc.weight_verified,
        label_attached=qc.label_attached,
        is_passed=qc.is_passed,
        notes=qc.notes,
        performed_by=qc.performed_by,
        performer_name=performer_name,
        checked_at=qc.checked_at,
        created_at=qc.created_at,
    )


def _format_user_name(user: User | None) -> str | None:
    return user.name if user else None


INBOUND_RECEIVED_SUBSTATUSES = {
    "AWAITING_PICK",
    "PICKING",
    "PICKED",
    "PACKING",
    "PACKED",
    "QC_PASSED",
    "DISPATCHED",
}
TERMINAL_ORDER_STATUSES = {"DELIVERED", "CLOSED", "CANCELLED"}


def _inbound_tracking_code() -> str:
    return f"QC-{uuid.uuid4().hex[:10].upper()}"


def _inbound_report_reference(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


TICKET_NOTE_META_PATTERN = re.compile(r"^\[meta:(?P<key>[a-z_]+)=(?P<value>.*)\]$")
INBOUND_RESOLUTION_LABELS = {
    "pending_review": "Pending review with vendor and support",
    "vendor_accept_move": "Vendor cleared the shipment to move to picking",
    "vendor_take_back": "Vendor will take back the damaged shipment",
}


def _parse_ticket_notes_metadata(raw_notes: str | None) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw_line in (raw_notes or "").splitlines():
        line = raw_line.strip()
        match = TICKET_NOTE_META_PATTERN.match(line)
        if match:
            metadata[match.group("key")] = match.group("value")
    return metadata


def _linked_issue_type(ticket: SupportTicket | None) -> str | None:
    if not ticket:
        return None
    return _parse_ticket_notes_metadata(ticket.notes).get("issue_type")


def _linked_resolution_action(ticket: SupportTicket | None) -> str | None:
    if not ticket:
        return None
    raw_action = (_parse_ticket_notes_metadata(ticket.notes).get("resolution_action") or "").strip().lower()
    # Backward compatibility: older support flows could mark a warehouse issue
    # as resolved without replacing the initial pending_review marker. Those
    # issues should continue through the normal inbound move flow instead of
    # staying blocked forever in WM inbound.
    if (ticket.status or "").strip().lower() == "resolved" and raw_action in {"", "pending_review"}:
        return "vendor_accept_move"
    return raw_action or None


def _ticket_reference_code(ticket: SupportTicket | None) -> str | None:
    return ticket.reference_code if ticket else None


def _is_inbound_issue_ticket(ticket: SupportTicket, order_id: UUID) -> bool:
    metadata = _parse_ticket_notes_metadata(ticket.notes)
    return (
        metadata.get("source") == "warehouse_inbound"
        and metadata.get("linked_order_id") == str(order_id)
        and metadata.get("issue_type") in {"mismatch", "damage"}
    )


async def _latest_inbound_issue_ticket(
    db: AsyncSession,
    order_id: UUID,
) -> SupportTicket | None:
    rows = (
        await db.execute(
            select(SupportTicket)
            .where(
                SupportTicket.notes.is_not(None),
                SupportTicket.notes.contains(str(order_id)),
            )
            .order_by(SupportTicket.updated_at.desc(), SupportTicket.created_at.desc())
        )
    ).scalars().all()
    for ticket in rows:
        if _is_inbound_issue_ticket(ticket, order_id):
            return ticket
    return None


def _inbound_status(order: Order) -> str | None:
    if (getattr(order, "status", "") or "").upper() in TERMINAL_ORDER_STATUSES:
        return None
    substatus = (order.warehouse_substatus or "").upper()
    if substatus in INBOUND_RECEIVED_SUBSTATUSES:
        return "Completed"
    if substatus == "ON_HOLD":
        return "OnHold"
    if substatus != "AWAITING_INBOUND":
        return None
    if order.arrived_at:
        return "Arrived"
    scheduled_at = order.scheduled_at
    if scheduled_at and scheduled_at > datetime.now(UTC):
        return "InTransit"
    return "Scheduled"


def _dock_status_for_shipment(status_name: str) -> str:
    if status_name == "Completed":
        return "Completed"
    if status_name in {"Arrived", "Receiving"}:
        return "Active"
    return "Scheduled"


def _is_recurring_inbound(order: Order) -> bool:
    notes = str(order.delivery_notes or "")
    return "RECURRING_RULE:" in notes and "|RUN:" in notes


def _strip_json_fences(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def _material_profile_for_inbound(
    *,
    order: Order,
    expected_qty: int,
    box_count: int,
    estimated_volume: float,
) -> str:
    cargo = (order.cargo_type or "General cargo").strip()
    if expected_qty >= 120 or estimated_volume >= 250:
        scale = "High-volume bulk unload"
    elif expected_qty >= 50 or estimated_volume >= 120:
        scale = "Medium dock unload"
    else:
        scale = "Light inbound unload"

    packaging = "palletized" if box_count >= max(2, expected_qty // 5) else "mixed loose + boxed"
    return f"{cargo} · {scale} · {packaging}"


def _heuristic_inbound_receive_plan(
    *,
    order: Order,
    supplier_name: str,
    status_name: str,
    expected_qty: int,
    box_count: int,
    estimated_volume: float,
    has_mismatch: bool,
    has_damage: bool,
    dock_names: list[str],
    active_dock_count: int,
) -> InboundReceivePlanResponse:
    recurring = _is_recurring_inbound(order)
    material_profile = _material_profile_for_inbound(
        order=order,
        expected_qty=expected_qty,
        box_count=box_count,
        estimated_volume=estimated_volume,
    )

    pallet_load = max(1, (expected_qty + 9) // 10)
    queue_minutes = active_dock_count * 12
    unload_minutes = max(15, pallet_load * 8 + max(0, expected_qty // 20))
    verification_minutes = max(10, expected_qty // 14) + (10 if has_mismatch else 0) + (8 if has_damage else 0)
    total_minutes = queue_minutes + unload_minutes + verification_minutes
    workers = 5 if expected_qty >= 120 else 4 if expected_qty >= 70 else 3 if expected_qty >= 30 else 2

    risk_score = (
        (35 if has_mismatch else 0)
        + (25 if has_damage else 0)
        + (10 if status_name == "InTransit" else 0)
        + (15 if expected_qty > 100 else 8 if expected_qty > 50 else 0)
        + (10 if active_dock_count > 2 else 4 if active_dock_count > 0 else 0)
    )
    risk_level = "High" if risk_score >= 50 else "Medium" if risk_score >= 25 else "Low"
    confidence = max(
        68,
        92
        - (10 if has_mismatch else 0)
        - (8 if has_damage else 0)
        - (6 if active_dock_count > 2 else active_dock_count * 2),
    )

    suggested_dock = dock_names[0] if dock_names else ("Dock 2" if expected_qty >= 90 else "Dock 1")
    staging_zone = "Inbound Buffer B" if expected_qty >= 90 else "Inbound Buffer A" if expected_qty >= 40 else "Fast Receive Lane"
    shipment_type = "Recurring inbound transfer" if recurring else "Ad-hoc inbound transfer"
    summary = (
        f"{shipment_type} from {supplier_name} with about {expected_qty} units. "
        f"Plan {workers} crew, {pallet_load} pallet run, and roughly {total_minutes} minutes to receive."
    )
    next_action = (
        "Keep dock and receiving crew on standby so the arrival scan can start immediately."
        if status_name == "InTransit"
        else "Start receiving at the dock, verify pallet count, then move stock to staging."
        if status_name == "Arrived"
        else "Complete verification and update stock before releasing the dock."
        if status_name == "Receiving"
        else "Review completed exceptions before archival."
        if status_name == "Completed"
        else "Confirm ETA with the vendor and reserve the suggested dock window."
    )
    reason = (
        "Plan is based on inbound quantity, current dock queue, shipment stage, package density, "
        "and any recorded mismatch or damage alerts."
    )
    watchouts = [
        f"{expected_qty} expected units",
        f"{pallet_load} pallet load",
        "Mismatch follow-up needed" if has_mismatch else "ASN count currently stable",
        "Damage inspection required" if has_damage else "No damage alert on record",
    ]

    return InboundReceivePlanResponse(
        order_id=order.id,
        asn=InboundReceivePlanShipment(
            id=order.tracking_code or f"ASN-{str(order.id)[:6].upper()}",
            supplier=supplier_name,
            status=status_name,
            shipment_type=shipment_type,
            material_profile=material_profile,
            expected_units=expected_qty,
            recurring=recurring,
        ),
        confidence=confidence,
        suggested_dock=suggested_dock,
        workers=workers,
        total_minutes=total_minutes,
        risk_level=risk_level,
        pallet_load=pallet_load,
        queue_minutes=queue_minutes,
        active_dock_count=active_dock_count,
        staging_zone=staging_zone,
        next_action=next_action,
        reason=reason,
        watchouts=watchouts,
        summary=summary,
        generated_by="fallback",
    )
