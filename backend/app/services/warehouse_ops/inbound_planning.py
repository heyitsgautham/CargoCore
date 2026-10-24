"""Inbound overview and the receive plan, with a Gemini plan when it is configured and a heuristic one otherwise."""

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from google.genai import types
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.labour import Labourer
from app.models.order import DamageReport, Order
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.models.vendor import VendorSupportTicket
from app.models.warehouse import (
    LoadingDock,
)
from app.schemas.warehouse_operations import (
    DockSlot,
    InboundReceivePlanResponse,
    InboundReceivePlanShipment,
    InboundResponse,
    InboundShipmentItem,
    InboundStats,
)
from app.services.warehouse_ops.common import (
    INBOUND_RECEIVED_SUBSTATUSES,
    INBOUND_RESOLUTION_LABELS,
    TERMINAL_ORDER_STATUSES,
    _dock_status_for_shipment,
    _get_order,
    _get_warehouse,
    _heuristic_inbound_receive_plan,
    _inbound_status,
    _is_active_inbound_supplier,
    _is_inbound_issue_ticket,
    _is_recurring_inbound,
    _linked_issue_type,
    _linked_resolution_action,
    _parse_ticket_notes_metadata,
    _strip_json_fences,
    _ticket_reference_code,
)
from app.utils.gemini import GEMINI_MODEL, GeminiConfigError, get_gemini_client


async def get_inbound_overview(
    db: AsyncSession,
    warehouse_id: UUID,
) -> InboundResponse:
    await _get_warehouse(db, warehouse_id)
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
