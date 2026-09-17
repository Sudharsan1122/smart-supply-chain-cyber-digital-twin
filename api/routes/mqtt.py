"""MQTT status endpoints."""
from fastapi import APIRouter
from ingestion.mqtt_client import mqtt_bridge

router = APIRouter(prefix="/mqtt", tags=["mqtt"])


@router.get("/status")
async def status():
    return mqtt_bridge.status()
