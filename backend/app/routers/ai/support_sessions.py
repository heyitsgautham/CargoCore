"""Live support sessions and the escalation center."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.routers.ai.access import SUPPORT_ROLES
from app.schemas.ai import (
    AgentReplyRequest,
    EscalationDetailListResponse,
    EscalationResponse,
    SupportSessionDetail,
    SupportSessionEscalateRequest,
    SupportSessionListResponse,
)
from app.services import ai_service, ai_support_service

router = APIRouter()


@router.get(
    "/support/sessions",
    response_model=SupportSessionListResponse,
    summary="List live support sessions for staff",
)
async def list_support_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    search: str | None = Query(default=None),
):
    return await ai_support_service.list_support_sessions(db=db, search=search)


@router.get(
    "/support/sessions/{session_id}",
    response_model=SupportSessionDetail,
    summary="Get staff view of a conversation session",
)
async def get_support_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_support_session_detail(db=db, session_id=session_id)


@router.post(
    "/support/sessions/{session_id}/take-over",
    response_model=SupportSessionDetail,
    summary="Take over a live AI conversation",
)
async def take_over_support_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.take_over_support_session(
        db=db,
        session_id=session_id,
        agent=user,
    )


@router.post(
    "/support/sessions/{session_id}/reply",
    response_model=SupportSessionDetail,
    summary="Send a human agent reply in a live conversation",
)
async def reply_to_support_session(
    session_id: UUID,
    data: AgentReplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.reply_to_support_session(
        db=db,
        session_id=session_id,
        agent=user,
        data=data,
    )


@router.post(
    "/support/sessions/{session_id}/escalate",
    response_model=EscalationResponse,
    summary="Escalate a support session from the live conversation view",
)
async def escalate_support_session(
    session_id: UUID,
    data: SupportSessionEscalateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.escalate_support_session(
        db=db,
        session_id=session_id,
        agent=user,
        data=data,
    )


# ── Escalation Center (enriched) ─────────────────────────────────────────────

@router.get(
    "/escalation-center",
    response_model=EscalationDetailListResponse,
    summary="List enriched escalations for the Escalation Center UI",
)
async def list_escalation_center(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    status: str | None = Query(default=None, description="OPEN or RESOLVED"),
):
    return await ai_support_service.list_enriched_escalations(db=db, status_filter=status)


@router.put(
    "/escalation-center/{escalation_id}/resolve",
    response_model=EscalationResponse,
    summary="Resolve an escalation from the Escalation Center",
)
async def resolve_escalation_center(
    escalation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    try:
        return await ai_service.resolve_escalation(db=db, escalation_id=escalation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
