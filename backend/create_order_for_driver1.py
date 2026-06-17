"""
Create a test order assigned to driver1@gmail.com for testing.
"""

import asyncio
import sys
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import select

sys.path.insert(0, ".")

from app.database import AsyncSessionLocal as SessionLocal
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.logistics import LogisticsVehicle


async def create_order_for_driver1():
    """Create test order for driver1@gmail.com."""
    async with SessionLocal() as db:
        # Get driver1
        result = await db.execute(
            select(User).where(User.email == "driver1@gmail.com")
        )
        driver = result.scalar_one_or_none()

        if not driver:
            print("Error: driver1@gmail.com not found in database!")
            return None

        print(f"Found driver: {driver.name} (ID: {driver.id})")
        print(f"Warehouse: {driver.warehouse_id}")

        # Get a vehicle
        vehicle_result = await db.execute(select(LogisticsVehicle).limit(1))
        vehicle = vehicle_result.scalar_one_or_none()

        if not vehicle:
            print("Error: No vehicles found!")
            return None

        print(f"Using vehicle: {vehicle.code} ({vehicle.license_plate})")

        # Create test order
        tracking_code = f"TEST-DRV1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        order = Order(
            tracking_code=tracking_code,
            status="ASSIGNED",
            cargo_type="Parcel",
            vehicle_type="Van",
            order_type="PARCEL_DELIVERY",
            customer_id=driver.id,
            warehouse_id=driver.warehouse_id,
            pickup_addr="Warehouse Mumbai, 400001",
            delivery_addr="Customer Address, Andheri West, Mumbai 400053",
            delivery_lat=19.1136,
            delivery_lng=72.8697,
            base_amount=1500.00,
            vehicle_amount=500.00,
            labor_amount=300.00,
            materials_amount=0.00,
            packing_amount=200.00,
            platform_fee=50.00,
            tax_amount=250.00,
            total_amount=2500.00,
            paid_amount=0.00,
            payment_mode="COD",
            payment_status="pending",
            scheduled_at=datetime.now() + timedelta(hours=1),
            service_time_block="09:00-12:00",
            assigned_driver_id=driver.id,
            assigned_vehicle_id=vehicle.id,
        )

        db.add(order)
        await db.flush()

        # Add order items
        items = [
            OrderItem(
                order_id=order.id,
                sku="TEST-SKU-001",
                quantity=3,
            ),
            OrderItem(
                order_id=order.id,
                sku="TEST-SKU-002",
                quantity=2,
            ),
        ]

        for item in items:
            db.add(item)

        await db.commit()
        await db.refresh(order)

        print(f"\n[SUCCESS] Test order created!")
        print(f"  Tracking Code: {tracking_code}")
        print(f"  Order ID: {order.id}")
        print(f"  Status: {order.status}")
        print(f"  Assigned Driver: driver1@gmail.com")
        print(f"  Assigned Vehicle: {vehicle.code}")
        print(f"  Total Amount: Rs.{order.total_amount}")
        print(f"  Payment Mode: {order.payment_mode}")

        return order


if __name__ == "__main__":
    asyncio.run(create_order_for_driver1())
