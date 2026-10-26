"""AI endpoints under /api/v1/ai: the customer chatbot, the support desk and the knowledge base.

FastAPI matches routes in registration order, so the sub-routers are included in the order the
endpoints were declared when they lived in one module.
"""

from fastapi import APIRouter

from app.routers.ai import (
    chat,
    contact,
    estimator,
    knowledge,
    support_cases,
    support_overview,
    support_sessions,
    tickets,
)

PREFIX = "/api/v1/ai"

router = APIRouter(tags=["AI"])
router.include_router(estimator.router, prefix=PREFIX)
router.include_router(chat.router, prefix=PREFIX)
router.include_router(contact.router, prefix=PREFIX)
router.include_router(support_overview.router, prefix=PREFIX)
router.include_router(support_sessions.router, prefix=PREFIX)
router.include_router(tickets.router, prefix=PREFIX)
router.include_router(support_cases.router, prefix=PREFIX)
router.include_router(knowledge.router, prefix=PREFIX)
