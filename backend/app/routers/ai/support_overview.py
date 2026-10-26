"""Support dashboard, settings and analytics."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.routers.ai.access import SUPPORT_ROLES
from app.schemas.ai import (
    SupportAnalyticsInsightExecutionResponse,
    SupportAnalyticsResponse,
    SupportDashboardResponse,
    SupportSettings,
    SupportSettingsResponse,
)
from app.services import ai_support_service

router = APIRouter()


@router.get(
    "/support/dashboard",
    response_model=SupportDashboardResponse,
    summary="Support dashboard data",
)
async def get_support_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_support_dashboard(db=db)


@router.get(
    "/support/settings",
    response_model=SupportSettingsResponse,
    summary="AI support system settings",
)
async def get_support_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_support_settings(db=db)


@router.put(
    "/support/settings",
    response_model=SupportSettingsResponse,
    summary="Update AI support system settings",
)
async def update_support_settings(
    data: SupportSettings,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.update_support_settings(db=db, user=user, data=data)


@router.get(
    "/support/analytics",
    response_model=SupportAnalyticsResponse,
    summary="Support analytics for the AI analytics dashboard",
)
async def get_support_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    time_range: str = Query(default="7D", alias="range"),
):
    return await ai_support_service.get_support_analytics(db=db, time_range=time_range)


@router.post(
    "/support/analytics/insights/{insight_id}/execute",
    response_model=SupportAnalyticsInsightExecutionResponse,
    summary="Create a follow-up ticket for an analytics insight",
)
async def execute_support_analytics_insight(
    insight_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    time_range: str = Query(default="7D", alias="range"),
):
    return await ai_support_service.execute_support_analytics_insight(
        db=db,
        insight_id=insight_id,
        time_range=time_range,
    )
