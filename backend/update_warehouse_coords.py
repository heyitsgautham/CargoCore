import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.warehouse import Warehouse

async def update_warehouse_coords():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Warehouse))
        warehouses = result.scalars().all()

        print(f'\nFound {len(warehouses)} warehouses\n')

        for w in warehouses:
            # Update Bangalore warehouse with proper coordinates
            if 'BANGALORE' in w.name.upper() or 'KARNATAKA' in (w.address or '').upper():
                w.lat = 12.9716
                w.lng = 77.5946
                db.add(w)
                print(f'Updated {w.name} with Bangalore coordinates')
            elif w.lat is None:
                # Default coords for other warehouses
                w.lat = 12.9716 + 0.05
                w.lng = 77.5946 + 0.05
                db.add(w)
                print(f'Updated {w.name} with default coordinates')

        await db.commit()
        print('\nDone!')

if __name__ == '__main__':
    asyncio.run(update_warehouse_coords())
