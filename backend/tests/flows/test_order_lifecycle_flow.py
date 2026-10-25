"""A customer order from booking to rating, over HTTP, with each step done by the role that owns it."""

import pytest
from sqlalchemy import select

from app.models.order import Order
from tests.factories import make_order

pytestmark = pytest.mark.asyncio


async def _call(client, world, method, path, role, json=None):
    return await client.request(method, f"/api/v1/orders{path}", json=json, headers=world.headers(role))


async def _order(db_session, order_id) -> Order:
    query = select(Order).where(Order.id == order_id).execution_options(populate_existing=True)
    return (await db_session.execute(query)).scalar_one()


async def test_customer_order_is_booked_dispatched_delivered_and_rated(client, world, db_session):
    created = await _call(
        client,
        world,
        "POST",
        "",
        "INDIVIDUAL",
        {
            "order_type": "INDIVIDUAL",
            "warehouse_id": str(world.warehouse.id),
            "pickup_addr": "14 MG Road, Bengaluru",
            "pickup_lat": 12.975,
            "pickup_lng": 77.606,
            "delivery_addr": "22 Indiranagar, Bengaluru",
            "delivery_lat": 12.978,
            "delivery_lng": 77.640,
            "cargo_weight_kg": 120,
            "total_amount": 2400,
        },
    )
    assert created.status_code == 201, created.text
    order_id = created.json()["id"]

    listing = await _call(client, world, "GET", "", "INDIVIDUAL")
    assert order_id in {row["id"] for row in listing.json()["items"]}

    updated = await _call(client, world, "PUT", f"/{order_id}", "INDIVIDUAL", {"cargo_type": "Furniture"})
    assert updated.status_code == 200, updated.text

    confirmed = await _call(client, world, "POST", f"/{order_id}/confirm", "LOGISTIC_MANAGER")
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "CONFIRMED"

    preview = await _call(client, world, "GET", f"/{order_id}/assignment-preview", "DISPATCHER")
    assert preview.status_code in (200, 404), preview.text

    assigned = await _call(
        client,
        world,
        "POST",
        f"/{order_id}/assign",
        "DISPATCHER",
        {"driver_id": str(world.users["DRIVER"].id), "vehicle_id": str(world.vehicle.id)},
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["status"] == "ASSIGNED"

    intelligence = await _call(client, world, "GET", f"/{order_id}/trip-intelligence", "DISPATCHER")
    assert intelligence.status_code == 200, intelligence.text

    in_transit = await _call(client, world, "POST", f"/{order_id}/transition", "DRIVER", {"next_status": "IN_TRANSIT"})
    assert in_transit.status_code == 200, in_transit.text

    pushed = await _call(
        client,
        world,
        "POST",
        f"/{order_id}/trip-intelligence/push",
        "DISPATCHER",
        {"selected_route": "primary", "dispatcher_note": "Avoid the flyover"},
    )
    assert pushed.status_code == 200, pushed.text

    deviation = await _call(
        client,
        world,
        "POST",
        f"/{order_id}/trip-intelligence/deviation",
        "DRIVER",
        {"reason": "Road closed", "details": "Water logging", "latitude": 12.97, "longitude": 77.61},
    )
    assert deviation.status_code == 200, deviation.text

    sent = await _call(client, world, "POST", f"/{order_id}/delivery-otp/send", "DRIVER", {"force_resend": False})
    assert sent.status_code == 200, sent.text
    otp = (await _order(db_session, order_id)).service_otp
    assert otp and otp.isdigit() and len(otp) == 4

    proof = {
        "image_data": "data:image/png;base64,iVBORw0KGgo=",
        "signature_data": "data:image/png;base64,iVBORw0KGgo=",
        "customer_name": "Asha Rao",
        "notes": "Left with the customer",
    }
    no_photo = await _call(client, world, "POST", f"/{order_id}/proof-of-delivery", "DRIVER", {"otp_code": otp})
    assert no_photo.status_code == 422

    wrong_code = "0000" if otp != "0000" else "1111"
    wrong = await _call(
        client, world, "POST", f"/{order_id}/proof-of-delivery", "DRIVER", {**proof, "otp_code": wrong_code}
    )
    assert wrong.status_code == 409
    assert wrong.json()["detail"] == "Invalid delivery OTP"

    delivered = await _call(
        client,
        world,
        "POST",
        f"/{order_id}/proof-of-delivery",
        "DRIVER",
        {**proof, "otp_code": otp},
    )
    assert delivered.status_code == 200, delivered.text
    assert delivered.json()["status"] == "DELIVERED"

    job_rating = await _call(client, world, "POST", f"/{order_id}/job-rating", "DRIVER", {"rating": 5, "feedback": "Smooth"})
    assert job_rating.status_code == 200, job_rating.text

    customer_rating = await _call(
        client, world, "POST", f"/{order_id}/customer-rating", "INDIVIDUAL", {"rating": 4, "feedback": "On time"}
    )
    assert customer_rating.status_code == 200, customer_rating.text

    stored = await _order(db_session, order_id)
    assert stored.customer_rating == 4
    assert stored.job_rating == 5
    assert stored.delivered_at is not None


async def test_status_machine_refuses_illegal_jumps(client, world):
    jump = await _call(
        client, world, "POST", f"/{world.order.id}/transition", "LOGISTIC_MANAGER", {"next_status": "DELIVERED"}
    )
    assert jump.status_code in (400, 409)

    unassigned = await _call(
        client, world, "POST", f"/{world.order.id}/transition", "LOGISTIC_MANAGER", {"next_status": "IN_TRANSIT"}
    )
    assert unassigned.status_code in (400, 409)


async def test_customer_can_cancel_and_staff_can_escalate(client, world, db_session):
    escalated = await _call(
        client, world, "POST", f"/{world.order.id}/escalate", "DISPATCHER", {"reason": "Customer unreachable"}
    )
    assert escalated.status_code in (200, 201), escalated.text

    cancelled = await _call(
        client, world, "POST", f"/{world.order.id}/cancel", "INDIVIDUAL", {"reason": "Plans changed"}
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "CANCELLED"

    again = await _call(client, world, "POST", f"/{world.order.id}/cancel", "INDIVIDUAL", {"reason": "Twice"})
    assert again.status_code in (400, 409)


async def test_other_customers_cannot_see_an_order(client, world, db_session):
    from tests.factories import make_user

    stranger = await make_user(db_session, "INDIVIDUAL")
    await db_session.commit()
    from tests.factories import auth_headers

    response = await client.get(f"/api/v1/orders/{world.order.id}", headers=auth_headers(stranger))

    assert response.status_code in (403, 404)


async def test_staff_can_soft_delete_and_dispatch_tools_run(client, world, db_session):
    draft = await make_order(db_session, world.users["INDIVIDUAL"], status="DRAFT", warehouse_id=world.warehouse.id)
    await db_session.commit()

    for path in ("/cluster", "/optimize-routes", "/auto-balance"):
        response = await _call(client, world, "POST", path, "DISPATCHER")
        assert response.status_code == 200, (path, response.text)

    deleted = await _call(client, world, "DELETE", f"/{draft.id}", "LOGISTIC_MANAGER")
    assert deleted.status_code == 204, deleted.text
    assert (await _order(db_session, draft.id)).is_deleted is True
