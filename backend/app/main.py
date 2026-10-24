import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import AsyncSessionLocal, engine, ro_engine
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers import ai as ai_router
from app.routers import auth as auth_router
from app.routers import customer as customer_router
from app.routers import damage_reports as damage_reports_router
from app.routers import dev_seed as dev_seed_router
from app.routers import finance as finance_router
from app.routers import geocoding as geocoding_router
from app.routers import inventory as inventory_router
from app.routers import labourers as labourers_router
from app.routers import logistics as logistics_router
from app.routers import orders as orders_router
from app.routers import rates as rates_router
from app.routers import tracking as tracking_router
from app.routers import users as users_router
from app.routers import vendor as vendor_router
from app.routers import warehouse_operations as warehouse_operations_router
from app.routers import warehouses as warehouses_router
from app.routers import ws_fleet as ws_fleet_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from loguru import logger

    from app.services import vendor_service
    from app.services.auth_service import ensure_logistic_manager_account

    if not settings.gemini_api_key:
        logger.warning(
            "GEMINI_API_KEY is not set. AI chatbot endpoints will return 503."
        )

    async with AsyncSessionLocal() as session:
        try:
            await ensure_logistic_manager_account(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    async def recurring_runner() -> None:
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    created = await vendor_service.run_due_recurring_rules(session)
                    if created:
                        await session.commit()
                        logger.info(f"Recurring schedules generated {created} inbound vendor order(s)")
            except Exception:
                logger.exception("Recurring scheduler run failed")
            await asyncio.sleep(300)

    recurring_task = asyncio.create_task(recurring_runner())

    yield

    recurring_task.cancel()
    with suppress(asyncio.CancelledError):
        await recurring_task

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
        allow_origins=[
            "http://localhost",
            "https://localhost",
            "capacitor://localhost",
            "ionic://localhost",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://192.168.1.3:5174",
            "http://192.168.1.3:8000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            # Android Capacitor origins
            "http://192.168.1.3",
            "https://192.168.1.3",
            "http://192.168.1.3:5173",
            "capacitor://192.168.1.3",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router.router)
    app.include_router(ai_router.router)
    app.include_router(customer_router.router)
    app.include_router(damage_reports_router.router)
    app.include_router(vendor_router.router)
    app.include_router(geocoding_router.router)
    app.include_router(users_router.router)
    app.include_router(warehouses_router.router)
    app.include_router(warehouse_operations_router.router)
    app.include_router(orders_router.router)
    app.include_router(inventory_router.router)
    app.include_router(labourers_router.router)
    app.include_router(logistics_router.router)
    app.include_router(rates_router.router)
    app.include_router(tracking_router.router)
    app.include_router(finance_router.router)
    app.include_router(ws_fleet_router.router)

    # Dev seed: GPS coordinate injection for testing AI dispatch features.
    # Role-gated (LOGISTIC_MANAGER / DISPATCHER) — safe to include in all envs.
    app.include_router(dev_seed_router.router)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()
