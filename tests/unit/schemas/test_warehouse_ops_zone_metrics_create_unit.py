import pytest
from pydantic import ValidationError

from app.schemas.warehouse_operations import ZoneMetricsCreate


def test_zone_metrics_create_accepts_valid_payload() -> None:
    model = ZoneMetricsCreate(
        zone_id="ZONE-A",
        orders_processed=5,
        picking_accuracy_pct=95.0,
        capacity_used_pct=60.0,
    )
    assert model.zone_id == "ZONE-A"
    assert model.picking_accuracy_pct == 95.0


def test_zone_metrics_create_rejects_accuracy_above_100() -> None:
    with pytest.raises(ValidationError):
        ZoneMetricsCreate(zone_id="ZONE-A", picking_accuracy_pct=101.0)
