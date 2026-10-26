"""Escalations, the escalation center and support tickets."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.ai.chat import SupportAgentSummary

# ── Escalation Schemas ────────────────────────────────────────────────────────

class EscalateRequest(BaseModel):
    reason: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Why this conversation needs human attention.",
    )


class EscalationResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    reason: str
    escalated_to_user_id: UUID | None = None
    escalated_at: datetime
    resolved_at: datetime | None = None
    status: str

    model_config = {"from_attributes": True}


class EscalationListResponse(BaseModel):
    escalations: list[EscalationResponse]


# ── Enriched Escalation (for Escalation Center UI) ────────────────────────────

class EscalationDetailItem(BaseModel):
    id: UUID
    conversation_id: UUID
    session_id: UUID
    reason: str
    status: str
    escalated_at: datetime
    resolved_at: datetime | None = None
    customer_name: str
    customer_email: str | None = None
    customer_role: str | None = None
    latest_order_tracking_code: str | None = None
    sentiment: str
    assigned_agent_name: str | None = None

    model_config = {"from_attributes": True}


class EscalationDetailListResponse(BaseModel):
    escalations: list[EscalationDetailItem]
    open_count: int
    resolved_count: int


# ── Support Ticket Schemas ─────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    priority: str = Field(default="medium")
    category: str = Field(default="general")
    customer_name: str | None = None


class TicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    category: str | None = None
    notes: str | None = None
    assigned_to_user_id: UUID | None = None
    resolution_action: str | None = None


class TicketReplyItem(BaseModel):
    from_name: str
    message: str
    created_at: datetime


class TicketResponse(BaseModel):
    id: UUID
    reference_code: str
    title: str
    description: str
    priority: str
    status: str
    category: str
    customer_name: str | None = None
    notes: str | None = None
    assigned_to_user_id: UUID | None = None
    assigned_agent_name: str | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    source: str = "manual"
    source_label: str = "Manual"
    requester_type: str | None = None
    issue_type: str | None = None
    resolution_action: str | None = None
    resolution_label: str | None = None
    linked_vendor_ticket_id: UUID | None = None
    linked_vendor_ticket_code: str | None = None
    linked_damage_report_id: UUID | None = None
    linked_order_id: UUID | None = None
    linked_order_tracking_code: str | None = None
    linked_vendor_replies: list[TicketReplyItem] = []
    can_delete: bool = True
    lm_action_steps: list[str] = []

    model_config = {"from_attributes": True}


class TicketStats(BaseModel):
    total: int
    new: int
    in_progress: int
    resolved: int
    urgent: int


class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]
    stats: TicketStats
    agents: list[SupportAgentSummary]
