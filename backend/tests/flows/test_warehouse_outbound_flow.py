"""A customer order moves through the warehouse over HTTP, as the warehouse manager screens drive it.

accept -> start picking -> pick each item -> complete picking -> start packing at a
station -> complete packing -> quality check -> pass -> load at a dock -> release.
"""

import pytest

pytestmark = pytest.mark.asyncio


def _ops(world, suffix: str) -> str:
    return f"/api/v1/warehouses/{world.warehouse.id}/operations{suffix}"


async def _post(client, world, suffix, json=None, role="WAREHOUSE_MANAGER"):
    return await client.post(_ops(world, suffix), json=json, headers=world.headers(role))


async def test_order_goes_from_acceptance_to_dock_release(client, world, db_session):
    order_id = world.order.id

    accepted = await _post(client, world, f"/orders/{order_id}/accept")
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["warehouse_substatus"] == "AWAITING_PICK"

    started = await _post(client, world, f"/orders/{order_id}/start-picking", {"labourer_id": str(world.labourer.id)})
    assert started.status_code == 200, started.text
    assert started.json()["assigned_labourer_id"] == str(world.labourer.id)

    again = await _post(client, world, f"/orders/{order_id}/start-picking", {})
    assert again.json()["message"] == "Picking already in progress"

    picked = await _post(client, world, f"/orders/{order_id}/pick-item", {"sku": "SKU-SOFA", "quantity_picked": 2})
    assert picked.status_code == 200, picked.text

    progress = await client.get(_ops(world, f"/orders/{order_id}/pick-progress"), headers=world.headers("WAREHOUSE_MANAGER"))
    assert progress.status_code == 200, progress.text

    completed = await _post(client, world, f"/orders/{order_id}/complete-picking")
    assert completed.status_code == 200, completed.text
    assert completed.json()["warehouse_substatus"] == "PICKED"

    await db_session.refresh(world.inventory_item)
    assert world.inventory_item.quantity_on_hand == 48

    packing = await _post(client, world, f"/orders/{order_id}/start-packing", {"station_id": str(world.station.id)})
    assert packing.status_code == 200, packing.text
    packed = await _post(client, world, f"/orders/{order_id}/complete-packing")
    assert packed.status_code == 200, packed.text
    assert packed.json()["warehouse_substatus"] == "PACKED"

    check = await _post(client, world, f"/orders/{order_id}/quality-check")
    assert check.status_code in (200, 201), check.text
    check_id = check.json()["id"]

    updated = await client.put(
        _ops(world, f"/quality-checks/{check_id}"),
        json={
            "goods_correct": True,
            "count_correct": True,
            "packaging_verified": True,
            "labor_assigned": True,
            "weight_verified": True,
            "label_attached": True,
            "notes": "All good",
        },
        headers=world.headers("WAREHOUSE_MANAGER"),
    )
    assert updated.status_code == 200, updated.text

    passed = await _post(client, world, f"/quality-checks/{check_id}/pass")
    assert passed.status_code == 200, passed.text

    loaded = await _post(
        client,
        world,
        f"/loading-docks/{world.dock.id}/assign",
        {"vehicle_id": str(world.vehicle.id), "carrier": "CargoCore Fleet", "order_id": str(order_id)},
    )
    assert loaded.status_code == 200, loaded.text

    released = await _post(
        client,
        world,
        f"/loading-docks/{world.dock.id}/release",
        {
            "items_scanned": True,
            "labor_present": True,
            "packing_loaded": True,
            "manifest_attached": True,
            "driver_confirmed": True,
            "weight_verified": True,
        },
    )
    assert released.status_code == 200, released.text


async def test_pass_is_refused_until_every_check_is_ticked(client, world):
    order_id = world.vendor_order.id
    for step, body in (
        ("start-picking", {}),
        ("pick-item", {"sku": "SKU-SOFA", "quantity_picked": 2}),
        ("complete-picking", None),
        ("start-packing", {}),
        ("complete-packing", None),
    ):
        response = await _post(client, world, f"/orders/{order_id}/{step}", body)
        assert response.status_code == 200, (step, response.text)

    check = await _post(client, world, f"/orders/{order_id}/quality-check")
    refused = await _post(client, world, f"/quality-checks/{check.json()['id']}/pass")

    assert refused.status_code == 400


async def test_picking_rules_reject_bad_requests(client, world):
    order_id = world.order.id

    skipped = await _post(client, world, f"/orders/{order_id}/complete-picking")
    assert skipped.status_code == 400

    await _post(client, world, f"/orders/{order_id}/accept")
    await _post(client, world, f"/orders/{order_id}/start-picking", {})
    reverted = await _post(client, world, f"/orders/{order_id}/revert-picking")
    assert reverted.status_code == 200
    assert reverted.json()["warehouse_substatus"] == "AWAITING_PICK"

    unknown_labourer = await _post(
        client, world, f"/orders/{order_id}/start-picking", {"labourer_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert unknown_labourer.status_code == 404


async def test_docks_and_stations_can_be_created_and_maintained(client, world):
    dock = await _post(client, world, "/loading-docks", {"dock_number": "D9"})
    assert dock.status_code in (200, 201), dock.text
    dock_id = dock.json()["id"]

    maintenance = await client.post(
        _ops(world, f"/loading-docks/{dock_id}/maintenance?is_maintenance=true"),
        headers=world.headers("WAREHOUSE_MANAGER"),
    )
    assert maintenance.status_code == 200, maintenance.text

    blocked = await _post(
        client, world, f"/loading-docks/{dock_id}/assign", {"vehicle_id": str(world.vehicle.id), "carrier": "X"}
    )
    assert blocked.status_code in (400, 409)

    station = await _post(client, world, "/packing-stations", {"station_number": "P9", "status": "available"})
    assert station.status_code in (200, 201), station.text
    station_update = await client.put(
        _ops(world, f"/packing-stations/{station.json()['id']}"),
        json={"status": "maintenance"},
        headers=world.headers("WAREHOUSE_MANAGER"),
    )
    assert station_update.status_code == 200, station_update.text

    listing = await client.get(_ops(world, "/loading-docks"), headers=world.headers("WAREHOUSE_MANAGER"))
    assert {d["dock_number"] for d in listing.json()["items"]} >= {"D1", "D9"}


async def test_packing_waits_for_packing_materials_to_be_issued(client, world, db_session):
    from tests.factories import make_inventory_item, make_order

    boxes = await make_inventory_item(db_session, world.warehouse, sku="SKU-CARTON", name="Moving carton", quantity_on_hand=30)
    order = await make_order(
        db_session,
        world.users["INDIVIDUAL"],
        warehouse_id=world.warehouse.id,
        warehouse_substatus="AWAITING_PICK",
        items=[("SKU-SOFA", 1), ("SKU-CARTON", 4)],
    )
    await db_session.commit()

    for step, body in (
        ("start-picking", {}),
        ("pick-item", {"sku": "SKU-SOFA", "quantity_picked": 1}),
        ("pick-item", {"sku": "SKU-CARTON", "quantity_picked": 4}),
        ("complete-picking", None),
        ("start-packing", {}),
    ):
        response = await _post(client, world, f"/orders/{order.id}/{step}", body)
        assert response.status_code == 200, (step, response.text)

    blocked = await _post(client, world, f"/orders/{order.id}/complete-packing")
    assert blocked.status_code == 409

    issued = await client.post(
        "/api/v1/inventory/movements",
        json={"item_id": str(boxes.id), "movement_type": "ISSUE", "quantity": 4, "reference_order_id": str(order.id)},
        headers=world.headers("WAREHOUSE_MANAGER"),
    )
    assert issued.status_code == 201, issued.text

    packed = await _post(client, world, f"/orders/{order.id}/complete-packing")
    assert packed.status_code == 200, packed.text
