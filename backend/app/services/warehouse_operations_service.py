"""Warehouse Operations Service.

Handles warehouse lifecycle operations: inbound receiving, picking, packing,
quality checks, loading dock management, returns grading, and zone metrics.
"""
import json
import re
import uuid
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from google.genai import types
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.labour import Labourer
from app.models.logistics import LogisticsReturnCase
from app.models.order import DamageReport, Order, OrderItem
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.models.vendor import VendorSupportReply, VendorSupportTicket
from app.models.warehouse import (
    LoadingDock,
    PackingStation,
    QualityCheck,
    ReturnGrading,
    Warehouse,
    WarehouseZoneMetrics,
)
from app.schemas.warehouse_operations import (
    WAREHOUSE_SUBSTATUS_TRANSITIONS,
    WAREHOUSE_SUBSTATUSES,
    AssignTruckRequest,
    DockSlot,
    DockVerificationData,
    InboundDamageReport,
    InboundMismatchReport,
    InboundReceivePlanResponse,
    InboundReceivePlanShipment,
    InboundResponse,
    InboundShipmentItem,
    InboundStats,
    LoadingDockCreate,
    LoadingDockListResponse,
    LoadingDockResponse,
    PackingStationCreate,
    PackingStationListResponse,
    PackingStationResponse,
    PackingStationUpdate,
    PerformanceMetrics,
    PerformanceResponse,
    PickingResponse,
    QualityCheckListResponse,
    QualityCheckResponse,
    QualityCheckUpdate,
    ReturnGradingCreate,
    ReturnGradingListResponse,
    ReturnGradingResponse,
    ReturnGradingUpdate,
    ScheduleInboundRequest,
    StartPackingRequest,
    StartPickingRequest,
    ZoneMetricsCreate,
    ZoneMetricsListResponse,
    ZoneMetricsResponse,
)
from app.utils.gemini import GEMINI_MODEL, GeminiConfigError, get_gemini_client

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


async def get_inbound_overview(
    db: AsyncSession,
    warehouse_id: UUID,
) -> InboundResponse:
    warehouse = await _get_warehouse(db, warehouse_id)
    orders = (
        await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.warehouse_id == warehouse_id,
                Order.order_type == "VENDOR",
                func.coalesce(Order.pickup_type, "hub") == "hub",
                Order.status.notin_(TERMINAL_ORDER_STATUSES),
                or_(
                    Order.warehouse_substatus == "AWAITING_INBOUND",
                    Order.warehouse_substatus == "ON_HOLD",
                    Order.warehouse_substatus.in_(INBOUND_RECEIVED_SUBSTATUSES),
                ),
            )
            .order_by(Order.scheduled_at.asc().nulls_last(), Order.created_at.desc())
        )
    ).scalars().all()

    order_ids = [order.id for order in orders]
    vendor_ids = list({order.customer_id for order in orders})

    vendors = {}
    if vendor_ids:
        vendor_rows = (
            await db.execute(
                select(User)
                .options(selectinload(User.role))
                .where(User.id.in_(vendor_ids), User.is_active.is_(True))
            )
        ).scalars().all()
        vendors = {vendor.id: vendor for vendor in vendor_rows}

    latest_damage_by_order: dict[UUID, DamageReport] = {}
    damage_count_by_order: dict[UUID, int] = {}
    if order_ids:
        damage_rows = (
            await db.execute(
                select(DamageReport)
                .where(DamageReport.order_id.in_(order_ids))
                .order_by(DamageReport.created_at.desc())
            )
        ).scalars().all()
        for report in damage_rows:
            if not report.order_id:
                continue
            damage_count_by_order[report.order_id] = damage_count_by_order.get(report.order_id, 0) + 1
            latest_damage_by_order.setdefault(report.order_id, report)

    latest_mismatch_by_order: dict[UUID, VendorSupportTicket] = {}
    mismatch_count_by_order: dict[UUID, int] = {}
    if order_ids:
        mismatch_rows = (
            await db.execute(
                select(VendorSupportTicket)
                .where(
                    VendorSupportTicket.order_id.in_(order_ids),
                    VendorSupportTicket.subject.ilike("Inbound mismatch:%"),
                )
                .order_by(VendorSupportTicket.created_at.desc())
            )
        ).scalars().all()
        for ticket in mismatch_rows:
            if not ticket.order_id:
                continue
            mismatch_count_by_order[ticket.order_id] = mismatch_count_by_order.get(ticket.order_id, 0) + 1
            latest_mismatch_by_order.setdefault(ticket.order_id, ticket)

    latest_issue_ticket_by_order: dict[UUID, SupportTicket] = {}
    if order_ids:
        linked_issue_rows = (
            await db.execute(
                select(SupportTicket)
                .where(
                    SupportTicket.notes.is_not(None),
                    or_(*[SupportTicket.notes.contains(str(order_id)) for order_id in order_ids]),
                )
                .order_by(SupportTicket.updated_at.desc(), SupportTicket.created_at.desc())
            )
        ).scalars().all()
        for ticket in linked_issue_rows:
            metadata = _parse_ticket_notes_metadata(ticket.notes)
            linked_order_raw = metadata.get("linked_order_id")
            if not linked_order_raw:
                continue
            try:
                linked_order_id = UUID(linked_order_raw)
            except ValueError:
                continue
            if linked_order_id not in order_ids or not _is_inbound_issue_ticket(ticket, linked_order_id):
                continue
            latest_issue_ticket_by_order.setdefault(linked_order_id, ticket)

    shipments: list[InboundShipmentItem] = []
    now = datetime.now(UTC)
    today = now.date()
    inbound_cutoff = today + timedelta(days=1)  # show recurring orders 1 day before their run date
    arrived_today = 0
    in_transit = 0
    mismatches_found = 0
    damage_reports = 0

    for order in orders:
        # Recurring inbound orders are only surfaced 1 day before their scheduled date
        if _is_recurring_inbound(order) and order.scheduled_at:
            if order.scheduled_at.date() > inbound_cutoff:
                continue

        status_name = _inbound_status(order)

        if not status_name:
            continue

        vendor = vendors.get(order.customer_id)
        if not _is_active_inbound_supplier(vendor):
            continue
        supplier_name = (
            (vendor.company_name if vendor and vendor.company_name else None)
            or (vendor.name if vendor else None)
            or "Unknown Supplier"
        )
        expected_qty = sum(int(item.quantity or 0) for item in order.items) or 1
        latest_mismatch = latest_mismatch_by_order.get(order.id)
        latest_damage = latest_damage_by_order.get(order.id)
        latest_issue_ticket = latest_issue_ticket_by_order.get(order.id)
        has_mismatch = bool(latest_mismatch)
        has_damage = bool(latest_damage)
        issue_type = _linked_issue_type(latest_issue_ticket)
        resolution_action = _linked_resolution_action(latest_issue_ticket)
        issue_ticket_id = latest_issue_ticket.id if latest_issue_ticket else None
        issue_ticket_reference = _ticket_reference_code(latest_issue_ticket)
        can_move_to_picking = resolution_action == "vendor_accept_move" or not (has_mismatch or has_damage)
        can_generate_take_back = resolution_action == "vendor_take_back"
        issue_blocking_reason = None
        if has_mismatch or has_damage:
            issue_blocking_reason = INBOUND_RESOLUTION_LABELS.get(
                resolution_action,
                "Warehouse cannot move this inbound until support confirms the vendor decision.",
            )

        if order.arrived_at and order.arrived_at.astimezone(UTC).date() == now.date():
            arrived_today += 1
        if status_name == "InTransit":
            in_transit += 1
        mismatches_found += mismatch_count_by_order.get(order.id, 0)
        damage_reports += damage_count_by_order.get(order.id, 0)

        shipments.append(
            InboundShipmentItem(
                id=order.id,
                tracking_code=order.tracking_code,
                supplier_name=supplier_name,
                supplier_id=vendor.id if vendor else None,
                expected_qty=expected_qty,
                received_qty=expected_qty if status_name == "Completed" else 0,
                eta=order.scheduled_at,
                scheduled_at=order.scheduled_at,
                status=status_name,
                has_mismatch=has_mismatch,
                has_damage=has_damage,
                mismatch_type=latest_mismatch.subject.split(":", 1)[-1].strip() if latest_mismatch else None,
                mismatch_details=latest_mismatch.description if latest_mismatch else None,
                damage_count=damage_count_by_order.get(order.id, 0),
                damage_description=latest_damage.description if latest_damage else None,
                issue_type=issue_type,
                issue_resolution_action=resolution_action,
                issue_resolution_label=INBOUND_RESOLUTION_LABELS.get(resolution_action),
                issue_status=latest_issue_ticket.status if latest_issue_ticket else None,
                issue_ticket_id=issue_ticket_id,
                issue_ticket_reference=issue_ticket_reference,
                issue_blocking_reason=issue_blocking_reason,
                can_move_to_picking=can_move_to_picking,
                can_generate_take_back=can_generate_take_back,
                warehouse_substatus=order.warehouse_substatus,
                order_id=order.id,
                total_amount=float(order.total_amount or 0.0),
                auto_debit_enabled=bool(order.delivery_notes and "autoDebitEnabled\": true" in str(order.delivery_notes).replace(" ", "")),
                is_recurring=_is_recurring_inbound(order),
                created_at=order.created_at,
            )
        )

    dock_schedule = [
        DockSlot(
            id=index + 1,
            time=(shipment.scheduled_at or shipment.created_at).astimezone(UTC).strftime("%H:%M"),
            supplier=shipment.supplier_name,
            dock=f"Dock {(index % 4) + 1}",
            pallets=max(1, (shipment.expected_qty + 9) // 10),
            status=_dock_status_for_shipment(shipment.status),
            order_id=shipment.order_id,
        )
        for index, shipment in enumerate(shipments[:6])
    ]

    return InboundResponse(
        stats=InboundStats(
            arrived_today=arrived_today,
            in_transit=in_transit,
            mismatches_found=mismatches_found,
            damage_reports=damage_reports,
        ),
        shipments=shipments,
        dock_schedule=dock_schedule,
    )


async def get_inbound_receive_plan(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> InboundReceivePlanResponse:
    warehouse = await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order does not belong to this warehouse")
    if order.order_type != "VENDOR" or (order.pickup_type or "hub").lower() != "hub":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AI receive plan is only available for hub-based vendor inbound orders")

    status_name = _inbound_status(order)
    if not status_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is not currently part of the inbound workflow")

    vendor = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == order.customer_id)
        )
    ).scalar_one_or_none()
    supplier_name = (
        (vendor.company_name if vendor and vendor.company_name else None)
        or (vendor.name if vendor else None)
        or "Unknown Supplier"
    )

    expected_qty = sum(int(item.quantity or 0) for item in order.items) or 1
    total_box_count = sum(int(item.box_count or 0) for item in order.items)
    estimated_volume = round(sum(float(item.estimated_volume or 0) for item in order.items), 2)

    latest_damage = (
        await db.execute(
            select(DamageReport)
            .where(DamageReport.order_id == order.id)
            .order_by(DamageReport.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    latest_mismatch = (
        await db.execute(
            select(VendorSupportTicket)
            .where(
                VendorSupportTicket.order_id == order.id,
                VendorSupportTicket.subject.ilike("Inbound mismatch:%"),
            )
            .order_by(VendorSupportTicket.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    has_damage = latest_damage is not None
    has_mismatch = latest_mismatch is not None

    loading_docks = (
        await db.execute(
            select(LoadingDock)
            .where(LoadingDock.warehouse_id == warehouse_id)
            .order_by(LoadingDock.dock_number.asc())
        )
    ).scalars().all()

    def dock_label(raw_value: str) -> str:
        value = (raw_value or "").strip()
        return value if value.lower().startswith("dock") else f"Dock {value}"

    free_dock_names = [dock_label(dock.dock_number) for dock in loading_docks if (dock.status or "").upper() == "FREE"]
    all_dock_names = [dock_label(dock.dock_number) for dock in loading_docks]
    active_dock_count = sum(1 for dock in loading_docks if (dock.status or "").upper() == "OCCUPIED")

    if not all_dock_names:
        all_dock_names = [f"Dock {idx}" for idx in range(1, 5)]
    dock_candidates = free_dock_names or all_dock_names

    available_labourers = (
        await db.execute(
            select(func.count(Labourer.id))
            .where(
                Labourer.warehouse_id == warehouse_id,
                Labourer.is_active.is_(True),
                Labourer.assigned_order_id.is_(None),
            )
        )
    ).scalar_one()
    total_labourers = (
        await db.execute(
            select(func.count(Labourer.id))
            .where(
                Labourer.warehouse_id == warehouse_id,
                Labourer.is_active.is_(True),
            )
        )
    ).scalar_one()

    recurring = _is_recurring_inbound(order)
    fallback = _heuristic_inbound_receive_plan(
        order=order,
        supplier_name=supplier_name,
        status_name=status_name,
        expected_qty=expected_qty,
        box_count=total_box_count,
        estimated_volume=estimated_volume,
        has_mismatch=has_mismatch,
        has_damage=has_damage,
        dock_names=dock_candidates,
        active_dock_count=active_dock_count,
    )

    prompt_facts = {
        "warehouse": {
            "name": warehouse.name,
            "address": warehouse.address,
            "dock_candidates": dock_candidates,
            "active_dock_count": active_dock_count,
            "total_docks_configured": len(all_dock_names),
            "available_unassigned_crew": int(available_labourers or 0),
            "total_active_crew": int(total_labourers or 0),
        },
        "shipment": {
            "tracking_code": order.tracking_code,
            "supplier_name": supplier_name,
            "order_type": order.order_type,
            "pickup_type": order.pickup_type or "hub",
            "status": status_name,
            "warehouse_substatus": order.warehouse_substatus,
            "scheduled_at": order.scheduled_at.isoformat() if order.scheduled_at else None,
            "arrived_at": order.arrived_at.isoformat() if order.arrived_at else None,
            "cargo_type": order.cargo_type or "General cargo",
            "vehicle_type": order.vehicle_type or "Unspecified",
            "expected_units": expected_qty,
            "box_count": total_box_count,
            "estimated_volume": estimated_volume,
            "recurring": recurring,
        },
        "issues": {
            "has_mismatch": has_mismatch,
            "mismatch_type": latest_mismatch.subject.split(":", 1)[-1].strip() if latest_mismatch else None,
            "mismatch_details": latest_mismatch.description if latest_mismatch else None,
            "has_damage": has_damage,
            "damage_description": latest_damage.description if latest_damage else None,
        },
        "fallback_reference": {
            "shipment_type": fallback.asn.shipment_type,
            "material_profile": fallback.asn.material_profile,
            "crew_needed": fallback.workers,
            "receive_time_minutes": fallback.total_minutes,
            "risk_level": fallback.risk_level,
            "pallet_load": fallback.pallet_load,
            "suggested_dock": fallback.suggested_dock,
            "staging_zone": fallback.staging_zone,
            "queue_minutes": fallback.queue_minutes,
            "summary": fallback.summary,
            "recommendation": fallback.next_action,
        },
    }

    prompt = (
        "You are Cargo-Core's warehouse inbound AI planner.\n"
        "Use only the facts provided. Do not invent sensors, scans, or materials not in the facts.\n"
        "Return ONLY valid JSON in this exact shape:\n"
        "{\n"
        '  "shipment_type": "Recurring inbound transfer",\n'
        '  "material_profile": "Electronics · Medium dock unload · palletized",\n'
        '  "crew_needed": 4,\n'
        '  "receive_time_minutes": 42,\n'
        '  "risk_level": "Medium",\n'
        '  "pallet_load": 3,\n'
        '  "suggested_dock": "Dock 2",\n'
        '  "staging_zone": "Inbound Buffer A",\n'
        '  "confidence": 88,\n'
        '  "queue_minutes": 12,\n'
        '  "summary": "One short operational summary.",\n'
        '  "recommendation": "One clear next action for the warehouse manager.",\n'
        '  "reasoning": "Why this receive plan makes sense.",\n'
        '  "watchouts": ["short item 1", "short item 2", "short item 3"]\n'
        "}\n"
        "Rules:\n"
        "- risk_level must be Low, Medium, or High.\n"
        "- crew_needed must be 1 to 12.\n"
        "- confidence must be 50 to 99.\n"
        "- watchouts must be short warehouse-facing strings.\n"
        "- If recurring is true, make shipment_type reflect that.\n"
        "- Material profile should describe cargo, load intensity, and packaging feel.\n\n"
        f"Facts:\n{json.dumps(prompt_facts, default=str, ensure_ascii=True, indent=2)}"
    )

    try:
        client = get_gemini_client()
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        parsed = json.loads(_strip_json_fences(response.text or ""))
        watchouts_raw = parsed.get("watchouts") if isinstance(parsed.get("watchouts"), list) else []
        watchouts = [str(item).strip() for item in watchouts_raw if str(item).strip()][:5] or fallback.watchouts
        risk_level = str(parsed.get("risk_level") or fallback.risk_level).title()
        if risk_level not in {"Low", "Medium", "High"}:
            risk_level = fallback.risk_level

        return InboundReceivePlanResponse(
            order_id=order.id,
            asn=InboundReceivePlanShipment(
                id=order.tracking_code or fallback.asn.id,
                supplier=supplier_name,
                status=status_name,
                shipment_type=str(parsed.get("shipment_type") or fallback.asn.shipment_type).strip(),
                material_profile=str(parsed.get("material_profile") or fallback.asn.material_profile).strip(),
                expected_units=expected_qty,
                recurring=recurring,
            ),
            confidence=max(50, min(99, int(parsed.get("confidence", fallback.confidence)))),
            suggested_dock=str(parsed.get("suggested_dock") or fallback.suggested_dock).strip(),
            workers=max(1, min(12, int(parsed.get("crew_needed", fallback.workers)))),
            total_minutes=max(1, int(parsed.get("receive_time_minutes", fallback.total_minutes))),
            risk_level=risk_level,
            pallet_load=max(1, int(parsed.get("pallet_load", fallback.pallet_load))),
            queue_minutes=max(0, int(parsed.get("queue_minutes", fallback.queue_minutes))),
            active_dock_count=active_dock_count,
            staging_zone=str(parsed.get("staging_zone") or fallback.staging_zone).strip(),
            next_action=str(parsed.get("recommendation") or fallback.next_action).strip(),
            reason=str(parsed.get("reasoning") or fallback.reason).strip(),
            watchouts=watchouts,
            summary=str(parsed.get("summary") or fallback.summary).strip(),
            generated_by="gemini",
        )
    except (GeminiConfigError, ValueError, json.JSONDecodeError, TypeError):
        return fallback
    except Exception:
        return fallback


async def report_inbound_mismatch(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data: InboundMismatchReport,
    reported_by: User,
) -> None:
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order does not belong to this warehouse")
    if order.order_type != "VENDOR" or (order.pickup_type or "hub").lower() != "hub":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only hub-based vendor inbound orders support mismatch reporting")

    vendor = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == order.customer_id)
        )
    ).scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found for this shipment")

    details = (data.details or "").strip()
    description = (
        f"Inbound mismatch raised by warehouse manager {reported_by.name} for shipment {order.tracking_code}.\n"
        f"Mismatch type: {data.mismatch_type}."
    )
    if details:
        description += f"\nDetails: {details}"

    ticket = VendorSupportTicket(
        vendor_id=vendor.id,
        order_id=order.id,
        subject=f"Inbound mismatch: {data.mismatch_type}",
        description=description,
        priority="High",
        status="Open",
    )
    db.add(ticket)
    await db.flush()

    db.add(
        VendorSupportReply(
            ticket_id=ticket.id,
            from_name=f"Warehouse Team ({reported_by.name})",
            message=description,
        )
    )
    await db.flush()

    from app.services import ai_support_service

    support_ticket = await ai_support_service.sync_vendor_ticket_to_support_ticket(
        db=db,
        vendor=vendor,
        vendor_ticket=ticket,
        source="warehouse_inbound",
        metadata_updates={
            "issue_type": "mismatch",
            "resolution_action": "pending_review",
            "lm_steps": "Review mismatch details with vendor||Reply in the vendor thread||Set final resolution for warehouse",
        },
    )
    await ai_support_service.create_user_notification(
        db,
        user_id=vendor.id,
        title="Warehouse flagged an inbound mismatch",
        message=f"{order.tracking_code}: Cargo-Core is waiting for your confirmation on the mismatch.",
        notification_type="warning",
    )
    await ai_support_service.notify_support_manager_about_ticket(
        db,
        ticket=support_ticket,
        source="warehouse_inbound",
    )


async def report_inbound_damage(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data: InboundDamageReport,
    reported_by: User,
) -> DamageReport:
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order does not belong to this warehouse")
    if order.order_type != "VENDOR" or (order.pickup_type or "hub").lower() != "hub":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only hub-based vendor inbound orders support damage reporting")

    description = (
        f"Inbound damage reported by warehouse manager {reported_by.name} for shipment {order.tracking_code}. "
        f"Damaged items: {data.damaged_count}. {data.description.strip()}"
    )
    photos = [data.photo_url] if data.photo_url else []

    report = DamageReport(
        reference_code=_inbound_report_reference("DMG"),
        customer_id=order.customer_id,
        order_id=order.id,
        description=description,
        photos=photos,
        flow_type="pickup_inspection",
        status="reported",
        qr_code=_inbound_report_reference("QR"),
    )
    db.add(report)
    await db.flush()
    vendor = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == order.customer_id)
        )
    ).scalar_one_or_none()
    if vendor:
        ticket = VendorSupportTicket(
            vendor_id=vendor.id,
            order_id=order.id,
            subject="Inbound damage reported",
            description=description,
            priority="High",
            status="Open",
        )
        db.add(ticket)
        await db.flush()

        db.add(
            VendorSupportReply(
                ticket_id=ticket.id,
                from_name=f"Warehouse Team ({reported_by.name})",
                message=description,
            )
        )
        await db.flush()

        from app.services import ai_support_service

        support_ticket = await ai_support_service.sync_vendor_ticket_to_support_ticket(
            db=db,
            vendor=vendor,
            vendor_ticket=ticket,
            source="warehouse_inbound",
            metadata_updates={
                "issue_type": "damage",
                "linked_damage_report_id": str(report.id),
                "resolution_action": "pending_review",
                "lm_steps": "Inspect damage photos from the warehouse||Confirm with vendor whether stock moves or returns||Update final resolution for warehouse",
            },
        )
        await ai_support_service.create_user_notification(
            db,
            user_id=vendor.id,
            title="Warehouse reported inbound damage",
            message=f"{order.tracking_code}: Support needs your decision on the damaged shipment.",
            notification_type="alert",
        )
        await ai_support_service.notify_support_manager_about_ticket(
            db,
            ticket=support_ticket,
            source="warehouse_inbound",
        )
    return report


async def schedule_inbound_delivery(
    db: AsyncSession,
    warehouse_id: UUID,
    data: ScheduleInboundRequest,
) -> Order:
    warehouse = await _get_warehouse(db, warehouse_id)
    normalized_supplier = data.supplier_name.strip().lower()

    vendor = (
        await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(
                User.is_active.is_(True),
                or_(
                    func.lower(User.name) == normalized_supplier,
                    func.lower(func.coalesce(User.company_name, "")) == normalized_supplier,
                    func.lower(func.coalesce(User.contact_person, "")) == normalized_supplier,
                ),
            )
        )
    ).scalars().all()

    matched_vendor = next((user for user in vendor if getattr(user.role, "name", None) == "VENDOR"), None)
    if not matched_vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active vendor matched that supplier name. Use an existing vendor/company name.",
        )

    order = Order(
        tracking_code=_inbound_tracking_code(),
        order_type="VENDOR",
        status="CONFIRMED",
        priority="NORMAL",
        warehouse_substatus="AWAITING_INBOUND",
        customer_id=matched_vendor.id,
        warehouse_id=warehouse_id,
        pickup_addr=data.supplier_name.strip(),
        pickup_type="hub",
        delivery_addr=warehouse.address,
        cargo_type="Inbound Shipment",
        vehicle_type="Scheduled Delivery",
        labor_count=0,
        base_amount=0,
        vehicle_amount=0,
        labor_amount=0,
        materials_amount=0,
        packing_amount=0,
        platform_fee=0,
        tax_amount=0,
        total_amount=0,
        payment_mode="invoice",
        payment_status="pending",
        declared_value=0,
        scheduled_at=data.scheduled_at,
        delivery_notes=(data.notes or data.dock_preference or "").strip() or None,
        delivery_lat=warehouse.lat,
        delivery_lng=warehouse.lng,
    )
    db.add(order)
    await db.flush()

    db.add(
        OrderItem(
            order_id=order.id,
            sku="INBOUND-LOAD",
            quantity=data.expected_qty,
            box_count=max(1, (data.expected_qty + 9) // 10),
            estimated_volume=None,
        )
    )
    await db.flush()
    return order


# ======================
# Accept Order
# ======================

async def accept_order_into_warehouse(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Accept a CONFIRMED order into the warehouse queue.
    Vendor orders → AWAITING_INBOUND (goods must arrive first via Inbound).
    Non-vendor orders → AWAITING_PICK directly.
    """
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.status not in {"CONFIRMED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only CONFIRMED orders can be accepted into the warehouse queue (got {order.status})",
        )

    # Idempotent — if already accepted, just return success
    if order.warehouse_substatus in {"AWAITING_INBOUND", "AWAITING_PICK", "PICKING", "PICKED", "PACKING", "PACKED", "QC_PASSED"}:
        return PickingResponse(
            order_id=order_id,
            warehouse_substatus=order.warehouse_substatus,
            assigned_labourer_id=None,
            message="Order already in warehouse queue",
        )

    # Vendor orders with 'hub' pickup wait in Inbound until goods physically arrive
    # Vendor orders with 'doorstep' pickup go directly to picking queue (driver picks from vendor's location)
    # Non-vendor orders go directly to picking queue
    if order.order_type == "VENDOR" and (order.pickup_type or "hub").lower() == "hub":
        initial_substatus = "AWAITING_INBOUND"
    else:
        initial_substatus = "AWAITING_PICK"
    order.warehouse_substatus = initial_substatus
    db.add(order)
    await db.flush()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus=initial_substatus,
        assigned_labourer_id=None,
        message="Order accepted — awaiting inbound receipt" if initial_substatus == "AWAITING_INBOUND" else "Order accepted into warehouse queue",
    )


async def mark_inbound_received(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Mark a vendor order's goods as physically received — transitions AWAITING_INBOUND → AWAITING_PICK."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_substatus != "AWAITING_INBOUND":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is not in AWAITING_INBOUND state (current: {order.warehouse_substatus})",
        )

    latest_issue_ticket = await _latest_inbound_issue_ticket(db, order.id)
    if latest_issue_ticket:
        resolution_action = _linked_resolution_action(latest_issue_ticket)
        if resolution_action != "vendor_accept_move":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=INBOUND_RESOLUTION_LABELS.get(
                    resolution_action,
                    "Inbound issue is still under review. Resolve it with vendor support before moving to picking.",
                ),
            )

    _validate_substatus_transition(order.warehouse_substatus, "AWAITING_PICK")
    order.warehouse_substatus = "AWAITING_PICK"
    db.add(order)
    await db.flush()

    vendor = (
        await db.execute(select(User).where(User.id == order.customer_id))
    ).scalar_one_or_none()
    if vendor:
        from app.services import ai_support_service

        await ai_support_service.create_user_notification(
            db,
            user_id=vendor.id,
            title="Inbound issue cleared",
            message=f"{order.tracking_code}: Warehouse has moved the approved shipment to picking.",
            notification_type="success",
        )

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="AWAITING_PICK",
        assigned_labourer_id=None,
        message="Goods received — order moved to picking queue",
    )


async def generate_vendor_take_back(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    acted_by: User,
) -> PickingResponse:
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.order_type != "VENDOR" or (order.pickup_type or "hub").lower() != "hub":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only hub-based vendor inbound orders support vendor take-back generation",
        )

    latest_issue_ticket = await _latest_inbound_issue_ticket(db, order.id)
    resolution_action = _linked_resolution_action(latest_issue_ticket)
    if resolution_action != "vendor_take_back":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Support must first confirm that the vendor will take this shipment back.",
        )

    if order.warehouse_substatus != "ON_HOLD":
        _validate_substatus_transition(order.warehouse_substatus, "ON_HOLD")
        order.warehouse_substatus = "ON_HOLD"
        db.add(order)
        await db.flush()

    vendor = (
        await db.execute(select(User).where(User.id == order.customer_id))
    ).scalar_one_or_none()
    if vendor:
        from app.services import ai_support_service

        await ai_support_service.create_user_notification(
            db,
            user_id=vendor.id,
            title="Vendor take-back generated",
            message=f"{order.tracking_code}: Warehouse marked the damaged inbound for vendor take-back.",
            notification_type="warning",
        )

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="ON_HOLD",
        assigned_labourer_id=None,
        message=f"Vendor take-back generated by {acted_by.name}",
    )


async def mark_inbound_arrived(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Mark a vendor inbound order as physically arrived at the warehouse dock."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.order_type != "VENDOR" or (order.pickup_type or "hub").lower() != "hub":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only hub-based vendor inbound orders can be marked as arrived",
        )

    if order.warehouse_substatus != "AWAITING_INBOUND":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is not in AWAITING_INBOUND state (current: {order.warehouse_substatus})",
        )

    if order.arrived_at is None:
        order.arrived_at = datetime.now(UTC)
        db.add(order)
        await db.flush()

    message = "Order marked as arrived"
    from app.services import vendor_service

    debited, debit_note = await vendor_service.auto_debit_recurring_order_if_eligible(
        db,
        order=order,
        trigger="arrived",
    )
    if debited:
        message = "Order marked as arrived. Auto-debit completed from vendor wallet"
    elif debit_note:
        message = f"Order marked as arrived. Auto-debit skipped: {debit_note}"

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="AWAITING_INBOUND",
        assigned_labourer_id=None,
        message=message,
    )


# ======================
# Picking Operations
# ======================

async def start_picking(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data: StartPickingRequest,
) -> PickingResponse:
    """Start picking process for an order."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    # Guard: vendor orders in AWAITING_INBOUND must go through Inbound first
    if order.warehouse_substatus == "AWAITING_INBOUND":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendor order goods have not been received yet. Complete inbound receiving first.",
        )

    # Idempotent: if already PICKING, return success immediately
    if order.warehouse_substatus == "PICKING":
        labourer_id = (
            await db.execute(
                select(Labourer.id).where(
                    Labourer.warehouse_id == warehouse_id,
                    Labourer.is_active.is_(True),
                    Labourer.assigned_order_id == order_id,
                ).limit(1)
            )
        ).scalar_one_or_none()
        return PickingResponse(
            order_id=order_id,
            warehouse_substatus="PICKING",
            assigned_labourer_id=labourer_id,
            message="Picking already in progress",
        )

    # Validate transition
    _validate_substatus_transition(order.warehouse_substatus, "PICKING")

    assigned_labourer_id = data.labourer_id
    if data.labourer_id:
        result = await db.execute(
            select(Labourer).where(
                Labourer.id == data.labourer_id,
                Labourer.warehouse_id == warehouse_id,
                Labourer.is_active.is_(True),
            )
        )
        labourer = result.scalar_one_or_none()
        if not labourer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Labourer not found or not active in this warehouse"
            )

        if labourer.assigned_order_id and labourer.assigned_order_id != order_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Selected labourer is already assigned to another order"
            )
        existing_assignments = (
            await db.execute(
                select(Labourer).where(
                    Labourer.warehouse_id == warehouse_id,
                    Labourer.assigned_order_id == order_id,
                    Labourer.id != labourer.id,
                )
            )
        ).scalars().all()
        for assigned_labourer in existing_assignments:
            assigned_labourer.assigned_order_id = None
        labourer.assigned_order_id = order_id
    else:
        labourer = (
            await db.execute(
                select(Labourer).where(
                    Labourer.warehouse_id == warehouse_id,
                    Labourer.is_active.is_(True),
                    Labourer.assigned_order_id == order_id,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if labourer:
            assigned_labourer_id = labourer.id
        else:
            labourer = (
                await db.execute(
                    select(Labourer).where(
                        Labourer.warehouse_id == warehouse_id,
                        Labourer.is_active.is_(True),
                        Labourer.assigned_order_id.is_(None),
                    ).limit(1)
                )
            ).scalar_one_or_none()
            if labourer:
                labourer.assigned_order_id = order_id
                assigned_labourer_id = labourer.id

    order.warehouse_substatus = "PICKING"
    order.picking_started_at = datetime.now(UTC)

    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="PICKING",
        assigned_labourer_id=assigned_labourer_id,
        message="Picking started successfully",
    )


async def revert_picking(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Undo start-picking: revert order from PICKING back to AWAITING_PICK."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    _validate_substatus_transition(order.warehouse_substatus, "AWAITING_PICK")

    order.warehouse_substatus = "AWAITING_PICK"
    order.picking_started_at = None

    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="AWAITING_PICK",
        assigned_labourer_id=None,
        message="Picking reverted to awaiting",
    )


async def complete_picking(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Complete picking process for an order and deduct inventory."""
    from app.models.inventory import InventoryItem, InventoryMovement
    from app.models.order import OrderItem, PickedItem

    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    _validate_substatus_transition(order.warehouse_substatus, "PICKED")

    order_items = (await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )).scalars().all()
    picked_items = (await db.execute(
        select(PickedItem).where(PickedItem.order_id == order_id)
    )).scalars().all()
    picked_by_sku = {picked_item.sku: picked_item for picked_item in picked_items}

    # Exclude packing materials (PKG-* or name-matched) — they are consumed during packing, not picking
    _PICK_PACKING_KWS = ["carton", "box", "bubble", "wrap", "tape", "crate", "blanket", "pad", "wardrobe", "packing", "pack"]
    cargo_items = []
    for _oi in order_items:
        if _oi.sku.startswith("PKG-"):
            continue
        _inv = (await db.execute(
            select(InventoryItem).where(InventoryItem.warehouse_id == warehouse_id, InventoryItem.sku == _oi.sku)
        )).scalar_one_or_none()
        if _inv:
            _text = ((_inv.name or "") + " " + (_inv.category or "")).lower()
            if any(kw in _text for kw in _PICK_PACKING_KWS):
                continue
        cargo_items.append(_oi)

    if picked_items:
        incomplete_items: list[str] = []
        for order_item in cargo_items:
            picked_item = picked_by_sku.get(order_item.sku)
            picked_qty = picked_item.quantity_picked if picked_item else 0
            if picked_qty < order_item.quantity:
                incomplete_items.append(
                    f"{order_item.sku} ({order_item.quantity - picked_qty} remaining)"
                )

        if incomplete_items:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="All order items must be confirmed before completing picking: "
                + ", ".join(incomplete_items),
            )
    else:
        # Only run fallback deduction if no prior movements exist for this order
        existing_movement = (
            await db.execute(
                select(InventoryMovement).where(
                    InventoryMovement.reference_order_id == order_id,
                    InventoryMovement.movement_type == "PICK",
                ).limit(1)
            )
        ).scalar_one_or_none()

        if not existing_movement:
            for order_item in cargo_items:  # Only deduct cargo items here; PKG-* deducted in complete_packing
                inventory_result = await db.execute(
                    select(InventoryItem).where(
                        InventoryItem.warehouse_id == warehouse_id,
                        InventoryItem.sku == order_item.sku,
                    )
                )
                inventory_item = inventory_result.scalar_one_or_none()

                if inventory_item:
                    deduct_qty = min(order_item.quantity, inventory_item.quantity_on_hand)
                    if deduct_qty > 0:
                        inventory_item.quantity_on_hand -= deduct_qty

                        movement = InventoryMovement(
                            item_id=inventory_item.id,
                            movement_type="PICK",
                            quantity=deduct_qty,
                            reference_order_id=order_id,
                            performed_by=None,
                        )
                        db.add(movement)

    order.warehouse_substatus = "PICKED"
    order.picking_completed_at = datetime.now(UTC)
    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="PICKED",
        assigned_labourer_id=None,
        message="Picking completed successfully.",
    )


async def confirm_pick_item(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data,  # ConfirmPickItemRequest
    user_id: UUID,
):
    """Confirm picking of a specific item (supports partial picking)."""
    from app.models.inventory import InventoryItem, InventoryMovement
    from app.models.order import OrderItem, PickedItem

    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    # Must be in PICKING status
    if order.warehouse_substatus != "PICKING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be in PICKING status to confirm items"
        )

    # Verify this SKU exists in the order
    order_item_result = await db.execute(
        select(OrderItem).where(
            OrderItem.order_id == order_id,
            OrderItem.sku == data.sku,
        )
    )
    order_item = order_item_result.scalar_one_or_none()
    if not order_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU {data.sku} not found in this order"
        )

    # Get or create PickedItem record
    picked_result = await db.execute(
        select(PickedItem).where(
            PickedItem.order_id == order_id,
            PickedItem.sku == data.sku,
        )
    )
    picked_item = picked_result.scalar_one_or_none()

    if not picked_item:
        picked_item = PickedItem(
            order_id=order_id,
            sku=data.sku,
            quantity_picked=0,
            quantity_required=order_item.quantity,
            picked_by=user_id,
            location=data.location,
            notes=data.notes,
        )
        db.add(picked_item)

    # Update picked quantity
    new_total = picked_item.quantity_picked + data.quantity_picked
    if new_total > picked_item.quantity_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pick {new_total} items (only {picked_item.quantity_required} required)"
        )

    picked_item.quantity_picked = new_total
    picked_item.picked_by = user_id
    if data.location:
        picked_item.location = data.location
    if data.notes:
        picked_item.notes = data.notes

    # Deduct inventory immediately
    inventory_result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.warehouse_id == warehouse_id,
            InventoryItem.sku == data.sku,
        )
    )
    inventory_item = inventory_result.scalar_one_or_none()

    if inventory_item:
        if inventory_item.quantity_on_hand < data.quantity_picked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for {data.sku}: "
                       f"need {data.quantity_picked}, available {inventory_item.quantity_on_hand}",
            )

        inventory_item.quantity_on_hand -= data.quantity_picked

        # Create movement record
        movement = InventoryMovement(
            item_id=inventory_item.id,
            movement_type="PICK",
            quantity=data.quantity_picked,
            reference_order_id=order_id,
            performed_by=user_id,
        )
        db.add(movement)

    await db.commit()
    picked_item = (
        await db.execute(
            select(PickedItem)
            .options(selectinload(PickedItem.picker))
            .where(PickedItem.id == picked_item.id)
        )
    ).scalar_one()

    from app.schemas.warehouse_operations import PickedItemResponse
    return PickedItemResponse(
        id=picked_item.id,
        order_id=picked_item.order_id,
        sku=picked_item.sku,
        quantity_picked=picked_item.quantity_picked,
        quantity_required=picked_item.quantity_required,
        picked_by=picked_item.picked_by,
        picker_name=_format_user_name(picked_item.picker),
        location=picked_item.location,
        notes=picked_item.notes,
        is_complete=picked_item.quantity_picked >= picked_item.quantity_required,
        created_at=picked_item.created_at,
        updated_at=picked_item.updated_at,
    )


async def get_pick_progress(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
):
    """Get picking progress for an order."""
    from app.models.order import OrderItem, PickedItem

    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    # Get all order items
    order_items_result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    order_items = order_items_result.scalars().all()

    # Get all picked items
    picked_items_result = await db.execute(
        select(PickedItem)
        .options(selectinload(PickedItem.picker))
        .where(PickedItem.order_id == order_id)
    )
    picked_items_list = picked_items_result.scalars().all()

    # Build picked items map
    picked_map = {pi.sku: pi for pi in picked_items_list}

    # Build response items
    items_response = []
    total_items = len(order_items)
    completed_count = 0

    for order_item in order_items:
        picked_item = picked_map.get(order_item.sku)

        if picked_item:
            from app.schemas.warehouse_operations import PickedItemResponse
            items_response.append(PickedItemResponse(
                id=picked_item.id,
                order_id=picked_item.order_id,
                sku=picked_item.sku,
                quantity_picked=picked_item.quantity_picked,
                quantity_required=picked_item.quantity_required,
                picked_by=picked_item.picked_by,
                picker_name=_format_user_name(picked_item.picker),
                location=picked_item.location,
                notes=picked_item.notes,
                is_complete=picked_item.quantity_picked >= picked_item.quantity_required,
                created_at=picked_item.created_at,
                updated_at=picked_item.updated_at,
            ))

            if picked_item.quantity_picked >= picked_item.quantity_required:
                completed_count += 1

    from app.schemas.warehouse_operations import PickProgressResponse
    return PickProgressResponse(
        order_id=order_id,
        total_items=total_items,
        picked_items=completed_count,
        is_complete=completed_count >= total_items,
        items=items_response,
    )


# ======================
# Packing Station Operations
# ======================

async def get_packing_stations(
    db: AsyncSession,
    warehouse_id: UUID,
) -> PackingStationListResponse:
    """Get all packing stations for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(PackingStation)
        .options(
            selectinload(PackingStation.assigned_labourer).selectinload(Labourer.user),
            selectinload(PackingStation.current_order),
        )
        .where(PackingStation.warehouse_id == warehouse_id)
        .order_by(PackingStation.station_number)
    )
    stations = result.scalars().all()

    items = []
    for station in stations:
        labourer_name = None
        if station.assigned_labourer and station.assigned_labourer.user:
            labourer_name = station.assigned_labourer.user.name

        order_tracking = None
        if station.current_order:
            order_tracking = station.current_order.tracking_code

        items.append(PackingStationResponse(
            id=station.id,
            warehouse_id=station.warehouse_id,
            station_number=station.station_number,
            status=station.status,
            assigned_labourer_id=station.assigned_labourer_id,
            assigned_labourer_name=labourer_name,
            current_order_id=station.current_order_id,
            current_order_tracking=order_tracking,
            items_packed_today=station.items_packed_today,
            created_at=station.created_at,
        ))

    return PackingStationListResponse(items=items, total=len(items))


async def create_packing_station(
    db: AsyncSession,
    warehouse_id: UUID,
    data: PackingStationCreate,
) -> PackingStationResponse:
    """Create a new packing station."""
    await _get_warehouse(db, warehouse_id)

    station = PackingStation(
        warehouse_id=warehouse_id,
        station_number=data.station_number,
        status=data.status,
    )
    db.add(station)
    await db.commit()
    await db.refresh(station)

    return PackingStationResponse(
        id=station.id,
        warehouse_id=station.warehouse_id,
        station_number=station.station_number,
        status=station.status,
        assigned_labourer_id=None,
        assigned_labourer_name=None,
        current_order_id=None,
        current_order_tracking=None,
        items_packed_today=0,
        created_at=station.created_at,
    )


async def update_packing_station(
    db: AsyncSession,
    warehouse_id: UUID,
    station_id: UUID,
    data: PackingStationUpdate,
) -> PackingStationResponse:
    """Update a packing station."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(PackingStation)
        .options(
            selectinload(PackingStation.assigned_labourer).selectinload(Labourer.user),
            selectinload(PackingStation.current_order),
        )
        .where(PackingStation.id == station_id, PackingStation.warehouse_id == warehouse_id)
    )
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packing station not found")

    if data.status is not None:
        station.status = data.status
    if data.assigned_labourer_id is not None:
        # Validate labourer belongs to this warehouse
        labourer_check = (
            await db.execute(
                select(Labourer).where(
                    Labourer.id == data.assigned_labourer_id,
                    Labourer.warehouse_id == warehouse_id,
                    Labourer.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not labourer_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Labourer not found or does not belong to this warehouse",
            )
        station.assigned_labourer_id = data.assigned_labourer_id
    if data.current_order_id is not None:
        station.current_order_id = data.current_order_id

    await db.commit()
    await db.refresh(station)

    labourer_name = None
    if station.assigned_labourer and station.assigned_labourer.user:
        labourer_name = station.assigned_labourer.user.name

    order_tracking = None
    if station.current_order:
        order_tracking = station.current_order.tracking_code

    return PackingStationResponse(
        id=station.id,
        warehouse_id=station.warehouse_id,
        station_number=station.station_number,
        status=station.status,
        assigned_labourer_id=station.assigned_labourer_id,
        assigned_labourer_name=labourer_name,
        current_order_id=station.current_order_id,
        current_order_tracking=order_tracking,
        items_packed_today=station.items_packed_today,
        created_at=station.created_at,
    )


async def start_packing(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    data: StartPackingRequest,
) -> PickingResponse:
    """Start packing process for an order."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    if order.warehouse_substatus == "PACKING":
        station = (
            await db.execute(
                select(PackingStation).where(PackingStation.current_order_id == order_id)
            )
        ).scalar_one_or_none()
        return PickingResponse(
            order_id=order_id,
            warehouse_substatus="PACKING",
            assigned_labourer_id=station.assigned_labourer_id if station else None,
            message="Packing already in progress",
        )

    _validate_substatus_transition(order.warehouse_substatus, "PACKING")

    # Verify all cargo items were fully picked (exclude packing materials — consumed during packing, not picking)
    from app.models.inventory import InventoryItem as _InvItem
    from app.models.order import OrderItem, PickedItem
    _PACKING_NAME_KWS = ["carton", "box", "bubble", "wrap", "tape", "crate", "blanket", "pad", "wardrobe", "packing", "pack"]

    order_items = (await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )).scalars().all()

    # Build cargo_items list: exclude PKG-* and any inventory item whose name/category is packing-related
    cargo_items = []
    for _oi in order_items:
        if _oi.sku.startswith("PKG-"):
            continue
        _inv = (await db.execute(
            select(_InvItem).where(_InvItem.warehouse_id == warehouse_id, _InvItem.sku == _oi.sku)
        )).scalar_one_or_none()
        if _inv:
            _text = ((_inv.name or "") + " " + (_inv.category or "")).lower()
            if any(kw in _text for kw in _PACKING_NAME_KWS):
                continue  # packing material — skip
        cargo_items.append(_oi)
    picked_items = (await db.execute(
        select(PickedItem).where(PickedItem.order_id == order_id)
    )).scalars().all()
    picked_by_sku = {pi.sku: pi for pi in picked_items}
    incomplete = [
        f"{oi.sku} ({oi.quantity - (picked_by_sku[oi.sku].quantity_picked if oi.sku in picked_by_sku else 0)} remaining)"
        for oi in cargo_items
        if (picked_by_sku.get(oi.sku).quantity_picked if oi.sku in picked_by_sku else 0) < oi.quantity
    ]
    if incomplete:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot start packing — picking incomplete for: " + ", ".join(incomplete),
        )

    station = None
    if data.station_id:
        result = await db.execute(
            select(PackingStation).where(
                PackingStation.id == data.station_id,
                PackingStation.warehouse_id == warehouse_id,
            )
        )
        station = result.scalar_one_or_none()
        if not station:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packing station not found")
    else:
        station = (
            await db.execute(
                select(PackingStation).where(PackingStation.warehouse_id == warehouse_id).order_by(PackingStation.station_number)
            )
        ).scalars().first()
        if station is None:
            station = PackingStation(
                warehouse_id=warehouse_id,
                station_number="PACK-01",
                status="ACTIVE",
            )
            db.add(station)
            await db.flush()

    station.current_order_id = order_id
    station.status = "ACTIVE"
    order.warehouse_substatus = "PACKING"
    order.packing_started_at = datetime.now(UTC)

    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="PACKING",
        assigned_labourer_id=station.assigned_labourer_id,
        message="Packing started successfully",
    )


async def complete_packing(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
) -> PickingResponse:
    """Complete packing process for an order."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    _validate_substatus_transition(order.warehouse_substatus, "PACKED")

    # Detect packing material OrderItems (PKG-* SKU or inventory item with packing keywords).
    # This list is used both for the issuance guard and for later inventory deduction.
    from app.models.inventory import InventoryItem, InventoryMovement
    from app.models.order import OrderItem

    # Packing material keywords for name-based detection
    PACKING_NAME_KEYWORDS = ["carton", "box", "bubble", "wrap", "tape", "crate", "blanket", "pad", "wardrobe", "packing", "pack"]

    # Get ALL order items; we'll split into cargo vs packing materials below
    all_order_items = (await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )).scalars().all()

    packing_material_items = []
    for oi in all_order_items:
        # PKG-* prefix is always a packing material
        if oi.sku.startswith("PKG-"):
            packing_material_items.append(oi)
            continue
        # Check if this SKU's inventory item is packing-related by name/category
        inv_check = (await db.execute(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.sku == oi.sku,
            )
        )).scalar_one_or_none()
        if inv_check:
            item_text = ((inv_check.name or "") + " " + (inv_check.category or "")).lower()
            if any(kw in item_text for kw in PACKING_NAME_KEYWORDS):
                packing_material_items.append(oi)

    # Guard: only block if the order actually has packing material items AND they haven't been issued
    if packing_material_items:
        issued = (await db.execute(
            select(InventoryMovement).where(
                InventoryMovement.reference_order_id == order_id,
                func.upper(InventoryMovement.movement_type) == 'ISSUE'
            ).limit(1)
        )).scalar_one_or_none()

        if not issued:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot complete packing — packing materials have not been issued to this order. "
                    "Go to Packing Materials, select this order, and issue the required materials first."
                ),
            )

    # Update station if assigned
    result = await db.execute(
        select(PackingStation).where(PackingStation.current_order_id == order_id)
    )
    station = result.scalar_one_or_none()
    if station:
        station.current_order_id = None
        station.items_packed_today += 1

    assigned_labourers = (
        await db.execute(
            select(Labourer).where(
                Labourer.warehouse_id == warehouse_id,
                Labourer.assigned_order_id == order_id,
            )
        )
    ).scalars().all()
    for labourer in assigned_labourers:
        labourer.assigned_order_id = None

    if packing_material_items:
        # Idempotency: skip if PACK movements already recorded for this order
        already_packed = (await db.execute(
            select(InventoryMovement).where(
                InventoryMovement.reference_order_id == order_id,
                InventoryMovement.movement_type == "PACK",
            ).limit(1)
        )).scalar_one_or_none()

        if not already_packed:
            # Keyword fallback map: covers both seeded PKG-* SKUs and manually-named inventory items
            PKG_KEYWORD_MAP = {
                "PKG-CARTON":        ["carton", "box"],
                "PKG-BUBBLE-WRAP":   ["bubble", "wrap"],
                "PKG-PLASTIC-CRATE": ["crate", "plastic"],
                "PKG-BLANKET":       ["blanket", "pad"],
                "PKG-WARDROBE-BOX":  ["wardrobe"],
                "PKG-TAPE":          ["tape"],
            }

            for pm_item in packing_material_items:
                # 1. Exact SKU match
                inv = (await db.execute(
                    select(InventoryItem).where(
                        InventoryItem.warehouse_id == warehouse_id,
                        InventoryItem.sku == pm_item.sku,
                    )
                )).scalar_one_or_none()

                # 2. Keyword name match fallback (handles manually-named inventory items)
                if not inv:
                    keywords = PKG_KEYWORD_MAP.get(pm_item.sku, [pm_item.sku.replace("PKG-", "").lower()])
                    for kw in keywords:
                        inv = (await db.execute(
                            select(InventoryItem).where(
                                InventoryItem.warehouse_id == warehouse_id,
                                InventoryItem.name.ilike(f"%{kw}%"),
                            )
                        )).scalar_one_or_none()
                        if inv:
                            break

                if inv:
                    deduct_qty = min(pm_item.quantity, inv.quantity_on_hand)
                    if deduct_qty > 0:
                        inv.quantity_on_hand -= deduct_qty
                        db.add(InventoryMovement(
                            item_id=inv.id,
                            movement_type="PACK",
                            quantity=deduct_qty,
                            reference_order_id=order_id,
                            performed_by=None,
                        ))

    order.warehouse_substatus = "PACKED"
    order.packing_completed_at = datetime.now(UTC)
    await db.commit()

    return PickingResponse(
        order_id=order_id,
        warehouse_substatus="PACKED",
        assigned_labourer_id=None,
        message="Packing completed successfully",
    )


# ======================
# Quality Check Operations
# ======================

async def create_quality_check(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    performed_by: UUID | None = None,
) -> QualityCheckResponse:
    """Create a new quality check record for an order."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    # Check if QC already exists
    result = await db.execute(
        select(QualityCheck).where(QualityCheck.order_id == order_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Quality check already exists for this order"
        )

    qc = QualityCheck(
        order_id=order_id,
        warehouse_id=warehouse_id,
        performed_by=performed_by,
    )
    db.add(qc)
    await db.commit()
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == qc.id)
    )
    qc = result.scalar_one()
    return _to_quality_check_response(qc)


async def list_quality_checks(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID | None = None,
) -> QualityCheckListResponse:
    """List quality checks for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    query = (
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.warehouse_id == warehouse_id)
        .order_by(QualityCheck.created_at.desc())
    )

    if order_id:
        query = query.where(QualityCheck.order_id == order_id)

    checks = (await db.execute(query)).scalars().all()
    return QualityCheckListResponse(
        items=[_to_quality_check_response(check) for check in checks],
        total=len(checks),
    )


async def get_quality_check(
    db: AsyncSession,
    warehouse_id: UUID,
    check_id: UUID,
) -> QualityCheckResponse:
    """Get a quality check by ID."""
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == check_id, QualityCheck.warehouse_id == warehouse_id)
    )
    qc = result.scalar_one_or_none()
    if not qc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality check not found")
    return _to_quality_check_response(qc)


async def update_quality_check(
    db: AsyncSession,
    warehouse_id: UUID,
    check_id: UUID,
    data: QualityCheckUpdate,
    performed_by: UUID | None = None,
) -> QualityCheckResponse:
    """Update a quality check."""
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == check_id, QualityCheck.warehouse_id == warehouse_id)
    )
    qc = result.scalar_one_or_none()
    if not qc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality check not found")

    if data.goods_correct is not None:
        qc.goods_correct = data.goods_correct
    if data.count_correct is not None:
        qc.count_correct = data.count_correct
    if data.packaging_verified is not None:
        qc.packaging_verified = data.packaging_verified
    if data.labor_assigned is not None:
        qc.labor_assigned = data.labor_assigned
    if data.weight_verified is not None:
        qc.weight_verified = data.weight_verified
    if data.label_attached is not None:
        qc.label_attached = data.label_attached
    if data.notes is not None:
        qc.notes = data.notes

    if performed_by:
        qc.performed_by = performed_by

    await db.commit()
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == qc.id)
    )
    qc = result.scalar_one()
    return _to_quality_check_response(qc)


async def pass_quality_check(
    db: AsyncSession,
    warehouse_id: UUID,
    check_id: UUID,
    performed_by: UUID | None = None,
) -> QualityCheckResponse:
    """Mark a quality check as passed and advance order substatus."""
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer), selectinload(QualityCheck.order))
        .where(QualityCheck.id == check_id, QualityCheck.warehouse_id == warehouse_id)
    )
    qc = result.scalar_one_or_none()
    if not qc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality check not found")

    # Validate all checks are complete
    if not all([
        qc.goods_correct,
        qc.count_correct,
        qc.packaging_verified,
        qc.labor_assigned,
        qc.weight_verified,
        qc.label_attached,
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All quality check items must be verified before passing"
        )

    # Validate order substatus transition
    order = qc.order
    _validate_substatus_transition(order.warehouse_substatus, "QC_PASSED")

    qc.is_passed = True
    qc.checked_at = datetime.now(UTC)
    if performed_by:
        qc.performed_by = performed_by

    order.warehouse_substatus = "QC_PASSED"

    await db.commit()
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == qc.id)
    )
    qc = result.scalar_one()
    return _to_quality_check_response(qc)


# ======================
# Loading Dock Operations
# ======================

async def get_loading_docks(
    db: AsyncSession,
    warehouse_id: UUID,
) -> LoadingDockListResponse:
    """Get all loading docks for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(LoadingDock)
        .options(selectinload(LoadingDock.assigned_order), selectinload(LoadingDock.assigned_vehicle))
        .where(LoadingDock.warehouse_id == warehouse_id)
        .order_by(LoadingDock.dock_number)
    )
    docks = result.scalars().all()

    # Lazy-seed: if this warehouse has no docks yet, create 6 now
    if not docks:
        for i in range(1, 7):
            db.add(LoadingDock(warehouse_id=warehouse_id, dock_number=str(i), status="FREE"))
        await db.flush()
        result = await db.execute(
            select(LoadingDock)
            .options(selectinload(LoadingDock.assigned_order), selectinload(LoadingDock.assigned_vehicle))
            .where(LoadingDock.warehouse_id == warehouse_id)
            .order_by(LoadingDock.dock_number)
        )
        docks = result.scalars().all()

    items = []
    now = datetime.now(UTC)
    for dock in docks:
        dwell_minutes = 0
        if dock.arrived_at and dock.status == "OCCUPIED":
            dwell_minutes = int((now - dock.arrived_at).total_seconds() / 60)

        order_tracking = None
        if dock.assigned_order:
            order_tracking = dock.assigned_order.tracking_code

        vehicle_code = None
        if dock.assigned_vehicle:
            v = dock.assigned_vehicle
            vehicle_code = f"{v.code} · {v.license_plate}" if v.license_plate else v.code

        items.append(LoadingDockResponse(
            id=dock.id,
            warehouse_id=dock.warehouse_id,
            dock_number=dock.dock_number,
            status=dock.status,
            assigned_vehicle_id=dock.assigned_vehicle_id,
            assigned_vehicle_code=vehicle_code,
            assigned_carrier=dock.assigned_carrier,
            assigned_order_id=dock.assigned_order_id,
            assigned_order_tracking=order_tracking,
            arrived_at=dock.arrived_at,
            loading_started_at=dock.loading_started_at,
            released_at=dock.released_at,
            dwell_minutes=dwell_minutes,
            created_at=dock.created_at,
        ))

    return LoadingDockListResponse(items=items, total=len(items))


async def create_loading_dock(
    db: AsyncSession,
    warehouse_id: UUID,
    data: LoadingDockCreate,
) -> LoadingDockResponse:
    """Create a new loading dock."""
    await _get_warehouse(db, warehouse_id)

    dock = LoadingDock(
        warehouse_id=warehouse_id,
        dock_number=data.dock_number,
        status="FREE",
    )
    db.add(dock)
    await db.commit()
    await db.refresh(dock)

    return LoadingDockResponse(
        id=dock.id,
        warehouse_id=dock.warehouse_id,
        dock_number=dock.dock_number,
        status=dock.status,
        assigned_vehicle_id=None,
        assigned_vehicle_code=None,
        assigned_carrier=None,
        assigned_order_id=None,
        assigned_order_tracking=None,
        arrived_at=None,
        loading_started_at=None,
        released_at=None,
        dwell_minutes=0,
        created_at=dock.created_at,
    )


async def assign_truck_to_dock(
    db: AsyncSession,
    warehouse_id: UUID,
    dock_id: UUID,
    data: AssignTruckRequest,
) -> LoadingDockResponse:
    """Assign a truck to a loading dock."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(LoadingDock)
        .options(selectinload(LoadingDock.assigned_order), selectinload(LoadingDock.assigned_vehicle))
        .where(LoadingDock.id == dock_id, LoadingDock.warehouse_id == warehouse_id)
    )
    dock = result.scalar_one_or_none()
    if not dock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loading dock not found")

    if dock.status != "FREE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dock is not available (current status: {dock.status})"
        )

    # Validate the vehicle exists and is available
    from app.models.logistics import LogisticsVehicle
    vehicle_result = await db.execute(
        select(LogisticsVehicle).where(LogisticsVehicle.id == data.vehicle_id)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    if vehicle.status == "In Use":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Vehicle {vehicle.code} is already in use")

    # If order is provided, update its substatus and persist vehicle on the order
    if data.order_id:
        order = await _get_order(db, data.order_id)
        if order.warehouse_id != warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order does not belong to this warehouse"
            )
        _validate_substatus_transition(order.warehouse_substatus, "ON_DOCK")
        order.warehouse_substatus = "ON_DOCK"
        order.assigned_vehicle_id = data.vehicle_id  # persist vehicle on order for dispatcher

    # Mark vehicle as In Use so it disappears from available lists
    vehicle.status = "In Use"

    dock.assigned_vehicle_id = data.vehicle_id
    dock.assigned_carrier = "Internal Fleet"
    dock.assigned_order_id = data.order_id
    dock.arrived_at = datetime.now(UTC)
    dock.status = "OCCUPIED"

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(LoadingDock)
        .options(selectinload(LoadingDock.assigned_order), selectinload(LoadingDock.assigned_vehicle))
        .where(LoadingDock.id == dock_id)
    )
    dock = result.scalar_one()

    order_tracking = dock.assigned_order.tracking_code if dock.assigned_order else None
    v = dock.assigned_vehicle
    vehicle_code = (f"{v.code} · {v.license_plate}" if v.license_plate else v.code) if v else None

    return LoadingDockResponse(
        id=dock.id,
        warehouse_id=dock.warehouse_id,
        dock_number=dock.dock_number,
        status=dock.status,
        assigned_vehicle_id=dock.assigned_vehicle_id,
        assigned_vehicle_code=vehicle_code,
        assigned_carrier=dock.assigned_carrier,
        assigned_order_id=dock.assigned_order_id,
        assigned_order_tracking=order_tracking,
        arrived_at=dock.arrived_at,
        loading_started_at=dock.loading_started_at,
        released_at=dock.released_at,
        dwell_minutes=0,
        created_at=dock.created_at,
    )


async def release_dock(
    db: AsyncSession,
    warehouse_id: UUID,
    dock_id: UUID,
    verification: DockVerificationData,
) -> LoadingDockResponse:
    """Release a loading dock after verification."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(LoadingDock)
        .options(selectinload(LoadingDock.assigned_order))
        .where(LoadingDock.id == dock_id, LoadingDock.warehouse_id == warehouse_id)
    )
    dock = result.scalar_one_or_none()
    if not dock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loading dock not found")

    if dock.status != "OCCUPIED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dock is not occupied (current status: {dock.status})"
        )

    # Verify all checks passed
    if not all([
        verification.items_scanned,
        verification.labor_present,
        verification.packing_loaded,
        verification.manifest_attached,
        verification.driver_confirmed,
        verification.weight_verified,
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All verification checks must pass before releasing dock"
        )

    # Update order substatus if assigned
    if dock.assigned_order:
        order = dock.assigned_order

        # Ensure QC was passed before allowing dispatch
        qc_passed = (
            await db.execute(
                select(QualityCheck).where(
                    QualityCheck.order_id == order.id,
                    QualityCheck.is_passed.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not qc_passed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Quality check must be passed before dispatching the order",
            )

        _validate_substatus_transition(order.warehouse_substatus, "DISPATCHED")
        order.warehouse_substatus = "DISPATCHED"

    now = datetime.now(UTC)
    dwell_minutes = 0
    if dock.arrived_at:
        dwell_minutes = int((now - dock.arrived_at).total_seconds() / 60)

    # If NO order was linked to this dock, there is nothing downstream to release the
    # vehicle — free it immediately so it doesn't stay stuck in "In Use" forever.
    # When an order IS linked, the vehicle stays "In Use" until the dispatcher moves
    # the order to IN_TRANSIT / DELIVERED (handled by _release_order_resources).
    if not dock.assigned_order and dock.assigned_vehicle_id:
        from app.models.logistics import LogisticsVehicle as _LV
        _veh = (await db.execute(select(_LV).where(_LV.id == dock.assigned_vehicle_id))).scalar_one_or_none()
        if _veh and _veh.status == "In Use":
            _veh.status = "Active"

    dock.released_at = now
    dock.status = "FREE"
    dock.assigned_vehicle_id = None
    dock.assigned_carrier = None
    dock.assigned_order_id = None
    dock.arrived_at = None
    dock.loading_started_at = None

    await db.commit()
    await db.refresh(dock)

    return LoadingDockResponse(
        id=dock.id,
        warehouse_id=dock.warehouse_id,
        dock_number=dock.dock_number,
        status=dock.status,
        assigned_vehicle_id=None,
        assigned_vehicle_code=None,
        assigned_carrier=None,
        assigned_order_id=None,
        assigned_order_tracking=None,
        arrived_at=None,
        loading_started_at=None,
        released_at=dock.released_at,
        dwell_minutes=dwell_minutes,
        created_at=dock.created_at,
    )


async def set_dock_maintenance(
    db: AsyncSession,
    warehouse_id: UUID,
    dock_id: UUID,
    is_maintenance: bool,
) -> LoadingDockResponse:
    """Set dock maintenance status."""
    await _get_warehouse(db, warehouse_id)

    result = await db.execute(
        select(LoadingDock)
        .where(LoadingDock.id == dock_id, LoadingDock.warehouse_id == warehouse_id)
    )
    dock = result.scalar_one_or_none()
    if not dock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loading dock not found")

    if dock.status == "OCCUPIED" and is_maintenance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot set maintenance while dock is occupied"
        )

    dock.status = "MAINTENANCE" if is_maintenance else "FREE"

    await db.commit()
    await db.refresh(dock)

    return LoadingDockResponse(
        id=dock.id,
        warehouse_id=dock.warehouse_id,
        dock_number=dock.dock_number,
        status=dock.status,
        assigned_vehicle_id=dock.assigned_vehicle_id,
        assigned_vehicle_code=None,
        assigned_carrier=dock.assigned_carrier,
        assigned_order_id=dock.assigned_order_id,
        assigned_order_tracking=None,
        arrived_at=dock.arrived_at,
        loading_started_at=dock.loading_started_at,
        released_at=dock.released_at,
        dwell_minutes=0,
        created_at=dock.created_at,
    )


# ======================
# Returns / Grading Operations
# ======================

async def _backfill_pending_return_gradings(
    db: AsyncSession,
    warehouse_id: UUID,
) -> None:
    linked_cases = (
        await db.execute(
            select(LogisticsReturnCase).where(
                LogisticsReturnCase.warehouse_id == warehouse_id,
                LogisticsReturnCase.reference_code.is_not(None),
            )
        )
    ).scalars().all()
    case_by_ref = {
        case.reference_code: case for case in linked_cases if case.reference_code
    }

    photo_review_refs = [
        ref for ref, case in case_by_ref.items() if getattr(case, "flow_type", None) == "photo_review"
    ]
    removed_any = False
    if photo_review_refs:
        stray_pending_gradings = (
            await db.execute(
                select(ReturnGrading).where(
                    ReturnGrading.warehouse_id == warehouse_id,
                    ReturnGrading.status == "pending",
                    ReturnGrading.rma_code.in_(photo_review_refs),
                )
            )
        ).scalars().all()
        for grading in stray_pending_gradings:
            await db.delete(grading)
            removed_any = True

    existing_rma_codes = set(
        (
            await db.execute(
                select(ReturnGrading.rma_code).where(ReturnGrading.warehouse_id == warehouse_id)
            )
        ).scalars().all()
    )

    return_cases = [
        case for case in linked_cases
        if getattr(case, "flow_type", None) == "pickup_inspection"
        and case.status in {
            "Pending",
            "Approved",
            "Pickup Requested",
            "Pickup Approved",
            "Pickup Scheduled",
            "Collected",
            "At Warehouse",
            "Arrived at Warehouse",
        }
    ]

    created_any = False
    for case in return_cases:
        if not case.reference_code or case.reference_code in existing_rma_codes:
            continue

        item_condition = "Awaiting Pickup" if case.status == "Pickup Scheduled" else "Pending Inspection"
        db.add(
            ReturnGrading(
                warehouse_id=warehouse_id,
                order_id=case.order_id,
                rma_code=case.reference_code,
                item_condition=item_condition,
                condition_notes=case.reason,
                disposition="pending",
                status="pending",
            )
        )
        existing_rma_codes.add(case.reference_code)
        created_any = True

    if created_any or removed_any:
        await db.commit()


async def get_return_gradings(
    db: AsyncSession,
    warehouse_id: UUID,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ReturnGradingListResponse:
    """Get all return gradings for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    if status_filter in (None, "pending"):
        await _backfill_pending_return_gradings(db, warehouse_id)

    query = select(ReturnGrading).where(ReturnGrading.warehouse_id == warehouse_id)

    if status_filter:
        query = query.where(ReturnGrading.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = (
        query
        .options(selectinload(ReturnGrading.order), selectinload(ReturnGrading.grader))
        .order_by(ReturnGrading.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    gradings = result.scalars().all()

    items = []
    for grading in gradings:
        order_tracking = grading.order.tracking_code if grading.order else None
        grader_name = grading.grader.name if grading.grader else None

        items.append(ReturnGradingResponse(
            id=grading.id,
            warehouse_id=grading.warehouse_id,
            order_id=grading.order_id,
            order_tracking=order_tracking,
            rma_code=grading.rma_code,
            item_condition=grading.item_condition,
            condition_notes=grading.condition_notes,
            disposition=grading.disposition,
            is_genuine=grading.is_genuine,
            recommended_outcome=grading.recommended_outcome,
            inspection_remarks=grading.inspection_remarks,
            damage_photo_url=grading.damage_photo_url,
            graded_by=grading.graded_by,
            grader_name=grader_name,
            graded_at=grading.graded_at,
            status=grading.status,
            created_at=grading.created_at,
        ))

    return ReturnGradingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def create_return_grading(
    db: AsyncSession,
    warehouse_id: UUID,
    data: ReturnGradingCreate,
    graded_by: UUID | None = None,
) -> ReturnGradingResponse:
    """Create a new return grading."""
    await _get_warehouse(db, warehouse_id)

    # Check for duplicate RMA code
    result = await db.execute(
        select(ReturnGrading).where(ReturnGrading.rma_code == data.rma_code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RMA code already exists"
        )

    grading = ReturnGrading(
        warehouse_id=warehouse_id,
        order_id=data.order_id,
        rma_code=data.rma_code,
        item_condition=data.item_condition,
        condition_notes=data.condition_notes,
        disposition=data.disposition,
        is_genuine=data.is_genuine,
        recommended_outcome=data.recommended_outcome,
        inspection_remarks=data.inspection_remarks,
        graded_by=graded_by,
        graded_at=datetime.now(UTC) if graded_by else None,
        status="pending",
    )
    db.add(grading)
    await db.commit()
    await db.refresh(grading)

    return ReturnGradingResponse(
        id=grading.id,
        warehouse_id=grading.warehouse_id,
        order_id=grading.order_id,
        order_tracking=None,
        rma_code=grading.rma_code,
        item_condition=grading.item_condition,
        condition_notes=grading.condition_notes,
        disposition=grading.disposition,
        is_genuine=grading.is_genuine,
        recommended_outcome=grading.recommended_outcome,
        inspection_remarks=grading.inspection_remarks,
        damage_photo_url=grading.damage_photo_url,
        graded_by=grading.graded_by,
        grader_name=None,
        graded_at=grading.graded_at,
        status=grading.status,
        created_at=grading.created_at,
    )


async def update_return_grading(
    db: AsyncSession,
    warehouse_id: UUID,
    grading_id: UUID,
    data: ReturnGradingUpdate,
) -> ReturnGradingResponse:
    """Update a return grading."""
    result = await db.execute(
        select(ReturnGrading)
        .options(selectinload(ReturnGrading.order), selectinload(ReturnGrading.grader))
        .where(ReturnGrading.id == grading_id, ReturnGrading.warehouse_id == warehouse_id)
    )
    grading = result.scalar_one_or_none()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return grading not found")

    provided_fields = data.model_fields_set
    if "item_condition" in provided_fields:
        grading.item_condition = data.item_condition
    if "condition_notes" in provided_fields:
        grading.condition_notes = data.condition_notes
    if "disposition" in provided_fields:
        grading.disposition = data.disposition
    if "is_genuine" in provided_fields:
        grading.is_genuine = data.is_genuine
    if "recommended_outcome" in provided_fields:
        grading.recommended_outcome = data.recommended_outcome
    if "inspection_remarks" in provided_fields:
        grading.inspection_remarks = data.inspection_remarks

    await db.commit()
    await db.refresh(grading)

    order_tracking = grading.order.tracking_code if grading.order else None
    grader_name = grading.grader.name if grading.grader else None

    return ReturnGradingResponse(
        id=grading.id,
        warehouse_id=grading.warehouse_id,
        order_id=grading.order_id,
        order_tracking=order_tracking,
        rma_code=grading.rma_code,
        item_condition=grading.item_condition,
        condition_notes=grading.condition_notes,
        disposition=grading.disposition,
        is_genuine=grading.is_genuine,
        recommended_outcome=grading.recommended_outcome,
        inspection_remarks=grading.inspection_remarks,
        damage_photo_url=grading.damage_photo_url,
        graded_by=grading.graded_by,
        grader_name=grader_name,
        graded_at=grading.graded_at,
        status=grading.status,
        created_at=grading.created_at,
    )


async def upload_damage_photo(
    db: AsyncSession,
    warehouse_id: UUID,
    grading_id: UUID,
    file: UploadFile,
) -> str:
    """Upload a damage photo for a return grading."""
    result = await db.execute(
        select(ReturnGrading).where(
            ReturnGrading.id == grading_id,
            ReturnGrading.warehouse_id == warehouse_id,
        )
    )
    grading = result.scalar_one_or_none()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return grading not found")

    # For now, store base64 or you could save to disk/S3
    # This is a simplified implementation - in production use S3 or similar
    import base64
    content = await file.read()
    photo_data = base64.b64encode(content).decode('utf-8')
    photo_url = f"data:{file.content_type};base64,{photo_data}"

    grading.damage_photo_url = photo_url
    await db.commit()

    return photo_url


async def complete_return_grading(
    db: AsyncSession,
    warehouse_id: UUID,
    grading_id: UUID,
    graded_by: UUID | None = None,
) -> ReturnGradingResponse:
    """Mark a return grading as completed."""
    result = await db.execute(
        select(ReturnGrading)
        .options(selectinload(ReturnGrading.order), selectinload(ReturnGrading.grader))
        .where(ReturnGrading.id == grading_id, ReturnGrading.warehouse_id == warehouse_id)
    )
    grading = result.scalar_one_or_none()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return grading not found")

    grading.status = "completed"
    grading.graded_at = datetime.now(UTC)
    if graded_by:
        grading.graded_by = graded_by

    # Sync condition and status back to the LM's LogisticsReturnCase so the
    # Logistic Manager can see the WM's physical assessment.
    if grading.rma_code:
        return_case = (await db.execute(
            select(LogisticsReturnCase).where(LogisticsReturnCase.reference_code == grading.rma_code)
        )).scalar_one_or_none()
        if return_case:
            return_case.condition = grading.item_condition
            if getattr(return_case, "flow_type", None) == "pickup_inspection":
                return_case.status = "Physically Inspected"
            db.add(return_case)

    await db.commit()
    await db.refresh(grading)

    order_tracking = grading.order.tracking_code if grading.order else None
    grader_name = grading.grader.name if grading.grader else None

    return ReturnGradingResponse(
        id=grading.id,
        warehouse_id=grading.warehouse_id,
        order_id=grading.order_id,
        order_tracking=order_tracking,
        rma_code=grading.rma_code,
        item_condition=grading.item_condition,
        condition_notes=grading.condition_notes,
        disposition=grading.disposition,
        is_genuine=grading.is_genuine,
        recommended_outcome=grading.recommended_outcome,
        inspection_remarks=grading.inspection_remarks,
        damage_photo_url=grading.damage_photo_url,
        graded_by=grading.graded_by,
        grader_name=grader_name,
        graded_at=grading.graded_at,
        status=grading.status,
        created_at=grading.created_at,
    )


# ======================
# Zone Metrics Operations
# ======================

async def get_zone_metrics(
    db: AsyncSession,
    warehouse_id: UUID,
    zone_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ZoneMetricsListResponse:
    """Get metrics for a specific zone."""
    await _get_warehouse(db, warehouse_id)

    query = select(WarehouseZoneMetrics).where(
        WarehouseZoneMetrics.warehouse_id == warehouse_id,
        WarehouseZoneMetrics.zone_id == zone_id,
    )

    if date_from:
        query = query.where(WarehouseZoneMetrics.metric_date >= date_from)
    if date_to:
        query = query.where(WarehouseZoneMetrics.metric_date <= date_to)

    query = query.order_by(WarehouseZoneMetrics.metric_date.desc())

    result = await db.execute(query)
    metrics = result.scalars().all()

    items = [
        ZoneMetricsResponse(
            id=m.id,
            warehouse_id=m.warehouse_id,
            zone_id=m.zone_id,
            metric_date=m.metric_date,
            orders_processed=m.orders_processed,
            picking_accuracy_pct=m.picking_accuracy_pct,
            active_pickers=m.active_pickers,
            capacity_used_pct=m.capacity_used_pct,
            throughput_items_per_hour=m.throughput_items_per_hour,
            created_at=m.created_at,
        )
        for m in metrics
    ]

    return ZoneMetricsListResponse(items=items, total=len(items))


async def record_zone_metrics(
    db: AsyncSession,
    warehouse_id: UUID,
    data: ZoneMetricsCreate,
) -> ZoneMetricsResponse:
    """Record metrics for a zone (upsert for today)."""
    await _get_warehouse(db, warehouse_id)
    today = date.today()

    # Check for existing record
    result = await db.execute(
        select(WarehouseZoneMetrics).where(
            WarehouseZoneMetrics.warehouse_id == warehouse_id,
            WarehouseZoneMetrics.zone_id == data.zone_id,
            WarehouseZoneMetrics.metric_date == today,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.orders_processed = data.orders_processed
        existing.picking_accuracy_pct = data.picking_accuracy_pct
        existing.active_pickers = data.active_pickers
        existing.capacity_used_pct = data.capacity_used_pct
        existing.throughput_items_per_hour = data.throughput_items_per_hour
        metrics = existing
    else:
        # Create new
        metrics = WarehouseZoneMetrics(
            warehouse_id=warehouse_id,
            zone_id=data.zone_id,
            metric_date=today,
            orders_processed=data.orders_processed,
            picking_accuracy_pct=data.picking_accuracy_pct,
            active_pickers=data.active_pickers,
            capacity_used_pct=data.capacity_used_pct,
            throughput_items_per_hour=data.throughput_items_per_hour,
        )
        db.add(metrics)

    await db.commit()
    await db.refresh(metrics)

    return ZoneMetricsResponse(
        id=metrics.id,
        warehouse_id=metrics.warehouse_id,
        zone_id=metrics.zone_id,
        metric_date=metrics.metric_date,
        orders_processed=metrics.orders_processed,
        picking_accuracy_pct=metrics.picking_accuracy_pct,
        active_pickers=metrics.active_pickers,
        capacity_used_pct=metrics.capacity_used_pct,
        throughput_items_per_hour=metrics.throughput_items_per_hour,
        created_at=metrics.created_at,
    )


# ======================
# Performance Metrics
# ======================

async def get_performance_metrics(
    db: AsyncSession,
    warehouse_id: UUID,
    time_range: str = "today",
) -> PerformanceResponse:
    """Get performance metrics for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    # Define date range
    now = datetime.now(UTC)
    if time_range == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == "week":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date.replace(day=start_date.day - start_date.weekday())
    elif time_range == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get orders created in the selected time period (for KPI totals and completion rate).
    result = await db.execute(
        select(Order).where(
            Order.warehouse_id == warehouse_id,
            Order.created_at >= start_date,
        )
    )
    period_orders = result.scalars().all()

    # Get ALL active (in-progress) orders for the pipeline breakdown regardless of creation date.
    # Orders can be created one day and processed over following days, so restricting by
    # created_at causes pipeline stages to show 0 for carryover orders.
    active_pipeline_statuses = [
        "AWAITING_PICK", "PICKING", "PICKED",
        "PACKING", "PACKED", "QC_PASSED",
        "READY_FOR_DISPATCH", "ON_DOCK", "ON_HOLD",
        "AWAITING_INBOUND",
    ]
    result = await db.execute(
        select(Order).where(
            Order.warehouse_id == warehouse_id,
            Order.warehouse_substatus.in_(active_pipeline_statuses),
            Order.status.notin_(TERMINAL_ORDER_STATUSES),
        )
    )
    active_orders = result.scalars().all()

    # Get labourers
    result = await db.execute(
        select(Labourer).where(Labourer.warehouse_id == warehouse_id)
    )
    labourers = result.scalars().all()

    # KPI totals: based on orders created in the period
    total_orders = len(period_orders)
    dispatched = sum(1 for o in period_orders if o.warehouse_substatus == "DISPATCHED")
    completion_rate = (dispatched / total_orders * 100) if total_orders > 0 else 0

    # Pipeline breakdown: current snapshot from active (in-progress) orders regardless of creation date
    status_breakdown: dict[str, int] = {}
    for order in active_orders:
        substatus = order.warehouse_substatus or "NONE"
        status_breakdown[substatus] = status_breakdown.get(substatus, 0) + 1
    # Fold dispatched-in-period into the breakdown for chart completeness
    status_breakdown["DISPATCHED"] = dispatched

    labor_breakdown = {"active": 0, "idle": 0, "off": 0}
    for labourer in labourers:
        if labourer.is_active:
            if labourer.assigned_order_id:
                labor_breakdown["active"] += 1
            else:
                labor_breakdown["idle"] += 1
        else:
            labor_breakdown["off"] += 1

    metrics = PerformanceMetrics(
        completion_rate=round(completion_rate, 1),
        on_hold_count=status_breakdown.get("ON_HOLD", 0),
        picking_active=status_breakdown.get("PICKING", 0),
        packing_active=status_breakdown.get("PACKING", 0),
        ready_for_dispatch=status_breakdown.get("READY_FOR_DISPATCH", 0) + status_breakdown.get("QC_PASSED", 0),
        dispatched_today=dispatched,
        total_orders=total_orders,
        status_breakdown=status_breakdown,
        labor_breakdown=labor_breakdown,
    )

    return PerformanceResponse(
        warehouse_id=warehouse_id,
        time_range=time_range,
        metrics=metrics,
    )
