"""The manager workspace: dispatch contacts, chats, meetings, tasks, notifications and alerts."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    DispatchContactItem,
    LogisticsAlertItem,
    LogisticsChatMessageCreate,
    LogisticsChatThreadCreate,
    LogisticsChatThreadItem,
    LogisticsChatThreadUpdate,
    LogisticsMeetingCreate,
    LogisticsMeetingItem,
    LogisticsMeetingParticipantItem,
    LogisticsMeetingUpdate,
    LogisticsNotificationItem,
    LogisticsNotificationUpdate,
    LogisticsTaskCreate,
    LogisticsTaskItem,
    LogisticsTaskUpdate,
)
from app.services import logistics_service

router = APIRouter()


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
