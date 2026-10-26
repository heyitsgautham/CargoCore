"""Support desk sessions, dashboard, analytics and settings."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.ai.chat import ContactSubmissionResponse


class SupportSessionEscalationSummary(BaseModel):
    id: UUID
    status: str
    reason: str
    escalated_at: datetime
    resolved_at: datetime | None = None
    escalated_to_user_id: UUID | None = None
    assigned_agent_name: str | None = None


class SupportSessionListItem(BaseModel):
    session_id: UUID
    user_id: UUID
    user_name: str
    user_email: str | None = None
    user_role: str | None = None
    user_phone: str | None = None
    first_message_at: datetime
    last_message: str
    last_message_role: str
    last_message_at: datetime
    message_count: int
    latest_order_tracking_code: str | None = None
    sentiment: str | None = None
    human_agent_engaged: bool = False
    assigned_agent_name: str | None = None
    needs_human_attention: bool = False
    attention_reason: str | None = None
    escalation: SupportSessionEscalationSummary | None = None


class SupportSessionListResponse(BaseModel):
    sessions: list[SupportSessionListItem]


class SupportConversationMessage(BaseModel):
    id: UUID
    role: str
    message: str
    intent: str | None = None
    created_at: datetime
    author_name: str | None = None
    author_role: str | None = None

    model_config = {"from_attributes": True}


class SupportSessionDetail(BaseModel):
    session: SupportSessionListItem
    messages: list[SupportConversationMessage]


class SupportDashboardStats(BaseModel):
    total_sessions: int
    active_sessions: int
    human_engaged_sessions: int
    sessions_needing_human: int
    open_escalations: int
    open_contact_forms: int
    new_contact_forms: int
    resolved_contact_forms: int
    user_messages_today: int
    assistant_messages_today: int


class SupportDashboardFeedItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    created_at: datetime


class SupportDashboardResponse(BaseModel):
    stats: SupportDashboardStats
    priority_sessions: list[SupportSessionListItem]
    recent_contact_submissions: list[ContactSubmissionResponse]
    activity_feed: list[SupportDashboardFeedItem]


class SupportAnalyticsMetric(BaseModel):
    id: str
    label: str
    icon: str
    value: float
    formatted_value: str
    trend: str
    trend_direction: str


class SupportAnalyticsResolutionChart(BaseModel):
    labels: list[str]
    ai_resolved: list[int]
    human_escalated: list[int]


class SupportAnalyticsEscalationReason(BaseModel):
    label: str
    count: int
    pct: int


class SupportAnalyticsSentimentChart(BaseModel):
    labels: list[str]
    ai_handled: list[float]
    human_handled: list[float]


class SupportAnalyticsInsight(BaseModel):
    id: str
    icon: str
    title: str
    text: str
    tone: str = Field(description="purple, blue, amber, red, or green")
    action_label: str = "Take Action"
    executed: bool = False


class SupportAnalyticsResponse(BaseModel):
    range: str
    generated_at: datetime
    metrics: list[SupportAnalyticsMetric]
    resolution_chart: SupportAnalyticsResolutionChart
    escalation_reasons: list[SupportAnalyticsEscalationReason]
    sentiment_chart: SupportAnalyticsSentimentChart
    insights: list[SupportAnalyticsInsight]


class SupportAnalyticsInsightExecutionResponse(BaseModel):
    insight_id: str
    ticket_id: UUID
    ticket_reference_code: str
    message: str


class SupportIntegrationStatus(BaseModel):
    provider: str
    label: str
    description: str
    connected: bool
    connection_source: str
    status_note: str
    editable: bool = False


class SupportSettings(BaseModel):
    tone: str = Field(..., min_length=2, max_length=60)
    language_mode: str = Field(..., min_length=2, max_length=60)
    sentiment_threshold: int = Field(..., ge=0, le=100)
    refund_limit_inr: int = Field(..., ge=0, le=500000)
    system_prompt: str = Field(..., min_length=20, max_length=20000)
    autonomous_replies: bool = True
    legal_threat_detection: bool = True
    real_time_sentiment_analysis: bool = True
    proactive_human_handover: bool = False


class SupportSettingsResponse(BaseModel):
    settings: SupportSettings
    integrations: list[SupportIntegrationStatus]
    updated_at: datetime | None = None
    autonomous_reply_guidance: str
    rag_recommended: bool
