import json
import uuid
from collections import OrderedDict
from datetime import UTC, date, datetime, time, timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.logistics import LogisticsVehicle, LogisticsZone
from app.models.order import DamageReport as DamageReportModel
from app.models.order import Order
from app.models.user import User
from app.models.vendor import (
    VendorApiKey,
    VendorBulkUpload,
    VendorRecurringRule,
    VendorSupportReply,
    VendorSupportTicket,
    VendorTeamMember,
)
from app.models.warehouse import Warehouse
from app.schemas.auth import UserProfile
from app.schemas.vendor import (
    VendorAnalytics,
    VendorApiKeyCreate,
    VendorApiKeyResponse,
    VendorBulkUploadCreate,
    VendorBulkUploadResponse,
    VendorBulkUploadUpdate,
    VendorDamageReport,
    VendorDamageReportCreate,
    VendorDamageReportsResponse,
    VendorDashboardResponse,
    VendorInvoicePayRequest,
    VendorInvoiceRecord,
    VendorInvoiceSummary,
    VendorMonthlyPoint,
    VendorRecurringCostEstimate,
    VendorRecurringCostEstimateRequest,
    VendorRecurringRuleCreate,
    VendorRecurringRuleResponse,
    VendorSettings,
    VendorSettingsResponse,
    VendorShipmentCost,
    VendorShipmentHistoryItem,
    VendorShipmentsResponse,
    VendorShipmentSummary,
    VendorStats,
    VendorSupportReplyCreate,
    VendorSupportReplyResponse,
    VendorSupportTicketCreate,
    VendorSupportTicketResponse,
    VendorTeamMemberCreate,
    VendorTeamMemberResponse,
)


def _ensure_vendor(user: User) -> None:
    if user.role.name != "VENDOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor endpoints are only available for vendor users",
        )


def _is_active_vendor_owner(user: User | None) -> bool:
    return bool(user and getattr(user, "is_active", False))


def _profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        name=user.name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        address=user.address,
        role=user.role.name,
        warehouse_id=user.warehouse_id,
        is_active=user.is_active,
        approval_status=user.approval_status,
        company_name=user.company_name,
        tax_id=user.tax_id,
        contact_person=user.contact_person,
        business_email=user.business_email,
        business_phone=user.business_phone,
        created_at=user.created_at,
    )


_WAREHOUSE_SUBSTATUSES = {"AWAITING_INBOUND", "AWAITING_PICK", "PICKING", "PICKED", "PACKING", "PACKED", "QC_PASSED"}


def _status_key(value: str) -> str:
    mapping = {
        "DRAFT": "pending",
        "CONFIRMED": "pending",
        "ASSIGNED": "transit",
        "IN_TRANSIT": "transit",
        "DELIVERED": "delivered",
        "CLOSED": "delivered",
        "CANCELLED": "cancelled",
    }
    return mapping.get(value.upper(), value.lower())


def _shipment_status_key(status: str, warehouse_substatus: str | None) -> str:
    """Status key shown to vendor — adds 'warehouse' phase for in-warehouse orders.

    Terminal statuses (DELIVERED, CLOSED, CANCELLED) always take priority;
    never let a lingering warehouse_substatus override them.
    """
    if status.upper() in {"DELIVERED", "CLOSED", "CANCELLED"}:
        return _status_key(status)
    if warehouse_substatus and warehouse_substatus.upper() in _WAREHOUSE_SUBSTATUSES:
        return "warehouse"
    return _status_key(status)


def _status_label(value: str) -> str:
    mapping = {
        "pending": "Pending",
        "warehouse": "In Warehouse",
        "transit": "In Transit",
        "delivered": "Delivered",
        "cancelled": "Cancelled",
    }
    return mapping.get(value, value.replace("_", " ").title())


def _progress(value: str) -> int:
    mapping = {"pending": 15, "warehouse": 35, "transit": 65, "delivered": 100, "cancelled": 0}
    return mapping.get(value, 0)


def _eta_label(order: Order) -> str:
    if order.status in {"DELIVERED", "CLOSED"}:
        return "Delivered"
    if order.status == "CANCELLED":
        return "Cancelled"
    if order.scheduled_at:
        return order.scheduled_at.strftime("%b %d, %Y")
    return order.created_at.strftime("%b %d, %Y")


def _history(order: Order) -> list[VendorShipmentHistoryItem]:
    created = order.created_at.strftime("%Y-%m-%d %H:%M")
    items = [VendorShipmentHistoryItem(status="Created", time=created)]
    if order.status in {"CONFIRMED", "ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        items.append(VendorShipmentHistoryItem(status="Confirmed", time=created))
    sub = (order.warehouse_substatus or "").upper()
    if sub in _WAREHOUSE_SUBSTATUSES:
        label_map = {
            "AWAITING_INBOUND": "Awaiting Inbound",
            "AWAITING_PICK": "Awaiting Pick",
            "PICKING": "Picking",
            "PICKED": "Picked",
            "PACKING": "Packing",
            "PACKED": "Packed",
            "QC_PASSED": "QC Passed",
        }
        items.append(VendorShipmentHistoryItem(status=label_map.get(sub, sub.title()), time=created))
    if order.status in {"ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        items.append(VendorShipmentHistoryItem(status="Assigned", time=created))
    if order.status in {"IN_TRANSIT", "DELIVERED", "CLOSED"}:
        items.append(VendorShipmentHistoryItem(status="In Transit", time=created))
    if order.status in {"DELIVERED", "CLOSED"}:
        items.append(VendorShipmentHistoryItem(status="Delivered", time=created))
    if order.status == "CANCELLED":
        items.append(
            VendorShipmentHistoryItem(
                status=f"Cancelled: {order.cancel_reason or 'No reason provided'}",
                time=created,
            )
        )
    return items


def _shipment(
    order: Order,
    *,
    driver_name: str | None = None,
    driver_phone: str | None = None,
    vehicle_code: str | None = None,
    customer_name: str | None = None,
    customer_phone: str | None = None,
) -> VendorShipmentSummary:
    key = _shipment_status_key(order.status, order.warehouse_substatus)
    return VendorShipmentSummary(
        id=order.id,
        tracking_code=order.tracking_code,
        status=order.status,
        status_label=_status_label(key),
        status_key=key,
        pickup_addr=order.pickup_addr,
        delivery_addr=order.delivery_addr,
        assigned_driver_id=order.assigned_driver_id,
        assigned_driver_name=driver_name,
        assigned_driver_phone=driver_phone,
        assigned_vehicle_id=order.assigned_vehicle_id,
        assigned_vehicle_code=vehicle_code,
        cargo_type=order.cargo_type,
        cargo_weight_kg=order.cargo_weight_kg,
        vehicle_type=order.vehicle_type,
        payment_mode=order.payment_mode,
        payment_status=order.payment_status,
        labor_count=order.labor_count,
        amount=order.total_amount,
        scheduled_at=order.scheduled_at,
        delivered_at=order.delivered_at,
        created_at=order.created_at,
        delivery_notes=order.delivery_notes,
        pod_photos=order.pod_photos or [],
        pod_signature=order.pod_signature,
        poc_signature=order.poc_signature,
        customer_name=customer_name,
        customer_phone=customer_phone,
        auto_debit_note=_latest_auto_debit_note(order.delivery_notes),
        eta_label=_eta_label(order),
        progress=_progress(key),
        cost=VendorShipmentCost(
            base=order.base_amount,
            vehicle=order.vehicle_amount,
            labor=order.labor_amount,
            materials=order.materials_amount,
            packing=order.packing_amount,
            platform_fee=order.platform_fee,
            taxes=order.tax_amount,
            total=order.total_amount,
        ),
        status_history=_history(order),
    )


async def _resolve_assignment_maps(
    db: AsyncSession,
    orders: list[Order],
) -> tuple[dict, dict, dict, dict, dict]:
    driver_ids = {order.assigned_driver_id for order in orders if order.assigned_driver_id}
    vehicle_ids = {order.assigned_vehicle_id for order in orders if order.assigned_vehicle_id}
    customer_ids = {order.customer_id for order in orders if order.customer_id}

    driver_names: dict = {}
    driver_phones: dict = {}
    if driver_ids:
        rows = (
            await db.execute(select(User.id, User.name, User.phone).where(User.id.in_(driver_ids)))
        ).all()
        driver_names = {row.id: row.name for row in rows}
        driver_phones = {row.id: row.phone for row in rows}

    vehicle_codes: dict = {}
    if vehicle_ids:
        rows = (
            await db.execute(
                select(LogisticsVehicle.id, LogisticsVehicle.code, LogisticsVehicle.license_plate).where(
                    LogisticsVehicle.id.in_(vehicle_ids)
                )
            )
        ).all()
        vehicle_codes = {
            row.id: (f"{row.code} · {row.license_plate}" if row.license_plate else row.code)
            for row in rows
        }

    customer_names: dict = {}
    customer_phones: dict = {}
    if customer_ids:
        rows = (
            await db.execute(select(User.id, User.name, User.phone).where(User.id.in_(customer_ids)))
        ).all()
        customer_names = {row.id: row.name for row in rows}
        customer_phones = {row.id: row.phone for row in rows}

    return driver_names, driver_phones, vehicle_codes, customer_names, customer_phones


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


def _invoice_status(order: Order, now: datetime) -> str:
    if order.payment_status == "paid":
        return "Paid"
    paid_amount = getattr(order, 'paid_amount', 0) or 0
    if paid_amount > 0:
        return "Partial"
    due_date = order.created_at + timedelta(days=30)
    if due_date.date() < now.date():
        return "Overdue"
    return "Unpaid"


def _invoice_record(order: Order, now: datetime) -> VendorInvoiceRecord:
    invoice_status = _invoice_status(order, now)
    paid = getattr(order, 'paid_amount', 0) or 0
    if invoice_status == "Paid":
        paid = order.total_amount
    return VendorInvoiceRecord(
        id=f"INV-{order.tracking_code}",
        order_id=order.id,
        tracking_code=order.tracking_code,
        date=order.created_at.strftime("%b %d, %Y"),
        due_date=(order.created_at + timedelta(days=30)).strftime("%b %d, %Y"),
        amount=order.total_amount,
        paid=paid,
        status=invoice_status,
    )


async def _orders_for_vendor(db: AsyncSession, user: User) -> list[Order]:
    today = datetime.now(UTC).date()
    cutoff = today + timedelta(days=1)  # show recurring orders 1 day before their run date

    all_orders = (
        await db.execute(
            select(Order).where(Order.customer_id == user.id).order_by(Order.created_at.desc())
        )
    ).scalars().all()

    result = []
    for order in all_orders:
        # Recurring orders (identified by RECURRING_RULE marker) are only visible
        # from the day before their scheduled date so the vendor/WH doesn't see
        # them too far in advance.
        if order.delivery_notes and "RECURRING_RULE:" in order.delivery_notes:
            if order.scheduled_at and order.scheduled_at.date() > cutoff:
                continue
        result.append(order)
    return result



def _monthly_points(orders: list[Order]) -> list[VendorMonthlyPoint]:
    now = datetime.now()
    month_buckets: OrderedDict[str, dict[str, float | int]] = OrderedDict()
    for offset in range(5, -1, -1):
        month = ((now.month - offset - 1) % 12) + 1
        year = now.year + ((now.month - offset - 1) // 12)
        month_key = datetime(year, month, 1).strftime("%b")
        month_buckets[month_key] = {"spend": 0.0, "orders": 0}

    for order in orders:
        month_key = order.created_at.strftime("%b")
        if month_key in month_buckets:
            month_buckets[month_key]["orders"] += 1
            month_buckets[month_key]["spend"] += order.total_amount

    return [
        VendorMonthlyPoint(month=month, spend=float(values["spend"]), orders=int(values["orders"]))
        for month, values in month_buckets.items()
    ]


def _analytics(orders: list[Order]) -> VendorAnalytics:
    total = len(orders)
    delivered = sum(1 for order in orders if _status_key(order.status) == "delivered")
    cancelled = sum(1 for order in orders if _status_key(order.status) == "cancelled")
    successful = max(total - cancelled, 0)
    avg_order_value = sum(order.total_amount for order in orders) / total if total else 0

    transit_days = []
    for order in orders:
        if order.scheduled_at:
            transit_days.append(abs((order.scheduled_at - order.created_at).days) or 1)

    on_time = round((delivered / successful) * 100, 1) if successful else 0
    success_rate = round((successful / total) * 100, 1) if total else 0

    return VendorAnalytics(
        monthly=_monthly_points(orders),
        on_time=on_time,
        avg_transit_days=round(sum(transit_days) / len(transit_days), 1) if transit_days else 0,
        avg_order_value=round(avg_order_value, 2),
        success_rate=success_rate,
    )


def _invoice_summary(orders: list[Order], credit_balance: float = 0.0) -> VendorInvoiceSummary:
    now = datetime.now()
    invoices = [_invoice_record(order, now) for order in orders if order.total_amount > 0]
    total_overdue = sum(invoice.amount - invoice.paid for invoice in invoices if invoice.status == "Overdue")
    total_unpaid = sum(1 for invoice in invoices if invoice.status != "Paid")
    current_month = now.strftime("%Y-%m")
    total_paid_this_month = sum(
        invoice.paid
        for invoice in invoices
        if invoice.status == "Paid" and datetime.strptime(invoice.date, "%b %d, %Y").strftime("%Y-%m") == current_month
    )
    return VendorInvoiceSummary(
        invoices=invoices,
        total_overdue=total_overdue,
        total_unpaid=total_unpaid,
        total_paid_this_month=total_paid_this_month,
        credit_balance=round(credit_balance, 2),
    )


def _bulk_upload_response(upload: VendorBulkUpload) -> VendorBulkUploadResponse:
    return VendorBulkUploadResponse(
        id=upload.id,
        filename=upload.filename,
        date=upload.created_at.strftime("%b %d, %Y"),
        orders=upload.orders,
        status=upload.status,
        errors=upload.errors,
        scheduled_for=upload.scheduled_for,
    )


def _api_key_response(api_key: VendorApiKey) -> VendorApiKeyResponse:
    return VendorApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=api_key.key_value,
        created=api_key.created_at.strftime("%b %d, %Y"),
        last_used=api_key.last_used_at.strftime("%b %d, %Y") if api_key.last_used_at else "Never",
        status=api_key.status,
    )


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


def _latest_auto_debit_note(delivery_notes: str | None) -> str | None:
    if not delivery_notes:
        return None
    lines = [line.strip() for line in str(delivery_notes).splitlines() if line.strip()]
    for line in reversed(lines):
        if not line.startswith("AUTODEBIT_EVENT|"):
            continue
        try:
            parts = line.split("|")
            fields = {}
            for part in parts[1:]:
                if ":" not in part:
                    continue
                k, v = part.split(":", 1)
                fields[k] = v
            note_type = fields.get("TYPE", "")
            msg = fields.get("MSG", "").strip()
            if not msg:
                continue
            if note_type.startswith("SKIPPED"):
                return f"Auto-debit skipped: {msg}"
            if note_type == "DEBT":
                return f"Auto-debit processed with wallet debt: {msg}"
            if note_type == "SUCCESS":
                return f"Auto-debit success: {msg}"
            return msg
        except Exception:
            continue
    return None


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


def _safe_float(value) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _normalize_uuid(value) -> uuid.UUID | None:
    if not value:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except Exception:
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in km between two lat/lon points."""
    import math
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


_OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"
_OSRM_TIMEOUT_SECONDS = 5.0


def _fallback_route_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Fallback heuristic when route service is unavailable."""
    return max(1.0, round(_haversine_km(lat1, lon1, lat2, lon2) * 1.35, 1))


async def _road_route_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> tuple[float, str]:
    """Return road-route km using OSRM, falling back to a padded estimate."""
    url = f"{_OSRM_BASE_URL}/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false"}
    try:
        async with httpx.AsyncClient(timeout=_OSRM_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
        route = (payload.get("routes") or [None])[0]
        if payload.get("code") != "Ok" or not route:
            return _fallback_route_km(lat1, lon1, lat2, lon2), "road_route_fallback"
        meters = float(route.get("distance") or 0.0)
        return max(1.0, round(meters / 1000.0, 1)), "road_route"
    except Exception:
        return _fallback_route_km(lat1, lon1, lat2, lon2), "road_route_fallback"


async def _resolve_recurring_warehouse(
    db: AsyncSession,
    *,
    hub_id: uuid.UUID | None = None,
    hub_name: str | None = None,
    fallback_to_first: bool = True,
) -> tuple[Warehouse | None, str]:
    warehouse = None
    if hub_id:
        warehouse = (
            await db.execute(
                select(Warehouse).where(
                    Warehouse.id == hub_id,
                    Warehouse.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if warehouse:
            return warehouse, "hub_id"

    normalized_hub_name = (hub_name or "").strip()
    if normalized_hub_name:
        warehouse = (
            await db.execute(
                select(Warehouse).where(
                    Warehouse.is_active.is_(True),
                    Warehouse.name.ilike(f"%{normalized_hub_name}%"),
                ).order_by(Warehouse.created_at.asc()).limit(1)
            )
        ).scalar_one_or_none()
        if warehouse:
            return warehouse, "hub_name"

    if not fallback_to_first:
        return None, "unresolved"

    warehouse = (
        await db.execute(
            select(Warehouse).where(Warehouse.is_active.is_(True)).order_by(Warehouse.created_at.asc()).limit(1)
        )
    ).scalar_one_or_none()
    return warehouse, "first_active" if warehouse else "unresolved"


async def _resolve_recurring_pickup_origin(
    db: AsyncSession,
    *,
    warehouse: Warehouse | None,
) -> tuple[float | None, float | None, str | None, str]:
    if warehouse and warehouse.lat is not None and warehouse.lng is not None:
        return warehouse.lat, warehouse.lng, warehouse.name, "warehouse_coordinates"

    if warehouse:
        zone = (
            await db.execute(
                select(LogisticsZone).where(
                    LogisticsZone.warehouse_id == warehouse.id,
                    LogisticsZone.status.ilike("active"),
                    LogisticsZone.lat.is_not(None),
                    LogisticsZone.lng.is_not(None),
                ).order_by(LogisticsZone.created_at.asc()).limit(1)
            )
        ).scalar_one_or_none()
        if zone:
            return zone.lat, zone.lng, zone.name or warehouse.name, "geofence_zone"

    return None, None, warehouse.name if warehouse else None, "missing_coordinates"


def _build_recurring_estimate_note(
    *,
    warehouse_name: str | None,
    warehouse_source: str,
    pickup_source: str,
    pickup_reference: str | None,
    distance_method: str,
) -> str:
    hub_label = warehouse_name or "selected hub"
    used_fallback = distance_method == "road_route_fallback"
    if pickup_source == "geofence_zone":
        zone_label = pickup_reference or hub_label
        prefix = (
            f"Estimate uses road-route distance from active geofence zone '{zone_label}' because "
            f"'{hub_label}' has no saved warehouse coordinates."
        )
    elif pickup_source == "missing_coordinates":
        prefix = f"'{hub_label}' has no saved warehouse coordinates or active geofence center, so only the base fee is shown."
    else:
        prefix = f"Estimate uses road-route distance from '{hub_label}' warehouse coordinates."

    if used_fallback and pickup_source != "missing_coordinates":
        prefix = f"{prefix} Live routing was unavailable, so a buffered fallback estimate was used."

    if warehouse_source == "first_active":
        return f"{prefix} Selected hub could not be matched exactly, so the first active warehouse was used."
    if warehouse_source == "unresolved":
        return f"{prefix} No matching active warehouse was found."
    return prefix


async def estimate_recurring_cost(
    db: AsyncSession,
    data: "VendorRecurringCostEstimateRequest",
) -> "VendorRecurringCostEstimate":
    """Estimate the per-run cost for a recurring schedule.

    Calculates road-route distance from the resolved warehouse pickup origin to
    the destination coordinates, then applies the configured rate card
    (baseBookingFee + perKmRate). Falls back to a buffered estimate if live
    routing is unavailable.
    """
    from app.routers.rates import _load as _load_rates

    wh, warehouse_source = await _resolve_recurring_warehouse(
        db,
        hub_id=data.hub_id,
        hub_name=data.hub_name,
        fallback_to_first=True,
    )

    rate_cfg = _load_rates()
    base_fee = float(rate_cfg.get("baseBookingFee", 220))
    per_km = float(rate_cfg.get("perKmRate", 12))

    pickup_lat, pickup_lng, pickup_reference, pickup_source = await _resolve_recurring_pickup_origin(
        db,
        warehouse=wh,
    )
    dist_km = 0.0
    distance_method = "road_route"
    if pickup_lat is not None and pickup_lng is not None:
        dist_km, distance_method = await _road_route_distance_km(
            pickup_lat,
            pickup_lng,
            data.destination_lat,
            data.destination_lon,
        )

    distance_cost = round(dist_km * per_km, 2)
    total_estimate = round(base_fee + distance_cost, 2)
    resolved_hub_name = wh.name if wh else (data.hub_name or None)

    return VendorRecurringCostEstimate(
        distance_km=round(dist_km, 2),
        base_fee=base_fee,
        distance_cost=distance_cost,
        total_estimate=total_estimate,
        rate_per_km=per_km,
        distance_method=distance_method,
        resolved_hub_name=resolved_hub_name,
        pickup_source=pickup_source,
        pickup_reference=pickup_reference,
        note=_build_recurring_estimate_note(
            warehouse_name=resolved_hub_name,
            warehouse_source=warehouse_source,
            pickup_source=pickup_source,
            pickup_reference=pickup_reference,
            distance_method=distance_method,
        ),
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


def _ticket_response(ticket: VendorSupportTicket) -> VendorSupportTicketResponse:
    return VendorSupportTicketResponse(
        id=f"TK-{str(ticket.id).split('-')[0].upper()}",
        backend_id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        order_id=str(ticket.order_id) if ticket.order_id else None,
        created=ticket.created_at.strftime("%b %d, %Y"),
        priority=ticket.priority,
        status=ticket.status,
        replies=[
            VendorSupportReplyResponse(
                from_name=reply.from_name,
                message=reply.message,
                time=reply.created_at.strftime("%b %d, %Y %I:%M %p"),
            )
            for reply in ticket.replies
        ],
    )


async def get_vendor_dashboard(db: AsyncSession, user: User) -> VendorDashboardResponse:
    _ensure_vendor(user)
    orders = await _orders_for_vendor(db, user)
    driver_names, driver_phones, vehicle_codes, customer_names, customer_phones = await _resolve_assignment_maps(db, orders)
    analytics = _analytics(orders)
    status_keys = [_status_key(order.status) for order in orders]
    current_month = datetime.now().strftime("%Y-%m")

    monthly_spend = sum(
        order.total_amount
        for order in orders
        if order.created_at.strftime("%Y-%m") == current_month
    )

    # Fetch real wallet balance from WalletTransaction table
    from app.services.wallet_service import get_wallet_balance
    wallet_balance = await get_wallet_balance(db, user.id)

    invoices = _invoice_summary(orders, credit_balance=wallet_balance)

    stats = VendorStats(
        total_shipments=len(orders),
        active_shipments=sum(1 for key in status_keys if key == "transit"),
        pending_shipments=sum(1 for key in status_keys if key == "pending"),
        delivered_shipments=sum(1 for key in status_keys if key == "delivered"),
        cancelled_shipments=sum(1 for key in status_keys if key == "cancelled"),
        monthly_spend=monthly_spend,
        outstanding_amount=sum(invoice.amount - invoice.paid for invoice in invoices.invoices if invoice.status != "Paid"),
        paid_this_month=invoices.total_paid_this_month,
        credit_balance=round(wallet_balance, 2),
    )

    return VendorDashboardResponse(
        profile=_profile(user),
        stats=stats,
        recent_shipments=[
            _shipment(
                order,
                driver_name=driver_names.get(order.assigned_driver_id),
                driver_phone=driver_phones.get(order.assigned_driver_id),
                vehicle_code=vehicle_codes.get(order.assigned_vehicle_id),
                customer_name=customer_names.get(order.customer_id),
                customer_phone=customer_phones.get(order.customer_id),
            )
            for order in orders[:5]
        ],
        analytics=analytics,
        invoices=invoices,
    )


async def get_vendor_shipments(db: AsyncSession, user: User) -> VendorShipmentsResponse:
    _ensure_vendor(user)
    orders = await _orders_for_vendor(db, user)
    driver_names, driver_phones, vehicle_codes, customer_names, customer_phones = await _resolve_assignment_maps(db, orders)
    return VendorShipmentsResponse(
        shipments=[
            _shipment(
                order,
                driver_name=driver_names.get(order.assigned_driver_id),
                driver_phone=driver_phones.get(order.assigned_driver_id),
                vehicle_code=vehicle_codes.get(order.assigned_vehicle_id),
                customer_name=customer_names.get(order.customer_id),
                customer_phone=customer_phones.get(order.customer_id),
            )
            for order in orders
        ]
    )


async def get_vendor_settings(user: User) -> VendorSettingsResponse:
    _ensure_vendor(user)
    return VendorSettingsResponse(
        settings=VendorSettings(
            company_name=user.company_name or user.name,
            tax_id=user.tax_id or "",
            contact_person=user.contact_person or user.name,
            phone=user.business_phone or user.phone,
            email=user.business_email or user.email,
            address=user.address,
            notification_prefs={
                "email": user.notifications_email,
                "sms": user.notifications_sms,
                "push": user.notifications_push,
                "orderUpdates": user.notifications_push,
                "invoiceAlerts": user.notifications_email,
                "promotions": user.notifications_promo,
            },
        )
    )


async def update_vendor_settings(
    db: AsyncSession, user: User, data: VendorSettings
) -> VendorSettingsResponse:
    _ensure_vendor(user)
    user.company_name = data.company_name or user.company_name or user.name
    user.tax_id = data.tax_id or user.tax_id
    user.contact_person = data.contact_person or user.contact_person or user.name
    user.business_email = data.email or user.business_email or user.email
    user.business_phone = data.phone
    user.phone = data.phone or user.phone
    user.address = data.address
    user.notifications_email = data.notification_prefs.get("email", True)
    user.notifications_sms = data.notification_prefs.get("sms", bool(user.phone))
    user.notifications_push = data.notification_prefs.get("push", True)
    user.notifications_promo = data.notification_prefs.get("promotions", False)
    db.add(user)
    await db.flush()
    return await get_vendor_settings(user)


async def get_vendor_damage_reports(
    db: AsyncSession, user: User
) -> VendorDamageReportsResponse:
    _ensure_vendor(user)
    reports = (
        await db.execute(
            select(DamageReportModel)
            .where(DamageReportModel.customer_id == user.id)
            .order_by(DamageReportModel.created_at.desc())
        )
    ).scalars().all()
    return VendorDamageReportsResponse(
        reports=[
            VendorDamageReport(
                id=report.reference_code,
                order_id=str(report.order_id) if report.order_id else "",
                description=report.description,
                photos=report.photos or [],
                status=report.status,
                qr_code=report.qr_code,
                created_at=report.created_at.isoformat(),
            )
            for report in reports
        ]
    )


async def create_vendor_damage_report(
    db: AsyncSession, user: User, data: VendorDamageReportCreate
) -> VendorDamageReport:
    _ensure_vendor(user)
    report = DamageReportModel(
        reference_code=f"VDR-{uuid.uuid4().hex[:6].upper()}",
        customer_id=user.id,
        order_id=uuid.UUID(data.order_id) if data.order_id else None,
        description=data.description,
        photos=data.photos,
        status="reported",
        qr_code=f"QR-{uuid.uuid4().hex[:8].upper()}",
    )
    db.add(report)
    await db.flush()
    return VendorDamageReport(
        id=report.reference_code,
        order_id=str(report.order_id) if report.order_id else "",
        description=report.description,
        photos=report.photos or [],
        status=report.status,
        qr_code=report.qr_code,
        created_at=report.created_at.isoformat() if report.created_at else datetime.now().isoformat(),
    )


async def list_team_members(db: AsyncSession, user: User) -> list[VendorTeamMemberResponse]:
    _ensure_vendor(user)
    rows = (
        await db.execute(
            select(VendorTeamMember)
            .where(VendorTeamMember.vendor_id == user.id)
            .order_by(VendorTeamMember.created_at.desc())
        )
    ).scalars().all()
    return [VendorTeamMemberResponse.model_validate(row) for row in rows]


async def create_team_member(
    db: AsyncSession, user: User, data: VendorTeamMemberCreate
) -> VendorTeamMemberResponse:
    _ensure_vendor(user)
    member = VendorTeamMember(
        vendor_id=user.id,
        name=data.name,
        email=data.email.lower(),
        role=data.role,
        status="Invited",
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return VendorTeamMemberResponse.model_validate(member)


async def delete_team_member(db: AsyncSession, user: User, member_id: uuid.UUID) -> None:
    _ensure_vendor(user)
    member = (
        await db.execute(
            select(VendorTeamMember).where(
                VendorTeamMember.id == member_id,
                VendorTeamMember.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
    await db.delete(member)


async def list_api_keys(db: AsyncSession, user: User) -> list[VendorApiKeyResponse]:
    _ensure_vendor(user)
    rows = (
        await db.execute(
            select(VendorApiKey)
            .where(VendorApiKey.vendor_id == user.id)
            .order_by(VendorApiKey.created_at.desc())
        )
    ).scalars().all()
    return [_api_key_response(row) for row in rows]


async def create_api_key(
    db: AsyncSession, user: User, data: VendorApiKeyCreate
) -> VendorApiKeyResponse:
    _ensure_vendor(user)
    api_key = VendorApiKey(vendor_id=user.id, name=data.name)
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)
    return _api_key_response(api_key)


async def revoke_api_key(db: AsyncSession, user: User, key_id: uuid.UUID) -> VendorApiKeyResponse:
    _ensure_vendor(user)
    api_key = (
        await db.execute(
            select(VendorApiKey).where(
                VendorApiKey.id == key_id,
                VendorApiKey.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    api_key.status = "Revoked"
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)
    return _api_key_response(api_key)


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


async def list_bulk_uploads(db: AsyncSession, user: User) -> list[VendorBulkUploadResponse]:
    _ensure_vendor(user)
    rows = (
        await db.execute(
            select(VendorBulkUpload)
            .where(VendorBulkUpload.vendor_id == user.id)
            .order_by(VendorBulkUpload.created_at.desc())
        )
    ).scalars().all()
    return [_bulk_upload_response(row) for row in rows]


async def create_bulk_upload(
    db: AsyncSession, user: User, data: VendorBulkUploadCreate
) -> VendorBulkUploadResponse:
    _ensure_vendor(user)
    upload = VendorBulkUpload(
        vendor_id=user.id,
        filename=data.filename,
        file_size_kb=data.file_size_kb,
        orders=data.orders,
        status=data.status,
        errors=data.errors,
        scheduled_for=data.scheduled_for,
    )
    db.add(upload)
    await db.flush()
    await db.refresh(upload)
    return _bulk_upload_response(upload)


async def update_bulk_upload(
    db: AsyncSession, user: User, upload_id: uuid.UUID, data: VendorBulkUploadUpdate
) -> VendorBulkUploadResponse:
    _ensure_vendor(user)
    upload = (
        await db.execute(
            select(VendorBulkUpload).where(
                VendorBulkUpload.id == upload_id,
                VendorBulkUpload.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulk upload not found")
    if data.status is not None:
        upload.status = data.status
    if data.errors is not None:
        upload.errors = data.errors
    if data.scheduled_for is not None:
        upload.scheduled_for = data.scheduled_for
    db.add(upload)
    await db.flush()
    await db.refresh(upload)
    return _bulk_upload_response(upload)


async def list_support_tickets(db: AsyncSession, user: User) -> list[VendorSupportTicketResponse]:
    _ensure_vendor(user)
    rows = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.vendor_id == user.id)
            .order_by(VendorSupportTicket.created_at.desc())
        )
    ).scalars().all()
    return [_ticket_response(row) for row in rows]


async def create_support_ticket(
    db: AsyncSession, user: User, data: VendorSupportTicketCreate
) -> VendorSupportTicketResponse:
    _ensure_vendor(user)
    order_id = uuid.UUID(data.shipment_id) if data.shipment_id else None
    ticket = VendorSupportTicket(
        vendor_id=user.id,
        order_id=order_id,
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        status="Open",
    )
    db.add(ticket)
    await db.flush()
    reply = VendorSupportReply(ticket_id=ticket.id, from_name="You", message=data.description)
    db.add(reply)
    await db.flush()
    from app.services import ai_support_service

    await ai_support_service.sync_vendor_ticket_to_support_ticket(
        db=db,
        vendor=user,
        vendor_ticket=ticket,
    )
    result = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.id == ticket.id)
        )
    ).scalar_one()
    return _ticket_response(result)


async def reply_support_ticket(
    db: AsyncSession, user: User, ticket_id: uuid.UUID, data: VendorSupportReplyCreate
) -> VendorSupportTicketResponse:
    _ensure_vendor(user)
    ticket = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(
                VendorSupportTicket.id == ticket_id,
                VendorSupportTicket.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    if ticket.status == "Resolved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This support ticket is already resolved and the chat is closed.",
        )
    reply = VendorSupportReply(ticket_id=ticket.id, from_name="You", message=data.message)
    db.add(reply)
    await db.flush()
    from app.services import ai_support_service

    await ai_support_service.sync_vendor_ticket_to_support_ticket(
        db=db,
        vendor=user,
        vendor_ticket=ticket,
    )
    refreshed = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(VendorSupportTicket.id == ticket.id)
        )
    ).scalar_one()
    return _ticket_response(refreshed)


async def resolve_support_ticket(
    db: AsyncSession, user: User, ticket_id: uuid.UUID
) -> VendorSupportTicketResponse:
    _ensure_vendor(user)
    ticket = (
        await db.execute(
            select(VendorSupportTicket)
            .options(selectinload(VendorSupportTicket.replies))
            .where(
                VendorSupportTicket.id == ticket_id,
                VendorSupportTicket.vendor_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    ticket.status = "Resolved"
    db.add(ticket)
    await db.flush()
    from app.services import ai_support_service

    await ai_support_service.sync_vendor_ticket_to_support_ticket(
        db=db,
        vendor=user,
        vendor_ticket=ticket,
    )
    await db.refresh(ticket, attribute_names=["replies"])
    return _ticket_response(ticket)


async def pay_invoice(
    db: AsyncSession, user: User, order_id: uuid.UUID, data: VendorInvoicePayRequest
) -> VendorInvoiceRecord:
    _ensure_vendor(user)
    order = (
        await db.execute(
            select(Order).where(Order.id == order_id, Order.customer_id == user.id)
        )
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if order.payment_status == "paid":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice already paid")

    outstanding = max(float(order.total_amount or 0.0) - float(order.paid_amount or 0.0), 0.0)
    if outstanding <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice already settled")

    payment_amount = min(float(data.amount or 0.0), outstanding)
    if payment_amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount must be greater than zero")

    from app.services import finance_service

    await finance_service.record_order_payment(
        db=db,
        order_id=order.id,
        amount=payment_amount,
        payment_mode="ONLINE",
        payment_method=data.payment_method,
        payment_ref=None,
        collected_by_user=None,
        notes="Vendor invoice payment",
    )

    await db.flush()
    await db.refresh(order)
    return _invoice_record(order, datetime.now())
