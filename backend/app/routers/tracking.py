"""
Real-time location tracking endpoint for dispatchers/customers
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.logistics import LogisticsDriverProfile, LogisticsVehicle
from app.models.user import User


class DriverLocationItem(BaseModel):
    driver_id: str
    driver_name: str
    latitude: float | None
    longitude: float | None
    vehicle_id: str | None
    vehicle_code: str | None
    status: str
    last_updated: str | None


router = APIRouter(prefix="/api/v1/tracking", tags=["Live Tracking"])


@router.get("/drivers", response_model=list[DriverLocationItem])
async def get_active_driver_locations(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Get real-time locations of all active drivers.
    Used by dispatchers/warehouse managers for live map view.
    """
    # Include all non-off-duty driver statuses used across the app.
    # `start_shift` sets status to "Active", while some seeded/test data uses
    # "On-Duty" and "In-Transit".
    active_statuses = ["active", "on-duty", "in-transit"]

    # Fetch all active drivers with latest known location
    query = (
        select(LogisticsDriverProfile, User, LogisticsVehicle)
        .join(User, LogisticsDriverProfile.user_id == User.id)
        .outerjoin(LogisticsVehicle, LogisticsDriverProfile.user_id == LogisticsVehicle.assigned_driver_id)
        .where(func.lower(LogisticsDriverProfile.status).in_(active_statuses))
        .order_by(
            LogisticsDriverProfile.updated_at.desc(),
            LogisticsVehicle.updated_at.desc().nullslast(),
        )
    )

    result = await db.execute(query)
    rows = result.all()

    locations = []
    seen_driver_ids = set()
    for profile, driver_user, vehicle in rows:
        if driver_user.id in seen_driver_ids:
            continue
        seen_driver_ids.add(driver_user.id)

        lat, lng = None, None
        if profile.current_location and ',' in profile.current_location:
            try:
                lat_str, lng_str = profile.current_location.split(',')
                lat = float(lat_str.strip())
                lng = float(lng_str.strip())
            except (ValueError, AttributeError):
                pass

        locations.append(DriverLocationItem(
            driver_id=str(driver_user.id),
            driver_name=driver_user.name,
            latitude=lat,
            longitude=lng,
            vehicle_id=str(vehicle.id) if vehicle else None,
            vehicle_code=vehicle.code if vehicle else None,
            status=profile.status,
            last_updated=profile.updated_at.isoformat() if profile.updated_at else None
        ))

    return locations


@router.get("/orders/{order_id}/driver", response_model=DriverLocationItem | None)
async def get_order_driver_location(
    order_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Get real-time location of the driver assigned to a specific order.
    Used by customers to track their delivery.
    """
    from uuid import UUID

    from app.models.order import Order

    # Get order
    order = await db.get(Order, UUID(order_id))
    if not order or not order.assigned_driver_id:
        return None

    # Get driver profile
    query = (
        select(LogisticsDriverProfile, User, LogisticsVehicle)
        .join(User, LogisticsDriverProfile.user_id == User.id)
        .outerjoin(LogisticsVehicle, LogisticsDriverProfile.user_id == LogisticsVehicle.assigned_driver_id)
        .where(LogisticsDriverProfile.user_id == order.assigned_driver_id)
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        return None

    profile, driver_user, vehicle = row

    lat, lng = None, None
    if profile.current_location and ',' in profile.current_location:
        try:
            lat_str, lng_str = profile.current_location.split(',')
            lat = float(lat_str.strip())
            lng = float(lng_str.strip())
        except (ValueError, AttributeError):
            pass

    return DriverLocationItem(
        driver_id=str(driver_user.id),
        driver_name=driver_user.name,
        latitude=lat,
        longitude=lng,
        vehicle_id=str(vehicle.id) if vehicle else None,
        vehicle_code=vehicle.code if vehicle else None,
        status=profile.status,
        last_updated=profile.updated_at.isoformat() if profile.updated_at else None
    )
