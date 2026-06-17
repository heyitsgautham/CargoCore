"""
Fix vehicle documents that have vehicle CODE as entity_id.
This script converts vehicle codes to vehicle UUIDs in the logistics_documents table.
Run this after updating the codebase to use vehicle UUIDs instead of codes.
"""
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.document import LogisticsDocument
from app.models.logistics import LogisticsVehicle


async def fix_vehicle_documents():
    """Fix vehicle documents to use vehicle UUID instead of vehicle code."""
    async with AsyncSessionLocal() as db:
        print("Starting vehicle document migration...")

        # Get all vehicles
        vehicles_result = await db.execute(select(LogisticsVehicle))
        vehicles = vehicles_result.scalars().all()

        # Create a map of vehicle code -> vehicle UUID
        vehicle_code_to_uuid = {vehicle.code: str(vehicle.id) for vehicle in vehicles}
        print(f"Found {len(vehicle_code_to_uuid)} vehicles in database")

        # Get all vehicle documents
        docs_result = await db.execute(
            select(LogisticsDocument).where(LogisticsDocument.entity_type == "VEHICLE")
        )
        vehicle_docs = docs_result.scalars().all()
        print(f"Found {len(vehicle_docs)} vehicle documents to check")

        fixed_count = 0
        skipped_count = 0

        for doc in vehicle_docs:
            # Check if entity_id is a vehicle code (not a UUID)
            # UUIDs have dashes and are 36 characters long
            if doc.entity_id in vehicle_code_to_uuid:
                # This is a vehicle code, convert it to UUID
                new_uuid = vehicle_code_to_uuid[doc.entity_id]
                old_code = doc.entity_id
                doc.entity_id = new_uuid
                db.add(doc)
                fixed_count += 1
                print(f"  ✓ Fixed document {doc.id}: {old_code} -> {new_uuid}")
            elif "-" in doc.entity_id and len(doc.entity_id) == 36:
                # This looks like a UUID, skip it
                skipped_count += 1
            else:
                # Unknown format, warn
                print(f"  ⚠ Warning: Document {doc.id} has unknown entity_id format: {doc.entity_id}")

        await db.commit()

        print("\n" + "="*60)
        print("Migration completed!")
        print(f"  Fixed: {fixed_count} documents")
        print(f"  Skipped (already UUID): {skipped_count} documents")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(fix_vehicle_documents())
