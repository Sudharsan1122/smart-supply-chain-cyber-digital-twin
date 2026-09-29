"""FastAPI application factory."""
from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI

from api.routes import api_router
from config.settings import settings
from database.db import AsyncSessionLocal, check_database_connection, dispose_engine
from digital_twin.graph import twin_graph
from digital_twin.state_manager import twin_state
from ingestion.ditto_sync import ditto_sync_loop
from ingestion.mqtt_client import mqtt_bridge

logger = logging.getLogger(__name__)


async def _background_risk_sweep():
    from detection.risk import score_all_assets
    while True:
        try:
            await asyncio.sleep(settings.risk_sweep_interval_seconds)
            async with AsyncSessionLocal() as session:
                await score_all_assets(session, persist=True)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Risk sweep error: %s", e)


async def _background_triage_sweep():
    from detection.triage import triage_pending
    while True:
        try:
            await asyncio.sleep(settings.triage_sweep_interval_seconds)
            async with AsyncSessionLocal() as session:
                results = await triage_pending(session, limit=settings.triage_batch_size)
                if results:
                    logger.info("Triage sweep: %d classified", len(results))
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Triage sweep error: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"   Environment: {settings.environment}")
    print(f"   Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print(f"   MQTT Broker: {settings.mqtt_broker_host}:{settings.mqtt_broker_port}")

    db_ok = await check_database_connection()
    if db_ok:
        print("   [OK] Database connection pool ready")
        async with AsyncSessionLocal() as session:
            await twin_graph.reload_from_db(session)
            print(f"   [OK] Twin graph loaded: {twin_graph.size} nodes")
            await twin_state.load_from_db(session)
            print(f"   [OK] Twin state loaded: {len(twin_state.all())} assets")
    else:
        print("   [!] Database unreachable - will retry on /api/ready")

    mqtt_bridge.start(asyncio.get_running_loop())
    print("   [OK] MQTT bridge starting")

    risk_task = asyncio.create_task(_background_risk_sweep())
    print(f"   [OK] Risk sweep every {settings.risk_sweep_interval_seconds}s")

    triage_task = asyncio.create_task(_background_triage_sweep())
    print(f"   [OK] Triage sweep every {settings.triage_sweep_interval_seconds}s")

    ditto_task = asyncio.create_task(ditto_sync_loop())
    print("   [OK] Ditto sync every 5s")

    yield

    print("Shutting down...")
    risk_task.cancel()
    triage_task.cancel()
    ditto_task.cancel()
    try:
        await risk_task
    except asyncio.CancelledError:
        pass
    try:
        await triage_task
    except asyncio.CancelledError:
        pass
    try:
        await ditto_task
    except asyncio.CancelledError:
        pass
    mqtt_bridge.stop()
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API-first Cyber Digital Twin for supply chain security",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
