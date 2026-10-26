"""Logistics endpoints under /api/v1/logistics for the logistics manager, the dispatcher and the driver app.

FastAPI matches routes in registration order, so the sub-routers are included in the order the
endpoints were declared when they lived in one module.
"""

from fastapi import APIRouter

from app.routers.logistics import drivers, manager, manifests, workspace

PREFIX = "/api/v1/logistics"

router = APIRouter(tags=["Logistics Manager"])
router.include_router(manager.router, prefix=PREFIX)
router.include_router(workspace.router, prefix=PREFIX)
router.include_router(manifests.router, prefix=PREFIX)
router.include_router(drivers.router, prefix=PREFIX)
