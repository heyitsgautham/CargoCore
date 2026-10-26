"""Pydantic schemas for the AI chatbot and support desk endpoints, re-exported from app.schemas.ai."""

from app.schemas.ai.chat import AgentReplyRequest as AgentReplyRequest
from app.schemas.ai.chat import ChatRequest as ChatRequest
from app.schemas.ai.chat import ChatResponse as ChatResponse
from app.schemas.ai.chat import (
    ContactSubmissionCreatePublic as ContactSubmissionCreatePublic,
)
from app.schemas.ai.chat import (
    ContactSubmissionListResponse as ContactSubmissionListResponse,
)
from app.schemas.ai.chat import (
    ContactSubmissionReplyRequest as ContactSubmissionReplyRequest,
)
from app.schemas.ai.chat import ContactSubmissionResponse as ContactSubmissionResponse
from app.schemas.ai.chat import ContactSubmissionStats as ContactSubmissionStats
from app.schemas.ai.chat import ContactSubmissionUpdate as ContactSubmissionUpdate
from app.schemas.ai.chat import ConversationHistory as ConversationHistory
from app.schemas.ai.chat import ConversationMessage as ConversationMessage
from app.schemas.ai.chat import SessionListItem as SessionListItem
from app.schemas.ai.chat import SessionListResponse as SessionListResponse
from app.schemas.ai.chat import SupportAgentSummary as SupportAgentSummary
from app.schemas.ai.chat import (
    SupportSessionEscalateRequest as SupportSessionEscalateRequest,
)
from app.schemas.ai.support_cases import (
    CustomerHistoryResponse as CustomerHistoryResponse,
)
from app.schemas.ai.support_cases import (
    SupportDamageReportCreate as SupportDamageReportCreate,
)
from app.schemas.ai.support_cases import (
    SupportDamageReportItem as SupportDamageReportItem,
)
from app.schemas.ai.support_cases import (
    SupportDamageReportListResponse as SupportDamageReportListResponse,
)
from app.schemas.ai.support_cases import (
    SupportDamageReportNotesUpdate as SupportDamageReportNotesUpdate,
)
from app.schemas.ai.support_cases import (
    SupportDamageReportStats as SupportDamageReportStats,
)
from app.schemas.ai.support_cases import SupportMessageCreate as SupportMessageCreate
from app.schemas.ai.support_cases import SupportMessageItem as SupportMessageItem
from app.schemas.ai.support_cases import SupportRefundCaseItem as SupportRefundCaseItem
from app.schemas.ai.support_cases import (
    SupportRefundCaseListResponse as SupportRefundCaseListResponse,
)
from app.schemas.ai.support_cases import (
    SupportRefundCaseStats as SupportRefundCaseStats,
)
from app.schemas.ai.support_cases import (
    SupportRefundCaseUrgentUpdate as SupportRefundCaseUrgentUpdate,
)
from app.schemas.ai.support_desk import (
    SupportAnalyticsEscalationReason as SupportAnalyticsEscalationReason,
)
from app.schemas.ai.support_desk import (
    SupportAnalyticsInsight as SupportAnalyticsInsight,
)
from app.schemas.ai.support_desk import (
    SupportAnalyticsInsightExecutionResponse as SupportAnalyticsInsightExecutionResponse,
)
from app.schemas.ai.support_desk import SupportAnalyticsMetric as SupportAnalyticsMetric
from app.schemas.ai.support_desk import (
    SupportAnalyticsResolutionChart as SupportAnalyticsResolutionChart,
)
from app.schemas.ai.support_desk import (
    SupportAnalyticsResponse as SupportAnalyticsResponse,
)
from app.schemas.ai.support_desk import (
    SupportAnalyticsSentimentChart as SupportAnalyticsSentimentChart,
)
from app.schemas.ai.support_desk import (
    SupportConversationMessage as SupportConversationMessage,
)
from app.schemas.ai.support_desk import (
    SupportDashboardFeedItem as SupportDashboardFeedItem,
)
from app.schemas.ai.support_desk import (
    SupportDashboardResponse as SupportDashboardResponse,
)
from app.schemas.ai.support_desk import SupportDashboardStats as SupportDashboardStats
from app.schemas.ai.support_desk import (
    SupportIntegrationStatus as SupportIntegrationStatus,
)
from app.schemas.ai.support_desk import SupportSessionDetail as SupportSessionDetail
from app.schemas.ai.support_desk import (
    SupportSessionEscalationSummary as SupportSessionEscalationSummary,
)
from app.schemas.ai.support_desk import SupportSessionListItem as SupportSessionListItem
from app.schemas.ai.support_desk import (
    SupportSessionListResponse as SupportSessionListResponse,
)
from app.schemas.ai.support_desk import SupportSettings as SupportSettings
from app.schemas.ai.support_desk import (
    SupportSettingsResponse as SupportSettingsResponse,
)
from app.schemas.ai.tickets import EscalateRequest as EscalateRequest
from app.schemas.ai.tickets import EscalationDetailItem as EscalationDetailItem
from app.schemas.ai.tickets import (
    EscalationDetailListResponse as EscalationDetailListResponse,
)
from app.schemas.ai.tickets import EscalationListResponse as EscalationListResponse
from app.schemas.ai.tickets import EscalationResponse as EscalationResponse
from app.schemas.ai.tickets import TicketCreate as TicketCreate
from app.schemas.ai.tickets import TicketListResponse as TicketListResponse
from app.schemas.ai.tickets import TicketReplyItem as TicketReplyItem
from app.schemas.ai.tickets import TicketResponse as TicketResponse
from app.schemas.ai.tickets import TicketStats as TicketStats
from app.schemas.ai.tickets import TicketUpdate as TicketUpdate
