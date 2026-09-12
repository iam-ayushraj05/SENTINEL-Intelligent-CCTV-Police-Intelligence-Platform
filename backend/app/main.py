# Triggering backend auto-reload for websockets support
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
from app.api.v1.router import api_router
from app.services.event_simulator import seed_demo_data, run_event_simulator_loop
from app.services.emergency_service import EmergencyService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("sentinel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Sentinel Command Center Backend...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.warning(f"Database initialization skipped or using in-memory mock: {e}")

    if settings.demo_mode:
        try:
            await seed_demo_data()
        except Exception as e:
            logger.warning(f"Demo data seeding note: {e}")

    simulator_task = None
    followup_task = asyncio.create_task(EmergencyService.run_alert_followup_worker())
    if settings.demo_mode:
        simulator_task = asyncio.create_task(run_event_simulator_loop())

    yield

    if simulator_task:
        simulator_task.cancel()
    followup_task.cancel()
    logger.info("Sentinel Command Center Backend shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-powered unified CCTV intelligence & smart policing command center platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sentinel-api", "demo_mode": settings.demo_mode}
