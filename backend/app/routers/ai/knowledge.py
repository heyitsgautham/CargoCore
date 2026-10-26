"""Knowledge base articles."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.routers.ai.access import SUPPORT_ROLES
from app.schemas.ai_config import (
    KnowledgeArticleCreate,
    KnowledgeArticleListResponse,
    KnowledgeArticleResponse,
    KnowledgeArticleUpdate,
)
from app.services import ai_support_service

router = APIRouter()


# ── Knowledge Base CRUD ───────────────────────────────────────────────────────

@router.get(
    "/knowledge-articles",
    response_model=KnowledgeArticleListResponse,
    summary="List all knowledge base articles",
)
async def list_knowledge_articles(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    active_only: bool = Query(True),
    audience: str | None = Query(None),
):
    return await ai_support_service.list_knowledge_articles(
        db=db, active_only=active_only, audience=audience
    )


@router.post(
    "/knowledge-articles",
    response_model=KnowledgeArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge base article",
)
async def create_knowledge_article(
    data: KnowledgeArticleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.create_knowledge_article(db=db, data=data, actor=user)


@router.get(
    "/knowledge-articles/{article_id}",
    response_model=KnowledgeArticleResponse,
    summary="Get a single knowledge base article",
)
async def get_knowledge_article(
    article_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    article = await ai_support_service.get_knowledge_article_by_id(db=db, article_id=article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.put(
    "/knowledge-articles/{article_id}",
    response_model=KnowledgeArticleResponse,
    summary="Update a knowledge base article",
)
async def update_knowledge_article(
    article_id: str,
    data: KnowledgeArticleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    article = await ai_support_service.update_knowledge_article(
        db=db, article_id=article_id, data=data, actor=user
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.delete(
    "/knowledge-articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a knowledge base article",
)
async def delete_knowledge_article(
    article_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    deleted = await ai_support_service.delete_knowledge_article(db=db, article_id=article_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Article not found")


@router.post(
    "/knowledge-articles/{article_id}/like",
    response_model=KnowledgeArticleResponse,
    summary="Increment the like count on an article",
)
async def like_knowledge_article(
    article_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    article = await ai_support_service.like_knowledge_article(db=db, article_id=article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
