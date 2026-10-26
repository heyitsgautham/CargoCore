"""Damage reports, refund cases and customer history for the support desk."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ── AI Support — Reverse Logistics (Damage Reports) ───────────────────────────

class SupportMessageItem(BaseModel):
    text: str
    sent_by: str
    sent_at: str


class SupportMessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    sent_by: str = Field(default="Support Agent", max_length=100)


class SupportDamageReportItem(BaseModel):
    id: UUID
    reference_code: str
    customer_id: UUID
    customer_name: str
    customer_email: str | None = None
    order_id: UUID | None = None
    order_tracking_code: str | None = None
    description: str
    photos: list[str] = []
    flow_type: str
    status: str
    support_notes: str | None = None
    support_messages: list[SupportMessageItem] = []
    sentiment: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SupportDamageReportCreate(BaseModel):
    customer_id: UUID
    order_id: UUID | None = None
    description: str = Field(..., min_length=5, max_length=5000)
    flow_type: str = Field(default="photo_review")


class SupportDamageReportNotesUpdate(BaseModel):
    support_notes: str = Field(default="", max_length=5000)


class SupportDamageReportStats(BaseModel):
    total: int
    reported: int
    photo_review: int
    pickup_inspection: int
    under_review: int


class SupportDamageReportListResponse(BaseModel):
    reports: list[SupportDamageReportItem]
    stats: SupportDamageReportStats


# ── AI Support — Refund Center ────────────────────────────────────────────────

class SupportRefundCaseItem(BaseModel):
    id: UUID
    reference_code: str
    customer_name: str
    customer_id: UUID | None = None
    order_id: UUID | None = None
    original_price: float
    refund_amount: float
    status: str
    flow_type: str
    is_urgent: bool = False
    urgent_reason: str | None = None
    support_notes: str | None = None
    sentiment: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SupportRefundCaseUrgentUpdate(BaseModel):
    is_urgent: bool
    urgent_reason: str | None = Field(default=None, max_length=1000)


class SupportRefundCaseStats(BaseModel):
    total_refunded_value: float
    pending_decision: int
    urgent_count: int


class SupportRefundCaseListResponse(BaseModel):
    cases: list[SupportRefundCaseItem]
    stats: SupportRefundCaseStats


# ── AI Support — Customer History ─────────────────────────────────────────────

class CustomerHistoryResponse(BaseModel):
    total_orders: int
    damage_reports_count: int
    escalations_count: int
    last_sentiment: str | None = None
