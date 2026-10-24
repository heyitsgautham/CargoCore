"""Knowledge base articles."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import AIKnowledgeArticle
from app.models.user import User

# ── AI System Settings ────────────────────────────────────────────────────────
# ── Knowledge Base CRUD ───────────────────────────────────────────────────────
from app.schemas.ai_config import (  # noqa: E402
    KnowledgeArticleCreate,
    KnowledgeArticleListResponse,
    KnowledgeArticleResponse,
    KnowledgeArticleUpdate,
)


def _article_to_schema(a: AIKnowledgeArticle) -> KnowledgeArticleResponse:
    return KnowledgeArticleResponse(
        id=a.id,
        audience=a.audience,
        title=a.title,
        keywords=list(a.keywords or []),
        content=a.content,
        category=a.category,
        article_type=a.article_type,
        is_active=a.is_active,
        likes=a.likes,
        author_initials=a.author_initials,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def _get_initials(name: str) -> str:
    parts = (name or "").split()
    if not parts:
        return "??"
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else parts[0][-1])).upper()


def _slugify(title: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:80]


async def list_knowledge_articles(
    db: AsyncSession,
    active_only: bool = True,
    audience: str | None = None,
) -> KnowledgeArticleListResponse:
    q = select(AIKnowledgeArticle)
    if active_only:
        q = q.where(AIKnowledgeArticle.is_active.is_(True))
    if audience:
        q = q.where(
            (AIKnowledgeArticle.audience == audience)
            | (AIKnowledgeArticle.audience == "ALL")
        )
    q = q.order_by(AIKnowledgeArticle.likes.desc(), AIKnowledgeArticle.title)
    rows = list((await db.execute(q)).scalars().all())
    return KnowledgeArticleListResponse(
        articles=[_article_to_schema(r) for r in rows],
        total=len(rows),
    )


async def get_knowledge_article_by_id(
    db: AsyncSession, article_id: str
) -> KnowledgeArticleResponse | None:
    row = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    return _article_to_schema(row) if row else None


async def create_knowledge_article(
    db: AsyncSession, data: KnowledgeArticleCreate, actor: User
) -> KnowledgeArticleResponse:
    import uuid as _uuid

    article_id = data.id or _slugify(data.title)
    existing = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    if existing:
        article_id = f"{article_id}_{_uuid.uuid4().hex[:6]}"

    row = AIKnowledgeArticle(
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
    db.add(row)
    await db.flush()
    return _article_to_schema(row)


async def update_knowledge_article(
    db: AsyncSession, article_id: str, data: KnowledgeArticleUpdate, actor: User
) -> KnowledgeArticleResponse | None:
    row = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    if not row:
        return None

    if data.title is not None:
        row.title = data.title
    if data.audience is not None:
        row.audience = data.audience
    if data.keywords is not None:
        row.keywords = data.keywords
    if data.content is not None:
        row.content = data.content
    if data.category is not None:
        row.category = data.category
    if data.article_type is not None:
        row.article_type = data.article_type
    if data.is_active is not None:
        row.is_active = data.is_active

    row.updated_by_user_id = actor.id
    row.updated_at = datetime.now(UTC)
    await db.flush()
    return _article_to_schema(row)


async def delete_knowledge_article(db: AsyncSession, article_id: str) -> bool:
    row = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    if not row:
        return False
    await db.delete(row)
    await db.flush()
    return True


async def like_knowledge_article(
    db: AsyncSession, article_id: str
) -> KnowledgeArticleResponse | None:
    row = (
        await db.execute(
            select(AIKnowledgeArticle).where(AIKnowledgeArticle.id == article_id)
        )
    ).scalar_one_or_none()
    if not row:
        return None
    row.likes += 1
    await db.flush()
    return _article_to_schema(row)
