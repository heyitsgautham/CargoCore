"""
Clear all dummy/seed data from the database.
This script removes:
- Finances (LogisticsTransaction)
- Attendance (LabourAttendance)
- Workforce (Labourer)
- RMA (LogisticsReturnCase)
- Analytics (LogisticsDailyStats, LogisticsMetric)
- History (LogisticsDailyStats)
- And all other logistics seed data
"""
import asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.labour import LabourAttendance, Labourer
from app.models.logistics import (
    LogisticsAlert,
    LogisticsChatMessage,
    LogisticsChatThread,
    LogisticsDailyStats,
    LogisticsDriverProfile,
    LogisticsEquipmentLedger,
    LogisticsEscalation,
    LogisticsMetric,
    LogisticsNotification,
    LogisticsReturnCase,
    LogisticsTask,
    LogisticsTransaction,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.document import LogisticsDocument
from app.models.inventory import InventoryItem, InventoryMovement, RestockRequest
from app.models.order import Order, OrderItem, PickedItem, DamageReport, CustomerQuote
from app.models.warehouse import (
    Warehouse,
    LoadingDock,
    PackingStation,
    QualityCheck,
    ReturnGrading,
    WarehouseZoneMetrics,
)
from app.models.vendor import VendorSupportTicket, VendorSupportReply
from app.models.user import User


async def clear_dummy_data():
    """Clear all dummy/seed data from the database."""
    async with AsyncSessionLocal() as db:
        print("Starting to clear dummy data...")

        # Order matters due to foreign key constraints
        # Delete in reverse order of creation

        print("  - Clearing LogisticsMetric...")
        await db.execute(delete(LogisticsMetric))

        print("  - Clearing LogisticsEquipmentLedger...")
        await db.execute(delete(LogisticsEquipmentLedger))

        print("  - Clearing LogisticsDocument...")
        await db.execute(delete(LogisticsDocument))

        print("  - Clearing LogisticsDailyStats (Analytics & History)...")
        await db.execute(delete(LogisticsDailyStats))

        print("  - Clearing LogisticsReturnCase (RMA)...")
        await db.execute(delete(LogisticsReturnCase))

        print("  - Clearing LogisticsEscalation...")
        await db.execute(delete(LogisticsEscalation))

        print("  - Clearing LogisticsChatMessage...")
        await db.execute(delete(LogisticsChatMessage))

        print("  - Clearing LogisticsChatThread...")
        await db.execute(delete(LogisticsChatThread))

        print("  - Clearing LogisticsTask...")
        await db.execute(delete(LogisticsTask))

        print("  - Clearing LogisticsNotification...")
        await db.execute(delete(LogisticsNotification))

        print("  - Clearing LogisticsAlert...")
        await db.execute(delete(LogisticsAlert))

        print("  - Clearing LogisticsZone...")
        await db.execute(delete(LogisticsZone))

        print("  - Clearing LogisticsTransaction (Finances)...")
        await db.execute(delete(LogisticsTransaction))

        print("  - Clearing LabourAttendance (Attendance)...")
        await db.execute(delete(LabourAttendance))

        print("  - Clearing Labourer (Workforce)...")
        await db.execute(delete(Labourer))

        # Delete tables that reference orders first
        print("  - Clearing VendorSupportReply...")
        await db.execute(delete(VendorSupportReply))

        print("  - Clearing VendorSupportTicket...")
        await db.execute(delete(VendorSupportTicket))

        print("  - Clearing QualityCheck...")
        await db.execute(delete(QualityCheck))

        print("  - Clearing ReturnGrading...")
        await db.execute(delete(ReturnGrading))

        print("  - Clearing LoadingDock...")
        await db.execute(delete(LoadingDock))

        print("  - Clearing PackingStation...")
        await db.execute(delete(PackingStation))

        print("  - Clearing DamageReport...")
        await db.execute(delete(DamageReport))

        print("  - Clearing PickedItem...")
        await db.execute(delete(PickedItem))

        print("  - Clearing OrderItem...")
        await db.execute(delete(OrderItem))

        print("  - Clearing RestockRequest...")
        await db.execute(delete(RestockRequest))

        print("  - Clearing InventoryMovement...")
        await db.execute(delete(InventoryMovement))

        print("  - Clearing InventoryItem...")
        await db.execute(delete(InventoryItem))

        print("  - Clearing CustomerQuote...")
        await db.execute(delete(CustomerQuote))

        print("  - Clearing Order...")
        await db.execute(delete(Order))

        print("  - Clearing LogisticsVehicle...")
        await db.execute(delete(LogisticsVehicle))

        print("  - Clearing LogisticsDriverProfile...")
        await db.execute(delete(LogisticsDriverProfile))

        print("  - Clearing WarehouseZoneMetrics...")
        await db.execute(delete(WarehouseZoneMetrics))

        # Delete seed users (but keep real users)
        # Seed users have specific emails ending with @cargocore.com
        print("  - Clearing seed users...")
        result = await db.execute(
            select(User).where(User.email.like('%@cargocore.com'))
        )
        seed_users = result.scalars().all()
        for user in seed_users:
            await db.delete(user)

        # Delete seed warehouses (the 3 warehouses created in seed)
        print("  - Clearing seed warehouses...")
        result = await db.execute(
            select(Warehouse).where(
                Warehouse.name.in_([
                    "North-East Hub",
                    "South Hub",
                    "West DC-04"
                ])
            )
        )
        seed_warehouses = result.scalars().all()
        for warehouse in seed_warehouses:
            await db.delete(warehouse)

        await db.commit()
        print("\nAll dummy data cleared successfully!")
        print("\nSummary:")
        print("  - Finances: Cleared")
        print("  - Attendance: Cleared")
        print("  - Workforce: Cleared")
        print("  - RMA: Cleared")
        print("  - Analytics: Cleared")
        print("  - History: Cleared")
        print("  - All logistics seed data: Cleared")


if __name__ == "__main__":
    asyncio.run(clear_dummy_data())
