"""Route aggregator."""
from fastapi import APIRouter

from api.routes.assets import router as assets_router
from api.routes.attack import router as attack_router
from api.routes.attack_stories import router as attack_stories_router
from api.routes.blast_radius import router as blast_radius_router
from api.routes.detections import router as detections_router
from api.routes.events import router as events_router
from api.routes.health import router as health_router
from api.routes.iocs import router as iocs_router
from api.routes.mqtt import router as mqtt_router
from api.routes.risk import router as risk_router
from api.routes.sources import router as sources_router
from api.routes.telemetry import router as telemetry_router
from api.routes.threat_intel import router as threat_intel_router
from api.routes.triage import router as triage_router
from api.routes.twin import router as twin_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(twin_router)
api_router.include_router(telemetry_router)
api_router.include_router(events_router)
api_router.include_router(assets_router)
api_router.include_router(mqtt_router)
api_router.include_router(detections_router)
api_router.include_router(risk_router)
api_router.include_router(iocs_router)
api_router.include_router(threat_intel_router)
api_router.include_router(triage_router)
api_router.include_router(blast_radius_router)
api_router.include_router(attack_router)
api_router.include_router(attack_stories_router)
api_router.include_router(sources_router)
