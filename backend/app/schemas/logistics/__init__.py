"""Logistics manager and driver app schemas, re-exported so callers import from app.schemas.logistics."""

from app.schemas.logistics.drivers import DriverAuditEventItem as DriverAuditEventItem
from app.schemas.logistics.drivers import DriverCashoutRequest as DriverCashoutRequest
from app.schemas.logistics.drivers import DriverCrewMemberItem as DriverCrewMemberItem
from app.schemas.logistics.drivers import (
    DriverDashboardContext as DriverDashboardContext,
)
from app.schemas.logistics.drivers import (
    DriverDispatchMessageCreate as DriverDispatchMessageCreate,
)
from app.schemas.logistics.drivers import (
    DriverDispatchThreadItem as DriverDispatchThreadItem,
)
from app.schemas.logistics.drivers import DriverEarnings as DriverEarnings
from app.schemas.logistics.drivers import (
    DriverFuelReceiptCreate as DriverFuelReceiptCreate,
)
from app.schemas.logistics.drivers import DriverHosSummary as DriverHosSummary
from app.schemas.logistics.drivers import DriverManifestSummary as DriverManifestSummary
from app.schemas.logistics.drivers import DriverShiftSummary as DriverShiftSummary
from app.schemas.logistics.drivers import (
    DriverTelemetryResponse as DriverTelemetryResponse,
)
from app.schemas.logistics.drivers import DriverValidationItem as DriverValidationItem
from app.schemas.logistics.drivers import (
    DriverVehicleBindRequest as DriverVehicleBindRequest,
)
from app.schemas.logistics.drivers import (
    LogisticsManifestCreate as LogisticsManifestCreate,
)
from app.schemas.logistics.drivers import LogisticsManifestItem as LogisticsManifestItem
from app.schemas.logistics.drivers import ManifestCrewMember as ManifestCrewMember
from app.schemas.logistics.requests import (
    CapitalInvestmentCreate as CapitalInvestmentCreate,
)
from app.schemas.logistics.requests import (
    LogisticsAiQueryRequest as LogisticsAiQueryRequest,
)
from app.schemas.logistics.requests import (
    LogisticsAiQueryResponse as LogisticsAiQueryResponse,
)
from app.schemas.logistics.requests import (
    LogisticsChatMessageCreate as LogisticsChatMessageCreate,
)
from app.schemas.logistics.requests import (
    LogisticsChatThreadCreate as LogisticsChatThreadCreate,
)
from app.schemas.logistics.requests import (
    LogisticsChatThreadUpdate as LogisticsChatThreadUpdate,
)
from app.schemas.logistics.requests import (
    LogisticsDocumentCreate as LogisticsDocumentCreate,
)
from app.schemas.logistics.requests import (
    LogisticsDocumentItem as LogisticsDocumentItem,
)
from app.schemas.logistics.requests import (
    LogisticsDocumentUpdateStatus as LogisticsDocumentUpdateStatus,
)
from app.schemas.logistics.requests import (
    LogisticsDriverCreate as LogisticsDriverCreate,
)
from app.schemas.logistics.requests import (
    LogisticsDriverUpdate as LogisticsDriverUpdate,
)
from app.schemas.logistics.requests import (
    LogisticsMeetingCreate as LogisticsMeetingCreate,
)
from app.schemas.logistics.requests import (
    LogisticsMeetingUpdate as LogisticsMeetingUpdate,
)
from app.schemas.logistics.requests import (
    LogisticsNotificationUpdate as LogisticsNotificationUpdate,
)
from app.schemas.logistics.requests import (
    LogisticsReturnCaseUpdate as LogisticsReturnCaseUpdate,
)
from app.schemas.logistics.requests import LogisticsTaskCreate as LogisticsTaskCreate
from app.schemas.logistics.requests import LogisticsTaskUpdate as LogisticsTaskUpdate
from app.schemas.logistics.requests import (
    LogisticsTransactionCreate as LogisticsTransactionCreate,
)
from app.schemas.logistics.requests import (
    LogisticsVehicleCreate as LogisticsVehicleCreate,
)
from app.schemas.logistics.requests import (
    LogisticsVehicleUpdate as LogisticsVehicleUpdate,
)
from app.schemas.logistics.requests import LogisticsZoneCreate as LogisticsZoneCreate
from app.schemas.logistics.requests import LogisticsZoneUpdate as LogisticsZoneUpdate
from app.schemas.logistics.views import DispatchContactItem as DispatchContactItem
from app.schemas.logistics.views import LogisticsAlertItem as LogisticsAlertItem
from app.schemas.logistics.views import (
    LogisticsBootstrapResponse as LogisticsBootstrapResponse,
)
from app.schemas.logistics.views import (
    LogisticsChatMessageItem as LogisticsChatMessageItem,
)
from app.schemas.logistics.views import (
    LogisticsChatThreadItem as LogisticsChatThreadItem,
)
from app.schemas.logistics.views import (
    LogisticsDashboardStats as LogisticsDashboardStats,
)
from app.schemas.logistics.views import LogisticsDriverItem as LogisticsDriverItem
from app.schemas.logistics.views import LogisticsEquipmentItem as LogisticsEquipmentItem
from app.schemas.logistics.views import (
    LogisticsEscalationItem as LogisticsEscalationItem,
)
from app.schemas.logistics.views import (
    LogisticsEscalationStatusUpdate as LogisticsEscalationStatusUpdate,
)
from app.schemas.logistics.views import LogisticsHubItem as LogisticsHubItem
from app.schemas.logistics.views import (
    LogisticsMaintenanceItem as LogisticsMaintenanceItem,
)
from app.schemas.logistics.views import LogisticsMeetingItem as LogisticsMeetingItem
from app.schemas.logistics.views import (
    LogisticsMeetingParticipantItem as LogisticsMeetingParticipantItem,
)
from app.schemas.logistics.views import (
    LogisticsNotificationItem as LogisticsNotificationItem,
)
from app.schemas.logistics.views import LogisticsReportItem as LogisticsReportItem
from app.schemas.logistics.views import (
    LogisticsReturnCaseItem as LogisticsReturnCaseItem,
)
from app.schemas.logistics.views import LogisticsTaskItem as LogisticsTaskItem
from app.schemas.logistics.views import (
    LogisticsTransactionItem as LogisticsTransactionItem,
)
from app.schemas.logistics.views import LogisticsUserItem as LogisticsUserItem
from app.schemas.logistics.views import LogisticsVehicleItem as LogisticsVehicleItem
from app.schemas.logistics.views import LogisticsZoneItem as LogisticsZoneItem
