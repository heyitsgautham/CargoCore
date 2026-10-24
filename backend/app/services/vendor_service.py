"""Vendor portal services.

The routers, the recurring scheduler in app/main.py and the warehouse inbound flow
call vendor operations through this module. The code lives in app/services/vendor/,
one module per area, and is re-exported here so callers keep a single import path.
"""

from app.services.vendor.account import (
    create_api_key as create_api_key,
)
from app.services.vendor.account import (
    create_team_member as create_team_member,
)
from app.services.vendor.account import (
    create_vendor_damage_report as create_vendor_damage_report,
)
from app.services.vendor.account import (
    delete_team_member as delete_team_member,
)
from app.services.vendor.account import (
    get_vendor_damage_reports as get_vendor_damage_reports,
)
from app.services.vendor.account import (
    get_vendor_dashboard as get_vendor_dashboard,
)
from app.services.vendor.account import (
    get_vendor_settings as get_vendor_settings,
)
from app.services.vendor.account import (
    get_vendor_shipments as get_vendor_shipments,
)
from app.services.vendor.account import (
    list_api_keys as list_api_keys,
)
from app.services.vendor.account import (
    list_team_members as list_team_members,
)
from app.services.vendor.account import (
    revoke_api_key as revoke_api_key,
)
from app.services.vendor.account import (
    update_vendor_settings as update_vendor_settings,
)
from app.services.vendor.billing import (
    pay_invoice as pay_invoice,
)
from app.services.vendor.recurring_estimate import (
    estimate_recurring_cost as estimate_recurring_cost,
)
from app.services.vendor.recurring_rules import (
    create_recurring_rule as create_recurring_rule,
)
from app.services.vendor.recurring_rules import (
    delete_recurring_rule as delete_recurring_rule,
)
from app.services.vendor.recurring_rules import (
    list_recurring_rules as list_recurring_rules,
)
from app.services.vendor.recurring_rules import (
    toggle_recurring_rule as toggle_recurring_rule,
)
from app.services.vendor.recurring_rules import (
    update_recurring_rule as update_recurring_rule,
)
from app.services.vendor.recurring_runs import (
    auto_debit_recurring_order_if_eligible as auto_debit_recurring_order_if_eligible,
)
from app.services.vendor.recurring_runs import (
    ensure_upcoming_recurring_orders as ensure_upcoming_recurring_orders,
)
from app.services.vendor.recurring_runs import (
    run_due_recurring_rules as run_due_recurring_rules,
)
from app.services.vendor.uploads_support import (
    create_bulk_upload as create_bulk_upload,
)
from app.services.vendor.uploads_support import (
    create_support_ticket as create_support_ticket,
)
from app.services.vendor.uploads_support import (
    list_bulk_uploads as list_bulk_uploads,
)
from app.services.vendor.uploads_support import (
    list_support_tickets as list_support_tickets,
)
from app.services.vendor.uploads_support import (
    reply_support_ticket as reply_support_ticket,
)
from app.services.vendor.uploads_support import (
    resolve_support_ticket as resolve_support_ticket,
)
from app.services.vendor.uploads_support import (
    update_bulk_upload as update_bulk_upload,
)
