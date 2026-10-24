"""Warehouse operations service.

Handles warehouse lifecycle operations: inbound receiving, picking, packing,
quality checks, loading dock management, returns grading, and zone metrics.
The code lives in app/services/warehouse_ops/, one module per stage, and is
re-exported here so the routers keep a single import path.
"""

from app.services.warehouse_ops.docks import (
    assign_truck_to_dock as assign_truck_to_dock,
)
from app.services.warehouse_ops.docks import (
    create_loading_dock as create_loading_dock,
)
from app.services.warehouse_ops.docks import (
    get_loading_docks as get_loading_docks,
)
from app.services.warehouse_ops.docks import (
    release_dock as release_dock,
)
from app.services.warehouse_ops.docks import (
    set_dock_maintenance as set_dock_maintenance,
)
from app.services.warehouse_ops.inbound_planning import (
    get_inbound_overview as get_inbound_overview,
)
from app.services.warehouse_ops.inbound_planning import (
    get_inbound_receive_plan as get_inbound_receive_plan,
)
from app.services.warehouse_ops.inbound_receiving import (
    accept_order_into_warehouse as accept_order_into_warehouse,
)
from app.services.warehouse_ops.inbound_receiving import (
    generate_vendor_take_back as generate_vendor_take_back,
)
from app.services.warehouse_ops.inbound_receiving import (
    mark_inbound_arrived as mark_inbound_arrived,
)
from app.services.warehouse_ops.inbound_receiving import (
    mark_inbound_received as mark_inbound_received,
)
from app.services.warehouse_ops.inbound_receiving import (
    report_inbound_damage as report_inbound_damage,
)
from app.services.warehouse_ops.inbound_receiving import (
    report_inbound_mismatch as report_inbound_mismatch,
)
from app.services.warehouse_ops.inbound_receiving import (
    schedule_inbound_delivery as schedule_inbound_delivery,
)
from app.services.warehouse_ops.metrics import (
    get_performance_metrics as get_performance_metrics,
)
from app.services.warehouse_ops.metrics import (
    get_zone_metrics as get_zone_metrics,
)
from app.services.warehouse_ops.metrics import (
    record_zone_metrics as record_zone_metrics,
)
from app.services.warehouse_ops.packing import (
    complete_packing as complete_packing,
)
from app.services.warehouse_ops.packing import (
    create_packing_station as create_packing_station,
)
from app.services.warehouse_ops.packing import (
    get_packing_stations as get_packing_stations,
)
from app.services.warehouse_ops.packing import (
    start_packing as start_packing,
)
from app.services.warehouse_ops.packing import (
    update_packing_station as update_packing_station,
)
from app.services.warehouse_ops.picking import (
    complete_picking as complete_picking,
)
from app.services.warehouse_ops.picking import (
    confirm_pick_item as confirm_pick_item,
)
from app.services.warehouse_ops.picking import (
    get_pick_progress as get_pick_progress,
)
from app.services.warehouse_ops.picking import (
    revert_picking as revert_picking,
)
from app.services.warehouse_ops.picking import (
    start_picking as start_picking,
)
from app.services.warehouse_ops.quality import (
    create_quality_check as create_quality_check,
)
from app.services.warehouse_ops.quality import (
    get_quality_check as get_quality_check,
)
from app.services.warehouse_ops.quality import (
    list_quality_checks as list_quality_checks,
)
from app.services.warehouse_ops.quality import (
    pass_quality_check as pass_quality_check,
)
from app.services.warehouse_ops.quality import (
    update_quality_check as update_quality_check,
)
from app.services.warehouse_ops.returns import (
    complete_return_grading as complete_return_grading,
)
from app.services.warehouse_ops.returns import (
    create_return_grading as create_return_grading,
)
from app.services.warehouse_ops.returns import (
    get_return_gradings as get_return_gradings,
)
from app.services.warehouse_ops.returns import (
    update_return_grading as update_return_grading,
)
from app.services.warehouse_ops.returns import (
    upload_damage_photo as upload_damage_photo,
)
