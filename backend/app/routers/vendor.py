from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.logistics import LogisticsNotificationItem, LogisticsNotificationUpdate
from app.schemas.vendor import (
    VendorApiKeyCreate,
    VendorApiKeyResponse,
    VendorBulkUploadCreate,
    VendorBulkUploadResponse,
    VendorBulkUploadUpdate,
    VendorDamageReport,
    VendorDamageReportCreate,
    VendorDamageReportsResponse,
    VendorDashboardResponse,
    VendorInvoicePayRequest,
    VendorInvoiceRecord,
    VendorRecurringCostEstimate,
    VendorRecurringCostEstimateRequest,
    VendorRecurringRuleCreate,
    VendorRecurringRuleResponse,
    VendorSettings,
    VendorSettingsResponse,
    VendorShipmentsResponse,
    VendorSupportReplyCreate,
    VendorSupportTicketCreate,
    VendorSupportTicketResponse,
    VendorTeamMemberCreate,
    VendorTeamMemberResponse,
)
from app.schemas.wallet import WalletSummary, WalletTopUpRequest, WalletTopUpResponse
from app.services import logistics_service, vendor_service, wallet_service

router = APIRouter(prefix="/api/v1/vendor", tags=["Vendor"])


@router.get("/dashboard", response_model=VendorDashboardResponse)
async def get_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.get_vendor_dashboard(db, current_user)


@router.get("/shipments", response_model=VendorShipmentsResponse)
async def get_shipments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.get_vendor_shipments(db, current_user)


@router.get("/settings", response_model=VendorSettingsResponse)
async def get_settings(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.get_vendor_settings(current_user)


@router.put("/settings", response_model=VendorSettingsResponse)
async def update_settings(
    data: VendorSettings,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.update_vendor_settings(db, current_user, data)


@router.get("/damage-reports", response_model=VendorDamageReportsResponse)
async def get_damage_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.get_vendor_damage_reports(db, current_user)


@router.post("/damage-reports", response_model=VendorDamageReport)
async def create_damage_report(
    data: VendorDamageReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.create_vendor_damage_report(db, current_user, data)


@router.get("/team-members", response_model=list[VendorTeamMemberResponse])
async def list_team_members(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.list_team_members(db, current_user)


@router.post("/team-members", response_model=VendorTeamMemberResponse)
async def create_team_member(
    data: VendorTeamMemberCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.create_team_member(db, current_user, data)


@router.delete("/team-members/{member_id}")
async def delete_team_member(
    member_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await vendor_service.delete_team_member(db, current_user, member_id)
    return {"message": "Team member removed"}


@router.get("/api-keys", response_model=list[VendorApiKeyResponse])
async def list_api_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.list_api_keys(db, current_user)


@router.post("/api-keys", response_model=VendorApiKeyResponse)
async def create_api_key(
    data: VendorApiKeyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.create_api_key(db, current_user, data)


@router.post("/api-keys/{key_id}/revoke", response_model=VendorApiKeyResponse)
async def revoke_api_key(
    key_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.revoke_api_key(db, current_user, key_id)


@router.get("/recurring-rules", response_model=list[VendorRecurringRuleResponse])
async def list_recurring_rules(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.list_recurring_rules(db, current_user)


@router.post("/recurring-rules", response_model=VendorRecurringRuleResponse)
async def create_recurring_rule(
    data: VendorRecurringRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.create_recurring_rule(db, current_user, data)


@router.put("/recurring-rules/{rule_id}", response_model=VendorRecurringRuleResponse)
async def update_recurring_rule(
    rule_id: UUID,
    data: VendorRecurringRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.update_recurring_rule(db, current_user, rule_id, data)


@router.post("/recurring-rules/{rule_id}/toggle", response_model=VendorRecurringRuleResponse)
async def toggle_recurring_rule(
    rule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.toggle_recurring_rule(db, current_user, rule_id)


@router.delete("/recurring-rules/{rule_id}")
async def delete_recurring_rule(
    rule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await vendor_service.delete_recurring_rule(db, current_user, rule_id)
    return {"message": "Recurring rule deleted"}


@router.post("/recurring/estimate-cost", response_model=VendorRecurringCostEstimate)
async def estimate_recurring_cost(
    data: VendorRecurringCostEstimateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Estimate the per-run delivery cost for a recurring schedule.

    Uses road-route distance from the resolved hub pickup point to the
    destination and applies the platform rate card (baseBookingFee + perKmRate).
    If live routing is unavailable, the backend falls back to a buffered estimate.
    This is called from the vendor's Create Schedule form after the vendor
    selects a destination on the map, so they can see the expected wallet debit
    before confirming the schedule.
    """
    result = await vendor_service.estimate_recurring_cost(db, data)
    await db.commit()
    return result


@router.get("/bulk-uploads", response_model=list[VendorBulkUploadResponse])
async def list_bulk_uploads(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.list_bulk_uploads(db, current_user)


@router.post("/bulk-uploads", response_model=VendorBulkUploadResponse)
async def create_bulk_upload(
    data: VendorBulkUploadCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.create_bulk_upload(db, current_user, data)


@router.put("/bulk-uploads/{upload_id}", response_model=VendorBulkUploadResponse)
async def update_bulk_upload(
    upload_id: UUID,
    data: VendorBulkUploadUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.update_bulk_upload(db, current_user, upload_id, data)


@router.get("/support-tickets", response_model=list[VendorSupportTicketResponse])
async def list_support_tickets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.list_support_tickets(db, current_user)


@router.post("/support-tickets", response_model=VendorSupportTicketResponse)
async def create_support_ticket(
    data: VendorSupportTicketCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.create_support_ticket(db, current_user, data)


@router.post("/support-tickets/{ticket_id}/reply", response_model=VendorSupportTicketResponse)
async def reply_support_ticket(
    ticket_id: UUID,
    data: VendorSupportReplyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.reply_support_ticket(db, current_user, ticket_id, data)


@router.post("/invoices/{order_id}/pay", response_model=VendorInvoiceRecord)
async def pay_invoice(
    order_id: UUID,
    data: VendorInvoicePayRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.pay_invoice(db, current_user, order_id, data)


@router.post("/support-tickets/{ticket_id}/resolve", response_model=VendorSupportTicketResponse)
async def resolve_support_ticket(
    ticket_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await vendor_service.resolve_support_ticket(db, current_user, ticket_id)


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
