import asyncio
import sys

sys.path.insert(0, '.')
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"Name: {u.name}, Email: {u.email}, Role: {u.role}")

if __name__ == "__main__":
    asyncio.run(main())
