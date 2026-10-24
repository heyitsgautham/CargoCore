"""
ai_config_service.py
CRUD operations for AI system settings (AISupportSettings) and
knowledge base articles (AIKnowledgeArticle).
"""
from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import AIKnowledgeArticle
from app.models.ai_support_settings import AISupportSettings
from app.models.user import User
from app.schemas.ai_config import (
    AISettingsUpdate,
    KnowledgeArticleCreate,
    KnowledgeArticleUpdate,
)

# ── AI System Settings ────────────────────────────────────────────────────────

DEFAULT_SYSTEM_PROMPT = (
    "You are the primary autonomous support agent for Cargo-Core Logistics.\n"
    "Your operational priorities are:\n"
    "1. De-escalate angry customers with empathy.\n"
    "2. Adhere strictly to approved SOPs and policy documents.\n"
    "3. Automatically process low-risk actions only when policy permits.\n"
    "4. Transfer to a human supervisor if legal threats are detected or confidence drops.\n\n"
    "Always communicate cleanly, concisely, and handle order references securely."
)


async def get_ai_settings(db: AsyncSession) -> AISupportSettings:
    """
    Return the single settings row.  Creates it with defaults if it doesn't
    exist yet (first-run scenario).
    """
    row = (await db.execute(select(AISupportSettings).limit(1))).scalar_one_or_none()
    if row is None:
        row = AISupportSettings(system_prompt=DEFAULT_SYSTEM_PROMPT)
        db.add(row)
        await db.flush()
    return row


async def update_ai_settings(
    db: AsyncSession,
    data: AISettingsUpdate,
    actor: User,
) -> AISupportSettings:
    row = await get_ai_settings(db)

    if data.tone is not None:
        row.tone = data.tone
    if data.language_mode is not None:
        row.language_mode = data.language_mode
    if data.sentiment_threshold is not None:
        row.sentiment_threshold = data.sentiment_threshold
    if data.refund_limit_inr is not None:
        row.refund_limit_inr = data.refund_limit_inr
    if data.system_prompt is not None:
        row.system_prompt = data.system_prompt
    if data.autonomous_replies is not None:
        row.autonomous_replies = data.autonomous_replies
    if data.legal_threat_detection is not None:
        row.legal_threat_detection = data.legal_threat_detection
    if data.real_time_sentiment_analysis is not None:
        row.real_time_sentiment_analysis = data.real_time_sentiment_analysis
    if data.proactive_human_handover is not None:
        row.proactive_human_handover = data.proactive_human_handover

    row.updated_by_user_id = actor.id
    row.updated_at = datetime.now(UTC)
    await db.flush()
    return row


# ── Knowledge Articles ────────────────────────────────────────────────────────


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug[:80]


async def list_knowledge_articles(
    db: AsyncSession, audience: str | None = None, active_only: bool = True
) -> list[AIKnowledgeArticle]:
    q = select(AIKnowledgeArticle)
    if active_only:
        q = q.where(AIKnowledgeArticle.is_active.is_(True))
    if audience:
        q = q.where(
            (AIKnowledgeArticle.audience == audience)
            | (AIKnowledgeArticle.audience == "ALL")
        )
    q = q.order_by(AIKnowledgeArticle.likes.desc(), AIKnowledgeArticle.title)
    return list((await db.execute(q)).scalars().all())


async def get_knowledge_article(
    db: AsyncSession, article_id: str
) -> AIKnowledgeArticle | None:
    return (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()


async def create_knowledge_article(
    db: AsyncSession, data: KnowledgeArticleCreate, actor: User
) -> AIKnowledgeArticle:
    article_id = data.id or _slugify(data.title)
    # Ensure uniqueness by appending suffix if needed
    existing = await get_knowledge_article(db, article_id)
    if existing:
        article_id = f"{article_id}_{uuid.uuid4().hex[:6]}"

    article = AIKnowledgeArticle(
        id=article_id,
        audience=data.audience,
        title=data.title,
        keywords=data.keywords or [],
        content=data.content,
        category=data.category,
        article_type=data.article_type,
        is_active=True,
        likes=0,
        author_initials=_get_initials(actor.name),
        updated_by_user_id=actor.id,
    )
    db.add(article)
    await db.flush()
    return article


async def update_knowledge_article(
    db: AsyncSession, article_id: str, data: KnowledgeArticleUpdate, actor: User
) -> AIKnowledgeArticle | None:
    article = await get_knowledge_article(db, article_id)
    if not article:
        return None

    if data.title is not None:
        article.title = data.title
    if data.audience is not None:
        article.audience = data.audience
    if data.keywords is not None:
        article.keywords = data.keywords
    if data.content is not None:
        article.content = data.content
    if data.category is not None:
        article.category = data.category
    if data.article_type is not None:
        article.article_type = data.article_type
    if data.is_active is not None:
        article.is_active = data.is_active

    article.updated_by_user_id = actor.id
    article.updated_at = datetime.now(UTC)
    await db.flush()
    return article


async def delete_knowledge_article(db: AsyncSession, article_id: str) -> bool:
    article = await get_knowledge_article(db, article_id)
    if not article:
        return False
    await db.delete(article)
    await db.flush()
    return True


async def like_knowledge_article(
    db: AsyncSession, article_id: str
) -> AIKnowledgeArticle | None:
    article = await get_knowledge_article(db, article_id)
    if not article:
        return None
    article.likes += 1
    await db.flush()
    return article


# ── helpers ───────────────────────────────────────────────────────────────────


def _get_initials(name: str) -> str:
    parts = (name or "").split()
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()
