"""Chat replies the warehouse assistant builds from a warehouse snapshot."""

from types import SimpleNamespace

from app.services.ai_chat import warehouse_messages as messages


def _snapshot(**overrides) -> dict:
    snapshot = {
        "warehouse": SimpleNamespace(name="North-East Hub"),
        "active_orders": 12,
        "pending_orders": 4,
        "picking_orders": 3,
        "ready_for_dispatch": 2,
        "available_staff": 5,
        "assigned_staff": 6,
        "on_field_staff": 1,
        "off_duty_staff": 2,
        "total_staff": 14,
        "available_names": ["Ravi", "Asha"],
        "on_field_names": [],
        "free_docks": 2,
        "occupied_docks": 1,
        "maintenance_docks": 1,
        "total_docks": 4,
        "occupied_dock_labels": ["Dock 3 (TRK-992)"],
        "free_space_label": "Zone C, 45% used",
        "busy_space_label": "Zone B, 85% used",
        "avg_daily_orders": 9,
        "projected_orders": 15,
        "suggested_staff": 7,
        "recent_orders": [],
        "pending_returns": 0,
        "completed_returns": 3,
        "recent_returns": [],
        "total_inventory_units": 1540,
        "low_stock_items": [],
        "pending_restocks": 1,
    }
    snapshot.update(overrides)
    return snapshot


def test_overview_lists_the_headline_counts() -> None:
    text = messages._warehouse_overview_message(_snapshot())

    assert text.startswith("Warehouse **North-East Hub** snapshot:")
    assert "- Staff available: **5/14**" in text
    assert "- Free docks: **2/4**" in text


def test_capacity_names_the_freest_and_busiest_areas() -> None:
    text = messages._warehouse_capacity_message(_snapshot())

    assert "Best free space right now: **Zone C, 45% used**." in text
    assert "Most loaded area: **Zone B, 85% used**." in text


def test_staff_reply_says_when_nobody_is_on_field() -> None:
    text = messages._warehouse_staff_message(_snapshot())

    assert "- Available names: Ravi, Asha" in text
    assert "- On-field names: No staff currently on field" in text
    assert "No unassigned staff listed" in messages._warehouse_staff_message(_snapshot(available_names=[]))


def test_workload_forecast_carries_the_projection() -> None:
    text = messages._warehouse_workload_message(_snapshot())

    assert "- Projected tomorrow load: **15** orders" in text
    assert "- Suggested active floor staff: **7**" in text


def test_pending_orders_list_at_most_five_recent_orders() -> None:
    orders = [
        SimpleNamespace(tracking_code=f"TRK-{n}", status="CONFIRMED", warehouse_substatus=None if n % 2 else "PICKING")
        for n in range(7)
    ]

    text = messages._warehouse_pending_orders_message(_snapshot(recent_orders=orders))

    assert text.count("\n- TRK-") == 5
    assert "- TRK-0: CONFIRMED | Stage: PICKING" in text
    assert "- TRK-1: CONFIRMED | Stage: N/A" in text
    assert "Recent warehouse orders" not in messages._warehouse_pending_orders_message(_snapshot())


def test_returns_reply_lists_gradings_or_says_there_are_none() -> None:
    grading = SimpleNamespace(rma_code="RMA-7", item_condition="DAMAGED", disposition="REFURBISH", status="DONE")

    assert "- RMA-7: DAMAGED -> REFURBISH | Status: DONE" in messages._warehouse_returns_message(
        _snapshot(recent_returns=[grading])
    )
    assert "No recent return gradings found" in messages._warehouse_returns_message(_snapshot())


def test_dock_reply_lists_occupied_docks_or_says_all_are_free() -> None:
    assert "- Dock 3 (TRK-992)" in messages._warehouse_dock_message(_snapshot())
    assert "All tracked docks are currently free." in messages._warehouse_dock_message(
        _snapshot(occupied_dock_labels=[])
    )


def test_inventory_reply_counts_low_stock_items() -> None:
    item = SimpleNamespace(name="Packing Tape", sku="INV-001", quantity_on_hand=40, safety_stock=200)

    text = messages._warehouse_inventory_message(_snapshot(low_stock_items=[item]))

    assert "**1** low-stock SKUs" in text
    assert "- Packing Tape (INV-001): 40 left vs safety stock 200" in text
    assert "No SKUs are currently below safety stock." in messages._warehouse_inventory_message(_snapshot())
