"""Local answers when Gemini is unavailable, and the message context sent with each request."""


from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.ai_chat.constants import (
    DISPATCHER_CONTEXTS,
    LOGISTIC_MANAGER_CONTEXTS,
    SUPPORT_CHAT_CONTEXT,
    WAREHOUSE_CONTEXTS,
)
from app.services.ai_chat.intents import (
    _extract_order_status_filter,
    _extract_tracking_code,
    _is_analytics_section_question,
    _is_current_orders_question,
    _is_knowledge_question,
    _is_order_status_list_question,
    _is_recurring_data_question,
    _is_refund_question,
    _is_support_question,
    _is_wallet_balance_question,
    _role_name,
)
from app.services.ai_chat.logistics_answers import (
    _build_logistics_manager_snapshot,
    _logistics_dashboard_message,
    _logistics_driver_status_message,
    _logistics_fleet_status_message,
    _logistics_inventory_message,
    _logistics_returns_message,
    _logistics_revenue_message,
)
from app.services.ai_chat.self_service import (
    _format_self_service_order_message,
    _list_current_self_service_orders,
    _list_self_service_orders_by_status,
    _lookup_self_service_order,
    _self_service_refund_message,
    _vendor_analytics_message,
    _vendor_recurring_orders_message,
    _vendor_support_message,
    _vendor_wallet_message,
)
from app.services.ai_chat.staff_intents import (
    _is_logistic_manager_chat_context,
    _is_logistics_dashboard_question,
    _is_logistics_driver_question,
    _is_logistics_fleet_question,
    _is_logistics_inventory_question,
    _is_logistics_returns_question,
    _is_logistics_revenue_question,
    _is_warehouse_capacity_question,
    _is_warehouse_chat_context,
    _is_warehouse_dock_question,
    _is_warehouse_inventory_question,
    _is_warehouse_pending_question,
    _is_warehouse_returns_question,
    _is_warehouse_staff_question,
    _is_warehouse_workload_question,
)
from app.services.ai_chat.support_handoff import _answer_from_retrieved_knowledge
from app.services.ai_chat.warehouse_answers import _build_warehouse_snapshot
from app.services.ai_chat.warehouse_messages import (
    _warehouse_capacity_message,
    _warehouse_dock_message,
    _warehouse_inventory_message,
    _warehouse_overview_message,
    _warehouse_pending_orders_message,
    _warehouse_returns_message,
    _warehouse_staff_message,
    _warehouse_workload_message,
)


async def _local_fallback_response(
    ro_db: AsyncSession,
    user: User,
    user_message: str,
    chat_context: str | None = None,
    warehouse_snapshot: dict | None = None,
) -> str | None:
    msg = (user_message or "").strip().lower()
    role = _role_name(user)
    noun = "shipment" if role == "VENDOR" else "order"

    # Greeting
    if msg in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}:
        first = user.name.split()[0] if user.name else "there"
        if _is_warehouse_chat_context(user, chat_context):
            return (
                f"Hi {first}! Ask me about queue pressure, staff availability, free space, docks, returns, or workload in your warehouse."
            )
        if role == "LOGISTIC_MANAGER":
            return (
                f"Hi {first}! Ask me about hub performance, driver status, fleet readiness, inventory pressure, alerts, returns, revenue, or network operations."
            )
        if role == "VENDOR":
            return f"Hi {first}! Ask me about your shipments, wallet balance, invoices, or anything about your account."
        return f"Hi {first}! Ask me about your orders, wallet balance, spending, or anything about your account."

    if _is_warehouse_chat_context(user, chat_context):
        snapshot = warehouse_snapshot or await _build_warehouse_snapshot(ro_db, user)
        if snapshot:
            if _is_warehouse_workload_question(msg):
                return _warehouse_workload_message(snapshot)
            if _is_warehouse_staff_question(msg):
                return _warehouse_staff_message(snapshot)
            if _is_warehouse_capacity_question(msg):
                return _warehouse_capacity_message(snapshot)
            if _is_warehouse_pending_question(msg):
                return _warehouse_pending_orders_message(snapshot)
            if _is_warehouse_returns_question(msg):
                return _warehouse_returns_message(snapshot)
            if _is_warehouse_dock_question(msg):
                return _warehouse_dock_message(snapshot)
            if _is_warehouse_inventory_question(msg):
                return _warehouse_inventory_message(snapshot)
            return _warehouse_overview_message(snapshot)

    if _is_logistic_manager_chat_context(user, chat_context):
        snapshot = await _build_logistics_manager_snapshot(ro_db)
        if _is_logistics_driver_question(msg):
            return _logistics_driver_status_message(snapshot)
        if _is_logistics_fleet_question(msg):
            return _logistics_fleet_status_message(snapshot)
        if _is_logistics_inventory_question(msg):
            return _logistics_inventory_message(snapshot)
        if _is_logistics_returns_question(msg):
            return _logistics_returns_message(snapshot)
        if _is_logistics_revenue_question(msg):
            return _logistics_revenue_message(snapshot)
        if _is_logistics_dashboard_question(msg):
            return _logistics_dashboard_message(snapshot)

    if _is_refund_question(msg):
        return await _self_service_refund_message(ro_db, user, role, user_message)

    if _is_knowledge_question(msg):
        knowledge_message = await _answer_from_retrieved_knowledge(ro_db, user, user_message)
        if knowledge_message:
            return knowledge_message

    if role == "VENDOR":
        if _is_wallet_balance_question(msg):
            return await _vendor_wallet_message(ro_db, user)
        if _is_analytics_section_question(msg):
            return await _vendor_analytics_message(ro_db, user)
        # Only fire the "raise a ticket" shortcut outside support_chat — inside support_chat
        # the AI should answer directly, not redirect to ticket creation.
        is_in_support_chat = (chat_context or "").strip().lower() == SUPPORT_CHAT_CONTEXT
        if not is_in_support_chat and _is_support_question(msg):
            return await _vendor_support_message(ro_db, user)
        if _is_recurring_data_question(msg):
            return await _vendor_recurring_orders_message(ro_db, user)

    if not _extract_tracking_code(user_message) and _is_order_status_list_question(msg, role):
        status_label, statuses = _extract_order_status_filter(msg)
        if status_label and statuses:
            return await _list_self_service_orders_by_status(
                ro_db=ro_db,
                user=user,
                role=role,
                status_label=status_label,
                statuses=statuses,
            )

    if _is_current_orders_question(msg, role):
        return await _list_current_self_service_orders(ro_db, user, role)

    # Tracking / order status
    order_keywords = ["where is my order", "where is my current order", "track my order", "order status",
                      "current order", "my shipment", "pending shipment", "show my shipment", "show my order",
                      "shipment status"]
    tracking_code = _extract_tracking_code(user_message)
    if tracking_code or any(k in msg for k in order_keywords):
        matched_order, requested_tracking_code = await _lookup_self_service_order(
            ro_db=ro_db,
            user=user,
            user_message=user_message,
        )
        if matched_order:
            return _format_self_service_order_message(
                matched_order,
                role=role,
                tracking_code=requested_tracking_code,
            )
        if requested_tracking_code:
            return f"I couldn't find {noun} **{requested_tracking_code}** in your account."
        return f"No {noun} found for your account yet."

    # Glossary questions — always answerable without AI
    if "bulk upload" in msg:
        return (
            "Bulk Upload lets you create many shipments at once by uploading a CSV or Excel file. "
            "Each row in the file represents one shipment with pickup, destination, and item details. "
            "Go to Bulk Upload in your dashboard to download the template and upload your file."
        )
    if any(k in msg for k in ["damage report", "what is damage"]):
        return (
            "A damage report is a record created when an item is found damaged during packing, transit, or delivery. "
            "It includes item details, remarks, and the stage where damage occurred."
        )
    if "analytics" in msg:
        if role == "LOGISTIC_MANAGER":
            return (
                "The logistics intelligence views show hub performance, revenue trends, fleet utilization, alert pressure, returns, and delivery outcomes across the network."
            )
        if role == "VENDOR":
            return (
                "The Analytics section shows monthly spend, shipment volume, success rate, "
                "and average order value for your vendor account."
            )
        return "The Analytics section shows booking volume, spend trends, and delivery outcomes for your account."
    if any(k in msg for k in ["what is quote", "what are quotes", "quote meaning", "quotation"]):
        return "A quote is the estimated cost shown before you confirm a booking, based on route, volume, labor, and packing."
    if "what is recurring" in msg or "what are recurring" in msg:
        return "Recurring shipments let you schedule automatic repeat deliveries on a weekly or monthly basis."
    if _is_wallet_balance_question(msg):
        return await _vendor_wallet_message(ro_db, user)
    if "wallet" in msg:
        return "Your wallet balance is shown in the header. You can top it up by clicking the balance amount. It is used to pay for orders automatically."
    if any(k in msg for k in ["how to track", "where to track", "tracking"]):
        return f"Track your {noun}s from the Orders/Shipments section in your dashboard. Click any {noun} to see live status updates."
    if any(k in msg for k in ["how to book", "book a move", "new booking", "create shipment"]):
        if role == "VENDOR":
            return "Go to Create Shipment in your vendor dashboard. Enter pickup, destination, cargo details, and confirm."
        return "Go to Book a Move in your dashboard. Enter pickup, destination, items, labor and packing options, then confirm."
    if "support" in msg:
        if role == "LOGISTIC_MANAGER":
            return (
                "Use Recovery Tickets, Communication, or escalation tools to coordinate follow-ups, exception handling, and human support across operations."
            )
        return (
            "Open the Help / Support section to raise a support ticket. "
            "You can describe shipment, invoice, or platform issues there."
        )

    # Generic fallback — role-aware
    if role == "VENDOR":
        return "I can answer questions about your shipments, wallet, invoices, spending history, and platform features. Ask me anything."
    if role == "LOGISTIC_MANAGER":
        return "I can answer questions about hub performance, driver and fleet status, inventory pressure, alerts, returns, revenue, and overall logistics operations."
    if role == "WAREHOUSE_MANAGER":
        return "I can answer questions about your warehouse operations, including queue pressure, staff availability, docks, returns, inventory pressure, and workload forecasts."
    if role == "DISPATCHER":
        return "I can answer questions about driver status, available drivers, pending orders, fleet vehicles, active trips, and SLA risk. Ask me anything."
    return "I can answer questions about your orders, wallet, spending history, quotes, and platform features. Ask me anything."


def _contextualize_user_message(
    user_message: str,
    chat_context: str | None,
    warehouse_snapshot: dict | None = None,
    dispatcher_snapshot: dict | None = None,
    logistic_manager_snapshot: dict | None = None,
) -> str:
    normalized = (chat_context or "").strip().lower()

    if normalized in WAREHOUSE_CONTEXTS and warehouse_snapshot:
        snapshot_facts = warehouse_snapshot.get("facts", [])[:12]
        return (
            "Smart WMS context.\n"
            "Current warehouse grounding facts:\n"
            + "\n".join(f"- {fact}" for fact in snapshot_facts)
            + f"\n\nUser question: {user_message}"
        )

    if normalized in DISPATCHER_CONTEXTS and dispatcher_snapshot:
        snapshot_facts = dispatcher_snapshot.get("facts", [])[:10]
        return (
            "Smart Dispatcher context.\n"
            "Current dispatch grounding facts:\n"
            + "\n".join(f"- {fact}" for fact in snapshot_facts)
            + f"\n\nUser question: {user_message}"
        )

    if normalized in LOGISTIC_MANAGER_CONTEXTS and logistic_manager_snapshot:
        snapshot_facts = logistic_manager_snapshot.get("facts", [])[:16]
        return (
            "Reports & Command Center context.\n"
            "Live network operational grounding facts:\n"
            + "\n".join(f"- {fact}" for fact in snapshot_facts)
            + f"\n\nUser question: {user_message}"
        )

    return user_message
