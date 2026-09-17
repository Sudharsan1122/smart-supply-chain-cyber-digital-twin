"""Health + readiness endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter

from config.settings import settings
from database.db import check_database_connection
from ingestion.mqtt_client import mqtt_bridge

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
    }


@router.get("/ready")
async def readiness_check():
    db_connected = await check_database_connection()
    mqtt_connected = mqtt_bridge.connected
    from digital_twin.graph import twin_graph
    twin_ready = twin_graph.size > 0

    checks = {
        "database": "connected" if db_connected else "disconnected",
        "mqtt": "connected" if mqtt_connected else "disconnected",
        "twin": "ready" if twin_ready else "empty",
    }
    return {
        "ready": db_connected and twin_ready,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
