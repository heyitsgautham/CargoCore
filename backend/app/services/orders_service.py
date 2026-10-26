"""Order services.

The routers call every order operation through this module. The code lives in
app/services/orders/, one module per stage, and is re-exported here so callers
and the tests that patch these functions keep a single import path.
"""

from app.services.orders.assignment import (
    assign_order as assign_order,
)
from app.services.orders.assignment import (
    confirm_order as confirm_order,
)
from app.services.orders.assignment import (
    get_order_assignment_preview as get_order_assignment_preview,
)
from app.services.orders.cancellation import (
    cancel_order as cancel_order,
)
from app.services.orders.cancellation import (
    escalate_order as escalate_order,
)
from app.services.orders.crud import (
    create_order as create_order,
)
from app.services.orders.crud import (
    get_order_detail as get_order_detail,
)
from app.services.orders.crud import (
    list_orders as list_orders,
)
from app.services.orders.crud import (
    soft_delete_order as soft_delete_order,
)
from app.services.orders.crud import (
    update_order as update_order,
)
from app.services.orders.delivery_proof import (
    house_shift_signoff as house_shift_signoff,
)
from app.services.orders.delivery_proof import (
    submit_customer_rating as submit_customer_rating,
)
from app.services.orders.delivery_proof import (
    submit_job_rating as submit_job_rating,
)
from app.services.orders.delivery_proof import (
    upload_proof_of_delivery as upload_proof_of_delivery,
)
from app.services.orders.items import (
    get_order_items as get_order_items,
)
from app.services.orders.items import (
    track_order as track_order,
)
from app.services.orders.items import (
    upsert_order_items as upsert_order_items,
)
from app.services.orders.routing import (
    auto_balance_drivers as auto_balance_drivers,
)
from app.services.orders.routing import (
    optimize_routes as optimize_routes,
)
from app.services.orders.transitions import (
    complete_return_order as complete_return_order,
)
from app.services.orders.transitions import (
    send_delivery_otp as send_delivery_otp,
)
from app.services.orders.transitions import (
    transition_order as transition_order,
)
from app.services.orders.trip_commands import (
    push_trip_command_update as push_trip_command_update,
)
from app.services.orders.trip_commands import (
    report_trip_deviation as report_trip_deviation,
)
from app.services.orders.trip_intelligence import (
    get_trip_intelligence as get_trip_intelligence,
)
from app.services.orders.trip_intelligence import (
    list_trip_intelligence as list_trip_intelligence,
)
