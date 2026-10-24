"""Seeds demo logistics data the first time a manager opens the dashboard."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import LogisticsDocument
from app.models.inventory import InventoryItem
from app.models.logistics import (
    LogisticsAlert,
    LogisticsChatMessage,
    LogisticsChatThread,
    LogisticsDailyStats,
    LogisticsDriverProfile,
    LogisticsEquipmentLedger,
    LogisticsEscalation,
    LogisticsMetric,
    LogisticsNotification,
    LogisticsReturnCase,
    LogisticsTask,
    LogisticsTransaction,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.order import Order
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.logistics.formatting import _now
from app.services.logistics.lookups import _get_or_create_user, _get_role


async def ensure_logistics_seed_data(db: AsyncSession, manager_user: User) -> None:
    warehouse_count = (await db.execute(select(func.count(Warehouse.id)))).scalar_one()
    if warehouse_count:
        return

    north = Warehouse(name="North-East Hub", address="12 Hudson Logistics Park, New York, NY", lat=40.7128, lng=-74.0060, capacity_limit=1500, is_active=True)
    south = Warehouse(name="South Hub", address="88 Austin Freight Avenue, Austin, TX", lat=30.2672, lng=-97.7431, capacity_limit=2000, is_active=True)
    west = Warehouse(name="West DC-04", address="44 Harbor Cargo Road, Los Angeles, CA", lat=34.0522, lng=-118.2437, capacity_limit=1200, is_active=True)
    db.add_all([north, south, west])
    await db.flush()

    wm_north = await _get_or_create_user(db, role_name="WAREHOUSE_MANAGER", email="ellen.r@cargocore.com", username="ellen_r", name="Ellen Ripley", warehouse_id=north.id, phone="+1 (555) 555-0101")
    wm_south = await _get_or_create_user(db, role_name="WAREHOUSE_MANAGER", email="sarah.c@cargocore.com", username="sarah_c", name="Sarah Connor", warehouse_id=south.id, phone="+1 (555) 123-4567")
    await _get_or_create_user(db, role_name="DISPATCHER", email="john.w@cargocore.com", username="john_w", name="John Wick", warehouse_id=north.id, phone="+1 (555) 987-6543")
    driver_one = await _get_or_create_user(db, role_name="DRIVER", email="david.m@cargocore.com", username="david_m", name="David Miller", warehouse_id=north.id, phone="+1 (555) 123-4567")
    driver_two = await _get_or_create_user(db, role_name="DRIVER", email="sarah.j@cargocore.com", username="sarah_j", name="Sarah Jenkins", warehouse_id=south.id, phone="+1 (555) 987-6543")

    north.manager_id = wm_north.id
    south.manager_id = wm_south.id
    west.manager_id = manager_user.id
    db.add_all([north, south, west])
    await db.flush()

    vendor_role = await _get_role(db, "VENDOR")
    customer = (await db.execute(select(User).where(User.role_id == vendor_role.id))).scalar_one_or_none() or manager_user

    db.add_all([
        LogisticsDriverProfile(user_id=driver_one.id, warehouse_id=north.id, status="breakdown", current_location="Route 4B", current_job="Delivery #9982", efficiency_score=85, avatar_color="bg-gray-700", chat_history=[{"id": 1, "text": "Dispatch, engine light just came on.", "sender": "driver", "time": "09:15 AM"}, {"id": 2, "text": "Copy that David. Sending mobile mechanic.", "sender": "dispatch", "time": "09:16 AM"}]),
        LogisticsDriverProfile(user_id=driver_two.id, warehouse_id=south.id, status="deviation", current_location="Sector 7", current_job="Delivery #9991", efficiency_score=92, avatar_color="bg-gray-700", chat_history=[{"id": 1, "text": "Traffic on Route 9 is blocked.", "sender": "driver", "time": "10:42 AM"}, {"id": 2, "text": "Reroute approved. Follow the AI map.", "sender": "dispatch", "time": "10:43 AM"}]),
    ])

    vehicle_one = LogisticsVehicle(code="TRK-992", vehicle_type="Heavy Truck", warehouse_id=north.id, assigned_driver_id=driver_one.id, model="Volvo FH16", year=2021, license_plate="NY-442-XM", status="In Shop", fuel_efficiency="8.2 MPG", mileage=124500, maintenance_issue="Engine Check Light", next_service_date=_now() + timedelta(days=3))
    vehicle_two = LogisticsVehicle(code="VAN-104", vehicle_type="Delivery Van", warehouse_id=north.id, assigned_driver_id=driver_two.id, model="Ford Transit", year=2022, license_plate="NY-991-AB", status="Scheduled", fuel_efficiency="18.5 MPG", mileage=45200, maintenance_issue="Tire Replacement", next_service_date=_now() + timedelta(days=10))
    vehicle_three = LogisticsVehicle(code="TRK-221", vehicle_type="Heavy Truck", warehouse_id=south.id, model="Peterbilt 579", year=2020, license_plate="TX-118-PQ", status="Active", fuel_efficiency="7.9 MPG", mileage=210000, next_service_date=_now() + timedelta(days=21))
    db.add_all([vehicle_one, vehicle_two, vehicle_three])
    await db.flush()

    orders = [
        Order(tracking_code="QC-LOGI001", order_type="VENDOR", status="IN_TRANSIT", customer_id=customer.id, warehouse_id=north.id, assigned_driver_id=driver_one.id, assigned_vehicle_id=vehicle_one.id, pickup_addr="Amazon FC, Newark, NJ", delivery_addr="Client DC, Boston, MA", cargo_type="Retail Goods", vehicle_type="Truck", labor_count=2, base_amount=12000, vehicle_amount=3000, labor_amount=1200, materials_amount=600, packing_amount=350, platform_fee=500, tax_amount=980, total_amount=18630, payment_mode="Credit", payment_status="paid", scheduled_at=_now() - timedelta(hours=3)),
        Order(tracking_code="QC-LOGI002", order_type="VENDOR", status="ASSIGNED", customer_id=customer.id, warehouse_id=south.id, assigned_driver_id=driver_two.id, assigned_vehicle_id=vehicle_two.id, pickup_addr="Vendor Hub, Austin, TX", delivery_addr="Retail Outlet, Dallas, TX", cargo_type="Electronics", vehicle_type="Van", labor_count=1, base_amount=8000, vehicle_amount=1800, labor_amount=600, materials_amount=220, packing_amount=180, platform_fee=350, tax_amount=700, total_amount=11850, payment_mode="COD", payment_status="pending", scheduled_at=_now() + timedelta(hours=2)),
        Order(tracking_code="QC-LOGI003", order_type="VENDOR", status="DELIVERED", customer_id=customer.id, warehouse_id=west.id, pickup_addr="Port Cargo Gate, LA", delivery_addr="Warehouse Client, San Diego, CA", cargo_type="Furniture", vehicle_type="Truck", labor_count=3, base_amount=14000, vehicle_amount=3400, labor_amount=1600, materials_amount=900, packing_amount=500, platform_fee=650, tax_amount=1220, total_amount=22270, payment_mode="Transfer", payment_status="paid", scheduled_at=_now() - timedelta(days=1)),
    ]
    db.add_all(orders)

    db.add_all([
        InventoryItem(warehouse_id=north.id, sku="INV-001", name="Packing Tape", category="Consumables", unit="Rolls", quantity_on_hand=1540, safety_stock=200, aisle="Zone A"),
        InventoryItem(warehouse_id=south.id, sku="INV-003", name="Cardboard Box (M)", category="Packaging", unit="Pcs", quantity_on_hand=850, safety_stock=1000, aisle="Zone B"),
        InventoryItem(warehouse_id=north.id, sku="INV-009", name="Cargo Straps", category="Cargo", unit="Set", quantity_on_hand=500, safety_stock=100, aisle="Loading Dock"),
        InventoryItem(warehouse_id=south.id, sku="INV-010", name="Utensils (Breakroom)", category="Utensils", unit="Set", quantity_on_hand=200, safety_stock=220, aisle="Breakroom"),
    ])

    db.add_all([
        LogisticsTransaction(warehouse_id=north.id, transaction_code="TX-99212", description="Client Payment - Amazon", transaction_type="Incoming", amount=15400, status="Completed"),
        LogisticsTransaction(warehouse_id=north.id, transaction_code="TX-99213", description="Fuel Expense - Shell", transaction_type="Expense", amount=-2400, status="Completed"),
        LogisticsTransaction(warehouse_id=south.id, transaction_code="TX-99214", description="Driver Payout - Weekly", transaction_type="Payroll", amount=-6500, status="Paid"),
        LogisticsTransaction(warehouse_id=south.id, transaction_code="TX-99215", description="COD Deposit - Zone A", transaction_type="Incoming", amount=1250, status="Pending"),
    ])

    db.add_all([
        LogisticsZone(warehouse_id=north.id, name="Downtown Delivery Zone", zone_type="Polygon", radius_km=12, status="Active", color_token="blue"),
        LogisticsZone(warehouse_id=north.id, name="North-East Hub Perimeter", zone_type="Circle", radius_km=0.5, status="Active", color_token="green"),
        LogisticsZone(warehouse_id=south.id, name="Red Zone - Construction", zone_type="Exclusion", radius_km=2.5, status="Alert", color_token="red"),
        LogisticsZone(warehouse_id=south.id, name="Airport Logistics Corridor", zone_type="Polygon", radius_km=45, status="Active", color_token="indigo"),
    ])

    db.add_all([
        LogisticsAlert(warehouse_id=north.id, alert_type="congestion", title="Hub Congestion Alert", description="North-East Hub is experiencing high dwell times (>45 mins).", severity="high", icon="error", location="North-East Hub", recommendation="Reroute incoming traffic to South Hub temporarily.", impact_json={"affectedDrivers": 12}, is_active=True),
        LogisticsAlert(warehouse_id=south.id, alert_type="delayed", title="Delayed Shipments", description="14 shipments at risk of missing SLA window in Sector 4.", severity="medium", icon="schedule", location="Sector 4", recommendation="Assign priority status to these deliveries.", impact_json={"impact": "Potential SLA breach for 14 clients"}, is_active=True),
    ])

    db.add_all([
        LogisticsNotification(title="New Hub Alert", message="North-East hub congestion > 90%", type="alert"),
        LogisticsNotification(title="Driver Update", message="David Miller reported breakdown", type="warning"),
        LogisticsNotification(title="Shipment Delivered", message="Order QC-LOGI003 delivered", type="success"),
        LogisticsTask(text="Review daily hub performance", status="Priority", target_time=_now() + timedelta(hours=1), repeat_rule="none"),
        LogisticsTask(text="Approve Fleet Maintenance", status="Done", target_time=_now() - timedelta(hours=2), repeat_rule="none"),
    ])

    thread_one = LogisticsChatThread(warehouse_id=north.id, name="Dispatcher Mike", status="Online", phone="+1 (555) 012-3456", muted=False, last_message="Two trucks are down.", last_message_at=_now() - timedelta(minutes=2))
    thread_two = LogisticsChatThread(warehouse_id=south.id, name="Warehouse Team A", status="Offline", phone="+1 (555) 012-7890", muted=False, last_message="Inventory count complete.", last_message_at=_now() - timedelta(hours=1))
    db.add_all([thread_one, thread_two])
    await db.flush()

    db.add_all([
        LogisticsChatMessage(thread_id=thread_one.id, sender="other", text="Hi Boss, we have a situation at Hub 4.", created_at=_now() - timedelta(minutes=6)),
        LogisticsChatMessage(thread_id=thread_one.id, sender="other", text="Two trucks are down.", created_at=_now() - timedelta(minutes=4)),
        LogisticsChatMessage(thread_id=thread_one.id, sender="me", text="Approved. Use the contingency budget.", created_at=_now() - timedelta(minutes=3)),
        LogisticsChatMessage(thread_id=thread_two.id, sender="other", text="Inventory count complete. Report filed.", created_at=_now() - timedelta(hours=1)),
        LogisticsEscalation(warehouse_id=south.id, title="Route Deviation Override Required", priority="High", requester_name="Sarah Connor", requester_role="Dispatcher (South Hub)", description="Driver Alex Morgan is requesting a geofence override due to road construction.", action_details="Approve Geofence Override for V-402", status="OPEN"),
        LogisticsEscalation(warehouse_id=north.id, title="Fuel Limit Exceeded Action Required", priority="Medium", requester_name="System Bot", requester_role="Automated Alert", description="Vehicle V-105 submitted a fuel receipt that exceeds the daily limit.", action_details="Review OCR Receipt vs GPS Log", status="OPEN"),
        LogisticsReturnCase(warehouse_id=north.id, order_id=orders[0].id, reference_code="RMA-9921", customer_name="Alice Cooper", reason="Damaged in transit", condition="Damaged", status="Pending", original_price=150, refund_amount=0, images=["https://placehold.co/600x400/png?text=Damaged+Box+Corner"]),
        LogisticsReturnCase(warehouse_id=south.id, order_id=orders[1].id, reference_code="RMA-9923", customer_name="Charlie Watts", reason="Changed Mind", condition="Unopened", status="Approved", original_price=1250, refund_amount=1250, images=[]),
    ])

    await db.flush()

    # Seed historical daily stats for the past 30 days
    for days_ago in range(30, 0, -1):
        stat_date = (_now() - timedelta(days=days_ago)).date()
        
        # Global stats
        daily_orders = 1000 + int((30 - days_ago) * 8.3) + (hash(str(stat_date)) % 150)
        daily_revenue = 35000 + int((30 - days_ago) * 500) + (hash(str(stat_date)) % 5000)
        
        db.add(LogisticsDailyStats(
            warehouse_id=None,
            stat_date=stat_date,
            orders_count=daily_orders,
            revenue=daily_revenue,
            deliveries_completed=int(daily_orders * 0.98),
            deliveries_failed=int(daily_orders * 0.02),
            sla_compliance=85 + (hash(str(stat_date)) % 15),
        ))
        
        # Per-warehouse stats
        for warehouse in [north, south, west]:
            ratio = 0.33 if warehouse == north else (0.45 if warehouse == south else 0.22)
            hub_orders = int(daily_orders * ratio)
            hub_revenue = daily_revenue * ratio
            
            db.add(LogisticsDailyStats(
                warehouse_id=warehouse.id,
                stat_date=stat_date,
                orders_count=hub_orders,
                revenue=hub_revenue,
                deliveries_completed=int(hub_orders * 0.98),
                deliveries_failed=int(hub_orders * 0.02),
                sla_compliance=82 + (hash(f"{warehouse.id}{stat_date}") % 18),
            ))

    db.add_all([
        LogisticsEquipmentLedger(warehouse_id=north.id, item_type="Crates (Standard)", issued_count=450, returned_count=410, reference_code="ORD-4920", status="Pending Collection"),
        LogisticsEquipmentLedger(warehouse_id=south.id, item_type="Thermal Blankets", issued_count=120, returned_count=120, reference_code="ORD-4921", status="Cleared"),
        LogisticsEquipmentLedger(warehouse_id=west.id, item_type="Pallets (Wood)", issued_count=800, returned_count=750, reference_code="ORD-4925", status="Pending Collection"),
        LogisticsEquipmentLedger(warehouse_id=None, item_type="Refrigerant Packs", issued_count=1800, returned_count=1500, reference_code="NET-SYS", status="Pending Collection"),
    ])

    metrics = []
    for i, (label, val) in enumerate(zip(["Jan", "Feb", "Mar", "Apr", "May", "Jun"], [5.2, 4.8, 4.4, 4.1, 3.9, 4.0], strict=True)):
        metrics.append(LogisticsMetric(metric_type="vendor_lead_time", label=label, value_main=val))
        metrics.append(LogisticsMetric(metric_type="safety_incidents", label=label, value_main=[2, 3, 1, 2, 1, 0][i]))
    
    for label, eff, ot in zip(["Shift A", "Shift B", "Shift C"], [92, 88, 95], [12, 18, 5], strict=True):
        metrics.append(LogisticsMetric(metric_type="shift_efficiency", label=label, value_main=eff, value_secondary=ot))
    
    for label, val in zip(["6am-9am", "9am-12pm", "12pm-3pm", "3pm-6pm", "6pm-9pm"], [15, 45, 25, 60, 20], strict=True):
        metrics.append(LogisticsMetric(metric_type="dwell_time", label=label, value_main=val))
    
    db.add_all(metrics)

    # Seed initial Fleet/Driver documents if not present
    existing_docs = (await db.execute(select(func.count(LogisticsDocument.id)))).scalar_one()
    if existing_docs == 0:
        db.add_all([
            # Vehicle Documents (using vehicle UUID as entity_id, not code)
            LogisticsDocument(entity_type="VEHICLE", entity_id=str(vehicle_one.id), hub_id=north.id, doc_type="Insurance Policy", document_url="https://placehold.co/400x500?text=" + vehicle_one.code + "+Insurance", status="Active", expiry_date=_now() + timedelta(days=180)),
            LogisticsDocument(entity_type="VEHICLE", entity_id=str(vehicle_one.id), hub_id=north.id, doc_type="Vehicle Registration", document_url="https://placehold.co/400x500?text=" + vehicle_one.code + "+Registration", status="Active", expiry_date=_now() + timedelta(days=300)),
            LogisticsDocument(entity_type="VEHICLE", entity_id=str(vehicle_two.id), hub_id=north.id, doc_type="Insurance Policy", document_url="https://placehold.co/400x500?text=" + vehicle_two.code + "+Insurance", status="Expiring Soon", expiry_date=_now() + timedelta(days=10)),
            # Driver Documents
            LogisticsDocument(entity_type="DRIVER", entity_id=str(driver_one.id), hub_id=north.id, doc_type="Commercial License (CDL)", document_url="https://placehold.co/400x500?text=" + driver_one.name.replace(" ", "+") + "+CDL", status="Active", expiry_date=_now() + timedelta(days=240)),
            LogisticsDocument(entity_type="DRIVER", entity_id=str(driver_two.id), hub_id=south.id, doc_type="Medical Certificate", document_url="https://placehold.co/400x500?text=" + driver_two.name.replace(" ", "+") + "+Medical", status="Pending Verification", expiry_date=_now() + timedelta(days=120)),
        ])
        await db.flush()
