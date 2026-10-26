"""Logistics manager operations: bootstrap, escalations, AI query, fleet, finance entries, returns and zones."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    CapitalInvestmentCreate,
    LogisticsAiQueryRequest,
    LogisticsAiQueryResponse,
    LogisticsBootstrapResponse,
    LogisticsDriverItem,
    LogisticsDriverUpdate,
    LogisticsEscalationItem,
    LogisticsEscalationStatusUpdate,
    LogisticsReturnCaseItem,
    LogisticsReturnCaseUpdate,
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

router = APIRouter()


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
