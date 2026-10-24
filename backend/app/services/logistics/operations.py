"""Vehicles, transactions, zones, tasks, manifests and documents."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import LogisticsDocument
from app.models.logistics import (
    LogisticsManifest,
    LogisticsTask,
    LogisticsTransaction,
    LogisticsVehicle,
    LogisticsZone,
)
from app.models.order import Order
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.logistics import (
    LogisticsDocumentCreate,
    LogisticsDocumentItem,
    LogisticsDocumentUpdateStatus,
    LogisticsManifestCreate,
    LogisticsManifestItem,
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
from app.services.logistics.bootstrap import build_bootstrap
from app.services.logistics.driver_context import _build_vehicle_item
from app.services.logistics.formatting import _now
from app.services.logistics.lookups import _get_vehicle, _get_zone


async def list_vehicles(
    db: AsyncSession,
    warehouse_id: UUID | None = None,
    driver_id: UUID | None = None,
    driver_scoped: bool = False,
) -> list[LogisticsVehicleItem]:
    query = select(LogisticsVehicle).order_by(LogisticsVehicle.created_at.desc())
    if warehouse_id is not None:
        query = query.where(LogisticsVehicle.warehouse_id == warehouse_id)
    if driver_scoped and driver_id is not None:
        if warehouse_id is not None:
            query = query.where(
                or_(
                    LogisticsVehicle.assigned_driver_id == driver_id,
                    and_(
                        LogisticsVehicle.warehouse_id == warehouse_id,
                        or_(
                            LogisticsVehicle.assigned_driver_id.is_(None),
                            LogisticsVehicle.assigned_driver_id == driver_id,
                        ),
                    ),
                )
            )
        else:
            query = query.where(LogisticsVehicle.assigned_driver_id == driver_id)
    vehicles = (await db.execute(query)).scalars().all()
    # Collect all user IDs: from permanent assignments + from active orders
    active_orders = (await db.execute(
        select(Order).where(
            Order.status.in_(["ASSIGNED", "IN_TRANSIT"]),
            Order.assigned_vehicle_id.isnot(None),
            Order.assigned_driver_id.isnot(None),
        )
    )).scalars().all()
    active_driver_by_vehicle: dict = {
        o.assigned_vehicle_id: o.assigned_driver_id for o in active_orders
    }
    permanent_user_ids = [v.assigned_driver_id for v in vehicles if v.assigned_driver_id]
    active_user_ids = list(active_driver_by_vehicle.values())
    all_user_ids = list({uid for uid in permanent_user_ids + active_user_ids if uid})
    users = (await db.execute(select(User).where(User.id.in_(all_user_ids)))).scalars().all() if all_user_ids else []
    user_map = {u.id: u for u in users}
    items: list[LogisticsVehicleItem] = []
    for vehicle in vehicles:
        if vehicle.assigned_driver_id in user_map:
            driver_name = user_map[vehicle.assigned_driver_id].name
        elif vehicle.id in active_driver_by_vehicle and active_driver_by_vehicle[vehicle.id] in user_map:
            driver_name = user_map[active_driver_by_vehicle[vehicle.id]].name
        else:
            driver_name = "Unassigned"
        items.append(_build_vehicle_item(vehicle, driver_name=driver_name))
    return items


async def create_vehicle(db: AsyncSession, data: LogisticsVehicleCreate) -> LogisticsVehicleItem:
    vehicle = LogisticsVehicle(**data.model_dump())
    db.add(vehicle)
    await db.flush()
    bootstrap = await build_bootstrap(db)
    return next(item for item in bootstrap.vehicles if item.id == vehicle.id)


async def update_vehicle(db: AsyncSession, vehicle_id: UUID, data: LogisticsVehicleUpdate) -> LogisticsVehicleItem:
    vehicle = await _get_vehicle(db, vehicle_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, key, value)
    db.add(vehicle)
    await db.flush()
    bootstrap = await build_bootstrap(db)
    return next(item for item in bootstrap.vehicles if item.id == vehicle.id)


async def create_transaction(db: AsyncSession, data: LogisticsTransactionCreate) -> LogisticsTransactionItem:
    import uuid as _uuid
    tx = LogisticsTransaction(
        warehouse_id=data.warehouse_id,
        transaction_code=f"TX-{str(_uuid.uuid4()).replace('-', '').upper()[:12]}",
        description=data.description,
        transaction_type=data.transaction_type,
        amount=data.amount,
        status=data.status,
        metadata_json=data.metadata_json,
    )
    db.add(tx)
    await db.flush()
    return LogisticsTransactionItem(
        id=tx.id,
        hub_id=tx.warehouse_id,
        transaction_code=tx.transaction_code,
        date=tx.transaction_date.strftime("%b %d, %Y"),
        desc=tx.description,
        type=tx.transaction_type,
        amount=tx.amount,
        status=tx.status,
        metadata_json=dict(tx.metadata_json or {}),
        related_order=None,
    )


async def create_zone(db: AsyncSession, data: LogisticsZoneCreate) -> LogisticsZoneItem:
    zone = LogisticsZone(**data.model_dump())
    db.add(zone)
    await db.flush()
    return LogisticsZoneItem(id=zone.id, hub_id=zone.warehouse_id, name=zone.name, type=zone.zone_type, radius=zone.radius_km, status=zone.status, color=zone.color_token, lat=zone.lat, lng=zone.lng)


async def list_zones(db: AsyncSession) -> list[LogisticsZoneItem]:
    zones = (
        await db.execute(select(LogisticsZone).order_by(LogisticsZone.created_at.desc()))
    ).scalars().all()
    return [
        LogisticsZoneItem(
            id=zone.id,
            hub_id=zone.warehouse_id,
            name=zone.name,
            type=zone.zone_type,
            radius=zone.radius_km,
            status=zone.status,
            color=zone.color_token,
            lat=zone.lat,
            lng=zone.lng,
        )
        for zone in zones
    ]


async def update_zone(db: AsyncSession, zone_id: UUID, data: LogisticsZoneUpdate) -> LogisticsZoneItem:
    zone = await _get_zone(db, zone_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(zone, key, value)
    db.add(zone)
    await db.flush()
    return LogisticsZoneItem(id=zone.id, hub_id=zone.warehouse_id, name=zone.name, type=zone.zone_type, radius=zone.radius_km, status=zone.status, color=zone.color_token, lat=zone.lat, lng=zone.lng)


async def delete_zone(db: AsyncSession, zone_id: UUID) -> MessageResponse:
    zone = await _get_zone(db, zone_id)
    await db.delete(zone)
    await db.flush()
    return MessageResponse(message="Zone deleted")


def _task_to_item(task: LogisticsTask) -> LogisticsTaskItem:
    return LogisticsTaskItem(
        id=task.id,
        text=task.text,
        status=task.status,
        target_time=task.target_time,
        repeat=task.repeat_rule,
        created_at=task.created_at,
        last_alert_time=task.last_alert_time,
        silenced=task.silenced,
    )


async def list_tasks(db: AsyncSession) -> list[LogisticsTaskItem]:
    tasks = (await db.execute(select(LogisticsTask).order_by(LogisticsTask.created_at.desc()))).scalars().all()
    return [_task_to_item(t) for t in tasks]


async def create_task(db: AsyncSession, data: LogisticsTaskCreate) -> LogisticsTaskItem:
    task = LogisticsTask(
        text=data.text,
        status=data.status,
        target_time=data.target_time,
        repeat_rule=data.repeat or "none",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_to_item(task)


async def delete_task(db: AsyncSession, task_id: UUID) -> MessageResponse:
    task = (await db.execute(select(LogisticsTask).where(LogisticsTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
    return MessageResponse(message="Task deleted")


async def update_task(db: AsyncSession, task_id: UUID, data: LogisticsTaskUpdate) -> LogisticsTaskItem:
    task = (await db.execute(select(LogisticsTask).where(LogisticsTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updates = data.model_dump(exclude_unset=True)
    if "repeat" in updates:
        task.repeat_rule = updates.pop("repeat")
    for key, value in updates.items():
        setattr(task, key, value)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_to_item(task)


def _manifest_to_item(m: LogisticsManifest) -> LogisticsManifestItem:
    from app.schemas.logistics import ManifestCrewMember
    crew = [ManifestCrewMember(**c) for c in (m.crew_list or [])]
    return LogisticsManifestItem(
        id=m.id,
        route_id=m.route_id,
        driver_name=m.driver_name,
        driver_id=m.driver_id,
        vehicle_code=m.vehicle_code,
        hub_name=m.hub_name,
        crew_config=m.crew_config,
        status=m.status,
        orders_count=m.orders_count,
        total_weight=m.total_weight,
        total_distance=m.total_distance,
        stop_count=m.stop_count,
        total_volume=m.total_volume,
        est_duration=m.est_duration,
        fragile_count=m.fragile_count,
        cod_count=m.cod_count,
        crew_list=crew,
        pushed=m.pushed,
        pushed_at=m.pushed_at,
        created_at=m.created_at,
    )


async def list_manifests(db: AsyncSession) -> list[LogisticsManifestItem]:
    result = await db.execute(
        select(LogisticsManifest).order_by(LogisticsManifest.created_at.desc()).limit(100)
    )
    return [_manifest_to_item(m) for m in result.scalars().all()]


async def create_manifest(db: AsyncSession, data: LogisticsManifestCreate, created_by_id: UUID | None = None) -> LogisticsManifestItem:
    crew_list = [c.model_dump() for c in data.crew_list] if data.crew_list else []
    manifest = LogisticsManifest(
        route_id=data.route_id,
        driver_name=data.driver_name,
        driver_id=data.driver_id,
        vehicle_code=data.vehicle_code,
        hub_name=data.hub_name,
        crew_config=data.crew_config,
        status="Draft",
        orders_count=data.orders_count,
        total_weight=data.total_weight,
        total_distance=data.total_distance,
        stop_count=data.stop_count,
        total_volume=data.total_volume,
        est_duration=data.est_duration,
        fragile_count=data.fragile_count,
        cod_count=data.cod_count,
        crew_list=crew_list,
        pushed=False,
        created_by_id=created_by_id,
    )
    db.add(manifest)
    await db.flush()
    return _manifest_to_item(manifest)


async def push_manifest(db: AsyncSession, manifest_id: UUID) -> LogisticsManifestItem:
    manifest = (await db.execute(select(LogisticsManifest).where(LogisticsManifest.id == manifest_id))).scalar_one_or_none()
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    manifest.pushed = True
    manifest.pushed_at = _now()
    manifest.status = "Dispatched"
    db.add(manifest)
    await db.flush()
    return _manifest_to_item(manifest)


async def create_document(db: AsyncSession, data: LogisticsDocumentCreate) -> LogisticsDocumentItem:
    doc = LogisticsDocument(
        entity_type=data.entity_type.upper(),
        entity_id=data.entity_id,
        hub_id=data.hub_id,
        doc_type=data.doc_type,
        document_url=data.document_url,
        expiry_date=data.expiry_date,
        status="Pending Verification"
    )
    db.add(doc)
    await db.flush()
    return doc


async def update_document_status(db: AsyncSession, doc_id: UUID, data: LogisticsDocumentUpdateStatus) -> LogisticsDocumentItem:
    doc = (await db.execute(select(LogisticsDocument).where(LogisticsDocument.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = data.status
    if data.notes is not None:
        doc.notes = data.notes

    db.add(doc)
    await db.flush()
    return doc
