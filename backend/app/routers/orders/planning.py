"""Order planning: assignment previews, driver and return-trip suggestions, clustering, route optimisation, batch assignment and trip intelligence."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.orders import (
    BatchConfirmRequest,
    ClusterResponse,
    DriverSuggestionResponse,
    OrderAssignmentPreview,
    OrderAssignRequest,
    OrderTripIntelligenceItem,
    ReturnTripResponse,
    TripCommandPushRequest,
    TripDeviationReportRequest,
)
from app.services import clustering_service, orders_service

router = APIRouter()


@router.get("/assignment-preview", response_model=OrderAssignmentPreview)
async def get_assignment_preview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    warehouse_id: UUID | None = Query(default=None),
):
    return await orders_service.get_order_assignment_preview(db, warehouse_id)


@router.get("/ai-driver-suggestions", response_model=DriverSuggestionResponse)
async def get_ai_driver_suggestions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """
    AI-powered (Gemini 2.5 Pro) driver suggestions for every unassigned CONFIRMED order.
    Ranks available drivers by proximity, workload, and order priority.
    Falls back to nearest-neighbour distance matching if Gemini is unavailable.
    """
    from app.services import dispatch_ai_service
    suggestions = await dispatch_ai_service.suggest_drivers_for_orders(db)
    return DriverSuggestionResponse(suggestions=suggestions, total=len(suggestions))


@router.get("/return-suggestions", response_model=ReturnTripResponse)
async def get_return_trip_suggestions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """
    Return-trip opportunities: drivers who recently completed a delivery and are
    within 8 km of a pending unassigned pickup.
    Gemini 2.5 Pro writes dispatch-quality explanations and re-ranks by urgency.
    """
    from app.services import dispatch_ai_service
    suggestions = await dispatch_ai_service.get_return_trip_suggestions(db)
    return ReturnTripResponse(suggestions=suggestions, total=len(suggestions))


@router.post("/cluster")
async def cluster_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
    radius_km: float = Query(default=5.0, ge=1.0, le=50.0),
):
    from sqlalchemy import select

    from app.models.order import Order
    from app.schemas.orders import ClusterOrderItem, OrderCluster

    orders = (
        await db.execute(select(Order).where(Order.status == "CONFIRMED").order_by(Order.created_at.desc()))
    ).scalars().all()

    clusters, unbatched = await clustering_service.cluster_orders(db, list(orders), radius_km=radius_km)

    def _to_item(order):
        return ClusterOrderItem(
            id=order.id, tracking_code=order.tracking_code,
            delivery_addr=order.delivery_addr, pickup_addr=order.pickup_addr,
            cargo_type=order.cargo_type, vehicle_type=order.vehicle_type,
            total_amount=order.total_amount, scheduled_at=order.scheduled_at,
            delivery_lat=order.delivery_lat, delivery_lng=order.delivery_lng,
        )

    cluster_results = []
    for c in clusters:
        cluster_results.append(OrderCluster(
            cluster_id=c.cluster_id,
            centroid_lat=c.centroid_lat, centroid_lng=c.centroid_lng,
            orders=[_to_item(g.order) for g in c.orders],
            total_distance_km=c.total_distance_km,
            efficiency_pct=c.efficiency_pct,
            total_weight=sum(g.order.total_amount for g in c.orders),
            time_window=c.time_window,
            order_count=len(c.orders),
        ))

    avg_eff = sum(c.efficiency_pct for c in clusters) / len(clusters) if clusters else 0
    total_clustered = sum(len(c.orders) for c in clusters)
    total_orders = total_clustered + len(unbatched)
    miles_saved = avg_eff * 0.35 if clusters else 0  # rough estimate

    return ClusterResponse(
        clusters=cluster_results,
        unbatched=[_to_item(o) for o in unbatched],
        total_orders=total_orders,
        estimated_miles_saved_pct=round(miles_saved, 1),
        avg_efficiency_pct=round(avg_eff, 1),
    ).model_dump(mode="json")


@router.post("/optimize-routes")
async def optimize_routes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
    optimize_for: str = "distance",
    prioritize_urgent: bool = False,
):
    return await orders_service.optimize_routes(db, optimize_for=optimize_for, prioritize_urgent=prioritize_urgent)


@router.post("/auto-balance")
async def auto_balance_drivers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """
    Auto-balance workload across drivers by redistributing ASSIGNED orders
    from overloaded drivers to underutilized ones.
    Does NOT touch IN_TRANSIT orders (already being delivered).
    """
    return await orders_service.auto_balance_drivers(db)


@router.post("/batch-assign")
async def batch_assign_orders(
    data: BatchConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):

    results = []
    for a in data.assignments:
        result = await orders_service.assign_order(
            db, a.order_id, OrderAssignRequest(driver_id=a.driver_id, vehicle_id=a.vehicle_id)
        )
        results.append(result)
    return [r.model_dump(mode="json") for r in results]


@router.get("/trip-intelligence", response_model=list[OrderTripIntelligenceItem])
async def list_trip_intelligence(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
    statuses: str = Query(default="ASSIGNED,IN_TRANSIT"),
):
    return await orders_service.list_trip_intelligence(db, statuses=statuses)


@router.get("/{order_id}/trip-intelligence", response_model=OrderTripIntelligenceItem)
async def get_trip_intelligence(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER", "DRIVER"))],
):
    return await orders_service.get_trip_intelligence(db, order_id, caller=user)


@router.post("/{order_id}/trip-intelligence/push", response_model=dict)
async def push_trip_command(
    order_id: UUID,
    data: TripCommandPushRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await orders_service.push_trip_command_update(db, order_id, data, caller=user)


@router.post("/{order_id}/trip-intelligence/deviation", response_model=dict)
async def report_trip_deviation(
    order_id: UUID,
    data: TripDeviationReportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    return await orders_service.report_trip_deviation(db, order_id, data, caller=user)
