import asyncio
import sys

sys.path.insert(0, '.')
from app.database import AsyncSessionLocal
from app.models.user import User
from app.routers.tracking import get_active_driver_locations


async def main():
    async with AsyncSessionLocal() as db:
        user = User(id="123e4567-e89b-12d3-a456-426614174000")
        try:
            res = await get_active_driver_locations(db, user)
            print("locations:", res)
        except Exception:
            import traceback
            traceback.print_exc()

asyncio.run(main())
