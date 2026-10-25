"""Fill an empty development database with the demo logistics world.

Creates the reserved Logistics Manager account, then three hubs with their
managers, a dispatcher, two drivers, vehicles, orders, stock and the equipment
ledger. A database that already has a hub is left alone.

    cd backend
    DEMO_STAFF_PASSWORD='choose-one' python -m scripts.seed_demo_data

Every demo staff account gets DEMO_STAFF_PASSWORD. Without it the script
generates one and prints it once.
"""

import asyncio
import os
import secrets

from app.database import AsyncSessionLocal
from app.services.auth_service import ensure_logistic_manager_account
from app.services.logistics.seed import ensure_logistics_seed_data


async def seed(staff_password: str) -> None:
    async with AsyncSessionLocal() as db:
        manager = await ensure_logistic_manager_account(db)
        await ensure_logistics_seed_data(db, manager, staff_password)
        await db.commit()


def main() -> None:
    staff_password = os.environ.get("DEMO_STAFF_PASSWORD") or secrets.token_urlsafe(12)
    asyncio.run(seed(staff_password))
    print("Demo data is in place.")
    if "DEMO_STAFF_PASSWORD" not in os.environ:
        print(f"Demo staff password: {staff_password}")


if __name__ == "__main__":
    main()
