import asyncio

import asyncpg

# DRIVER2 order: QC-5F79455689, assigned_driver_id = bad3c903-2fc2-439e-8563-4b101ecc9c40
# available vehicles: VH-01 through VH-04 (all Active, no assigned_driver_id)
# We'll assign VH-01 (KA-01-AB-8838) to DRIVER2's order

DRIVER2_ORDER_TRACKING = 'QC-5F79455689'
DRIVER2_ID = 'bad3c903-2fc2-439e-8563-4b101ecc9c40'
VEHICLE_TO_ASSIGN = '9e18cd29-de5c-49fd-8d5d-83f8cfe32514'  # VH-01
VEHICLE_CODE = 'VH-01'

async def main():
    conn = await asyncpg.connect('postgresql://logistics_user:logistics_pass@localhost:5432/logistics_db')
    
    # 1. Set assigned_vehicle_id on the order
    updated = await conn.fetchrow("""
        UPDATE orders
        SET assigned_vehicle_id = $1
        WHERE tracking_code = $2
        RETURNING tracking_code, assigned_vehicle_id, assigned_driver_id
    """, VEHICLE_TO_ASSIGN, DRIVER2_ORDER_TRACKING)
    print(f"Updated order: {dict(updated)}")
    
    # 2. Mark vehicle as In Use
    await conn.execute("""
        UPDATE logistics_vehicles
        SET status = 'In Use', assigned_driver_id = $1
        WHERE id = $2
    """, DRIVER2_ID, VEHICLE_TO_ASSIGN)
    print(f"Marked {VEHICLE_CODE} as In Use and linked to DRIVER2")
    
    await conn.close()
    print("Done! Refresh the dispatcher to see the vehicle number.")

asyncio.run(main())
