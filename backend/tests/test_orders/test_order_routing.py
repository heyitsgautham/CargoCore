from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsEscalation
from app.models.order import Order
from app.models.user import Role, User
from app.models.warehouse import Warehouse
from app.utils.hashing import hash_password
from tests.conftest import REGISTER_PAYLOAD

pytestmark = pytest.mark.asyncio


async def _get_registered_user(db_session: AsyncSession) -> User:
    result = await db_session.execute(
        select(User).where(User.email == REGISTER_PAYLOAD["email"])
    )
    return result.scalar_one()


async def _get_role_id(db_session: AsyncSession, role_name: str) -> int:
    result = await db_session.execute(
        select(Role.id).where(Role.name == role_name)
    )
    return result.scalar_one()


def _auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _create_operational_user_and_login(
    client: AsyncClient,
    db_session: AsyncSession,
    *,
    role_name: str,
    warehouse_id,
    name: str,
    username: str,
    email: str,
    password: str = "StrongPass123",
) -> dict:
    role_id = await _get_role_id(db_session, role_name)
    user = User(
        name=name,
        username=username,
        email=email,
        phone="9000000000",
        password_hash=hash_password(password),
        role_id=role_id,
        warehouse_id=warehouse_id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()


async def test_create_order_auto_assigns_single_active_warehouse(
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user_tokens: dict,
):
    warehouse = Warehouse(name="North Hub", address="123 North Road, Delhi", is_active=True)
    db_session.add(warehouse)
    await db_session.flush()

    response = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {registered_user_tokens['access_token']}"},
        json={
            "order_type": "INDIVIDUAL",
            "pickup_addr": "12 Pickup Street, Delhi",
            "delivery_addr": "45 Delivery Street, Noida",
            "total_amount": 2500,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["warehouse_id"] == str(warehouse.id)


async def test_create_order_prefers_less_loaded_warehouse_when_multiple_exist(
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user_tokens: dict,
):
    user = await _get_registered_user(db_session)

    busy_warehouse = Warehouse(name="Busy Hub", address="1 Busy Road, Delhi", is_active=True)
    available_warehouse = Warehouse(name="Available Hub", address="2 Free Road, Noida", is_active=True)
    db_session.add_all([busy_warehouse, available_warehouse])
    await db_session.flush()

    # Both hubs must be operational, since auto-assignment skips hubs with no staff or orders.
    dispatcher_role = (
        await db_session.execute(select(Role).where(Role.name == "DISPATCHER"))
    ).scalar_one()
    db_session.add(
        User(
            name="Available Dispatcher",
            username="available.dispatcher",
            email="available.dispatcher@example.com",
            password_hash=hash_password("StrongPass123"),
            role_id=dispatcher_role.id,
            warehouse_id=available_warehouse.id,
            is_active=True,
        )
    )
    db_session.add(
        Order(
            tracking_code="QC-EXISTLOAD",
            order_type="INDIVIDUAL",
            status="DRAFT",
            customer_id=user.id,
            warehouse_id=busy_warehouse.id,
            pickup_addr="Existing Pickup Address",
            delivery_addr="Existing Delivery Address",
        )
    )
    await db_session.flush()

    response = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {registered_user_tokens['access_token']}"},
        json={
            "order_type": "INDIVIDUAL",
            "pickup_addr": "89 New Pickup Street, Delhi",
            "delivery_addr": "90 New Delivery Street, Gurgaon",
            "total_amount": 3200,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["warehouse_id"] == str(available_warehouse.id)


async def test_create_order_skips_fresh_non_operational_hub_for_auto_assignment(
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user_tokens: dict,
):
    user = await _get_registered_user(db_session)
    dispatcher_role_id = await _get_role_id(db_session, "DISPATCHER")

    ready_warehouse = Warehouse(name="Ready Hub", address="7 Ready Road, Delhi", is_active=True)
    fresh_warehouse = Warehouse(name="Fresh Hub", address="8 Fresh Road, Noida", is_active=True)
    db_session.add_all([ready_warehouse, fresh_warehouse])
    await db_session.flush()

    db_session.add(
        User(
            name="Ready Dispatcher",
            username="ready_dispatcher",
            email="ready.dispatcher@example.com",
            phone="9000000001",
            password_hash="test",
            role_id=dispatcher_role_id,
            warehouse_id=ready_warehouse.id,
            is_active=True,
        )
    )
    db_session.add(
        Order(
            tracking_code="QC-READYLOAD",
            order_type="INDIVIDUAL",
            status="DRAFT",
            customer_id=user.id,
            warehouse_id=ready_warehouse.id,
            pickup_addr="Existing Pickup Address",
            delivery_addr="Existing Delivery Address",
        )
    )
    await db_session.flush()

    response = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {registered_user_tokens['access_token']}"},
        json={
            "order_type": "INDIVIDUAL",
            "pickup_addr": "11 Auto Pickup Street, Delhi",
            "delivery_addr": "22 Auto Delivery Street, Gurgaon",
            "total_amount": 4100,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["warehouse_id"] == str(ready_warehouse.id)


async def test_cancel_order_refunds_legacy_paid_order_without_payment_rows(
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user_tokens: dict,
):
    warehouse = Warehouse(name="Refund Hub", address="12 Refund Road, Delhi", is_active=True)
    db_session.add(warehouse)
    await db_session.flush()

    create_response = await client.post(
        "/api/v1/orders",
        headers=_auth_headers(registered_user_tokens),
        json={
            "order_type": "INDIVIDUAL",
            "pickup_addr": "12 Pickup Street, Delhi",
            "delivery_addr": "45 Delivery Street, Noida",
            "total_amount": 2500,
            "payment_mode": "Full Payment",
            "payment_status": "paid",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["paid_amount"] == 0
    assert created["payment_status"] == "paid"

    cancel_response = await client.post(
        f"/api/v1/orders/{created['id']}/cancel",
        headers=_auth_headers(registered_user_tokens),
        json={"reason": "Changed plans"},
    )

    assert cancel_response.status_code == 200
    cancelled = cancel_response.json()
    assert cancelled["status"] == "CANCELLED"
    assert cancelled["wallet_refund_amount"] == 2500
    assert cancelled["payment_status"] == "refunded"

    wallet_response = await client.get(
        "/api/v1/customer/wallet",
        headers=_auth_headers(registered_user_tokens),
    )

    assert wallet_response.status_code == 200
    wallet = wallet_response.json()
    assert wallet["balance"] == 2500
    assert any(tx["reason"] == "CANCELLATION_REFUND" for tx in wallet["transactions"])


async def test_create_order_with_initial_partial_payment_refunds_only_paid_amount_on_cancel(
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user_tokens: dict,
):
    warehouse = Warehouse(name="Partial Hub", address="98 Ledger Lane, Delhi", is_active=True)
    db_session.add(warehouse)
    await db_session.flush()

    create_response = await client.post(
        "/api/v1/orders",
        headers=_auth_headers(registered_user_tokens),
        json={
            "order_type": "INDIVIDUAL",
            "pickup_addr": "10 Start Avenue, Delhi",
            "delivery_addr": "20 Finish Avenue, Gurugram",
            "total_amount": 4000,
            "payment_mode": "Partial",
            "payment_status": "pending",
            "initial_payment_amount": 1200,
            "initial_payment_ref": "pay_partial_123",
            "initial_payment_mode": "ONLINE",
            "initial_payment_method": "Razorpay",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["paid_amount"] == 1200
    assert created["payment_status"] == "partial"

    cancel_response = await client.post(
        f"/api/v1/orders/{created['id']}/cancel",
        headers=_auth_headers(registered_user_tokens),
        json={"reason": "Reschedule later"},
    )

    assert cancel_response.status_code == 200
    cancelled = cancel_response.json()
    assert cancelled["wallet_refund_amount"] == 1200
    assert cancelled["payment_status"] == "refunded"

    wallet_response = await client.get(
        "/api/v1/customer/wallet",
        headers=_auth_headers(registered_user_tokens),
    )

    assert wallet_response.status_code == 200
    wallet = wallet_response.json()
    assert wallet["balance"] == 1200
    assert any(tx["amount"] == 1200 for tx in wallet["transactions"])


async def test_cancel_order_refunds_half_for_legacy_partial_booking_without_recorded_paid_amount(
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user_tokens: dict,
):
    warehouse = Warehouse(name="Legacy Partial Hub", address="77 Legacy Road, Delhi", is_active=True)
    db_session.add(warehouse)
    await db_session.flush()

    create_response = await client.post(
        "/api/v1/orders",
        headers=_auth_headers(registered_user_tokens),
        json={
            "order_type": "INDIVIDUAL",
            "pickup_addr": "1 Legacy Pickup, Delhi",
            "delivery_addr": "2 Legacy Drop, Noida",
            "total_amount": 3000,
            "payment_mode": "Partial",
            "payment_status": "pending",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["paid_amount"] == 0
    assert created["payment_status"] == "pending"

    cancel_response = await client.post(
        f"/api/v1/orders/{created['id']}/cancel",
        headers=_auth_headers(registered_user_tokens),
        json={"reason": "Not moving now"},
    )

    assert cancel_response.status_code == 200
    cancelled = cancel_response.json()
    assert cancelled["wallet_refund_amount"] == 1500

    wallet_response = await client.get(
        "/api/v1/customer/wallet",
        headers=_auth_headers(registered_user_tokens),
    )

    assert wallet_response.status_code == 200
    wallet = wallet_response.json()
    assert wallet["balance"] == 1500


async def test_dispatcher_can_escalate_order_into_logistics_queue(
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user_tokens: dict,
):
    warehouse = Warehouse(name="Escalation Hub", address="15 Escalation Road, Delhi", is_active=True)
    db_session.add(warehouse)
    await db_session.flush()

    dispatcher_tokens = await _create_operational_user_and_login(
        client,
        db_session,
        role_name="DISPATCHER",
        warehouse_id=warehouse.id,
        name="Dispatch Lead",
        username="dispatch_lead",
        email="dispatch.lead@example.com",
    )

    create_response = await client.post(
        "/api/v1/orders",
        headers=_auth_headers(registered_user_tokens),
        json={
            "order_type": "INDIVIDUAL",
            "pickup_addr": "10 Pickup Street, Delhi",
            "delivery_addr": "50 Delivery Street, Noida",
            "total_amount": 3200,
            "warehouse_id": str(warehouse.id),
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()

    confirm_response = await client.post(
        f"/api/v1/orders/{created['id']}/confirm",
        headers=_auth_headers(dispatcher_tokens),
    )
    assert confirm_response.status_code == 403

    user = await _get_registered_user(db_session)
    order = (
        await db_session.execute(select(Order).where(Order.id == UUID(created["id"])))
    ).scalar_one()
    order.status = "ASSIGNED"
    order.warehouse_id = warehouse.id
    order.customer_id = user.id
    db_session.add(order)
    await db_session.flush()

    escalate_response = await client.post(
        f"/api/v1/orders/{created['id']}/escalate",
        headers=_auth_headers(dispatcher_tokens),
        json={"reason": "Driver no-show, manager intervention required"},
    )

    assert escalate_response.status_code == 200
    escalation_body = escalate_response.json()
    assert escalation_body["status"] == "OPEN"
    assert created["tracking_code"] in escalation_body["title"]

    stored = (
        await db_session.execute(
            select(LogisticsEscalation).where(LogisticsEscalation.id == UUID(escalation_body["id"]))
        )
    ).scalar_one()
    assert f"[order:{created['id']}]" in (stored.action_details or "")

    list_response = await client.get(
        "/api/v1/orders?status_filter=ASSIGNED&page_size=20",
        headers=_auth_headers(dispatcher_tokens),
    )
    assert list_response.status_code == 200
    listed = list_response.json()["items"]
    listed_order = next(item for item in listed if item["id"] == created["id"])
    assert listed_order["escalated"] is True
    assert listed_order["escalation_status"] == "OPEN"


async def test_dispatcher_cannot_cancel_in_transit_order(
    client: AsyncClient,
    db_session: AsyncSession,
    registered_user_tokens: dict,
):
    warehouse = Warehouse(name="Transit Hub", address="99 Transit Road, Delhi", is_active=True)
    db_session.add(warehouse)
    await db_session.flush()

    dispatcher_tokens = await _create_operational_user_and_login(
        client,
        db_session,
        role_name="DISPATCHER",
        warehouse_id=warehouse.id,
        name="Transit Dispatcher",
        username="transit_dispatcher",
        email="transit.dispatcher@example.com",
    )

    create_response = await client.post(
        "/api/v1/orders",
        headers=_auth_headers(registered_user_tokens),
        json={
            "order_type": "INDIVIDUAL",
            "pickup_addr": "1 Warehouse Gate, Delhi",
            "delivery_addr": "2 Customer Lane, Gurugram",
            "total_amount": 4100,
            "warehouse_id": str(warehouse.id),
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()

    order = (
        await db_session.execute(select(Order).where(Order.id == UUID(created["id"])))
    ).scalar_one()
    order.status = "IN_TRANSIT"
    order.warehouse_id = warehouse.id
    db_session.add(order)
    await db_session.flush()

    cancel_response = await client.post(
        f"/api/v1/orders/{created['id']}/cancel",
        headers=_auth_headers(dispatcher_tokens),
        json={"reason": "Need to stop this"},
    )

    assert cancel_response.status_code == 409
    assert "Escalate it instead" in cancel_response.json()["detail"]
