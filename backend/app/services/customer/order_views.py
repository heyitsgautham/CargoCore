"""Turn orders into the shapes the customer portal shows: status labels, tracking logs, dashboard rows."""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.user import User
from app.schemas.auth import UserProfile
from app.schemas.customer import (
    CustomerDashboardActiveMove,
    CustomerDashboardCostSummary,
    CustomerDashboardDriver,
    CustomerDashboardOrder,
)


def ui_status(status_value: str) -> str:
    mapping = {
        "DRAFT": "pending",
        "CONFIRMED": "pending",
        "ASSIGNED": "dispatched",
        "IN_TRANSIT": "in-transit",
        "DELIVERED": "delivered",
        "CLOSED": "delivered",
        "CANCELLED": "cancelled",
    }
    return mapping.get(status_value.upper(), status_value.lower())


def cargo_type(order: Order) -> str:
    if order.cargo_type:
        return order.cargo_type
    return "Household Goods" if order.order_type.upper() == "INDIVIDUAL" else "Shipment"


def service_otp(order: Order) -> str:
    if order.service_otp:
        return order.service_otp
    digits = "".join(ch for ch in order.tracking_code if ch.isdigit())
    return (digits[-4:] or "0000").zfill(4)


def service_time_block(order: Order) -> str:
    if order.service_time_block:
        return order.service_time_block
    if order.scheduled_at:
        return order.scheduled_at.strftime("%I:%M %p")
    return "TBD"


def progress_for_status(status_value: str) -> int:
    mapping = {
        "pending": 15,
        "dispatched": 40,
        "in-transit": 65,
        "delivered": 100,
        "cancelled": 0,
    }
    return mapping.get(ui_status(status_value), 0)


def eta_label(order: Order) -> str:
    if order.status in {"DELIVERED", "CLOSED"}:
        return f"Delivered {fmt(order.delivered_at or order.updated_at)}".strip()
    if order.status == "CANCELLED":
        return "Cancelled"
    if order.scheduled_at:
        return order.scheduled_at.strftime("%d %b, %I:%M %p")
    return "TBD"


def fmt(dt) -> str:
    if dt is None:
        return ""
    return dt.strftime("%d %b %Y, %I:%M %p")


def tracking_log(order: Order, qc_checked_at=None) -> list[dict]:
    created = fmt(order.created_at)
    ws = order.warehouse_substatus or ""
    # Backfill display: confirmed orders with no substatus yet still show as queued
    if not ws and order.status in {"CONFIRMED", "ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        ws = "AWAITING_PICK"

    AFTER_AWAITING = {"PICKING", "PICKED", "PACKING", "PACKED", "QC_PASSED", "READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_PICKED   = {"PACKING", "PACKED", "QC_PASSED", "READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_PACKING  = {"PACKED", "QC_PASSED", "READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_QC       = {"READY_FOR_DISPATCH", "ON_DOCK", "DISPATCHED"}
    AFTER_READY    = {"ON_DOCK", "DISPATCHED"}

    entries = [
        {"event": "Order created", "time": created, "icon": "receipt_long", "color": "blue"},
    ]

    if order.status in {"CONFIRMED", "ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        entries.append({"event": "Order confirmed", "time": created, "icon": "check_circle", "color": "green"})

    # Warehouse: Queued for picking
    if ws in AFTER_AWAITING | {"AWAITING_PICK"}:
        entries.append({
            "event": "Queued for Picking",
            "description": "Your order has been queued at the warehouse and is awaiting a pick team.",
            "time": created,
            "icon": "hourglass_empty",
            "color": "amber",
        })

    # Warehouse: On hold
    if ws == "ON_HOLD":
        entries.append({
            "event": "Order On Hold",
            "description": "Your order is temporarily on hold — usually due to insufficient labourers.",
            "time": fmt(order.updated_at),
            "icon": "pause_circle",
            "color": "red",
        })

    # Warehouse: Picking started
    if ws in AFTER_AWAITING:
        entries.append({
            "event": "Picking started",
            "description": "Warehouse staff have started gathering your items from the shelves.",
            "time": fmt(order.picking_started_at) or "In progress",
            "icon": "shopping_basket",
            "color": "blue",
        })

    # Warehouse: Picking completed
    if ws in AFTER_PICKED | {"PICKED"}:
        entries.append({
            "event": "Picking completed",
            "description": "All items have been gathered and are ready to be packed.",
            "time": fmt(order.picking_completed_at) or "Completed",
            "icon": "inventory_2",
            "color": "cyan",
        })

    # Warehouse: Packing started
    if ws in AFTER_PICKED:
        entries.append({
            "event": "Packing started",
            "description": "Your items are being boxed and prepared for dispatch.",
            "time": fmt(order.packing_started_at) or "In progress",
            "icon": "package_2",
            "color": "amber",
        })

    # Warehouse: Packing completed
    if ws in AFTER_PACKING | {"PACKED"}:
        entries.append({
            "event": "Packing completed",
            "description": "All items are securely packed and awaiting quality check.",
            "time": fmt(order.packing_completed_at) or "Completed",
            "icon": "deployed_code",
            "color": "green",
        })

    # Warehouse: Quality check passed
    if ws in AFTER_QC | {"QC_PASSED"}:
        entries.append({
            "event": "Quality check passed",
            "description": "Your shipment has passed all quality and safety checks.",
            "time": fmt(qc_checked_at) or "Verified",
            "icon": "verified",
            "color": "green",
        })

    # Warehouse: Ready for dispatch / on dock
    if ws in AFTER_READY | {"READY_FOR_DISPATCH"} or order.status in {"ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        entries.append({
            "event": "Ready for dispatch",
            "description": "Your shipment is on the loading dock and ready to be picked up.",
            "time": fmt(order.updated_at) if ws in AFTER_READY | {"READY_FOR_DISPATCH"} else created,
            "icon": "local_shipping",
            "color": "blue",
        })

    # Driver assigned
    if order.status in {"ASSIGNED", "IN_TRANSIT", "DELIVERED", "CLOSED"}:
        entries.append({
            "event": "Driver assigned",
            "description": "A driver and vehicle have been assigned to your shipment.",
            "time": fmt(order.updated_at),
            "icon": "person_pin_circle",
            "color": "blue",
        })

    # In transit
    if ws == "DISPATCHED" or order.status in {"IN_TRANSIT", "DELIVERED", "CLOSED"}:
        entries.append({
            "event": "Shipment in transit",
            "description": "Your shipment is on its way to the destination.",
            "time": fmt(order.updated_at) if ws == "DISPATCHED" else created,
            "icon": "local_shipping",
            "color": "green",
        })

    # Delivered
    if order.status in {"DELIVERED", "CLOSED"}:
        entries.append({
            "event": "Delivery completed",
            "description": "Your order has been delivered successfully.",
            "time": fmt(order.delivered_at or order.updated_at),
            "icon": "where_to_vote",
            "color": "green",
        })

    # Cancelled
    if order.status == "CANCELLED":
        entries.append({
            "event": "Order cancelled",
            "description": order.cancel_reason or "No reason provided",
            "time": fmt(order.updated_at),
            "icon": "cancel",
            "color": "red",
        })

    return entries


def to_dashboard_order(order: Order) -> CustomerDashboardOrder:
    return CustomerDashboardOrder(
        id=order.id,
        tracking_code=order.tracking_code,
        order_type=order.order_type,
        status=order.status,
        ui_status=ui_status(order.status),
        pickup_addr=order.pickup_addr,
        delivery_addr=order.delivery_addr,
        scheduled_at=order.scheduled_at,
        created_at=order.created_at,
        vehicle_type=order.vehicle_type or order.order_type.lower(),
        total_amount=order.total_amount,
    )


def to_active_move(order: Order, driver_lookup: dict | None = None) -> CustomerDashboardActiveMove:
    driver_payload = (driver_lookup or {}).get(order.assigned_driver_id)
    return CustomerDashboardActiveMove(
        id=order.id,
        tracking_code=order.tracking_code,
        status=order.status,
        ui_status=ui_status(order.status),
        pickup_addr=order.pickup_addr,
        delivery_addr=order.delivery_addr,
        scheduled_at=order.scheduled_at,
        created_at=order.created_at,
        vehicle_type=order.vehicle_type or order.order_type.lower(),
        cargo_type=cargo_type(order),
        progress=progress_for_status(order.status),
        eta_label=eta_label(order),
        service_otp=service_otp(order),
        service_time_block=service_time_block(order),
        labor_count=order.labor_count,
        driver=CustomerDashboardDriver(
            name=driver_payload["name"] if driver_payload else None,
            phone=driver_payload["phone"] if driver_payload else None,
            rating=driver_payload["rating"] if driver_payload else None,
        ),
        cost=CustomerDashboardCostSummary(
            base=order.base_amount,
            vehicle=order.vehicle_amount,
            labor=order.labor_amount,
            materials=order.materials_amount,
            packing=order.packing_amount,
            platform_fee=order.platform_fee,
            taxes=order.tax_amount,
            total=order.total_amount,
        ),
    )


async def build_driver_lookup(db: AsyncSession, orders: list[Order]) -> dict:
    driver_ids = {order.assigned_driver_id for order in orders if order.assigned_driver_id}
    if not driver_ids:
        return {}

    rows = (
        await db.execute(
            select(User.id, User.name, User.phone).where(User.id.in_(driver_ids))
        )
    ).all()
    return {
        row.id: {
            "name": row.name,
            "phone": row.phone,
            "rating": None,
        }
        for row in rows
    }


def to_user_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        name=user.name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        address=user.address,
        role=user.role.name,
        is_active=user.is_active,
        created_at=user.created_at,
    )
