"""Customer support desk services.

The routers and the other services call support operations through this module.
The code lives in app/services/support/, one module per area of the support desk,
and is re-exported here so callers and the tests that patch these functions keep
a single import path.
"""

from app.services.support.analytics import (
    execute_support_analytics_insight as execute_support_analytics_insight,
)
from app.services.support.analytics import (
    get_support_analytics as get_support_analytics,
)
from app.services.support.contacts import (
    create_public_contact_submission as create_public_contact_submission,
)
from app.services.support.contacts import (
    create_user_notification as create_user_notification,
)
from app.services.support.contacts import (
    delete_contact_submission as delete_contact_submission,
)
from app.services.support.contacts import (
    get_default_support_manager as get_default_support_manager,
)
from app.services.support.contacts import (
    get_support_settings as get_support_settings,
)
from app.services.support.contacts import (
    list_contact_submissions as list_contact_submissions,
)
from app.services.support.contacts import (
    notify_support_manager_about_ticket as notify_support_manager_about_ticket,
)
from app.services.support.contacts import (
    reply_to_contact_submission as reply_to_contact_submission,
)
from app.services.support.contacts import (
    update_contact_submission as update_contact_submission,
)
from app.services.support.contacts import (
    update_support_settings as update_support_settings,
)
from app.services.support.damage_refunds import (
    create_support_damage_report as create_support_damage_report,
)
from app.services.support.damage_refunds import (
    flag_refund_case_urgent as flag_refund_case_urgent,
)
from app.services.support.damage_refunds import (
    get_customer_history as get_customer_history,
)
from app.services.support.damage_refunds import (
    list_support_damage_reports as list_support_damage_reports,
)
from app.services.support.damage_refunds import (
    list_support_refund_cases as list_support_refund_cases,
)
from app.services.support.damage_refunds import (
    send_support_message as send_support_message,
)
from app.services.support.damage_refunds import (
    update_damage_report_notes as update_damage_report_notes,
)
from app.services.support.dashboard import (
    get_support_dashboard as get_support_dashboard,
)
from app.services.support.knowledge import (
    create_knowledge_article as create_knowledge_article,
)
from app.services.support.knowledge import (
    delete_knowledge_article as delete_knowledge_article,
)
from app.services.support.knowledge import (
    get_knowledge_article_by_id as get_knowledge_article_by_id,
)
from app.services.support.knowledge import (
    like_knowledge_article as like_knowledge_article,
)
from app.services.support.knowledge import (
    list_knowledge_articles as list_knowledge_articles,
)
from app.services.support.knowledge import (
    update_knowledge_article as update_knowledge_article,
)
from app.services.support.sessions import (
    escalate_support_session as escalate_support_session,
)
from app.services.support.sessions import (
    get_support_session_detail as get_support_session_detail,
)
from app.services.support.sessions import (
    list_enriched_escalations as list_enriched_escalations,
)
from app.services.support.sessions import (
    list_support_sessions as list_support_sessions,
)
from app.services.support.sessions import (
    reply_to_support_session as reply_to_support_session,
)
from app.services.support.sessions import (
    take_over_support_session as take_over_support_session,
)
from app.services.support.tickets import (
    create_ticket as create_ticket,
)
from app.services.support.tickets import (
    delete_ticket as delete_ticket,
)
from app.services.support.tickets import (
    get_recovery_tickets_count as get_recovery_tickets_count,
)
from app.services.support.tickets import (
    list_tickets as list_tickets,
)
from app.services.support.tickets import (
    mark_ai_handoff_ticket_in_progress as mark_ai_handoff_ticket_in_progress,
)
from app.services.support.tickets import (
    reply_to_ticket as reply_to_ticket,
)
from app.services.support.tickets import (
    resolve_ai_handoff_escalations_for_ticket as resolve_ai_handoff_escalations_for_ticket,
)
from app.services.support.tickets import (
    resolve_ai_handoff_ticket_for_session as resolve_ai_handoff_ticket_for_session,
)
from app.services.support.tickets import (
    sync_ai_handoff_ticket as sync_ai_handoff_ticket,
)
from app.services.support.tickets import (
    sync_vendor_ticket_to_support_ticket as sync_vendor_ticket_to_support_ticket,
)
from app.services.support.tickets import (
    update_ticket as update_ticket,
)
