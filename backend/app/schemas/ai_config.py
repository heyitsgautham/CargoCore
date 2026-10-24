"""
ai_config.py — Pydantic schemas for AI settings and knowledge base CRUD.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── AI System Settings ────────────────────────────────────────────────────────


class AISettingsResponse(BaseModel):
    id: uuid.UUID
    tone: str
    language_mode: str
    sentiment_threshold: int
    refund_limit_inr: int
    system_prompt: str
    autonomous_replies: bool
    legal_threat_detection: bool
    real_time_sentiment_analysis: bool
    proactive_human_handover: bool
    updated_at: datetime
    updated_by_user_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class AISettingsUpdate(BaseModel):
    tone: str | None = None
    language_mode: str | None = None
    sentiment_threshold: int | None = Field(None, ge=0, le=100)
    refund_limit_inr: int | None = Field(None, ge=0)
    system_prompt: str | None = None
    autonomous_replies: bool | None = None
    legal_threat_detection: bool | None = None
    real_time_sentiment_analysis: bool | None = None
    proactive_human_handover: bool | None = None


# ── Knowledge Articles ────────────────────────────────────────────────────────


class KnowledgeArticleResponse(BaseModel):
    id: str
    audience: str
    title: str
    keywords: list[str]
    content: str
    category: str | None = None
    article_type: str
    is_active: bool
    likes: int
    author_initials: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeArticleCreate(BaseModel):
    id: str | None = Field(None, description="Optional slug — auto-generated from title if omitted")
    audience: str = Field("ALL", pattern="^(ALL|VENDOR|INDIVIDUAL)$")
    title: str = Field(..., min_length=3, max_length=255)
    keywords: list[str] = Field(default_factory=list)
    content: str = Field(..., min_length=10)
    category: str | None = None
    article_type: str = Field("SOP", pattern="^(SOP|Policy|Script|Guide)$")


class KnowledgeArticleUpdate(BaseModel):
    title: str | None = None
    audience: str | None = Field(None, pattern="^(ALL|VENDOR|INDIVIDUAL)$")
    keywords: list[str] | None = None
    content: str | None = None
    category: str | None = None
    article_type: str | None = Field(None, pattern="^(SOP|Policy|Script|Guide)$")
    is_active: bool | None = None


class KnowledgeArticleListResponse(BaseModel):
    articles: list[KnowledgeArticleResponse]
    total: int
