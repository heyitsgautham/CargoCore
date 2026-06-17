import pytest
from pydantic import ValidationError

from app.schemas.warehouse_operations import ZoneMetricsCreate


VALID_CASES = [{'zone_id': 'ZONE-0', 'orders_processed': 0, 'picking_accuracy_pct': 0.0, 'active_pickers': 0, 'capacity_used_pct': 0.0, 'throughput_items_per_hour': 0.0}, {'zone_id': 'ZONE-1', 'orders_processed': 1, 'picking_accuracy_pct': 10.0, 'active_pickers': 1, 'capacity_used_pct': 10.0, 'throughput_items_per_hour': 1.0}, {'zone_id': 'ZONE-2', 'orders_processed': 2, 'picking_accuracy_pct': 20.5, 'active_pickers': 2, 'capacity_used_pct': 20.5, 'throughput_items_per_hour': 2.0}, {'zone_id': 'ZONE-3', 'orders_processed': 3, 'picking_accuracy_pct': 35.0, 'active_pickers': 3, 'capacity_used_pct': 35.0, 'throughput_items_per_hour': 3.0}, {'zone_id': 'ZONE-4', 'orders_processed': 4, 'picking_accuracy_pct': 50.0, 'active_pickers': 4, 'capacity_used_pct': 50.0, 'throughput_items_per_hour': 4.0}, {'zone_id': 'ZONE-5', 'orders_processed': 5, 'picking_accuracy_pct': 75.0, 'active_pickers': 5, 'capacity_used_pct': 75.0, 'throughput_items_per_hour': 5.0}, {'zone_id': 'ZONE-6', 'orders_processed': 6, 'picking_accuracy_pct': 90.0, 'active_pickers': 6, 'capacity_used_pct': 90.0, 'throughput_items_per_hour': 6.0}, {'zone_id': 'ZONE-7', 'orders_processed': 7, 'picking_accuracy_pct': 100.0, 'active_pickers': 7, 'capacity_used_pct': 100.0, 'throughput_items_per_hour': 7.0}]
INVALID_CASES = [{'zone_id': '', 'picking_accuracy_pct': 50.0}, {'zone_id': 'ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ', 'picking_accuracy_pct': 50.0}, {'zone_id': 'ZONE-A', 'orders_processed': -1}, {'zone_id': 'ZONE-A', 'picking_accuracy_pct': -0.1}, {'zone_id': 'ZONE-A', 'picking_accuracy_pct': 100.1}, {'zone_id': 'ZONE-A', 'active_pickers': -1}, {'zone_id': 'ZONE-A', 'capacity_used_pct': -0.1}, {'zone_id': 'ZONE-A', 'throughput_items_per_hour': -0.1}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_warehouse_ops_zone_metrics_bulk_unit_valid_bulk(payload) -> None:
    model = ZoneMetricsCreate(**payload)
    assert isinstance(model, ZoneMetricsCreate)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_warehouse_ops_zone_metrics_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        ZoneMetricsCreate(**payload)
