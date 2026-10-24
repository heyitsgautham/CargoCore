"""Vendor access checks, the vendor profile, shipment status mapping and the latest auto-debit note."""


from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsVehicle
from app.models.order import Order
from app.models.user import User
from app.schemas.auth import UserProfile
from app.schemas.vendor import (
    VendorShipmentCost,
    VendorShipmentHistoryItem,
    VendorShipmentSummary,
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
