import asyncio
import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://logistics_user:logistics_pass@localhost:5432/logistics_db"

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

engine = create_async_engine(os.environ["DATABASE_URL"])

async def q():
    async with AsyncSession(engine) as s:
        # Order info
        print("=== Order QC-5F79455689 ===")
        r = await s.execute(text("""
            SELECT o.tracking_code, o.status, o.assigned_driver_id, o.assigned_vehicle_id,
                   u.name as driver_name,
                   v.license_plate, v.code as vcode, v.model, v.id as vid
            FROM orders o
            LEFT JOIN users u ON u.id = o.assigned_driver_id
            LEFT JOIN logistics_vehicles v ON v.assigned_driver_id = o.assigned_driver_id
            WHERE o.tracking_code = 'QC-5F79455689'
        """))
        for row in r.fetchall():
            print(f"  tracking={row[0]}, status={row[1]}")
            print(f"  driver_id={row[2]}, driver={row[4]}")
            print(f"  order vehicle_id={row[3]}")
            print(f"  vehicle via driver: id={str(row[8])[:8] if row[8] else None}, code={row[6]}, plate={row[5]}, model={row[7]}")

        # All vehicles
        print("\n=== All Vehicles ===")
        r2 = await s.execute(text("SELECT id, code, license_plate, model, vehicle_type, assigned_driver_id FROM logistics_vehicles"))
        for row in r2.fetchall():
            print(f"  id={str(row[0])[:8]}, code={row[1]}, plate={row[2]}, model={row[3]}, driver_id={str(row[5])[:8] if row[5] else None}")

asyncio.run(q())


