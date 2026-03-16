from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, ro_engine, Base
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers import auth as auth_router
from app.routers import ai as ai_router
from app.routers import inventory as inventory_router
from app.routers import labourers as labourers_router
from app.routers import orders as orders_router
from app.routers import users as users_router
from app.routers import warehouses as warehouses_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from loguru import logger

    if not settings.gemini_api_key:
        logger.warning(
            "GEMINI_API_KEY is not set. AI chatbot endpoints will return 503."
        )
    yield
    # Shutdown: dispose async engines
    await engine.dispose()
    await ro_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Logistics & Move Management API",
        description="Backend API for the Logistics & Personal Move Management System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router.router)
    app.include_router(ai_router.router)
    app.include_router(users_router.router)
    app.include_router(warehouses_router.router)
    app.include_router(orders_router.router)
    app.include_router(inventory_router.router)
    app.include_router(labourers_router.router)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()
