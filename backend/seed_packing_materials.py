"""
Seed packing material inventory items (PKG- SKUs) into all active warehouses.
Run once: python seed_packing_materials.py

These SKUs are used by the booking flow when customers order packing materials.
Once seeded, confirm_order will check and deduct these from inventory.
If a warehouse already has these SKUs, they are skipped.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.inventory import InventoryItem
from app.models.warehouse import Warehouse

PACKING_MATERIALS = [
    {"sku": "PKG-CARTON",        "name": "Carton Boxes (Large)",  "category": "Packing Materials", "unit": "pcs",   "quantity_on_hand": 500, "safety_stock": 50,  "cost_price": 35,  "selling_price": 60},
    {"sku": "PKG-BUBBLE-WRAP",   "name": "Bubble Wrap Rolls",     "category": "Packing Materials", "unit": "rolls", "quantity_on_hand": 200, "safety_stock": 20,  "cost_price": 70,  "selling_price": 120},
    {"sku": "PKG-PLASTIC-CRATE", "name": "Plastic Crates",        "category": "Packing Materials", "unit": "pcs",   "quantity_on_hand": 100, "safety_stock": 10,  "cost_price": 120, "selling_price": 200},
    {"sku": "PKG-BLANKET",       "name": "Padded Blankets",        "category": "Packing Materials", "unit": "pcs",   "quantity_on_hand": 150, "safety_stock": 15,  "cost_price": 45,  "selling_price": 80},
    {"sku": "PKG-WARDROBE-BOX",  "name": "Wardrobe Boxes",         "category": "Packing Materials", "unit": "pcs",   "quantity_on_hand": 50,  "safety_stock": 5,   "cost_price": 200, "selling_price": 350},
    {"sku": "PKG-TAPE",          "name": "Packing Tape",           "category": "Packing Materials", "unit": "rolls", "quantity_on_hand": 300, "safety_stock": 30,  "cost_price": 22,  "selling_price": 40},
]

async def seed():
    async with AsyncSessionLocal() as db:
        # Get all active warehouses
        warehouses = (await db.execute(
            select(Warehouse).where(Warehouse.is_active.is_(True))
        )).scalars().all()

        if not warehouses:
            print("No active warehouses found. Nothing to seed.")
            return

        created = 0
        skipped = 0

        for warehouse in warehouses:
            print(f"\nWarehouse: {warehouse.name} ({warehouse.id})")
            for mat in PACKING_MATERIALS:
                # Check if already exists
                existing = (await db.execute(
                    select(InventoryItem).where(
                        InventoryItem.warehouse_id == warehouse.id,
                        InventoryItem.sku == mat["sku"],
                    )
                )).scalar_one_or_none()

                if existing:
                    print(f"  ✓ SKU {mat['sku']} already exists (qty: {existing.quantity_on_hand})")
                    skipped += 1
                    continue

                item = InventoryItem(
                    warehouse_id=warehouse.id,
                    sku=mat["sku"],
                    name=mat["name"],
                    category=mat["category"],
                    unit=mat["unit"],
                    quantity_on_hand=mat["quantity_on_hand"],
                    safety_stock=mat["safety_stock"],
                    cost_price=mat.get("cost_price", 0.0),
                    selling_price=mat.get("selling_price", 0.0),
                )
                db.add(item)
                print(f"  + Created {mat['sku']} — {mat['name']} (qty: {mat['quantity_on_hand']}, cost: ₹{mat.get('cost_price', 0)}, sell: ₹{mat.get('selling_price', 0)})")
                created += 1

        await db.commit()
        print(f"\n✅ Done! Created {created} items, skipped {skipped} existing.")


if __name__ == "__main__":
    asyncio.run(seed())
