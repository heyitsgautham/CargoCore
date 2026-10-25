"""Every GET route answers without a server error for each role.

The route list comes from the app's own OpenAPI schema, so a new GET route is
covered as soon as it is registered. Path parameters are filled with ids from
the seeded world, or a random UUID when the world has no matching row, in
which case a 404 is the expected answer.
"""

import re
import uuid

import pytest

from app.main import app

ROLES = ["LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER", "INDIVIDUAL", "VENDOR", "AI_AGENT"]

# Routes that stream or upgrade rather than return a JSON body.
SKIP_PATHS = {"/ws/fleet"}


def _get_routes() -> list[str]:
    return sorted(
        path for path, methods in app.openapi()["paths"].items() if "get" in methods and path not in SKIP_PATHS
    )


def _path_values(world) -> dict[str, str]:
    return {
        "warehouse_id": str(world.warehouse.id),
        "order_id": str(world.order.id),
        "labourer_id": str(world.labourer.id),
        "user_id": str(world.users["INDIVIDUAL"].id),
        "driver_id": str(world.users["DRIVER"].id),
        "vehicle_id": str(world.vehicle.id),
        "zone_id": str(world.zone.id),
        "dock_id": str(world.dock.id),
        "station_id": str(world.station.id),
        "item_id": str(world.inventory_item.id),
        "tracking_code": world.order.tracking_code,
        "reference_code": "DMG-UNKNOWN",
    }


def _fill(path: str, values: dict[str, str]) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1), str(uuid.uuid4())), path)


@pytest.mark.asyncio
@pytest.mark.parametrize("role_name", ROLES)
async def test_no_get_route_returns_a_server_error(client, world, role_name):
    values = _path_values(world)
    failures = []
    for path in _get_routes():
        response = await client.get(_fill(path, values), headers=world.headers(role_name))
        if response.status_code >= 500:
            failures.append(f"{response.status_code} GET {path}: {response.text[:160]}")

    assert not failures, "\n".join(failures)


@pytest.mark.asyncio
async def test_proof_of_delivery_html_renders_from_the_backend_template(client, world):
    response = await client.get(
        f"/api/v1/orders/{world.order.id}/proof-of-delivery", headers=world.headers("LOGISTIC_MANAGER")
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<html" in response.text.lower()
