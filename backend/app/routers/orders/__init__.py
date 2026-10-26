"""Order endpoints under /api/v1/orders.

FastAPI matches routes in registration order, so the sub-routers are included in this order on purpose.
The planning routes such as /trip-intelligence must come before /{order_id} in detail.
"""

from fastapi import APIRouter

from app.routers.orders import collection, completion, delivery, detail, planning

PREFIX = "/api/v1/orders"

router = APIRouter(tags=["Orders"])
router.include_router(collection.router, prefix=PREFIX)
router.include_router(planning.router, prefix=PREFIX)
router.include_router(detail.router, prefix=PREFIX)
router.include_router(delivery.router, prefix=PREFIX)
router.include_router(completion.router, prefix=PREFIX)
