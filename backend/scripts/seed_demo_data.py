"""Fill an empty development database with the demo logistics world.

Creates the reserved Logistics Manager account, then three hubs with their
managers, a dispatcher, two drivers, vehicles, orders, stock and the equipment
ledger. It then adds a demo customer, an approved demo vendor, and live floor
work at the North-East Hub: labourers, docks, packing stations and orders at
every warehouse stage. A database that already has a hub is left alone.

    cd backend
    DEMO_STAFF_PASSWORD='choose-one' python -m scripts.seed_demo_data

Every demo account gets DEMO_STAFF_PASSWORD. Without it the script generates
one and prints it once.
"""

import asyncio
import os
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.labour import Labourer
from app.models.order import Order, OrderItem
from app.models.warehouse import LoadingDock, PackingStation, Warehouse
from app.services.admin_bootstrap import ensure_logistic_manager_account
from app.services.logistics.lookups import _get_or_create_user
from app.services.logistics.seed import ensure_logistics_seed_data

# (tracking code, order type, status, warehouse substatus, priority, cargo)
FLOOR_ORDERS = [
    ("QC-DEMO101", "INDIVIDUAL", "PENDING", None, "NORMAL", "Household goods"),
    ("QC-DEMO102", "VENDOR", "CONFIRMED", "AWAITING_INBOUND", "HIGH", "Electronics"),
    ("QC-DEMO103", "INDIVIDUAL", "CONFIRMED", "AWAITING_PICK", "NORMAL", "Furniture"),
    ("QC-DEMO104", "VENDOR", "CONFIRMED", "AWAITING_PICK", "URGENT", "Retail goods"),
    ("QC-DEMO105", "INDIVIDUAL", "CONFIRMED", "PICKING", "NORMAL", "Appliances"),
    ("QC-DEMO106", "VENDOR", "CONFIRMED", "PICKED", "HIGH", "Electronics"),
    ("QC-DEMO107", "INDIVIDUAL", "CONFIRMED", "PACKING", "NORMAL", "Household goods"),
    ("QC-DEMO108", "VENDOR", "CONFIRMED", "PACKED", "NORMAL", "Retail goods"),
    ("QC-DEMO109", "INDIVIDUAL", "CONFIRMED", "QC_PASSED", "HIGH", "Furniture"),
    ("QC-DEMO110", "VENDOR", "ASSIGNED", "READY_FOR_DISPATCH", "NORMAL", "Retail goods"),
    ("QC-DEMO111", "INDIVIDUAL", "DELIVERED", "DISPATCHED", "NORMAL", "Household goods"),
]


async def seed_floor_activity(db: AsyncSession, staff_password: str) -> None:
    """Add a customer, a vendor and in-progress floor work to the North-East Hub."""
    hub = (await db.execute(select(Warehouse).where(Warehouse.name == "North-East Hub"))).scalar_one()
    customer = await _get_or_create_user(
        db, role_name="INDIVIDUAL", email="demo.individual@example.com", username="demo_individual",
        name="Priya Sharma", phone="+91 98450 11223", password=staff_password,
    )
    vendor = await _get_or_create_user(
        db, role_name="VENDOR", email="demo.vendor@example.com", username="demo_vendor",
        name="Arjun Mehta", phone="+91 98860 44556", password=staff_password,
    )
    vendor.company_name = "Mehta Home Retail"
    vendor.approval_status = "APPROVED"

    labourers = []
    for index, (name, skills) in enumerate(
        [("Ravi Kumar", ["picking"]), ("Meena Das", ["packing"]), ("Imran Shaikh", ["loading", "picking"])],
        start=1,
    ):
        user = await _get_or_create_user(
            db, role_name="LABOURER", email=f"labourer{index}@cargocore.com", name=name,
            warehouse_id=hub.id, password=staff_password,
        )
        labourers.append(Labourer(user_id=user.id, warehouse_id=hub.id, skill_tags=skills, is_active=True))
    db.add_all(labourers)
    db.add_all([
        LoadingDock(warehouse_id=hub.id, dock_number="D1", status="FREE"),
        LoadingDock(warehouse_id=hub.id, dock_number="D2", status="MAINTENANCE"),
        PackingStation(warehouse_id=hub.id, station_number="P1", status="ACTIVE"),
        PackingStation(warehouse_id=hub.id, station_number="P2", status="CLOSED"),
    ])

    now = datetime.now(UTC)
    for offset, (code, order_type, status, substatus, priority, cargo) in enumerate(FLOOR_ORDERS):
        owner = vendor if order_type == "VENDOR" else customer
        order = Order(
            tracking_code=code, order_type=order_type, status=status, warehouse_substatus=substatus,
            priority=priority, customer_id=owner.id, warehouse_id=hub.id,
            pickup_addr=f"{12 + offset} MG Road, Bengaluru", pickup_lat=12.9716, pickup_lng=77.5946,
            delivery_addr=f"{40 + offset} Indiranagar 100 Ft Road, Bengaluru", delivery_lat=12.9719, delivery_lng=77.6412,
            cargo_type=cargo, vehicle_type="Mini Truck", labor_count=2, base_amount=2400, vehicle_amount=900,
            labor_amount=600, packing_amount=250, platform_fee=120, tax_amount=380, total_amount=4650,
            payment_mode="UPI", payment_status="paid" if status != "PENDING" else "pending",
            scheduled_at=now + timedelta(hours=offset - 4),
            delivered_at=now - timedelta(hours=2) if status == "DELIVERED" else None,
        )
        db.add(order)
        await db.flush()
        db.add_all([
            OrderItem(order_id=order.id, sku="INV-001", quantity=2, box_count=1),
            OrderItem(order_id=order.id, sku="INV-002", quantity=1, box_count=1),
        ])
    await db.flush()


async def seed(staff_password: str) -> None:
    async with AsyncSessionLocal() as db:
        if (await db.execute(select(func.count(Warehouse.id)))).scalar_one():
            print("The database already has hubs, so nothing was added.")
            return
        manager = await ensure_logistic_manager_account(db)
        await ensure_logistics_seed_data(db, manager, staff_password)
        await seed_floor_activity(db, staff_password)
        await db.commit()
        print("Demo data is in place.")


def main() -> None:
    staff_password = os.environ.get("DEMO_STAFF_PASSWORD") or secrets.token_urlsafe(12)
    asyncio.run(seed(staff_password))
    if "DEMO_STAFF_PASSWORD" not in os.environ:
        print(f"Demo staff password: {staff_password}")


if __name__ == "__main__":
    main()
