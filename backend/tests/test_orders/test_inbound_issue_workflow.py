import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.logistics import LogisticsNotification
from app.models.order import Order, OrderItem
from app.models.support_ticket import SupportTicket
from app.models.user import Role, User
from app.models.vendor import VendorSupportTicket
from app.models.warehouse import Warehouse
from app.schemas.ai import AgentReplyRequest, TicketUpdate
from app.schemas.warehouse_operations import InboundDamageReport
from app.services import ai_support_service
from app.services.warehouse_operations_service import (
    generate_vendor_take_back,
    mark_inbound_received,
    report_inbound_damage,
)

pytestmark = pytest.mark.asyncio


async def _role(db_session, name: str) -> Role:
    return (
        await db_session.execute(select(Role).where(Role.name == name))
    ).scalar_one()


async def _build_inbound_context(db_session):
    vendor_role = await _role(db_session, "VENDOR")
    warehouse_manager_role = await _role(db_session, "WAREHOUSE_MANAGER")
    support_role = await _role(db_session, "LOGISTIC_MANAGER")

    warehouse = Warehouse(name="Inbound Ops Hub", address="10 Dock Street", is_active=True)
    db_session.add(warehouse)
    await db_session.flush()

    vendor = User(
        name="Vendor Contact",
        username="vendor.contact",
        email="vendor.contact@example.com",
        password_hash="hashed-password",
        role_id=vendor_role.id,
        company_name="Vendor Goods Co",
        is_active=True,
    )
    warehouse_manager = User(
        name="Warehouse Maya",
        username="warehouse.maya",
        email="warehouse.maya@example.com",
        password_hash="hashed-password",
        role_id=warehouse_manager_role.id,
        warehouse_id=warehouse.id,
        is_active=True,
    )
    support_manager = User(
        name="Support Liam",
        username="support.liam",
        email="support.liam@example.com",
        password_hash="hashed-password",
        role_id=support_role.id,
        is_active=True,
    )
    db_session.add_all([vendor, warehouse_manager, support_manager])
    await db_session.flush()

    order = Order(
        tracking_code="QC-INBOUND-1001",
        order_type="VENDOR",
        status="CONFIRMED",
        customer_id=vendor.id,
        warehouse_id=warehouse.id,
        warehouse_substatus="AWAITING_INBOUND",
        pickup_addr="Vendor Yard",
        pickup_type="hub",
        delivery_addr=warehouse.address,
    )
    db_session.add(order)
    await db_session.flush()

    db_session.add(
        OrderItem(
            order_id=order.id,
            sku="SKU-INBOUND-1",
            quantity=12,
            box_count=2,
        )
    )
    await db_session.flush()

    return warehouse, vendor, warehouse_manager, support_manager, order


@pytest.mark.asyncio
async def test_inbound_damage_creates_vendor_and_support_workflow_records(db_session):
    warehouse, vendor, warehouse_manager, support_manager, order = await _build_inbound_context(db_session)

    report = await report_inbound_damage(
        db_session,
        warehouse.id,
        order.id,
        InboundDamageReport(
            damaged_count=2,
            description="Two cartons arrived torn and wet.",
            photo_url="data:image/jpeg;base64,abc123",
        ),
        warehouse_manager,
    )
    await db_session.flush()

    vendor_ticket = (
        await db_session.execute(
            select(VendorSupportTicket).where(VendorSupportTicket.order_id == order.id)
        )
    ).scalar_one()
    support_ticket = (
        await db_session.execute(
            select(SupportTicket).where(SupportTicket.notes.contains(str(vendor_ticket.id)))
        )
    ).scalar_one()
    notifications = (
        await db_session.execute(select(LogisticsNotification).order_by(LogisticsNotification.created_at.asc()))
    ).scalars().all()

    assert report.order_id == order.id
    assert vendor_ticket.subject == "Inbound damage reported"
    assert "[meta:source=warehouse_inbound]" in (support_ticket.notes or "")
    assert "[meta:issue_type=damage]" in (support_ticket.notes or "")
    assert f"[meta:linked_damage_report_id={report.id}]" in (support_ticket.notes or "")
    assert any(item.target_user_id == vendor.id for item in notifications)
    assert any(item.target_user_id == support_manager.id for item in notifications)


@pytest.mark.asyncio
async def test_inbound_damage_resolution_controls_move_and_take_back(db_session):
    warehouse, vendor, warehouse_manager, support_manager, order = await _build_inbound_context(db_session)

    await report_inbound_damage(
        db_session,
        warehouse.id,
        order.id,
        InboundDamageReport(
            damaged_count=1,
            description="Pallet wrapping is broken and units are scratched.",
            photo_url=None,
        ),
        warehouse_manager,
    )
    await db_session.flush()

    support_ticket = (
        await db_session.execute(
            select(SupportTicket).where(SupportTicket.notes.contains(str(order.id)))
        )
    ).scalars().first()

    with pytest.raises(HTTPException) as blocked:
        await mark_inbound_received(db_session, warehouse.id, order.id)
    assert blocked.value.status_code == 409

    await ai_support_service.update_ticket(
        db_session,
        support_ticket.id,
        TicketUpdate(status="resolved", resolution_action="vendor_accept_move"),
        actor=support_manager,
    )
    move_result = await mark_inbound_received(db_session, warehouse.id, order.id)
    assert move_result.warehouse_substatus == "AWAITING_PICK"

    order.warehouse_substatus = "AWAITING_INBOUND"
    db_session.add(order)
    await db_session.flush()

    await ai_support_service.update_ticket(
        db_session,
        support_ticket.id,
        TicketUpdate(status="resolved", resolution_action="vendor_take_back"),
        actor=support_manager,
    )
    take_back_result = await generate_vendor_take_back(
        db_session,
        warehouse.id,
        order.id,
        warehouse_manager,
    )
    assert take_back_result.warehouse_substatus == "ON_HOLD"


@pytest.mark.asyncio
async def test_warehouse_inbound_ticket_requires_resolution_action_when_resolving(db_session):
    warehouse, vendor, warehouse_manager, support_manager, order = await _build_inbound_context(db_session)

    await report_inbound_damage(
        db_session,
        warehouse.id,
        order.id,
        InboundDamageReport(
            damaged_count=1,
            description="One carton arrived crushed.",
            photo_url=None,
        ),
        warehouse_manager,
    )
    await db_session.flush()

    support_ticket = (
        await db_session.execute(
            select(SupportTicket).where(SupportTicket.notes.contains(str(order.id)))
        )
    ).scalars().first()

    with pytest.raises(HTTPException) as blocked:
        await ai_support_service.update_ticket(
            db_session,
            support_ticket.id,
            TicketUpdate(status="resolved"),
            actor=support_manager,
        )

    assert blocked.value.status_code == 400
    assert "Vendor Cleared For Move" in blocked.value.detail


@pytest.mark.asyncio
async def test_support_reply_is_blocked_after_inbound_issue_is_resolved(db_session):
    warehouse, vendor, warehouse_manager, support_manager, order = await _build_inbound_context(db_session)

    await report_inbound_damage(
        db_session,
        warehouse.id,
        order.id,
        InboundDamageReport(
            damaged_count=1,
            description="One carton arrived crushed.",
            photo_url=None,
        ),
        warehouse_manager,
    )
    await db_session.flush()

    support_ticket = (
        await db_session.execute(
            select(SupportTicket).where(SupportTicket.notes.contains(str(order.id)))
        )
    ).scalars().first()

    await ai_support_service.update_ticket(
        db_session,
        support_ticket.id,
        TicketUpdate(status="resolved", resolution_action="vendor_accept_move"),
        actor=support_manager,
    )

    with pytest.raises(HTTPException) as blocked:
        await ai_support_service.reply_to_ticket(
            db_session,
            support_ticket.id,
            AgentReplyRequest(message="Please confirm once more."),
            support_manager,
        )

    assert blocked.value.status_code == 409
    assert "chat is closed" in blocked.value.detail


@pytest.mark.asyncio
async def test_legacy_resolved_pending_review_ticket_allows_move_to_picking(db_session):
    warehouse, vendor, warehouse_manager, support_manager, order = await _build_inbound_context(db_session)

    await report_inbound_damage(
        db_session,
        warehouse.id,
        order.id,
        InboundDamageReport(
            damaged_count=1,
            description="Legacy resolved ticket compatibility case.",
            photo_url=None,
        ),
        warehouse_manager,
    )
    await db_session.flush()

    support_ticket = (
        await db_session.execute(
            select(SupportTicket).where(SupportTicket.notes.contains(str(order.id)))
        )
    ).scalars().first()

    support_ticket.status = "resolved"
    db_session.add(support_ticket)
    await db_session.flush()

    move_result = await mark_inbound_received(db_session, warehouse.id, order.id)
    assert move_result.warehouse_substatus == "AWAITING_PICK"
