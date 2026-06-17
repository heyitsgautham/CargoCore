import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.warehouse import Warehouse

async def check_warehouses():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Warehouse))
        warehouses = result.scalars().all()
        print(f'\nTotal warehouses in database: {len(warehouses)}\n')
        for w in warehouses:
            print(f'  - {w.name}')
            print(f'    ID: {w.id}')
            print(f'    Address: {w.address}')
            print()

if __name__ == '__main__':
    asyncio.run(check_warehouses())
