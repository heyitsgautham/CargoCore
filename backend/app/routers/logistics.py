from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    CapitalInvestmentCreate,
    DispatchContactItem,
    DriverAuditEventItem,
    DriverCashoutRequest,
    DriverCrewMemberItem,
    DriverDashboardContext,
    DriverDispatchMessageCreate,
    DriverDispatchThreadItem,
    DriverFuelReceiptCreate,
    DriverHosSummary,
    DriverShiftSummary,
    DriverTelemetryResponse,
    DriverVehicleBindRequest,
    LogisticsAiQueryRequest,
    LogisticsAiQueryResponse,
    LogisticsAlertItem,
    LogisticsBootstrapResponse,
    LogisticsChatMessageCreate,
    LogisticsChatThreadCreate,
    LogisticsChatThreadItem,
    LogisticsChatThreadUpdate,
    LogisticsDocumentCreate,
    LogisticsDocumentItem,
    LogisticsDocumentUpdateStatus,
    LogisticsDriverItem,
    LogisticsDriverUpdate,
    LogisticsEscalationItem,
    LogisticsEscalationStatusUpdate,
    LogisticsManifestCreate,
    LogisticsManifestItem,
    LogisticsMeetingCreate,
    LogisticsMeetingItem,
    LogisticsMeetingParticipantItem,
    LogisticsMeetingUpdate,
    LogisticsNotificationItem,
    LogisticsNotificationUpdate,
    LogisticsReturnCaseItem,
    LogisticsReturnCaseUpdate,
    LogisticsTaskCreate,
    LogisticsTaskItem,
    LogisticsTaskUpdate,
    LogisticsTransactionCreate,
    LogisticsTransactionItem,
    LogisticsVehicleCreate,
    LogisticsVehicleItem,
    LogisticsVehicleUpdate,
    LogisticsZoneCreate,
    LogisticsZoneItem,
    LogisticsZoneUpdate,
)
from app.services import logistics_service

router = APIRouter(prefix="/api/v1/logistics", tags=["Logistics Manager"])


@router.get("/bootstrap", response_model=LogisticsBootstrapResponse)
async def bootstrap(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.build_bootstrap(db)


@router.put("/escalations/{escalation_id}", response_model=LogisticsEscalationItem)
async def update_escalation_status(
    escalation_id: UUID,
    data: LogisticsEscalationStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.update_escalation_status(db, escalation_id, data)


@router.post("/ai/query", response_model=LogisticsAiQueryResponse)
async def ai_query(
    data: LogisticsAiQueryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.answer_ai_query(db, data.query)


@router.get("/vehicles", response_model=list[LogisticsVehicleItem])
async def list_vehicles(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER", "DRIVER"))],
):
    warehouse_id = getattr(user, "warehouse_id", None)
    # Warehouse managers only see their own warehouse's vehicles; logistic managers and dispatchers see all
    if getattr(user, "role", None) and user.role.name == "WAREHOUSE_MANAGER" and warehouse_id:
        return await logistics_service.list_vehicles(db, warehouse_id=warehouse_id)
    if getattr(user, "role", None) and user.role.name == "DRIVER":
        return await logistics_service.list_vehicles(
            db,
            warehouse_id=warehouse_id,
            driver_id=user.id,
            driver_scoped=True,
        )
    return await logistics_service.list_vehicles(db)


@router.get("/drivers", response_model=list[LogisticsDriverItem])
async def list_drivers(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    warehouse_id = getattr(user, "warehouse_id", None)
    if getattr(user, "role", None) and user.role.name == "DISPATCHER" and warehouse_id:
        return await logistics_service.list_drivers(db, warehouse_id=warehouse_id)
    return await logistics_service.list_drivers(db)



@router.put("/drivers/{driver_id}", response_model=LogisticsDriverItem)
async def update_driver(
    driver_id: UUID,
    data: LogisticsDriverUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    if getattr(getattr(user, "role", None), "name", None) == "DISPATCHER":
        dispatcher_only_fields = [data.current_location, data.current_job, data.warehouse_id, data.efficiency_score]
        if any(value is not None for value in dispatcher_only_fields):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dispatchers can only update driver suspension status")
        if data.status not in {"Active", "Suspended"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dispatcher driver status must be Active or Suspended")
    return await logistics_service.update_driver(db, driver_id, data)


@router.post("/vehicles", response_model=LogisticsVehicleItem, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    data: LogisticsVehicleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.create_vehicle(db, data)


@router.put("/vehicles/{vehicle_id}", response_model=LogisticsVehicleItem)
async def update_vehicle(
    vehicle_id: UUID,
    data: LogisticsVehicleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.update_vehicle(db, vehicle_id, data)


@router.post("/transactions", response_model=LogisticsTransactionItem, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: LogisticsTransactionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.create_transaction(db, data)


@router.post("/capital-investment", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_capital_investment(
    data: CapitalInvestmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    from app.services import finance_service
    result = await finance_service.create_capital_investment(
        db,
        amount=data.amount,
        description=data.description,
        funding_source=data.funding_source,
        warehouse_id=data.warehouse_id,
        investment_date=data.investment_date,
    )
    await db.commit()
    return result


@router.put("/returns/{case_id}", response_model=LogisticsReturnCaseItem)
async def update_return_case(
    case_id: UUID,
    data: LogisticsReturnCaseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.update_return_case(db, case_id, data)


@router.post("/returns/{case_id}/issue-refund")
async def issue_return_refund(
    case_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.issue_return_refund(db, case_id)


@router.post("/returns/{case_id}/schedule-pickup", response_model=LogisticsReturnCaseItem)
async def schedule_return_pickup(
    case_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    """Schedule a driver pickup for an approved return case."""
    return await logistics_service.schedule_return_pickup(db, case_id)


@router.post("/zones", response_model=LogisticsZoneItem, status_code=status.HTTP_201_CREATED)
async def create_zone(
    data: LogisticsZoneCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.create_zone(db, data)


@router.get("/zones", response_model=list[LogisticsZoneItem])
async def list_zones(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.list_zones(db)


@router.put("/zones/{zone_id}", response_model=LogisticsZoneItem)
async def update_zone(
    zone_id: UUID,
    data: LogisticsZoneUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.update_zone(db, zone_id, data)


@router.delete("/zones/{zone_id}", response_model=MessageResponse)
async def delete_zone(
    zone_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.delete_zone(db, zone_id)


@router.get("/dispatch-contacts", response_model=list[DispatchContactItem])
async def get_dispatch_contacts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.get_dispatch_contacts(db)


@router.get("/chats", response_model=list[LogisticsChatThreadItem])
async def list_chats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER", "WAREHOUSE_MANAGER"))],
):
    return await logistics_service.list_chat_threads(db)


@router.post("/chats", response_model=LogisticsChatThreadItem, status_code=status.HTTP_201_CREATED)
async def create_chat(
    data: LogisticsChatThreadCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.create_chat_thread(db, data)


@router.post("/chats/{thread_id}/messages", response_model=LogisticsChatThreadItem)
async def add_chat_message(
    thread_id: UUID,
    data: LogisticsChatMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER", "WAREHOUSE_MANAGER"))],
):
    return await logistics_service.add_chat_message(db, thread_id, data)


@router.put("/chats/{thread_id}", response_model=LogisticsChatThreadItem)
async def update_chat(
    thread_id: UUID,
    data: LogisticsChatThreadUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER", "WAREHOUSE_MANAGER"))],
):
    return await logistics_service.mute_chat_thread(db, thread_id, data)


@router.delete("/chats/{thread_id}", response_model=MessageResponse)
async def delete_chat(
    thread_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.delete_chat_thread(db, thread_id)


@router.get("/meetings", response_model=list[LogisticsMeetingItem])
async def list_meetings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.list_meetings(db, current_user)


@router.get("/meeting-participants", response_model=list[LogisticsMeetingParticipantItem])
async def list_meeting_participants(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.list_meeting_participants(db, current_user)


@router.post("/meetings", response_model=LogisticsMeetingItem, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    data: LogisticsMeetingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.create_meeting(db, data, current_user)


@router.put("/meetings/{meeting_id}", response_model=LogisticsMeetingItem)
async def update_meeting(
    meeting_id: UUID,
    data: LogisticsMeetingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.update_meeting(db, meeting_id, data, current_user)


@router.delete("/meetings/{meeting_id}", response_model=MessageResponse)
async def delete_meeting(
    meeting_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.delete_meeting(db, meeting_id, current_user)


@router.get("/tasks", response_model=list[LogisticsTaskItem])
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.list_tasks(db)


@router.post("/tasks", response_model=LogisticsTaskItem, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: LogisticsTaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.create_task(db, data)


@router.put("/tasks/{task_id}", response_model=LogisticsTaskItem)
async def update_task(
    task_id: UUID,
    data: LogisticsTaskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.update_task(db, task_id, data)


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
async def delete_task(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.delete_task(db, task_id)


@router.get("/notifications", response_model=list[LogisticsNotificationItem])
async def get_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.get_notifications(db, current_user)


@router.put("/notifications/{notification_id}", response_model=LogisticsNotificationItem)
async def update_notification(
    notification_id: UUID,
    data: LogisticsNotificationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.update_notification(db, notification_id, data, current_user)


@router.post("/notifications/mark-all-read", response_model=MessageResponse)
async def mark_all_notifications_read(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.mark_all_notifications_read(db, current_user)


@router.delete("/notifications", response_model=MessageResponse)
async def clear_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.clear_notifications(db, current_user)


@router.post("/notifications/broadcast", response_model=MessageResponse)
async def send_broadcast(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
    payload: dict = Body(...),
):
    return await logistics_service.send_broadcast(db, payload)


@router.get("/alerts", response_model=list[LogisticsAlertItem])
async def list_alerts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.list_alerts(db)


@router.post("/alerts", response_model=dict)
async def create_alert(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
    payload: dict = Body(...),
):
    alert = await logistics_service.create_alert(db, payload)
    return alert.model_dump()


@router.post("/alerts/{alert_id}/resolve", response_model=MessageResponse)
async def resolve_alert(
    alert_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.resolve_alert(db, alert_id)


@router.get("/manifests", response_model=list[LogisticsManifestItem])
async def list_manifests(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.list_manifests(db)


@router.post("/manifests", response_model=LogisticsManifestItem, status_code=status.HTTP_201_CREATED)
async def create_manifest(
    data: LogisticsManifestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.create_manifest(db, data, created_by_id=user.id)


@router.post("/manifests/{manifest_id}/push", response_model=LogisticsManifestItem)
async def push_manifest(
    manifest_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await logistics_service.push_manifest(db, manifest_id)


@router.post("/documents", response_model=LogisticsDocumentItem, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: LogisticsDocumentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.create_document(db, data)


@router.put("/documents/{doc_id}/status", response_model=LogisticsDocumentItem)
async def update_document_status(
    doc_id: UUID,
    data: LogisticsDocumentUpdateStatus,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER"))],
):
    return await logistics_service.update_document_status(db, doc_id, data)


@router.get("/drivers/me/dashboard", response_model=DriverDashboardContext)
async def get_driver_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.get_driver_dashboard(db, user)


@router.get("/drivers/me/shift", response_model=DriverShiftSummary)
async def get_driver_shift(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.get_driver_shift(db, user)


@router.get("/drivers/me/hos", response_model=DriverHosSummary)
async def get_driver_hos(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.get_driver_hos(db, user)


@router.get("/drivers/me/crew", response_model=list[DriverCrewMemberItem])
async def get_driver_crew(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.get_driver_crew(db, user)


@router.post("/drivers/me/crew/{labourer_id}/check-in", response_model=DriverCrewMemberItem)
async def check_in_driver_crew_member(
    labourer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.check_in_driver_crew_member(db, user, labourer_id)


@router.get("/drivers/me/telemetry", response_model=DriverTelemetryResponse)
async def get_driver_telemetry(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.get_driver_telemetry(db, user)


@router.post("/drivers/me/bind-vehicle", response_model=LogisticsVehicleItem)
async def bind_driver_vehicle(
    data: DriverVehicleBindRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.bind_driver_vehicle(db, user, data)


@router.post("/drivers/me/shift/start", response_model=dict)
async def start_shift(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.start_shift(db, user)


@router.post("/drivers/me/shift/end", response_model=dict)
async def end_shift(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.end_shift(db, user)


from pydantic import BaseModel


class VehicleReturnRequest(BaseModel):
    odometer_km: int | None = None
    fuel_level_pct: int | None = None
    notes: str | None = None
    condition_photo: str | None = None  # base64, stored client-side only for now


@router.post("/drivers/me/return-vehicle", response_model=dict)
async def return_vehicle(
    data: VehicleReturnRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.return_vehicle(
        db, user,
        odometer_km=data.odometer_km,
        fuel_level_pct=data.fuel_level_pct,
        notes=data.notes,
    )


class LocationUpdateParams(BaseModel):
    latitude: float
    longitude: float

@router.post("/drivers/me/location", response_model=dict)
async def update_driver_location(
    data: LocationUpdateParams,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.update_driver_location(db, user, data.latitude, data.longitude)


@router.post("/drivers/me/fuel-receipt", response_model=dict)
async def submit_fuel_receipt(
    data: DriverFuelReceiptCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    result = await logistics_service.submit_fuel_receipt(db, user, data)
    return {"message": result.message}


@router.get("/drivers/me/dispatch-thread", response_model=DriverDispatchThreadItem)
async def get_dispatch_thread(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.get_driver_dispatch_thread(db, user)


@router.post("/drivers/me/dispatch-thread/messages", response_model=DriverDispatchThreadItem)
async def send_dispatch_message(
    data: DriverDispatchMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.add_driver_dispatch_message(db, user, data)


@router.get("/drivers/me/manager-thread", response_model=DriverDispatchThreadItem)
async def get_manager_thread(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.get_driver_manager_thread(db, user)


@router.post("/drivers/me/manager-thread/messages", response_model=DriverDispatchThreadItem)
async def send_manager_message(
    data: DriverDispatchMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.add_driver_manager_message(db, user, data)


@router.get("/drivers/me/audit", response_model=list[DriverAuditEventItem])
async def get_driver_audit(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    return await logistics_service.get_driver_audit_log(db, user)


@router.post("/drivers/me/crisis-alert", response_model=dict)
async def send_driver_crisis_alert(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
    payload: dict = Body(...),
):
    """Send a crisis/SOS alert from driver - visible in dispatcher's crisis management"""
    alert = await logistics_service.create_driver_crisis_alert(db, user, payload)
    return {"message": "Crisis alert sent", "alert_id": str(alert.id)}


@router.get("/drivers/me/notifications", response_model=list[LogisticsNotificationItem])
async def get_driver_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    """Get notifications visible to the current driver (broadcasts sent to drivers)."""
    return await logistics_service.get_notifications(db, user)


@router.post("/drivers/me/cashout", response_model=dict)
async def request_cashout(
    data: DriverCashoutRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[object, Depends(require_role("DRIVER"))],
):
    result = await logistics_service.request_driver_cashout(db, user, data)
    return {"message": result.message}
