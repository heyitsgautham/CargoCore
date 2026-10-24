from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.customer import (
    CustomerDamageReport,
    CustomerDamageReportCreate,
    CustomerDamageReportsResponse,
    CustomerPaymentsSummary,
    CustomerProfileResponse,
    CustomerQuotesResponse,
    CustomerSettings,
    CustomerSettingsResponse,
    CustomerTrackingResponse,
)
from app.schemas.logistics import LogisticsNotificationItem, LogisticsNotificationUpdate
from app.schemas.wallet import WalletSummary, WalletTopUpRequest, WalletTopUpResponse
from app.services import customer_service, logistics_service, wallet_service

router = APIRouter(prefix="/api/v1/customer", tags=["Customer"])


@router.get("/dashboard")
async def get_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await customer_service.get_customer_dashboard(db, current_user)
    return result.model_dump(mode="json")


@router.get("/tracking", response_model=CustomerTrackingResponse)
async def get_tracking(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await customer_service.get_customer_tracking(db, current_user)


@router.get("/payments", response_model=CustomerPaymentsSummary)
async def get_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await customer_service.get_customer_payments(db, current_user)


@router.get("/profile", response_model=CustomerProfileResponse)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await customer_service.get_customer_profile(current_user)


@router.get("/quotes", response_model=CustomerQuotesResponse)
async def get_quotes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await customer_service.get_customer_quotes(db, current_user)


@router.post("/quotes/{quote_id}/convert")
async def convert_quote(
    quote_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await customer_service.convert_customer_quote(db, current_user, quote_id)


@router.get("/damage-reports", response_model=CustomerDamageReportsResponse)
async def get_damage_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await customer_service.get_customer_damage_reports(db, current_user)


@router.post("/damage-reports", response_model=CustomerDamageReport)
async def create_damage_report(
    data: CustomerDamageReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await customer_service.create_customer_damage_report(db, current_user, data)


@router.get("/settings", response_model=CustomerSettingsResponse)
async def get_settings(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await customer_service.get_customer_settings(current_user)


@router.put("/settings", response_model=CustomerSettingsResponse)
async def update_settings(
    data: CustomerSettings,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await customer_service.update_customer_settings(db, current_user, data)


@router.delete("/account", response_model=MessageResponse)
async def delete_account(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await customer_service.delete_customer_account(db, current_user)
    return MessageResponse(message="Account deleted successfully")


@router.get("/wallet", response_model=WalletSummary)
async def get_wallet(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await wallet_service.get_wallet_summary(db, current_user)


@router.post("/wallet/top-up", response_model=WalletTopUpResponse)
async def top_up_wallet(
    data: WalletTopUpRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await wallet_service.top_up_wallet(db, user=current_user, amount=data.amount)
    await db.commit()
    return result


@router.post("/wallet/backfill-debits")
async def backfill_wallet_debits(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Backfill missing DEBIT entries for old wallet payments recorded via the wrong endpoint."""
    created = await wallet_service.backfill_wallet_debits(db, current_user)
    await db.commit()
    return {"created": created}


# ── Notification endpoints ────────────────────────────────────────────────────

@router.get("/notifications", response_model=list[LogisticsNotificationItem])
async def get_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await logistics_service.get_notifications(db, current_user)


@router.put("/notifications/{notification_id}", response_model=LogisticsNotificationItem)
async def update_notification(
    notification_id: UUID,
    data: LogisticsNotificationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await logistics_service.update_notification(db, notification_id, data, current_user)
    await db.commit()
    return result


@router.post("/notifications/mark-all-read", response_model=MessageResponse)
async def mark_all_notifications_read(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await logistics_service.mark_all_notifications_read(db, current_user)
    await db.commit()
    return result


@router.delete("/notifications", response_model=MessageResponse)
async def clear_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await logistics_service.clear_notifications(db, current_user)
    await db.commit()
    return result
