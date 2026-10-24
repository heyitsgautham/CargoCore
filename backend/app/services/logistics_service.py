"""Public entry point for the logistics services.

The routers call every logistics operation through this module. The code lives in
app/services/logistics/, one module per feature, and is re-exported here so that
callers keep a single import path.
"""

from app.services.logistics.ai_query import (
    answer_ai_query as answer_ai_query,
)
from app.services.logistics.alerts import (
    clear_notifications as clear_notifications,
)
from app.services.logistics.alerts import (
    create_alert as create_alert,
)
from app.services.logistics.alerts import (
    create_driver_crisis_alert as create_driver_crisis_alert,
)
from app.services.logistics.alerts import (
    get_notifications as get_notifications,
)
from app.services.logistics.alerts import (
    list_alerts as list_alerts,
)
from app.services.logistics.alerts import (
    mark_all_notifications_read as mark_all_notifications_read,
)
from app.services.logistics.alerts import (
    resolve_alert as resolve_alert,
)
from app.services.logistics.alerts import (
    update_notification as update_notification,
)
from app.services.logistics.bootstrap import (
    build_bootstrap as build_bootstrap,
)
from app.services.logistics.bootstrap import (
    update_escalation_status as update_escalation_status,
)
from app.services.logistics.chat import (
    add_chat_message as add_chat_message,
)
from app.services.logistics.chat import (
    create_chat_thread as create_chat_thread,
)
from app.services.logistics.chat import (
    delete_chat_thread as delete_chat_thread,
)
from app.services.logistics.chat import (
    get_dispatch_contacts as get_dispatch_contacts,
)
from app.services.logistics.chat import (
    list_chat_threads as list_chat_threads,
)
from app.services.logistics.chat import (
    mute_chat_thread as mute_chat_thread,
)
from app.services.logistics.driver_messages import (
    add_driver_dispatch_message as add_driver_dispatch_message,
)
from app.services.logistics.driver_messages import (
    add_driver_manager_message as add_driver_manager_message,
)
from app.services.logistics.driver_messages import (
    get_driver_audit_log as get_driver_audit_log,
)
from app.services.logistics.driver_messages import (
    get_driver_dispatch_thread as get_driver_dispatch_thread,
)
from app.services.logistics.driver_messages import (
    get_driver_manager_thread as get_driver_manager_thread,
)
from app.services.logistics.driver_messages import (
    request_driver_cashout as request_driver_cashout,
)
from app.services.logistics.driver_shift import (
    bind_driver_vehicle as bind_driver_vehicle,
)
from app.services.logistics.driver_shift import (
    check_in_driver_crew_member as check_in_driver_crew_member,
)
from app.services.logistics.driver_shift import (
    end_shift as end_shift,
)
from app.services.logistics.driver_shift import (
    get_driver_crew as get_driver_crew,
)
from app.services.logistics.driver_shift import (
    get_driver_dashboard as get_driver_dashboard,
)
from app.services.logistics.driver_shift import (
    get_driver_hos as get_driver_hos,
)
from app.services.logistics.driver_shift import (
    get_driver_shift as get_driver_shift,
)
from app.services.logistics.driver_shift import (
    get_driver_telemetry as get_driver_telemetry,
)
from app.services.logistics.driver_shift import (
    return_vehicle as return_vehicle,
)
from app.services.logistics.driver_shift import (
    send_broadcast as send_broadcast,
)
from app.services.logistics.driver_shift import (
    start_shift as start_shift,
)
from app.services.logistics.driver_shift import (
    submit_fuel_receipt as submit_fuel_receipt,
)
from app.services.logistics.driver_shift import (
    update_driver_location as update_driver_location,
)
from app.services.logistics.drivers import (
    create_driver as create_driver,
)
from app.services.logistics.drivers import (
    list_drivers as list_drivers,
)
from app.services.logistics.drivers import (
    update_driver as update_driver,
)
from app.services.logistics.meetings import (
    create_meeting as create_meeting,
)
from app.services.logistics.meetings import (
    delete_meeting as delete_meeting,
)
from app.services.logistics.meetings import (
    list_meeting_participants as list_meeting_participants,
)
from app.services.logistics.meetings import (
    list_meetings as list_meetings,
)
from app.services.logistics.meetings import (
    update_meeting as update_meeting,
)
from app.services.logistics.operations import (
    create_document as create_document,
)
from app.services.logistics.operations import (
    create_manifest as create_manifest,
)
from app.services.logistics.operations import (
    create_task as create_task,
)
from app.services.logistics.operations import (
    create_transaction as create_transaction,
)
from app.services.logistics.operations import (
    create_vehicle as create_vehicle,
)
from app.services.logistics.operations import (
    create_zone as create_zone,
)
from app.services.logistics.operations import (
    delete_task as delete_task,
)
from app.services.logistics.operations import (
    delete_zone as delete_zone,
)
from app.services.logistics.operations import (
    list_manifests as list_manifests,
)
from app.services.logistics.operations import (
    list_tasks as list_tasks,
)
from app.services.logistics.operations import (
    list_vehicles as list_vehicles,
)
from app.services.logistics.operations import (
    list_zones as list_zones,
)
from app.services.logistics.operations import (
    push_manifest as push_manifest,
)
from app.services.logistics.operations import (
    update_document_status as update_document_status,
)
from app.services.logistics.operations import (
    update_task as update_task,
)
from app.services.logistics.operations import (
    update_vehicle as update_vehicle,
)
from app.services.logistics.operations import (
    update_zone as update_zone,
)
from app.services.logistics.returns import (
    issue_return_refund as issue_return_refund,
)
from app.services.logistics.returns import (
    schedule_return_pickup as schedule_return_pickup,
)
from app.services.logistics.returns import (
    update_return_case as update_return_case,
)
from app.services.logistics.seed import (
    ensure_logistics_seed_data as ensure_logistics_seed_data,
)
