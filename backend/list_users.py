import asyncio
import sys
sys.path.insert(0, '.')
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"Name: {u.name}, Email: {u.email}, Role: {u.role}")

if __name__ == "__main__":
    asyncio.run(main())
