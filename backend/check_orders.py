import asyncio

import asyncpg


async def main():
    conn = await asyncpg.connect('postgresql://logistics_user:logistics_pass@localhost:5432/logistics_db')
    
    # Check IN_TRANSIT / ASSIGNED orders and their vehicle assignments
    rows = await conn.fetch("""
        SELECT o.tracking_code, o.status, o.assigned_driver_id, o.assigned_vehicle_id,
               u.name as driver_name, v.code as vehicle_code, v.license_plate
        FROM orders o
        LEFT JOIN users u ON u.id = o.assigned_driver_id
        LEFT JOIN logistics_vehicles v ON v.id = o.assigned_vehicle_id
        WHERE o.status IN ('ASSIGNED', 'IN_TRANSIT')
        ORDER BY o.created_at DESC
        LIMIT 10
    """)
    print("=== ACTIVE ORDERS ===")
    for r in rows:
        print(dict(r))
    
    print("\n=== VEHICLES ===")
    vrows = await conn.fetch("SELECT id, code, license_plate, assigned_driver_id, status FROM logistics_vehicles LIMIT 15")
    for r in vrows:
        print(dict(r))
    
    await conn.close()

asyncio.run(main())
