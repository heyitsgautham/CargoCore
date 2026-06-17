"""
Delete test data created for driver app testing.

Usage:
    python delete_test_data.py
"""

import asyncio
import sys
from sqlalchemy import select, delete

# Add backend to path
sys.path.insert(0, ".")

from app.database import AsyncSessionLocal as SessionLocal
from app.models.order import Order, OrderItem
from app.models.user import User


async def delete_test_orders():
    """Delete all test orders."""
    async with SessionLocal() as db:
        # Delete test order items first (foreign key constraint)
        result = await db.execute(
            select(Order).where(Order.tracking_code.like("TEST-%"))
        )
        test_orders = result.scalars().all()

        if not test_orders:
            print("ℹ️  No test orders found")
            return

        order_ids = [order.id for order in test_orders]

        # Delete order items
        await db.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))

        # Delete orders
        deleted = await db.execute(delete(Order).where(Order.id.in_(order_ids)))
        await db.commit()

        print(f"✅ Deleted {deleted.rowcount} test orders")


async def delete_test_driver():
    """Delete test driver user."""
    async with SessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == "driver.test@cargocore.com")
        )
        driver = result.scalar_one_or_none()

        if not driver:
            print("ℹ️  Test driver not found")
            return

        await db.delete(driver)
        await db.commit()
        print(f"✅ Deleted test driver: driver.test@cargocore.com")


async def main():
    print("🧹 Cleaning up test data...\n")

    await delete_test_orders()
    # Uncomment if you want to delete the test driver too
    # await delete_test_driver()

    print("\n✅ Test data cleanup complete!")


if __name__ == "__main__":
    asyncio.run(main())
