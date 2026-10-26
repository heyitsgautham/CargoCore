"""Support tickets."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.routers.ai.access import SUPPORT_ROLES
from app.schemas.ai import (
    AgentReplyRequest,
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from app.services import ai_support_service

router = APIRouter()


# ── Support Tickets ───────────────────────────────────────────────────────────

@router.get(
    "/tickets",
    response_model=TicketListResponse,
    summary="List all support tickets",
)
async def list_tickets(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.list_tickets(db=db)


@router.get(
    "/recovery-tickets/count",
    summary="Count of open AI-analytics recovery tickets for the Logistics Manager",
)
async def recovery_tickets_count(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_recovery_tickets_count(db=db)


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket",
)
async def create_ticket(
    data: TicketCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.create_ticket(db=db, data=data, actor=user)


@router.put(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    summary="Update a support ticket",
)
async def update_ticket(
    ticket_id: UUID,
    data: TicketUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.update_ticket(db=db, ticket_id=ticket_id, data=data, actor=user)


@router.post(
    "/tickets/{ticket_id}/reply",
    response_model=TicketResponse,
    summary="Reply to a linked vendor ticket from the support dashboard",
)
async def reply_to_ticket(
    ticket_id: UUID,
    data: AgentReplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.reply_to_ticket(db=db, ticket_id=ticket_id, data=data, actor=user)


@router.delete(
    "/tickets/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a support ticket",
)
async def delete_ticket(
    ticket_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    await ai_support_service.delete_ticket(db=db, ticket_id=ticket_id, actor=user)
