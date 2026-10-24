"""Quick check of drivers and orders for Auto-Balance testing"""
import asyncio

from sqlalchemy import text

from app.database import engine


async def check():
    async with engine.connect() as conn:
        print("=" * 50)
        print("DRIVERS:")
        print("-" * 50)
        result = await conn.execute(text("""
            SELECT u.name, ldp.status, ldp.current_job
            FROM logistics_driver_profiles ldp
            JOIN users u ON u.id = ldp.user_id
            ORDER BY u.name
        """))
        for r in result.fetchall():
            print(f"  {r[0]}: status={r[1]}, current_job={r[2] or 'FREE'}")
        
        print("\n" + "=" * 50)
        print("ORDERS BY STATUS:")
        print("-" * 50)
        result = await conn.execute(text("""
            SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY status
        """))
        for r in result.fetchall():
            print(f"  {r[0]}: {r[1]}")
        
        print("\n" + "=" * 50)
        print("ASSIGNED ORDERS (ready for balancing):")
        print("-" * 50)
        result = await conn.execute(text("""
            SELECT o.tracking_code, u.name as driver, o.status
            FROM orders o
            LEFT JOIN users u ON u.id = o.assigned_driver_id
            WHERE o.status = 'ASSIGNED'
        """))
        rows = result.fetchall()
        if not rows:
            print("  (No ASSIGNED orders - Auto-Balance needs ASSIGNED orders!)")
        for r in rows:
            print(f"  {r[0]} -> {r[1]}")
        
        print("\n" + "=" * 50)
        print("CONFIRMED ORDERS (unassigned, can be assigned first):")
        print("-" * 50)
        result = await conn.execute(text("""
            SELECT tracking_code FROM orders 
            WHERE status = 'CONFIRMED' AND assigned_driver_id IS NULL
            LIMIT 5
        """))
        rows = result.fetchall()
        if not rows:
            print("  (No unassigned CONFIRMED orders)")
        for r in rows:
            print(f"  {r[0]}")

asyncio.run(check())
