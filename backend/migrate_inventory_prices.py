"""
One-off migration: add cost_price and selling_price columns to inventory_items.
Safe to run multiple times (uses IF NOT EXISTS / ignores duplicate column errors).
"""
import asyncio
from sqlalchemy import text
from app.database import engine


async def run():
    async with engine.begin() as conn:
        print("Adding cost_price column...")
        await conn.execute(text("""
            ALTER TABLE inventory_items
            ADD COLUMN IF NOT EXISTS cost_price FLOAT NOT NULL DEFAULT 0.0;
        """))
        print("Adding selling_price column...")
        await conn.execute(text("""
            ALTER TABLE inventory_items
            ADD COLUMN IF NOT EXISTS selling_price FLOAT NOT NULL DEFAULT 0.0;
        """))
        print("Done! Both columns added successfully.")


if __name__ == "__main__":
    asyncio.run(run())
