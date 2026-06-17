"""
Script to seed equipment ledger data
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database import AsyncSessionLocal
from app.models.logistics import LogisticsEquipmentLedger
from app.models.warehouse import Warehouse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


async def seed_equipment_ledger():
    """Seed equipment ledger data"""
    print("Seeding Equipment Ledger Data...")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Check if equipment ledger is already populated
        existing_count = await db.scalar(select(func.count()).select_from(LogisticsEquipmentLedger))
        
        if existing_count > 0:
            print(f"⚠ Equipment ledger already has {existing_count} records.")
            response = input("Do you want to clear and reseed? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Aborted.")
                return
            
            # Delete existing records
            from sqlalchemy import delete
            await db.execute(delete(LogisticsEquipmentLedger))
            print(f"✓ Deleted {existing_count} existing records")
        
        # Get warehouses
        warehouses = (await db.execute(select(Warehouse))).scalars().all()
        
        if len(warehouses) < 3:
            print("✗ Not enough warehouses found in database.")
            print("  Please run the main logistics seeding first.")
            return
        
        north = warehouses[0]
        south = warehouses[1]
        west = warehouses[2]
        
        print(f"Found warehouses:")
        print(f"  - {north.name} (ID: {north.id})")
        print(f"  - {south.name} (ID: {south.id})")
        print(f"  - {west.name} (ID: {west.id})")
        
        # Create equipment ledger records
        equipment_records = [
            LogisticsEquipmentLedger(
                warehouse_id=north.id,
                item_type="Crates (Standard)",
                issued_count=450,
                returned_count=410,
                reference_code="ORD-4920",
                status="Pending Collection"
            ),
            LogisticsEquipmentLedger(
                warehouse_id=south.id,
                item_type="Thermal Blankets",
                issued_count=120,
                returned_count=120,
                reference_code="ORD-4921",
                status="Cleared"
            ),
            LogisticsEquipmentLedger(
                warehouse_id=west.id,
                item_type="Pallets (Wood)",
                issued_count=800,
                returned_count=750,
                reference_code="ORD-4925",
                status="Pending Collection"
            ),
            LogisticsEquipmentLedger(
                warehouse_id=None,
                item_type="Refrigerant Packs",
                issued_count=1800,
                returned_count=1500,
                reference_code="NET-SYS",
                status="Pending Collection"
            ),
        ]
        
        db.add_all(equipment_records)
        await db.commit()
        
        print(f"\n✓ Successfully seeded {len(equipment_records)} equipment ledger records:")
        for eq in equipment_records:
            print(f"  - {eq.item_type}: {eq.issued_count} issued, {eq.returned_count} returned")
    
    print("\n" + "=" * 60)
    print("Equipment ledger seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_equipment_ledger())
