"""
Create a test order for driver app end-to-end testing.

Usage:
    python create_test_order.py
"""

import asyncio
import sys
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import select

# Add backend to path
sys.path.insert(0, ".")

from app.database import AsyncSessionLocal as SessionLocal
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.logistics import LogisticsVehicle


async def get_or_create_test_driver():
    """Get or create a test driver user."""
    async with SessionLocal() as db:
        # Check if test driver exists
        result = await db.execute(
            select(User).where(User.email == "driver.test@cargocore.com")
        )
        driver = result.scalar_one_or_none()

        if not driver:
            print("❌ Test driver not found. Creating one...")
            from app.models.user import Role

            # Get DRIVER role
            role_result = await db.execute(select(Role).where(Role.name == "DRIVER"))
            driver_role = role_result.scalar_one_or_none()

            if not driver_role:
                print("❌ DRIVER role not found in database")
                return None

            # Create test driver
            from passlib.context import CryptContext

            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

            driver = User(
                id=uuid4(),
                email="driver.test@cargocore.com",
                name="Test Driver",
                phone="+91 98765 43210",
                password_hash=pwd_context.hash("Test@123"),
                role_id=driver_role.id,
                role=driver_role,
            )
            db.add(driver)
            await db.commit()
            await db.refresh(driver)
            print(f"✅ Created test driver: {driver.email}")

        return driver


async def get_test_vehicle():
    """Get a test vehicle."""
    async with SessionLocal() as db:
        result = await db.execute(select(LogisticsVehicle).limit(1))
        vehicle = result.scalar_one_or_none()

        if not vehicle:
            print("❌ No vehicles found in database")
            return None

        return vehicle


async def create_test_order(driver, vehicle):
    """Create a test order assigned to the driver."""
    async with SessionLocal() as db:
        tracking_code = f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        order = Order(
            tracking_code=tracking_code,
            status="ASSIGNED",
            cargo_type="Parcel",
            vehicle_type="Van",
            order_type="PARCEL_DELIVERY",
            customer_name="Test Customer",
            customer_phone="+91 98765 99999",
            customer_id=driver.id,  # Using driver as customer for testing
            pickup_addr="Test Warehouse, Mumbai 400001",
            delivery_addr="Test Delivery Address, Andheri West, Mumbai 400053",
            delivery_lat=19.1136,
            delivery_lng=72.8697,
            total_weight=5.0,
            total_volume=2.0,
            total_amount=1500.00,
            paid_amount=0.00,
            payment_mode="COD",
            payment_status="PENDING",
            scheduled_at=datetime.now() + timedelta(hours=1),
            delivery_deadline=datetime.now() + timedelta(days=1),
            service_time_block="09:00-12:00",
            assigned_driver_id=driver.id,
            assigned_vehicle_id=vehicle.id,
            assigned_vehicle_code=f"{vehicle.code} · {vehicle.license_plate}",
        )

        db.add(order)
        await db.flush()

        # Add order items
        items = [
            OrderItem(
                order_id=order.id,
                sku="TEST-ITEM-001",
                name="Test Package 1",
                quantity=2,
                unit_price=500.00,
                subtotal=1000.00,
            ),
            OrderItem(
                order_id=order.id,
                sku="TEST-ITEM-002",
                name="Test Package 2",
                quantity=1,
                unit_price=500.00,
                subtotal=500.00,
            ),
        ]

        for item in items:
            db.add(item)

        await db.commit()
        await db.refresh(order)

        print(f"\n✅ Test order created successfully!")
        print(f"   Tracking Code: {tracking_code}")
        print(f"   Order ID: {order.id}")
        print(f"   Status: {order.status}")
        print(f"   Assigned Driver: {driver.email}")
        print(f"   Assigned Vehicle: {vehicle.code}")
        print(f"   Delivery Address: {order.delivery_addr}")
        print(f"   Total Amount: ₹{order.total_amount}")
        print(f"   Payment Mode: {order.payment_mode}")

        return order


async def main():
    print("🚀 Creating test order for driver app testing...\n")

    driver = await get_or_create_test_driver()
    if not driver:
        print("❌ Failed to get/create test driver")
        return

    vehicle = await get_test_vehicle()
    if not vehicle:
        print("❌ Failed to get test vehicle")
        return

    order = await create_test_order(driver, vehicle)

    print("\n📱 Driver App Login Credentials:")
    print(f"   Email: driver.test@cargocore.com")
    print(f"   Password: Test@123")
    print("\n🔍 Now test the complete flow:")
    print("   1. Login with driver credentials")
    print("   2. Complete pre-shift safety checks")
    print("   3. Bind vehicle")
    print("   4. Complete vehicle inspection")
    print("   5. Select job type and accept order")
    print("   6. Verify load")
    print("   7. Start route and navigate")
    print("   8. Mark arrival at customer location")
    print("   9. Complete delivery execution")
    print("  10. Upload proof of delivery (photo + signature)")
    print("  11. Verify order status changed to DELIVERED")


if __name__ == "__main__":
    asyncio.run(main())
