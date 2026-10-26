"""Endpoints the driver app calls for the signed-in driver under /drivers/me."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.schemas.logistics import (
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
    LogisticsNotificationItem,
    LogisticsVehicleItem,
)
from app.services import logistics_service

router = APIRouter()


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
