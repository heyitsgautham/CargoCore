"""
ai_config.py — Pydantic schemas for knowledge base CRUD.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
