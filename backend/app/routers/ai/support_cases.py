"""Damage reports, refund cases and customer history for the support desk."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.routers.ai.access import SUPPORT_ROLES
from app.schemas.ai import (
    CustomerHistoryResponse,
    SupportDamageReportCreate,
    SupportDamageReportItem,
    SupportDamageReportListResponse,
    SupportDamageReportNotesUpdate,
    SupportMessageCreate,
    SupportRefundCaseItem,
    SupportRefundCaseListResponse,
    SupportRefundCaseUrgentUpdate,
)
from app.services import ai_support_service

router = APIRouter()


# ── AI Support — Reverse Logistics (Damage Reports) ──────────────────────────

@router.get(
    "/support/damage-reports",
    response_model=SupportDamageReportListResponse,
    summary="List all damage reports enriched for AI support staff",
)
async def list_support_damage_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.list_support_damage_reports(db=db)


@router.post(
    "/support/damage-reports",
    response_model=SupportDamageReportItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a damage report on a customer's behalf",
)
async def create_support_damage_report(
    data: SupportDamageReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.create_support_damage_report(db=db, data=data)


@router.put(
    "/support/damage-reports/{report_id}/notes",
    response_model=SupportDamageReportItem,
    summary="Update support notes on a damage report",
)
async def update_damage_report_notes(
    report_id: UUID,
    data: SupportDamageReportNotesUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.update_damage_report_notes(db=db, report_id=report_id, data=data)


@router.post(
    "/support/damage-reports/{report_id}/message",
    response_model=SupportDamageReportItem,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to the customer for a damage report case",
)
async def send_support_message(
    report_id: UUID,
    data: SupportMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.send_support_message(db=db, report_id=report_id, data=data, agent=user)


# ── AI Support — Refund Center ────────────────────────────────────────────────

@router.get(
    "/support/refund-cases",
    response_model=SupportRefundCaseListResponse,
    summary="List return cases with refund info for AI support staff",
)
async def list_support_refund_cases(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.list_support_refund_cases(db=db)


@router.put(
    "/support/refund-cases/{case_id}/urgent",
    response_model=SupportRefundCaseItem,
    summary="Set or clear urgency flag on a return case",
)
async def flag_refund_case_urgent(
    case_id: UUID,
    data: SupportRefundCaseUrgentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.flag_refund_case_urgent(db=db, case_id=case_id, data=data)


# ── AI Support — Customer History ─────────────────────────────────────────────

@router.get(
    "/support/customer-history/{user_id}",
    response_model=CustomerHistoryResponse,
    summary="Get customer history summary for support sidebar",
)
async def get_customer_history(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_customer_history(db=db, user_id=user_id)
