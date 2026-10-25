"""The demo seed behind backend/scripts/seed_demo_data.py."""

from sqlalchemy import func, select

from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.admin_bootstrap import ensure_logistic_manager_account
from app.services.logistics.seed import ensure_logistics_seed_data
from scripts.seed_demo_data import FLOOR_ORDERS, seed_floor_activity

LOGIN = "/api/v1/auth/login"


async def test_demo_staff_sign_in_with_the_chosen_password_only(client, db_session):
    manager = await ensure_logistic_manager_account(db_session)
    await ensure_logistics_seed_data(db_session, manager, "Demo-Staff-Pass-9")
    await db_session.commit()

    chosen = await client.post(LOGIN, json={"email": "ellen.r@cargocore.com", "password": "Demo-Staff-Pass-9"})
    guessed = await client.post(LOGIN, json={"email": "john.w@cargocore.com", "password": "12345678"})

    assert chosen.status_code == 200
    assert chosen.json()["user"]["role"] == "WAREHOUSE_MANAGER"
    assert guessed.status_code == 401


async def test_seed_leaves_a_database_with_hubs_alone(db_session):
    manager = await ensure_logistic_manager_account(db_session)
    await ensure_logistics_seed_data(db_session, manager, "Demo-Staff-Pass-9")
    users_after_first = (await db_session.execute(select(func.count(User.id)))).scalar_one()

    await ensure_logistics_seed_data(db_session, manager, "Another-Pass-1")

    assert (await db_session.execute(select(func.count(Warehouse.id)))).scalar_one() == 3
    assert (await db_session.execute(select(func.count(User.id)))).scalar_one() == users_after_first


async def test_floor_activity_puts_orders_at_every_warehouse_stage(client, db_session):
    manager = await ensure_logistic_manager_account(db_session)
    await ensure_logistics_seed_data(db_session, manager, "Demo-Staff-Pass-9")
    await seed_floor_activity(db_session, "Demo-Staff-Pass-9")
    await db_session.commit()

    stages = set(
        (await db_session.execute(select(Order.warehouse_substatus).where(Order.tracking_code.like("QC-DEMO%"))))
        .scalars()
        .all()
    )
    vendor = await client.post(LOGIN, json={"email": "demo.vendor@example.com", "password": "Demo-Staff-Pass-9"})

    assert stages == {row[3] for row in FLOOR_ORDERS}
    assert {"AWAITING_PICK", "PICKING", "PACKING", "QC_PASSED", "READY_FOR_DISPATCH"} <= stages
    assert vendor.status_code == 200
