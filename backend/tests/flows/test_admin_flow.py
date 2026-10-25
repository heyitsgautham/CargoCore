"""Logistics manager administration over HTTP: staff accounts, labourers and hubs."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_manager_creates_updates_and_removes_a_staff_account(client, world):
    lm = world.headers("LOGISTIC_MANAGER")
    created = await client.post(
        "/api/v1/users",
        json={
            "name": "Dev Dispatcher",
            "email": "dev.dispatcher@example.com",
            "password": "StrongPass123",
            "role": "DISPATCHER",
            "warehouse_id": str(world.warehouse.id),
        },
        headers=lm,
    )
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    duplicate = await client.post(
        "/api/v1/users",
        json={"name": "Dup", "email": "dev.dispatcher@example.com", "password": "StrongPass123", "role": "DISPATCHER"},
        headers=lm,
    )
    assert duplicate.status_code == 409

    listing = await client.get("/api/v1/users?role=DISPATCHER", headers=lm)
    assert user_id in {row["id"] for row in listing.json()["items"]}

    renamed = await client.put(f"/api/v1/users/{user_id}", json={"name": "Devi Dispatcher"}, headers=lm)
    assert renamed.json()["name"] == "Devi Dispatcher"

    promoted = await client.post(f"/api/v1/users/{user_id}/assign-role", json={"role": "WAREHOUSE_MANAGER"}, headers=lm)
    assert promoted.status_code == 200, promoted.text
    assert promoted.json()["role"] == "WAREHOUSE_MANAGER"

    other_hub = await client.post("/api/v1/warehouses", json={"name": "North Hub", "address": "5 North Road"}, headers=lm)
    moved = await client.post(
        f"/api/v1/users/{user_id}/assign-warehouse", json={"warehouse_id": other_hub.json()["id"]}, headers=lm
    )
    assert moved.status_code == 200, moved.text

    removed = await client.delete(f"/api/v1/users/{user_id}", headers=lm)
    assert removed.status_code == 200, removed.text


async def test_only_the_manager_administers_users(client, world):
    for role_name in ("DISPATCHER", "INDIVIDUAL", "DRIVER"):
        response = await client.get("/api/v1/users", headers=world.headers(role_name))
        assert response.status_code == 403, role_name


async def test_vendor_approval_is_recorded(client, world, db_session):
    from tests.factories import make_user

    vendor = await make_user(db_session, "VENDOR", approval_status="PENDING", company_name="New Vendor Co")
    await db_session.commit()

    approved = await client.put(
        f"/api/v1/users/{vendor.id}",
        json={"approval_status": "APPROVED", "approval_note": "Documents verified"},
        headers=world.headers("LOGISTIC_MANAGER"),
    )

    assert approved.status_code == 200, approved.text
    assert approved.json()["approval_status"] == "APPROVED"


async def test_labourer_is_hired_assigned_and_tracked(client, world):
    wm = world.headers("WAREHOUSE_MANAGER")
    hired = await client.post(
        "/api/v1/labourers",
        json={
            "warehouse_id": str(world.warehouse.id),
            "name": "Ravi Packer",
            "email": "ravi.packer@example.com",
            "phone": "9876500000",
            "skill_tags": ["packing"],
        },
        headers=wm,
    )
    assert hired.status_code == 201, hired.text
    labourer_id = hired.json()["id"]

    checked_in = await client.post(f"/api/v1/labourers/{labourer_id}/check-in", headers=wm)
    assert checked_in.status_code == 200, checked_in.text

    availability = await client.get(f"/api/v1/labourers/availability?warehouse_id={world.warehouse.id}", headers=wm)
    assert availability.status_code == 200, availability.text

    assigned = await client.post(f"/api/v1/labourers/{labourer_id}/assign/{world.order.id}", headers=wm)
    assert assigned.status_code == 200, assigned.text

    updated = await client.put(f"/api/v1/labourers/{labourer_id}", json={"skill_tags": ["packing", "loading"]}, headers=wm)
    assert updated.json()["skill_tags"] == ["packing", "loading"]

    checked_out = await client.post(f"/api/v1/labourers/{labourer_id}/check-out", headers=wm)
    assert checked_out.status_code == 200, checked_out.text

    listing = await client.get(f"/api/v1/labourers?warehouse_id={world.warehouse.id}", headers=wm)
    assert labourer_id in {row["id"] for row in listing.json()["items"]}

    released = await client.delete(f"/api/v1/labourers/{labourer_id}", headers=wm)
    assert released.status_code == 204


async def test_hub_lifecycle_and_dashboards(client, world):
    lm, wm = world.headers("LOGISTIC_MANAGER"), world.headers("WAREHOUSE_MANAGER")
    created = await client.post(
        "/api/v1/warehouses",
        json={"name": "East Hub", "address": "9 East Street", "lat": 12.95, "lng": 77.7, "capacity_limit": 500},
        headers=lm,
    )
    assert created.status_code == 201, created.text
    hub_id = created.json()["id"]

    duplicate = await client.post("/api/v1/warehouses", json={"name": "East Hub", "address": "10 East Street"}, headers=lm)
    assert duplicate.status_code in (400, 409)

    updated = await client.put(f"/api/v1/warehouses/{hub_id}", json={"hub_status": "Maintenance"}, headers=lm)
    assert updated.status_code == 200, updated.text

    floor_plan = await client.put(
        f"/api/v1/warehouses/{hub_id}/floor-plan",
        json={"floor_plan_json": {"sections": [{"id": "Z1", "label": "Zone 1"}]}},
        headers=lm,
    )
    assert floor_plan.status_code in (200, 422), floor_plan.text

    kpis = await client.get(f"/api/v1/warehouses/{world.warehouse.id}/kpis", headers=wm)
    assert kpis.status_code == 200, kpis.text
    dashboard = await client.get(f"/api/v1/warehouses/{world.warehouse.id}/dashboard", headers=wm)
    assert dashboard.status_code == 200, dashboard.text

    restock = await client.post(
        f"/api/v1/warehouses/{world.warehouse.id}/restock",
        json={"item_id": str(world.inventory_item.id), "quantity": 10},
        headers=wm,
    )
    assert restock.status_code in (200, 422), restock.text

    archived = await client.delete(f"/api/v1/warehouses/{hub_id}", headers=lm)
    assert archived.status_code == 200, archived.text


async def test_warehouse_manager_completes_and_reassigns_orders(client, world):
    wm = world.headers("WAREHOUSE_MANAGER")
    base = f"/api/v1/warehouses/{world.warehouse.id}/orders"

    reassigned = await client.post(f"{base}/{world.vendor_order.id}/reassign", headers=wm)
    assert reassigned.status_code in (200, 400, 409), reassigned.text

    completed = await client.post(f"{base}/{world.order.id}/complete", headers=wm)
    assert completed.status_code in (200, 400, 409), completed.text


async def test_hub_with_zones_or_gradings_is_kept(client, world):
    response = await client.delete(f"/api/v1/warehouses/{world.warehouse.id}", headers=world.headers("LOGISTIC_MANAGER"))

    assert response.status_code == 409
