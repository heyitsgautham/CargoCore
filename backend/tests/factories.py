"""Builders for database rows that the flow tests share.

Every helper adds rows to the given session and flushes, so callers can read
generated ids straight away. Users are created with their role relationship
loaded, because services read user.role outside an async greenlet.
"""

from __future__ import annotations

import itertools
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem
from app.models.labour import Labourer
from app.models.logistics import (
    LogisticsDriverProfile,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.order import Order, OrderItem
from app.models.user import Role, User
from app.models.warehouse import LoadingDock, PackingStation, Warehouse
from app.utils.hashing import hash_password
from app.utils.jwt import create_access_token

# Fresh each run, so no fixture password is written down anywhere.
PASSWORD = secrets.token_urlsafe(12)
_counter = itertools.count(1)


def _n() -> int:
    return next(_counter)


async def role(db: AsyncSession, name: str) -> Role:
    return (await db.execute(select(Role).where(Role.name == name))).scalar_one()


async def make_warehouse(db: AsyncSession, **overrides) -> Warehouse:
    n = _n()
    warehouse = Warehouse(
        name=overrides.pop("name", f"Hub {n}"),
        address=overrides.pop("address", f"{n} Dock Road, Bengaluru"),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db.add(warehouse)
    await db.flush()
    return warehouse


async def make_user(db: AsyncSession, role_name: str, **overrides) -> User:
    n = _n()
    user_role = await role(db, role_name)
    slug = f"{role_name.lower()}.{n}"
    user = User(
        name=overrides.pop("name", f"{role_name.title()} {n}"),
        username=overrides.pop("username", slug),
        email=overrides.pop("email", f"{slug}@example.com"),
        phone=overrides.pop("phone", f"90000{n:05d}"),
        password_hash=hash_password(overrides.pop("password", PASSWORD)),
        role_id=user_role.id,
        role=user_role,
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db.add(user)
    await db.flush()
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "role": user.role.name})
    return {"Authorization": f"Bearer {token}"}


async def make_order(db: AsyncSession, customer: User, **overrides) -> Order:
    n = _n()
    items = overrides.pop("items", [("SKU-SOFA", 2)])
    order = Order(
        tracking_code=overrides.pop("tracking_code", f"QC-T{n:05d}"),
        order_type=overrides.pop("order_type", "INDIVIDUAL"),
        status=overrides.pop("status", "CONFIRMED"),
        customer_id=customer.id,
        pickup_addr=overrides.pop("pickup_addr", f"{n} Pickup Street, Bengaluru"),
        delivery_addr=overrides.pop("delivery_addr", f"{n} Delivery Avenue, Bengaluru"),
        pickup_lat=overrides.pop("pickup_lat", 12.9716),
        pickup_lng=overrides.pop("pickup_lng", 77.5946),
        delivery_lat=overrides.pop("delivery_lat", 12.9352),
        delivery_lng=overrides.pop("delivery_lng", 77.6245),
        total_amount=overrides.pop("total_amount", 1500.0),
        scheduled_at=overrides.pop("scheduled_at", datetime.now(UTC) + timedelta(hours=4)),
        **overrides,
    )
    db.add(order)
    await db.flush()
    for sku, quantity in items:
        db.add(OrderItem(order_id=order.id, sku=sku, quantity=quantity, box_count=1))
    await db.flush()
    return order


async def make_inventory_item(db: AsyncSession, warehouse: Warehouse, **overrides) -> InventoryItem:
    n = _n()
    item = InventoryItem(
        warehouse_id=warehouse.id,
        sku=overrides.pop("sku", f"SKU-{n}"),
        name=overrides.pop("name", f"Product {n}"),
        quantity_on_hand=overrides.pop("quantity_on_hand", 50),
        selling_price=overrides.pop("selling_price", 40.0),
        **overrides,
    )
    db.add(item)
    await db.flush()
    return item


async def make_labourer(db: AsyncSession, warehouse: Warehouse, **overrides) -> Labourer:
    user = await make_user(db, "LABOURER", warehouse_id=warehouse.id)
    labourer = Labourer(user_id=user.id, warehouse_id=warehouse.id, is_active=True, **overrides)
    db.add(labourer)
    await db.flush()
    return labourer


async def make_vehicle(db: AsyncSession, **overrides) -> LogisticsVehicle:
    n = _n()
    vehicle = LogisticsVehicle(
        code=overrides.pop("code", f"KA01AB{n:04d}"),
        vehicle_type=overrides.pop("vehicle_type", "Mini Truck"),
        **overrides,
    )
    db.add(vehicle)
    await db.flush()
    return vehicle


async def make_driver(db: AsyncSession, warehouse: Warehouse, **profile) -> tuple[User, LogisticsDriverProfile]:
    user = await make_user(db, "DRIVER", warehouse_id=warehouse.id)
    driver_profile = LogisticsDriverProfile(user_id=user.id, **profile)
    db.add(driver_profile)
    await db.flush()
    return user, driver_profile


@dataclass
class World:
    """One hub with a user for every role and a little of everything around it."""

    warehouse: Warehouse
    users: dict[str, User]
    order: Order
    vendor_order: Order
    inventory_item: InventoryItem
    labourer: Labourer
    vehicle: LogisticsVehicle
    driver_profile: LogisticsDriverProfile
    zone: LogisticsZone
    dock: LoadingDock
    station: PackingStation
    extra: dict = field(default_factory=dict)

    def headers(self, role_name: str) -> dict[str, str]:
        return auth_headers(self.users[role_name])


async def build_world(db: AsyncSession) -> World:
    warehouse = await make_warehouse(db, lat=12.97, lng=77.59, manager_id=None)
    users = {
        name: await make_user(db, name, warehouse_id=warehouse.id if name in {"WAREHOUSE_MANAGER", "DISPATCHER"} else None)
        for name in ("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER", "INDIVIDUAL", "VENDOR", "AI_AGENT")
    }
    users["VENDOR"].company_name = "Acme Supplies"
    users["VENDOR"].approval_status = "APPROVED"
    driver, driver_profile = await make_driver(db, warehouse, status="Active")
    users["DRIVER"] = driver
    vehicle = await make_vehicle(db)
    order = await make_order(db, users["INDIVIDUAL"], warehouse_id=warehouse.id)
    vendor_order = await make_order(
        db, users["VENDOR"], order_type="VENDOR", warehouse_id=warehouse.id, warehouse_substatus="AWAITING_PICK"
    )
    inventory_item = await make_inventory_item(db, warehouse, sku="SKU-SOFA", name="Three-seat sofa")
    labourer = await make_labourer(db, warehouse)
    zone = LogisticsZone(warehouse_id=warehouse.id, name="Zone A")
    dock = LoadingDock(warehouse_id=warehouse.id, dock_number="D1")
    station = PackingStation(warehouse_id=warehouse.id, station_number="P1")
    db.add_all([zone, dock, station])
    await db.commit()
    return World(
        warehouse=warehouse,
        users=users,
        order=order,
        vendor_order=vendor_order,
        inventory_item=inventory_item,
        labourer=labourer,
        vehicle=vehicle,
        driver_profile=driver_profile,
        zone=zone,
        dock=dock,
        station=station,
    )
