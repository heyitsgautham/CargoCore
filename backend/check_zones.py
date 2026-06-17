import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.logistics import LogisticsZone

async def check_zones():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(LogisticsZone))
        zones = result.scalars().all()
        print(f'\nTotal zones in database: {len(zones)}\n')
        for z in zones:
            print(f'  - {z.name}')
            print(f'    Type: {z.zone_type}')
            print(f'    Radius: {z.radius_km}km')
            print(f'    Status: {z.status}')
            print(f'    Warehouse ID: {z.warehouse_id}')
            print()

if __name__ == '__main__':
    asyncio.run(check_zones())
