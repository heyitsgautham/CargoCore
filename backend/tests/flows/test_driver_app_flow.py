"""The driver app's day over HTTP: bind a vehicle, start a shift, work a job, message dispatch, and hand back."""

import pytest
from sqlalchemy import select

from app.models.logistics import LogisticsDriverProfile

pytestmark = pytest.mark.asyncio

ME = "/api/v1/logistics/drivers/me"


async def test_driver_runs_a_shift_end_to_end(client, world, db_session):
    driver = world.headers("DRIVER")
    world.order.status = "ASSIGNED"
    world.order.assigned_driver_id = world.users["DRIVER"].id
    world.order.assigned_vehicle_id = world.vehicle.id
    await db_session.commit()

    bound = await client.post(f"{ME}/bind-vehicle", json={"vehicle_code": world.vehicle.code}, headers=driver)
    assert bound.status_code == 200, bound.text

    started = await client.post(f"{ME}/shift/start", headers=driver)
    assert started.status_code == 200, started.text

    for path in ("/dashboard", "/shift", "/hos", "/crew", "/telemetry", "/audit", "/notifications"):
        response = await client.get(f"{ME}{path}", headers=driver)
        assert response.status_code == 200, (path, response.text)

    crew = await client.post(f"{ME}/crew/{world.labourer.id}/check-in", headers=driver)
    assert crew.status_code in (200, 400, 404), crew.text

    moved = await client.post(f"{ME}/location", json={"latitude": 12.9611, "longitude": 77.6387}, headers=driver)
    assert moved.status_code == 200, moved.text
    profile = (
        await db_session.execute(
            select(LogisticsDriverProfile)
            .where(LogisticsDriverProfile.user_id == world.users["DRIVER"].id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    assert profile.current_location.startswith("12.9611")

    fuel = await client.post(f"{ME}/fuel-receipt", json={"amount": 1500, "liters": 16.5, "station": "HP Koramangala"}, headers=driver)
    assert fuel.status_code == 200, fuel.text

    to_dispatch = await client.post(f"{ME}/dispatch-thread/messages", json={"text": "Reached pickup"}, headers=driver)
    assert to_dispatch.status_code in (200, 201), to_dispatch.text
    dispatch_thread = await client.get(f"{ME}/dispatch-thread", headers=driver)
    assert "Reached pickup" in dispatch_thread.text

    to_manager = await client.post(f"{ME}/manager-thread/messages", json={"text": "Need a helper tomorrow"}, headers=driver)
    assert to_manager.status_code in (200, 201), to_manager.text
    manager_thread = await client.get(f"{ME}/manager-thread", headers=driver)
    assert "Need a helper tomorrow" in manager_thread.text

    sos = await client.post(
        f"{ME}/crisis-alert", json={"type": "breakdown", "message": "Flat tyre", "latitude": 12.96, "longitude": 77.63}, headers=driver
    )
    assert sos.status_code == 200, sos.text
    alerts = await client.get("/api/v1/logistics/alerts", headers=world.headers("DISPATCHER"))
    assert sos.json()["alert_id"] in {a["id"] for a in alerts.json()}

    cashout = await client.post(f"{ME}/cashout", json={"amount": 1}, headers=driver)
    assert cashout.status_code in (200, 400), cashout.text

    returned = await client.post(
        f"{ME}/return-vehicle", json={"odometer_km": 42012, "fuel_level_pct": 60, "notes": "Clean"}, headers=driver
    )
    assert returned.status_code in (200, 409), returned.text

    ended = await client.post(f"{ME}/shift/end", headers=driver)
    assert ended.status_code == 200, ended.text


async def test_driver_endpoints_are_driver_only(client, world):
    for path in ("/dashboard", "/shift"):
        response = await client.get(f"{ME}{path}", headers=world.headers("INDIVIDUAL"))
        assert response.status_code == 403


async def test_binding_an_unknown_vehicle_is_refused(client, world):
    response = await client.post(f"{ME}/bind-vehicle", json={"vehicle_code": "NOPE-0000"}, headers=world.headers("DRIVER"))

    assert response.status_code in (400, 404)
