import pytest
from sqlalchemy import select

from app.models.logistics import LogisticsReturnCase
from app.models.order import Order
from app.models.user import Role, User
from app.models.wallet import WalletTransaction
from app.models.warehouse import ReturnGrading, Warehouse
from app.schemas.customer import CustomerDamageReportCreate
from app.schemas.logistics import LogisticsReturnCaseUpdate
from app.schemas.orders import CancelOrderRequest, OrderCreate
from app.schemas.warehouse_operations import ReturnGradingCreate
from app.services.customer_service import create_customer_damage_report
from app.services.finance_service import get_finance_summary, record_order_payment
from app.services.logistics_service import build_bootstrap, update_return_case
from app.services.orders_service import cancel_order, create_order
from app.services.return_charge_service import (
    apply_rejected_claim_transport_charge,
    get_unattached_pending_transport_charge_total,
)
from app.services.wallet_service import get_wallet_balance
from app.services.warehouse_operations_service import (
    create_return_grading,
    get_return_gradings,
)


@pytest.mark.asyncio
async def test_damage_report_creates_pending_return_grading_for_warehouse_order(db_session):
    individual_role = (
        await db_session.execute(select(Role).where(Role.name == "INDIVIDUAL"))
    ).scalar_one()

    warehouse = Warehouse(name="Returns Hub", address="123 Warehouse Road")
    db_session.add(warehouse)
    await db_session.flush()

    customer = User(
        name="Casey Customer",
        username="casey.customer",
        email="casey.customer@example.com",
        password_hash="hashed-password",
        role_id=individual_role.id,
        role=individual_role,
    )
    db_session.add(customer)
    await db_session.flush()

    order = Order(
        tracking_code="ORD-RET-1001",
        order_type="INDIVIDUAL",
        status="DELIVERED",
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        pickup_addr="10 Pickup Street",
        delivery_addr="20 Delivery Street",
        total_amount=499.0,
    )
    db_session.add(order)
    await db_session.flush()

    result = await create_customer_damage_report(
        db_session,
        customer,
        CustomerDamageReportCreate(
            order_id=str(order.id),
            description="Outer box arrived crushed and the item is scratched.",
            photos=["photo-1.png"],
        ),
    )

    return_case = (
        await db_session.execute(
            select(LogisticsReturnCase).where(
                LogisticsReturnCase.reference_code == result.id
            )
        )
    ).scalar_one()
    grading = (
        await db_session.execute(
            select(ReturnGrading).where(ReturnGrading.rma_code == result.id)
        )
    ).scalar_one()

    assert return_case.order_id == order.id
    assert return_case.warehouse_id == warehouse.id
    assert grading.order_id == order.id
    assert grading.warehouse_id == warehouse.id
    assert grading.status == "pending"
    assert grading.disposition == "pending"
    assert grading.item_condition == "Pending Inspection"
    assert grading.condition_notes == "Outer box arrived crushed and the item is scratched."


@pytest.mark.asyncio
async def test_pending_return_case_is_backfilled_into_awaiting_grading_queue(db_session):
    warehouse = Warehouse(name="Backfill Hub", address="456 Warehouse Lane")
    db_session.add(warehouse)
    await db_session.flush()

    return_case = LogisticsReturnCase(
        warehouse_id=warehouse.id,
        order_id=None,
        reference_code="DMG-BACKFILL",
        customer_name="Pat Pending",
        reason="Customer reported transit damage.",
        condition="Reported",
        status="Pending",
        original_price=120.0,
        refund_amount=0.0,
        images=[],
    )
    db_session.add(return_case)
    await db_session.commit()

    response = await get_return_gradings(db_session, warehouse.id, status_filter="pending")

    created_grading = (
        await db_session.execute(
            select(ReturnGrading).where(ReturnGrading.rma_code == "DMG-BACKFILL")
        )
    ).scalar_one()

    assert any(item.rma_code == "DMG-BACKFILL" for item in response.items)
    assert created_grading.warehouse_id == warehouse.id
    assert created_grading.status == "pending"
    assert created_grading.item_condition == "Pending Inspection"


@pytest.mark.asyncio
async def test_create_return_grading_persists_wm_inspection_metadata(db_session):
    warehouse_manager_role = (
        await db_session.execute(select(Role).where(Role.name == "WAREHOUSE_MANAGER"))
    ).scalar_one()

    warehouse = Warehouse(name="Inspection Hub", address="789 Inspection Road")
    db_session.add(warehouse)
    await db_session.flush()

    grader = User(
        name="Wanda Manager",
        username="wanda.manager",
        email="wanda.manager@example.com",
        password_hash="hashed-password",
        role_id=warehouse_manager_role.id,
        warehouse_id=warehouse.id,
    )
    db_session.add(grader)
    await db_session.flush()

    created = await create_return_grading(
        db_session,
        warehouse.id,
        data=ReturnGradingCreate(
            order_id=None,
            rma_code="RMA-INSPECT-1",
            item_condition="Damaged",
            condition_notes="Corner crushed and wheel housing cracked.",
            disposition="claims",
            is_genuine=True,
            recommended_outcome="Partial Refund",
            inspection_remarks="Transport damage confirmed after unpacking.",
        ),
        graded_by=grader.id,
    )

    assert created.is_genuine is True
    assert created.recommended_outcome == "Partial Refund"
    assert created.inspection_remarks == "Transport damage confirmed after unpacking."

    stored = (
        await db_session.execute(
            select(ReturnGrading).where(ReturnGrading.rma_code == "RMA-INSPECT-1")
        )
    ).scalar_one()
    assert stored.is_genuine is True
    assert stored.recommended_outcome == "Partial Refund"
    assert stored.inspection_remarks == "Transport damage confirmed after unpacking."


@pytest.mark.asyncio
async def test_logistics_return_payload_includes_completed_wm_inspection_details(db_session):
    individual_role = (
        await db_session.execute(select(Role).where(Role.name == "INDIVIDUAL"))
    ).scalar_one()
    warehouse_manager_role = (
        await db_session.execute(select(Role).where(Role.name == "WAREHOUSE_MANAGER"))
    ).scalar_one()

    warehouse = Warehouse(name="LM Visibility Hub", address="987 Visibility Road")
    db_session.add(warehouse)
    await db_session.flush()

    customer = User(
        name="Logistics Customer",
        username="logistics.customer",
        email="logistics.customer@example.com",
        password_hash="hashed-password",
        role_id=individual_role.id,
        warehouse_id=warehouse.id,
    )
    grader = User(
        name="Priya Warehouse",
        username="priya.warehouse",
        email="priya.warehouse@example.com",
        password_hash="hashed-password",
        role_id=warehouse_manager_role.id,
        warehouse_id=warehouse.id,
    )
    db_session.add_all([customer, grader])
    await db_session.flush()

    order = Order(
        tracking_code="ORD-LM-2001",
        order_type="INDIVIDUAL",
        status="DELIVERED",
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        pickup_addr="12 Pickup Street",
        delivery_addr="34 Delivery Street",
        total_amount=899.0,
    )
    db_session.add(order)
    await db_session.flush()

    case = LogisticsReturnCase(
        warehouse_id=warehouse.id,
        order_id=order.id,
        reference_code="RMA-LM-2001",
        customer_name=customer.name,
        reason="Customer requested physical check after transit damage.",
        flow_type="pickup_inspection",
        condition="Reported",
        status="At Warehouse",
        original_price=899.0,
        refund_amount=0.0,
        images=["customer-photo.png"],
    )
    grading = ReturnGrading(
        warehouse_id=warehouse.id,
        order_id=order.id,
        rma_code="RMA-LM-2001",
        item_condition="Broken",
        condition_notes="Frame bent and top panel cracked.",
        disposition="claims",
        is_genuine=False,
        recommended_outcome="Reject Claim",
        inspection_remarks="Damage pattern does not match transit impact; packaging intact.",
        damage_photo_url="data:image/png;base64,abc123",
        graded_by=grader.id,
        status="completed",
    )
    db_session.add_all([case, grading])
    await db_session.commit()

    payload = await build_bootstrap(db_session)
    item = next(r for r in payload.returns if r.reference_code == "RMA-LM-2001")

    assert item.status == "Physically Inspected"
    assert item.condition == "Broken"
    assert item.wm_disposition == "claims"
    assert item.wm_is_genuine is False
    assert item.wm_recommended_outcome == "Reject Claim"
    assert item.wm_inspection_remarks == "Damage pattern does not match transit impact; packaging intact."
    assert item.wm_grader_name == "Priya Warehouse"
    assert "data:image/png;base64,abc123" in item.images


@pytest.mark.asyncio
async def test_update_return_case_response_keeps_wm_inspection_context(db_session):
    warehouse_manager_role = (
        await db_session.execute(select(Role).where(Role.name == "WAREHOUSE_MANAGER"))
    ).scalar_one()

    warehouse = Warehouse(name="Status Update Hub", address="55 Update Lane")
    db_session.add(warehouse)
    await db_session.flush()

    grader = User(
        name="Riya Inspector",
        username="riya.inspector",
        email="riya.inspector@example.com",
        password_hash="hashed-password",
        role_id=warehouse_manager_role.id,
        warehouse_id=warehouse.id,
    )
    case = LogisticsReturnCase(
        warehouse_id=warehouse.id,
        order_id=None,
        reference_code="RMA-STATUS-1",
        customer_name="Status Customer",
        reason="Physical inspection completed.",
        flow_type="pickup_inspection",
        condition="Reported",
        status="Physically Inspected",
        original_price=450.0,
        refund_amount=0.0,
        images=[],
    )
    db_session.add_all([grader, case])
    await db_session.flush()

    db_session.add(
        ReturnGrading(
            warehouse_id=warehouse.id,
            order_id=None,
            rma_code="RMA-STATUS-1",
            item_condition="Damaged",
            condition_notes="Surface scratch and loose base.",
            disposition="claims",
            is_genuine=True,
            recommended_outcome="Full Refund",
            inspection_remarks="Claim validated after unpacking and test run.",
            graded_by=grader.id,
            status="completed",
        )
    )
    await db_session.commit()

    updated = await update_return_case(
        db_session,
        case.id,
        LogisticsReturnCaseUpdate(status="Approved", refund_amount=450.0),
    )

    assert updated.status == "Approved"
    assert updated.wm_is_genuine is True
    assert updated.wm_recommended_outcome == "Full Refund"
    assert updated.wm_inspection_remarks == "Claim validated after unpacking and test run."
    assert updated.wm_grader_name == "Riya Inspector"


@pytest.mark.asyncio
async def test_rejected_physical_inspection_auto_applies_transport_charge_for_not_genuine_claim(db_session):
    individual_role = (
        await db_session.execute(select(Role).where(Role.name == "INDIVIDUAL"))
    ).scalar_one()
    warehouse_manager_role = (
        await db_session.execute(select(Role).where(Role.name == "WAREHOUSE_MANAGER"))
    ).scalar_one()

    warehouse = Warehouse(name="Auto Charge Hub", address="12 Auto Charge Road")
    db_session.add(warehouse)
    await db_session.flush()

    customer = User(
        name="Auto Charge Customer",
        username="auto.charge.customer",
        email="auto.charge.customer@example.com",
        password_hash="hashed-password",
        role_id=individual_role.id,
        role=individual_role,
    )
    grader = User(
        name="Auto Charge WM",
        username="auto.charge.wm",
        email="auto.charge.wm@example.com",
        password_hash="hashed-password",
        role_id=warehouse_manager_role.id,
        warehouse_id=warehouse.id,
    )
    db_session.add_all([customer, grader])
    await db_session.flush()

    order = Order(
        tracking_code="ORD-AUTO-CHARGE-1",
        order_type="INDIVIDUAL",
        status="DELIVERED",
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        pickup_addr="Auto Pickup",
        delivery_addr="Auto Drop",
        total_amount=1200.0,
    )
    db_session.add(order)
    await db_session.flush()

    db_session.add(
        WalletTransaction(
            user_id=customer.id,
            transaction_kind="CREDIT",
            reason="TOPUP",
            amount=800.0,
            description="Test topup",
        )
    )

    case = LogisticsReturnCase(
        warehouse_id=warehouse.id,
        order_id=order.id,
        reference_code="DMG-AUTO-CHARGE",
        customer_name=customer.name,
        reason="Physical inspection completed.",
        flow_type="pickup_inspection",
        condition="Reported",
        status="Physically Inspected",
        original_price=1200.0,
        refund_amount=0.0,
        images=[],
    )
    db_session.add(case)
    await db_session.flush()

    db_session.add(
        ReturnGrading(
            warehouse_id=warehouse.id,
            order_id=order.id,
            rma_code="DMG-AUTO-CHARGE",
            item_condition="No transit damage",
            condition_notes="Not genuine.",
            disposition="claims",
            is_genuine=False,
            recommended_outcome="Reject Claim",
            inspection_remarks="Packaging intact. Damage not caused in transit.",
            graded_by=grader.id,
            status="completed",
        )
    )
    await db_session.commit()

    updated = await update_return_case(
        db_session,
        case.id,
        LogisticsReturnCaseUpdate(status="Rejected"),
    )

    assert updated.status == "Rejected"
    assert updated.transport_charge_amount == 500.0
    assert updated.transport_charge_wallet_collected == 500.0
    assert updated.transport_charge_pending_amount == 0.0
    assert updated.transport_charge_status == "Collected from Wallet"
    assert await get_wallet_balance(db_session, customer.id) == 300.0


@pytest.mark.asyncio
async def test_rejected_claim_transport_charge_debits_wallet_and_hits_finance(db_session):
    individual_role = (
        await db_session.execute(select(Role).where(Role.name == "INDIVIDUAL"))
    ).scalar_one()

    warehouse = Warehouse(name="Charge Hub", address="11 Charge Lane")
    db_session.add(warehouse)
    await db_session.flush()

    customer = User(
        name="Wallet Customer",
        username="wallet.customer",
        email="wallet.customer@example.com",
        password_hash="hashed-password",
        role_id=individual_role.id,
        role=individual_role,
    )
    db_session.add(customer)
    await db_session.flush()

    original_order = Order(
        tracking_code="ORD-CHARGE-1",
        order_type="INDIVIDUAL",
        status="DELIVERED",
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        pickup_addr="Old Pickup",
        delivery_addr="Old Drop",
        total_amount=1200.0,
    )
    db_session.add(original_order)
    await db_session.flush()

    db_session.add(
        WalletTransaction(
            user_id=customer.id,
            order_id=None,
            transaction_kind="CREDIT",
            reason="TOPUP",
            amount=700.0,
            description="Manual wallet top-up",
        )
    )

    case = LogisticsReturnCase(
        warehouse_id=warehouse.id,
        order_id=original_order.id,
        reference_code="DMG-RTC-1",
        customer_name=customer.name,
        reason="Rejected after physical inspection.",
        flow_type="pickup_inspection",
        condition="Not Genuine",
        status="Rejected",
        original_price=1200.0,
        refund_amount=0.0,
        images=[],
    )
    db_session.add(case)
    await db_session.flush()

    charged = await apply_rejected_claim_transport_charge(
        db_session,
        case=case,
        customer_id=customer.id,
    )

    await db_session.commit()
    await db_session.refresh(case)

    assert charged == 500.0
    assert case.transport_charge_amount == 500.0
    assert case.transport_charge_wallet_collected == 500.0
    assert case.transport_charge_pending_amount == 0.0
    assert case.transport_charge_status == "Collected from Wallet"
    assert await get_wallet_balance(db_session, customer.id) == 200.0

    finance = await get_finance_summary(db_session)
    assert finance["total_revenue"] == 500.0
    assert finance["revenue_by_mode"]["RETURN_CHARGE"] == 500.0


@pytest.mark.asyncio
async def test_next_order_carries_forward_pending_transport_charge_without_refunding_it_on_cancel(db_session):
    individual_role = (
        await db_session.execute(select(Role).where(Role.name == "INDIVIDUAL"))
    ).scalar_one()

    warehouse = Warehouse(name="Carry Hub", address="44 Carry Street")
    db_session.add(warehouse)
    await db_session.flush()

    customer = User(
        name="Carry Customer",
        username="carry.customer",
        email="carry.customer@example.com",
        password_hash="hashed-password",
        role_id=individual_role.id,
        role=individual_role,
    )
    db_session.add(customer)
    await db_session.flush()

    original_order = Order(
        tracking_code="ORD-CARRY-ORIG",
        order_type="INDIVIDUAL",
        status="DELIVERED",
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        pickup_addr="Orig Pickup",
        delivery_addr="Orig Drop",
        total_amount=1400.0,
    )
    db_session.add(original_order)
    await db_session.flush()

    case = LogisticsReturnCase(
        warehouse_id=warehouse.id,
        order_id=original_order.id,
        reference_code="DMG-CARRY-1",
        customer_name=customer.name,
        reason="Rejected claim with pending transport charge.",
        flow_type="pickup_inspection",
        condition="Not Genuine",
        status="Rejected",
        original_price=1400.0,
        refund_amount=0.0,
        transport_charge_amount=500.0,
        transport_charge_wallet_collected=0.0,
        transport_charge_pending_amount=500.0,
        transport_charge_status="Pending Next Order",
        images=[],
    )
    db_session.add(case)
    await db_session.flush()

    booked = await create_order(
        db_session,
        OrderCreate(
            order_type="INDIVIDUAL",
            warehouse_id=warehouse.id,
            pickup_addr="New Pickup",
            delivery_addr="New Drop",
            cargo_type="Household Goods",
            vehicle_type="tempo",
            labor_count=1,
            base_amount=700.0,
            vehicle_amount=200.0,
            labor_amount=100.0,
            materials_amount=0.0,
            packing_amount=0.0,
            platform_fee=50.0,
            tax_amount=50.0,
            total_amount=1100.0,
            payment_mode="ONLINE",
            payment_status="pending",
        ),
        customer,
    )

    new_order = (
        await db_session.execute(select(Order).where(Order.id == booked.id))
    ).scalar_one()
    await db_session.refresh(case)

    assert new_order.carry_forward_charge_amount == 500.0
    assert new_order.total_amount == 1600.0
    assert case.transport_charge_order_id == new_order.id
    assert await get_unattached_pending_transport_charge_total(db_session, customer.id) == 0.0

    await record_order_payment(
        db_session,
        order_id=new_order.id,
        amount=600.0,
        payment_mode="ONLINE",
        payment_method="UPI",
        payment_ref="PAY-CARRY-600",
    )
    await db_session.flush()
    await db_session.refresh(new_order)
    await db_session.refresh(case)

    assert new_order.carry_forward_charge_paid_amount == 500.0
    assert case.transport_charge_pending_amount == 0.0
    assert case.transport_charge_status == "Collected"

    cancelled = await cancel_order(
        db_session,
        new_order.id,
        CancelOrderRequest(reason="Plans changed"),
        customer,
    )
    await db_session.flush()

    assert cancelled.wallet_refund_amount == 100.0
    assert await get_wallet_balance(db_session, customer.id) == 100.0
