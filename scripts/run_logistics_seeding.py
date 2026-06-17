"""
Script to run complete logistics seeding including equipment ledger
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database import AsyncSessionLocal
from app.services.logistics_service import ensure_logistics_seed_data
from app.services.auth_service import ensure_logistic_manager_account


async def run_seeding():
    """Run complete logistics seeding"""
    print("Running Logistics Seeding...")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # First ensure the logistic manager account exists
            print("\n1. Ensuring Logistic Manager account exists...")
            manager = await ensure_logistic_manager_account(db)
            print(f"✓ Logistic Manager: {manager.email}")
            
            # Then seed logistics data (warehouses, vehicles, equipment, etc.)
            print("\n2. Seeding logistics data...")
            await ensure_logistics_seed_data(db, manager)
            print("✓ Logistics data seeding complete!")
            
            await db.commit()
            
            print("\n" + "=" * 60)
            print("✓ All seeding complete!")
            print("\nYou can now:")
            print("  - Login with: logisticmanager@gmail.com / 12345678")
            print("  - View equipment ledger in Reports > Inventory (Boxes/Tools)")
            
        except Exception as e:
            await db.rollback()
            print(f"\n✗ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(run_seeding())
