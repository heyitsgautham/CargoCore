"""Stock management over HTTP: items, movements, low stock, pick lists, restock and material requests."""

import json

import pytest

from app.services import material_request_service

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/inventory"


@pytest.fixture()
def rates_file(tmp_path, monkeypatch):
    """Approving a material request writes the rate card, so point it at a scratch copy."""
    path = tmp_path / "rates_config.json"
    path.write_text(json.dumps({"materials": [{"id": "box", "name": "Box", "rate": 50, "unit": "pcs"}]}))
    monkeypatch.setattr(material_request_service, "_RATES_CONFIG_PATH", path)
    return path


async def test_item_crud_movements_and_low_stock(client, world):
    headers = world.headers("WAREHOUSE_MANAGER")
    created = await client.post(
        BASE,
        json={
            "warehouse_id": str(world.warehouse.id),
            "sku": "SKU-TAPE",
            "name": "Packing tape",
            "category": "Packing",
            "quantity_on_hand": 5,
            "safety_stock": 10,
            "selling_price": 25,
            "aisle": "Z1-A3",
            "shelf": "2",
            "bin": "B",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    item_id = created.json()["id"]

    low = await client.get(f"{BASE}/low-stock?warehouse_id={world.warehouse.id}", headers=headers)
    assert item_id in {row["id"] for row in low.json()}

    received = await client.post(
        f"{BASE}/movements", json={"item_id": item_id, "movement_type": "INBOUND", "quantity": 20}, headers=headers
    )
    assert received.status_code == 201, received.text

    detail = await client.get(f"{BASE}/{item_id}", headers=headers)
    assert detail.json()["quantity_on_hand"] == 25

    overdraw = await client.post(
        f"{BASE}/movements", json={"item_id": item_id, "movement_type": "ISSUE", "quantity": 500}, headers=headers
    )
    assert overdraw.status_code == 409

    movements = await client.get(f"{BASE}/movements?item_id={item_id}", headers=headers)
    assert [m["movement_type"].upper() for m in movements.json()] == ["INBOUND"]

    renamed = await client.put(f"{BASE}/{item_id}", json={"name": "Brown tape", "safety_stock": 2}, headers=headers)
    assert renamed.json()["name"] == "Brown tape"

    categories = await client.get(f"{BASE}/categories?warehouse_id={world.warehouse.id}", headers=headers)
    assert "Packing" in categories.json()

    listing = await client.get(f"{BASE}?warehouse_id={world.warehouse.id}&sku=SKU-TAPE", headers=headers)
    assert listing.json()["total"] == 1

    # The item has a movement, so it keeps its history instead of being deleted.
    kept = await client.delete(f"{BASE}/{item_id}", headers=headers)
    assert kept.status_code == 409


async def test_an_item_without_history_can_be_deleted(client, world):
    headers = world.headers("WAREHOUSE_MANAGER")
    created = await client.post(
        BASE, json={"warehouse_id": str(world.warehouse.id), "sku": "SKU-TEMP", "name": "Temp"}, headers=headers
    )
    item_id = created.json()["id"]

    deleted = await client.delete(f"{BASE}/{item_id}", headers=headers)
    assert deleted.status_code == 200
    gone = await client.get(f"{BASE}/{item_id}", headers=headers)
    assert gone.status_code == 404


async def test_customers_cannot_touch_inventory(client, world):
    response = await client.get(BASE, headers=world.headers("INDIVIDUAL"))
    assert response.status_code == 403


async def test_pick_list_points_at_the_shelf(client, world):
    response = await client.post(f"{BASE}/pick-list/{world.order.id}", headers=world.headers("WAREHOUSE_MANAGER"))

    assert response.status_code == 200, response.text
    lines = response.json()["items"]
    assert [line["sku"] for line in lines] == ["SKU-SOFA"]


async def test_restock_request_is_raised_escalated_and_approved(client, world):
    wm, lm = world.headers("WAREHOUSE_MANAGER"), world.headers("LOGISTIC_MANAGER")
    raised = await client.post(
        f"{BASE}/restock-requests", json={"item_id": str(world.inventory_item.id), "quantity": 30}, headers=wm
    )
    assert raised.status_code == 201, raised.text
    request_id = raised.json()["id"]

    escalated = await client.post(f"{BASE}/restock-requests/{request_id}/escalate", headers=wm)
    assert escalated.status_code == 200, escalated.text

    pending = await client.get(f"{BASE}/restock-requests?status=PENDING", headers=lm)
    assert request_id in {row["id"] for row in pending.json()["items"]}

    approved = await client.put(
        f"{BASE}/restock-requests/{request_id}/status",
        json={"status": "APPROVED", "manager_notes": "Order from the usual supplier"},
        headers=lm,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "APPROVED"

    twice = await client.put(f"{BASE}/restock-requests/{request_id}/status", json={"status": "REJECTED"}, headers=lm)
    assert twice.status_code == 400


async def test_material_request_approval_adds_the_material_everywhere(client, world, rates_file):
    wm, lm = world.headers("WAREHOUSE_MANAGER"), world.headers("LOGISTIC_MANAGER")
    requested = await client.post(
        f"{BASE}/material-requests",
        json={"material_name": "Corner protector", "category": "Packing", "unit": "pcs", "suggested_rate": 15},
        headers=wm,
    )
    assert requested.status_code == 201, requested.text
    request_id = requested.json()["id"]

    approved = await client.put(
        f"{BASE}/material-requests/{request_id}/approve", json={"approved_rate": 18, "manager_notes": "OK"}, headers=lm
    )
    assert approved.status_code == 200, approved.text

    names = [material["name"] for material in json.loads(rates_file.read_text())["materials"]]
    assert "Corner protector" in names

    stock = await client.get(f"{BASE}?warehouse_id={world.warehouse.id}&page_size=100", headers=wm)
    assert "Corner protector" in {row["name"] for row in stock.json()["items"]}

    second = await client.post(f"{BASE}/material-requests", json={"material_name": "Foam sheet"}, headers=wm)
    rejected = await client.put(
        f"{BASE}/material-requests/{second.json()['id']}/reject", json={"manager_notes": "Not needed"}, headers=lm
    )
    assert rejected.json()["status"] == "REJECTED"

    listing = await client.get(f"{BASE}/material-requests", headers=lm)
    assert listing.json()["total"] == 2
