"""Notifications, driver crisis alerts and dispatcher alerts."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsAlert,
    LogisticsNotification,
)
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    LogisticsAlertItem,
    LogisticsNotificationItem,
    LogisticsNotificationUpdate,
)
from app.services.logistics.formatting import (
    _fmt_relative,
    _notification_visible_to_user,
)


async def get_notifications(db: AsyncSession, current_user: User) -> list[LogisticsNotificationItem]:
    notifications = (await db.execute(select(LogisticsNotification).order_by(LogisticsNotification.created_at.desc()))).scalars().all()
    notifications = [item for item in notifications if _notification_visible_to_user(item, current_user)]
    return [LogisticsNotificationItem(id=item.id, title=item.title, message=item.message, time=_fmt_relative(item.created_at), created_at=item.created_at, read=item.is_read, type=item.type) for item in notifications]


async def update_notification(db: AsyncSession, notification_id: UUID, data: LogisticsNotificationUpdate, current_user: User) -> LogisticsNotificationItem:
    notification = (await db.execute(select(LogisticsNotification).where(LogisticsNotification.id == notification_id))).scalar_one_or_none()
    if not notification or not _notification_visible_to_user(notification, current_user):
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = data.read
    db.add(notification)
    await db.flush()
    return LogisticsNotificationItem(id=notification.id, title=notification.title, message=notification.message, time=_fmt_relative(notification.created_at), created_at=notification.created_at, read=notification.is_read, type=notification.type)


async def mark_all_notifications_read(db: AsyncSession, current_user: User) -> MessageResponse:
    notifications = (await db.execute(select(LogisticsNotification))).scalars().all()
    for notification in notifications:
        if not _notification_visible_to_user(notification, current_user):
            continue
        notification.is_read = True
        db.add(notification)
    await db.flush()
    return MessageResponse(message="Notifications marked as read")


async def clear_notifications(db: AsyncSession, current_user: User) -> MessageResponse:
    notifications = (await db.execute(select(LogisticsNotification))).scalars().all()
    for notification in notifications:
        if not _notification_visible_to_user(notification, current_user):
            continue
        await db.delete(notification)
    await db.flush()
    return MessageResponse(message="Notifications cleared")


async def create_driver_crisis_alert(db: AsyncSession, user, payload: dict) -> LogisticsAlert:
    """Create a crisis alert from a driver - for SOS, accidents, breakdowns etc."""
    alert_type = payload.get("type", "sos")
    
    # Get driver name
    driver_name = user.name or user.email.split("@")[0]
    
    # Build alert title based on type
    type_labels = {
        "sos": "🚨 SOS Alert",
        "accident": "🚗 Accident Report", 
        "breakdown": "🔧 Vehicle Breakdown",
        "security": "🔐 Security Threat",
        "medical": "🏥 Medical Emergency"
    }
    title = f"{type_labels.get(alert_type, '🚨 Emergency')} — {driver_name}"
    
    # Build description
    location = payload.get("location", "Location unknown")
    description = payload.get("description", f"Driver {driver_name} triggered {alert_type} alert")
    if payload.get("latitude") and payload.get("longitude"):
        location = f"{payload['latitude']}, {payload['longitude']}"
        description += f" at coordinates {location}"
    
    # Severity based on type
    severity_map = {"sos": "critical", "accident": "critical", "medical": "critical", "security": "high", "breakdown": "high"}
    severity = severity_map.get(alert_type, "high")
    
    # Icon based on type
    icon_map = {"sos": "emergency", "accident": "car_crash", "breakdown": "build", "security": "security", "medical": "local_hospital"}
    icon = icon_map.get(alert_type, "warning")
    
    alert = LogisticsAlert(
        alert_type=alert_type,
        title=title,
        description=description,
        severity=severity,
        icon=icon,
        location=location,
        recommendation=f"Contact driver {driver_name} immediately. Dispatch emergency response if needed.",
        impact_json={"driver_id": str(user.id), "driver_name": driver_name, "alert_type": alert_type},
        is_active=True,
    )
    db.add(alert)
    await db.flush()
    
    # Broadcast crisis alert to dispatcher dashboard via WebSocket
    try:
        from app.routers.ws_fleet import fleet_manager
        await fleet_manager.broadcast({
            "type": "crisis_alert",
            "alert_id": str(alert.id),
            "alert_type": alert_type,
            "title": title,
            "description": description,
            "severity": severity,
            "icon": icon,
            "location": location,
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "driver_id": str(user.id),
            "driver_name": driver_name,
            "timestamp": datetime.now(UTC).isoformat(),
        })
    except Exception:
        pass  # WebSocket broadcast is best-effort
    
    return alert


async def create_alert(db: AsyncSession, payload: dict) -> LogisticsAlertItem:
    alert = LogisticsAlert(
        warehouse_id=payload.get("warehouse_id"),
        alert_type=payload.get("type", "manual"),
        title=payload["title"],
        description=payload["description"],
        severity=payload.get("severity", "medium"),
        icon=payload.get("icon"),
        location=payload.get("location"),
        recommendation=payload.get("recommendation"),
        impact_json=payload.get("impact"),
        is_active=True,
    )
    db.add(alert)
    await db.flush()
    return LogisticsAlertItem(id=alert.id, type=alert.alert_type, title=alert.title, description=alert.description, severity=alert.severity, icon=alert.icon, timestamp=alert.created_at.strftime("%I:%M %p"), location=alert.location, recommendation=alert.recommendation, impact=alert.impact_json)


async def resolve_alert(db: AsyncSession, alert_id: UUID) -> MessageResponse:
    alert = (await db.execute(select(LogisticsAlert).where(LogisticsAlert.id == alert_id))).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = False
    db.add(alert)
    await db.flush()
    return MessageResponse(message="Alert resolved")


async def list_alerts(db: AsyncSession) -> list[LogisticsAlertItem]:
    result = await db.execute(
        select(LogisticsAlert)
        .where(LogisticsAlert.is_active == True)
        .order_by(LogisticsAlert.created_at.desc())
        .limit(50)
    )
    alerts = result.scalars().all()
    return [
        LogisticsAlertItem(
            id=a.id,
            type=a.alert_type,
            title=a.title,
            description=a.description,
            severity=a.severity,
            icon=a.icon,
            timestamp=a.created_at.strftime("%I:%M %p"),
            location=a.location,
            recommendation=a.recommendation,
            impact=a.impact_json,
        )
        for a in alerts
    ]
