"""Logistics manager desk over HTTP: fleet, finance, zones, chat, meetings, tasks, notifications, alerts and documents."""

import pytest

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/logistics"


async def test_fleet_vehicles_and_drivers_are_managed(client, world):
    lm = world.headers("LOGISTIC_MANAGER")
    created = await client.post(
        f"{BASE}/vehicles",
        json={
            "code": "KA05MX7788",
            "vehicle_type": "Tempo",
            "warehouse_id": str(world.warehouse.id),
            "model": "Tata Ace",
            "year": 2022,
            "status": "Active",
        },
        headers=lm,
    )
    assert created.status_code in (200, 201), created.text
    vehicle_id = created.json()["id"]

    serviced = await client.put(
        f"{BASE}/vehicles/{vehicle_id}", json={"status": "Maintenance", "maintenance_issue": "Brake pads"}, headers=lm
    )
    assert serviced.json()["status"] == "Maintenance"

    vehicles = await client.get(f"{BASE}/vehicles", headers=lm)
    assert vehicle_id in {v["id"] for v in vehicles.json()}

    driver = await client.put(
        f"{BASE}/drivers/{world.users['DRIVER'].id}",
        json={"status": "On Break", "current_location": "12.97,77.59"},
        headers=lm,
    )
    assert driver.status_code == 200, driver.text

    drivers = await client.get(f"{BASE}/drivers", headers=lm)
    assert drivers.status_code == 200, drivers.text

    bootstrap = await client.get(f"{BASE}/bootstrap", headers=lm)
    assert bootstrap.status_code == 200, bootstrap.text
    assert "vehicles" in bootstrap.json()


async def test_finance_entries_are_recorded(client, world):
    lm = world.headers("LOGISTIC_MANAGER")
    expense = await client.post(
        f"{BASE}/transactions",
        json={"description": "Diesel top-up", "transaction_type": "expense", "amount": 3200, "warehouse_id": str(world.warehouse.id)},
        headers=lm,
    )
    assert expense.status_code in (200, 201), expense.text

    investment = await client.post(
        f"{BASE}/capital-investment",
        json={"amount": 50000, "description": "New forklift", "funding_source": "Owner", "warehouse_id": str(world.warehouse.id)},
        headers=lm,
    )
    assert investment.status_code in (200, 201), investment.text


async def test_zones_are_created_updated_and_removed(client, world):
    lm = world.headers("LOGISTIC_MANAGER")
    zone = await client.post(
        f"{BASE}/zones",
        json={"warehouse_id": str(world.warehouse.id), "name": "Koramangala", "zone_type": "Radius", "radius_km": 4, "lat": 12.93, "lng": 77.62},
        headers=lm,
    )
    assert zone.status_code in (200, 201), zone.text
    zone_id = zone.json()["id"]

    renamed = await client.put(f"{BASE}/zones/{zone_id}", json={"name": "Koramangala East"}, headers=lm)
    assert renamed.json()["name"] == "Koramangala East"

    zones = await client.get(f"{BASE}/zones", headers=lm)
    assert zone_id in {z["id"] for z in zones.json()}

    removed = await client.delete(f"{BASE}/zones/{zone_id}", headers=lm)
    assert removed.status_code == 200, removed.text


async def test_chat_threads_carry_messages(client, world):
    lm = world.headers("LOGISTIC_MANAGER")
    thread = await client.post(
        f"{BASE}/chats", json={"name": "North hub crew", "phone": "9000000001", "warehouse_id": str(world.warehouse.id)}, headers=lm
    )
    assert thread.status_code in (200, 201), thread.text
    thread_id = thread.json()["id"]

    sent = await client.post(f"{BASE}/chats/{thread_id}/messages", json={"text": "Truck leaves at 6"}, headers=lm)
    assert sent.status_code in (200, 201), sent.text

    muted = await client.put(f"{BASE}/chats/{thread_id}", json={"muted": True}, headers=lm)
    assert muted.status_code == 200, muted.text

    threads = await client.get(f"{BASE}/chats", headers=lm)
    assert thread_id in {t["id"] for t in threads.json()}

    contacts = await client.get(f"{BASE}/dispatch-contacts", headers=world.headers("DISPATCHER"))
    assert contacts.status_code in (200, 404), contacts.text

    removed = await client.delete(f"{BASE}/chats/{thread_id}", headers=lm)
    assert removed.status_code == 200, removed.text


async def test_meetings_are_scheduled_and_validated(client, world):
    lm = world.headers("LOGISTIC_MANAGER")
    meeting = {
        "topic": "Weekly hub review",
        "description": "Throughput and staffing",
        "meeting_type": "gmeet",
        "link": "https://meet.google.com/abc-defg-hij",
        "date": "2026-11-02",
        "start_time": "10:00",
        "end_time": "10:30",
        "participants": [str(world.users["WAREHOUSE_MANAGER"].id)],
    }
    created = await client.post(f"{BASE}/meetings", json=meeting, headers=lm)
    assert created.status_code in (200, 201), created.text
    meeting_id = created.json()["id"]

    backwards = await client.post(f"{BASE}/meetings", json={**meeting, "start_time": "11:00", "end_time": "10:00"}, headers=lm)
    assert backwards.status_code in (400, 422)

    moved = await client.put(f"{BASE}/meetings/{meeting_id}", json={"start_time": "11:00", "end_time": "11:45"}, headers=lm)
    assert moved.status_code == 200, moved.text

    seen_by_invitee = await client.get(f"{BASE}/meetings", headers=world.headers("WAREHOUSE_MANAGER"))
    assert meeting_id in {m["id"] for m in seen_by_invitee.json()}

    removed = await client.delete(f"{BASE}/meetings/{meeting_id}", headers=lm)
    assert removed.status_code == 200, removed.text


async def test_tasks_notifications_and_broadcasts(client, world):
    lm = world.headers("LOGISTIC_MANAGER")
    task = await client.post(f"{BASE}/tasks", json={"text": "Renew fleet insurance", "target_time": "2026-11-01T17:00:00Z"}, headers=lm)
    assert task.status_code in (200, 201), task.text
    task_id = task.json()["id"]
    done = await client.put(f"{BASE}/tasks/{task_id}", json={"status": "done"}, headers=lm)
    assert done.status_code == 200, done.text
    assert (await client.delete(f"{BASE}/tasks/{task_id}", headers=lm)).status_code == 200

    broadcast = await client.post(
        f"{BASE}/notifications/broadcast",
        json={"audience": "drivers", "type": "info", "title": "Rain alert", "message": "Drive slowly on ORR"},
        headers=lm,
    )
    assert broadcast.status_code == 200, broadcast.text

    driver_notifications = await client.get(f"{BASE}/drivers/me/notifications", headers=world.headers("DRIVER"))
    assert any("ORR" in n["message"] for n in driver_notifications.json())

    notifications = await client.get(f"{BASE}/notifications", headers=lm)
    for item in notifications.json()[:1]:
        read = await client.put(f"{BASE}/notifications/{item['id']}", json={"read": True}, headers=lm)
        assert read.status_code == 200, read.text
    assert (await client.post(f"{BASE}/notifications/mark-all-read", headers=lm)).status_code == 200
    assert (await client.delete(f"{BASE}/notifications", headers=lm)).status_code == 200


async def test_alerts_are_raised_and_resolved(client, world):
    dispatcher = world.headers("DISPATCHER")
    raised = await client.post(
        f"{BASE}/alerts",
        json={"type": "traffic", "title": "Jam on Hosur Road", "description": "40 minute delay", "severity": "high"},
        headers=dispatcher,
    )
    assert raised.status_code == 200, raised.text
    alert_id = raised.json()["id"]

    listed = await client.get(f"{BASE}/alerts", headers=dispatcher)
    assert alert_id in {a["id"] for a in listed.json()}

    resolved = await client.post(f"{BASE}/alerts/{alert_id}/resolve", headers=dispatcher)
    assert resolved.status_code == 200, resolved.text


async def test_manifests_and_documents(client, world):
    lm = world.headers("LOGISTIC_MANAGER")
    manifest = await client.post(
        f"{BASE}/manifests",
        json={
            "route_id": "RT-101",
            "driver_name": world.users["DRIVER"].name,
            "driver_id": str(world.users["DRIVER"].id),
            "vehicle_code": world.vehicle.code,
            "hub_name": world.warehouse.name,
            "orders_count": 3,
            "stop_count": 3,
        },
        headers=lm,
    )
    assert manifest.status_code in (200, 201), manifest.text
    pushed = await client.post(f"{BASE}/manifests/{manifest.json()['id']}/push", headers=lm)
    assert pushed.status_code == 200, pushed.text

    document = await client.post(
        f"{BASE}/documents",
        json={"entity_type": "vehicle", "entity_id": world.vehicle.code, "doc_type": "Insurance", "expiry_date": "2027-01-31T00:00:00Z"},
        headers=lm,
    )
    assert document.status_code in (200, 201), document.text
    verified = await client.put(
        f"{BASE}/documents/{document.json()['id']}/status", json={"status": "Verified", "notes": "Checked"}, headers=lm
    )
    assert verified.status_code == 200, verified.text


async def test_escalations_move_through_their_statuses(client, world):
    raised = await client.post(
        f"/api/v1/orders/{world.order.id}/escalate", json={"reason": "Address unclear"}, headers=world.headers("DISPATCHER")
    )
    escalation_id = raised.json()["id"]

    updated = await client.put(
        f"{BASE}/escalations/{escalation_id}", json={"status": "RESOLVED"}, headers=world.headers("LOGISTIC_MANAGER")
    )
    assert updated.status_code == 200, updated.text


async def test_ai_query_answers_from_live_data_without_gemini(client, world, db_session):
    from app.models.logistics import LogisticsReturnCase, LogisticsTask

    db_session.add_all(
        [
            LogisticsReturnCase(
                warehouse_id=world.warehouse.id,
                reference_code="DMG-AIQ1",
                customer_name="Asha",
                reason="Scratched",
                condition="Reported",
                status="Pending",
                refund_amount=120.0,
            ),
            LogisticsTask(text="Call the insurer"),
        ]
    )
    await db_session.commit()

    queries = (
        "hello",
        "give me a dashboard summary",
        "any risk right now",
        "How many drivers are active?",
        "fleet utilization",
        "orders on the road",
        "returns waiting",
        "revenue this month",
        "which hub is underperforming",
        "low stock",
        "staff on shift",
        "my todo list",
        "escalations waiting",
        "zone coverage",
        "unread notifications",
        "sla trend",
        "what can you do",
        "something unrelated",
    )
    for query in queries:
        response = await client.post(f"{BASE}/ai/query", json={"query": query}, headers=world.headers("LOGISTIC_MANAGER"))
        assert response.status_code == 200, (query, response.text)
        assert response.json()["text"]
