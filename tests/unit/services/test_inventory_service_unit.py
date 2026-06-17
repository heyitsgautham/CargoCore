from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import inventory_service


def test_split_zone_and_aisle_variants() -> None:
    assert inventory_service._split_zone_and_aisle(None) == (None, None)
    assert inventory_service._split_zone_and_aisle("") == (None, None)
    assert inventory_service._split_zone_and_aisle("Z1-A12") == ("Z1", "A12")
    assert inventory_service._split_zone_and_aisle("A12") == (None, "A12")
    assert inventory_service._split_zone_and_aisle("Z9-ROW-1") == ("Z9", "ROW-1")


def test_build_floor_plan_lookup_maps_hierarchy_and_cells() -> None:
    floor_plan_json = {
        "groups": [{"id": "g1", "name": "Cold"}],
        "sections": [{"id": "s1", "groupId": "g1", "label": "S-1"}],
        "racks": [{"id": "r1", "sectionId": "s1", "label": "R-1", "cols": 4}],
        "products": [
            {"sku": "SKU-1", "rackId": "r1", "cell": 5},
            {"sku": "SKU-2", "rackId": "r1", "cell": "X"},
            "not-a-dict",
        ],
    }

    lookup = inventory_service._build_floor_plan_lookup(floor_plan_json)

    assert lookup["SKU-1"] == {
        "zone": "Cold",
        "section": "S-1",
        "rack": "R-1",
        "cell": "R2C1",
    }
    assert lookup["SKU-2"]["cell"] == "X"


def test_build_floor_plan_lookup_handles_non_dict_input() -> None:
    assert inventory_service._build_floor_plan_lookup(None) == {}
    assert inventory_service._build_floor_plan_lookup([]) == {}


def test_build_location_payload_prefers_floor_plan_zone_and_builds_path() -> None:
    inventory_item = SimpleNamespace(aisle="Z9-A12", shelf="S2", bin="B3")
    floor_plan_lookup = {
        "SKU-1": {
            "zone": "Z1",
            "section": "SEC-A",
            "rack": "R-3",
            "cell": "R1C2",
        }
    }

    payload = inventory_service._build_location_payload(inventory_item, floor_plan_lookup, "SKU-1")

    assert payload["zone"] == "Z1"
    assert payload["aisle"] == "A12"
    assert payload["section"] == "SEC-A"
    assert payload["rack"] == "R-3"
    assert payload["shelf"] == "S2"
    assert payload["bin"] == "B3"
    assert payload["cell"] == "R1C2"
    assert "Zone Z1" in payload["location_path"]
    assert "Aisle A12" in payload["location_path"]
    assert "Cell R1C2" in payload["location_path"]


def test_build_location_payload_returns_unmapped_message_when_empty() -> None:
    payload = inventory_service._build_location_payload(None, {}, "SKU-404")
    assert payload["location_path"] == "Location not mapped"


def test_to_movement_response_maps_related_models() -> None:
    movement = SimpleNamespace(
        id=uuid4(),
        item_id=uuid4(),
        movement_type="restock",
        quantity=15,
        reference_order_id=uuid4(),
        performed_by=uuid4(),
        created_at=datetime(2026, 4, 17, 12, 0, tzinfo=timezone.utc),
    )
    item = SimpleNamespace(
        warehouse_id=uuid4(),
        sku="PKG-BOX",
        name="Packing Box",
        category="Packing Materials",
        unit="pcs",
    )
    order = SimpleNamespace(tracking_code="QC-ORDER123")
    performer = SimpleNamespace(name="Warehouse User")

    response = inventory_service._to_movement_response(movement, item, order, performer)

    assert response.movement_type == "RESTOCK"
    assert response.reference_order_tracking == "QC-ORDER123"
    assert response.performed_by_name == "Warehouse User"
    assert response.item_sku == "PKG-BOX"


def test_to_restock_response_maps_requester_and_item() -> None:
    request_id = uuid4()
    req = SimpleNamespace(
        id=request_id,
        item_id=uuid4(),
        warehouse_id=uuid4(),
        quantity=30,
        status="PENDING",
        requested_by=uuid4(),
        manager_notes=None,
        created_at=datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 17, 9, 30, tzinfo=timezone.utc),
    )
    item = SimpleNamespace(sku="PKG-BUBBLE-WRAP", name="Bubble Wrap")
    requester = SimpleNamespace(name="WM User")

    response = inventory_service._to_restock_response(req, item, requester)

    assert response.id == request_id
    assert response.requested_by_name == "WM User"
    assert response.item_sku == "PKG-BUBBLE-WRAP"


def test_material_sku_generation() -> None:
    assert inventory_service._material_sku("Bubble Wrap") == "PKG-BUBBLE-WRAP"
    assert inventory_service._material_sku("Foam Sheet") == "PKG-FOAM-SHEET"


def test_add_material_to_rates_adds_and_updates_material(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    rates_path = tmp_path / "rates_config.json"
    rates_path.write_text(json.dumps({"materials": []}), encoding="utf-8")
    monkeypatch.setattr(inventory_service, "_RATES_CONFIG_PATH", rates_path)

    inventory_service._add_material_to_rates("Foam Sheet", 42.5, "pcs")

    data = json.loads(rates_path.read_text(encoding="utf-8"))
    materials = data["materials"]
    foam = [row for row in materials if row.get("id") == "foamSheet"]
    assert len(foam) == 1
    assert foam[0]["rate"] == 42.5
    assert foam[0]["unit"] == "pcs"

    inventory_service._add_material_to_rates("Foam Sheet", 47.0, "pack")

    data = json.loads(rates_path.read_text(encoding="utf-8"))
    materials = data["materials"]
    foam = [row for row in materials if row.get("id") == "foamSheet"]
    assert len(foam) == 1
    assert foam[0]["rate"] == 47.0
    assert foam[0]["unit"] == "pack"


def test_add_material_to_rates_converts_legacy_materials_dict(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    rates_path = tmp_path / "rates_config.json"
    legacy = {"materials": {"box": 60, "bubbleWrap": 18, "crate": 210}}
    rates_path.write_text(json.dumps(legacy), encoding="utf-8")
    monkeypatch.setattr(inventory_service, "_RATES_CONFIG_PATH", rates_path)

    inventory_service._add_material_to_rates("Kraft Paper", 15.0, "m")

    data = json.loads(rates_path.read_text(encoding="utf-8"))
    materials = data["materials"]

    assert isinstance(materials, list)
    assert any(row.get("id") == "box" for row in materials)
    kraft = [row for row in materials if row.get("id") == "kraftPaper"]
    assert len(kraft) == 1
    assert kraft[0]["rate"] == 15.0
