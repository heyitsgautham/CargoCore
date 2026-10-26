"""The customer chatbot: chat, conversation history, sessions and escalations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_ro_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.routers.ai.access import SUPPORT_ROLES
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    EscalateRequest,
    EscalationListResponse,
    EscalationResponse,
    SessionListResponse,
)
from app.services import ai_service

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the AI chatbot",
    description=(
        "Send a natural language message. The AI decides whether to query the "
        "database or respond directly. Pass `session_id` to continue an existing "
        "conversation, or omit it to start a new one."
    ),
)
async def chat(
    data: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    ro_db: Annotated[AsyncSession, Depends(get_ro_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await ai_service.chat(
            db=db,
            ro_db=ro_db,
            user=user,
            session_id=data.session_id,
            user_message=data.message,
            chat_context=data.context,
            order_id=data.order_id,
        )
    except Exception:
        # Safety net — never let an unhandled exception reach the client as 500
        import traceback
        traceback.print_exc()
        return ChatResponse(
            session_id=data.session_id or __import__("uuid").uuid4(),
            message="Sorry, an unexpected error occurred. Please try again.",
            intent="error",
            sql_generated=None,
            linked_order_id=data.order_id,
        )


@router.get(
    "/conversations/{session_id}",
    response_model=ConversationHistory,
    summary="Get conversation history",
    description="Retrieve all messages for a specific conversation session.",
)
async def get_conversation(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    history = await ai_service.get_conversation_history(
        db=db, session_id=session_id, user_id=user.id
    )
    if not history.messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or you don't have access to it.",
        )
    return history


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="List chat sessions",
    description="List all conversation sessions for the current user, most recent first.",
)
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await ai_service.get_user_sessions(db=db, user_id=user.id)


@router.post(
    "/escalate/{conversation_id}",
    response_model=EscalationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Escalate conversation to human agent",
    description="Flag a conversation for human review. The conversation must belong to the requesting user.",
)
async def escalate_conversation(
    conversation_id: UUID,
    data: EscalateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await ai_service.escalate_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user.id,
            reason=data.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/escalations",
    response_model=EscalationListResponse,
    summary="List escalations",
    description="Human agent view: list all escalations. Use ?status=OPEN or ?status=RESOLVED to filter.",
)
async def list_escalations(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    status: str | None = Query(default=None, description="Filter by status: OPEN or RESOLVED"),
):
    escalations = await ai_service.list_escalations(db=db, status_filter=status)
    return EscalationListResponse(escalations=escalations)


@router.put(
    "/escalations/{escalation_id}/resolve",
    response_model=EscalationResponse,
    summary="Resolve an escalation",
    description="Mark an escalation as resolved. Restricted to LOGISTIC_MANAGER and AI_AGENT roles.",
)
async def resolve_escalation(
    escalation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    try:
        return await ai_service.resolve_escalation(db=db, escalation_id=escalation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
