"""Chat replies built from a warehouse snapshot: overview, capacity, staff, workload, orders, returns, docks and inventory."""


def _warehouse_overview_message(snapshot: dict) -> str:
    warehouse = snapshot["warehouse"]
    return (
        f"Warehouse **{warehouse.name}** snapshot:\n"
        f"- Active orders: **{snapshot['active_orders']}**\n"
        f"- Awaiting warehouse action: **{snapshot['pending_orders']}**\n"
        f"- Picking / packing now: **{snapshot['picking_orders']}**\n"
        f"- Ready for dispatch: **{snapshot['ready_for_dispatch']}**\n"
        f"- Staff available: **{snapshot['available_staff']}/{snapshot['total_staff']}**\n"
        f"- Free docks: **{snapshot['free_docks']}/{snapshot['total_docks']}**"
    )


def _warehouse_capacity_message(snapshot: dict) -> str:
    return (
        f"Best free space right now: **{snapshot['free_space_label']}**.\n"
        f"Most loaded area: **{snapshot['busy_space_label']}**.\n"
        f"Free docks: **{snapshot['free_docks']}/{snapshot['total_docks']}**. "
        f"Active orders on the warehouse floor: **{snapshot['active_orders']}**."
    )


def _warehouse_staff_message(snapshot: dict) -> str:
    available_line = ", ".join(snapshot["available_names"]) if snapshot["available_names"] else "No unassigned staff listed"
    on_field_line = ", ".join(snapshot["on_field_names"]) if snapshot["on_field_names"] else "No staff currently on field"
    return (
        f"Staff status right now:\n"
        f"- Available: **{snapshot['available_staff']}**\n"
        f"- Assigned on floor: **{snapshot['assigned_staff']}**\n"
        f"- On field: **{snapshot['on_field_staff']}**\n"
        f"- Off duty: **{snapshot['off_duty_staff']}**\n"
        f"- Available names: {available_line}\n"
        f"- On-field names: {on_field_line}"
    )


def _warehouse_workload_message(snapshot: dict) -> str:
    return (
        f"Tomorrow's workload forecast:\n"
        f"- 7-day average inbound volume: **{snapshot['avg_daily_orders']}** orders/day\n"
        f"- Current active pipeline: **{snapshot['active_orders']}** orders\n"
        f"- Projected tomorrow load: **{snapshot['projected_orders']}** orders\n"
        f"- Suggested active floor staff: **{snapshot['suggested_staff']}**\n"
        f"- Available now: **{snapshot['available_staff']}**"
    )


def _warehouse_pending_orders_message(snapshot: dict) -> str:
    lines = [
        f"Orders needing warehouse attention: **{snapshot['pending_orders']}**.",
        f"Picking / packing in progress: **{snapshot['picking_orders']}**. Ready for dispatch: **{snapshot['ready_for_dispatch']}**.",
    ]
    if snapshot["recent_orders"]:
        lines.append("Recent warehouse orders:")
        for order in snapshot["recent_orders"][:5]:
            lines.append(
                f"- {order.tracking_code}: {order.status} | Stage: {order.warehouse_substatus or 'N/A'}"
            )
    return "\n".join(lines)


def _warehouse_returns_message(snapshot: dict) -> str:
    lines = [
        f"Returns / damage snapshot: **{snapshot['pending_returns']}** pending gradings and **{snapshot['completed_returns']}** completed in the latest batch.",
    ]
    if snapshot["recent_returns"]:
        lines.append("Latest graded returns:")
        for grading in snapshot["recent_returns"][:5]:
            lines.append(
                f"- {grading.rma_code}: {grading.item_condition} -> {grading.disposition} | Status: {grading.status}"
            )
    else:
        lines.append("No recent return gradings found for this warehouse.")
    return "\n".join(lines)


def _warehouse_dock_message(snapshot: dict) -> str:
    lines = [
        f"Loading dock status: **{snapshot['free_docks']}** free, **{snapshot['occupied_docks']}** occupied, **{snapshot['maintenance_docks']}** under maintenance.",
    ]
    if snapshot["occupied_dock_labels"]:
        lines.append("Occupied docks:")
        lines.extend(f"- {label}" for label in snapshot["occupied_dock_labels"])
    else:
        lines.append("All tracked docks are currently free.")
    return "\n".join(lines)


def _warehouse_inventory_message(snapshot: dict) -> str:
    lines = [
        f"Inventory health: **{snapshot['total_inventory_units']}** units on hand, **{len(snapshot['low_stock_items'])}** low-stock SKUs, **{snapshot['pending_restocks']}** pending restock requests.",
    ]
    if snapshot["low_stock_items"]:
        lines.append("Most urgent low-stock items:")
        for item in snapshot["low_stock_items"]:
            lines.append(
                f"- {item.name} ({item.sku}): {item.quantity_on_hand} left vs safety stock {item.safety_stock}"
            )
    else:
        lines.append("No SKUs are currently below safety stock.")
    return "\n".join(lines)
