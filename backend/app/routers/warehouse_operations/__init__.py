"""Warehouse floor endpoints under /api/v1/warehouses/{warehouse_id}/operations.

FastAPI matches routes in registration order, so the sub-routers are included in the order the
endpoints were declared when they lived in one module.
"""

from fastapi import APIRouter

from app.routers.warehouse_operations import receiving, returns, stations

PREFIX = "/api/v1/warehouses/{warehouse_id}/operations"

router = APIRouter(tags=["Warehouse Operations"])
router.include_router(receiving.router, prefix=PREFIX)
router.include_router(stations.router, prefix=PREFIX)
router.include_router(returns.router, prefix=PREFIX)
