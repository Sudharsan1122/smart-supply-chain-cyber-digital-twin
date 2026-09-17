"""Phase 5 - Payload normalization."""
from typing import Any
from api.schemas.telemetry import TelemetryPayload


METRIC_MAP = {
    "speed": ("speed", "km/h"),
    "fuel": ("fuel", "pct"),
    "battery": ("battery", "pct"),
    "temperature": ("temperature", "celsius"),
    "humidity": ("humidity", "pct"),
    "occupancy": ("occupancy", "count"),
    "power_consumption": ("power_consumption", "kW"),
    "auth_events": ("auth_events", "count"),
    "failed_logins": ("failed_logins", "count"),
    "api_calls": ("api_calls", "count"),
    "unusual_api_calls": ("unusual_api_calls", "count"),
}


def to_metric_rows(payload: TelemetryPayload) -> list[dict[str, Any]]:
    rows = []
    for field, (metric, unit) in METRIC_MAP.items():
        value = getattr(payload, field, None)
        if value is None:
            continue
        rows.append({"metric": metric, "value": float(value), "unit": unit})
    if payload.gps is not None:
        rows.append({
            "metric": "position", "value": None, "unit": "latlon",
            "payload": {"lat": payload.gps.latitude, "lon": payload.gps.longitude},
        })
    if payload.door_status:
        rows.append({
            "metric": "door_status", "value": None, "unit": "state",
            "payload": {"status": payload.door_status},
        })
    return rows


def derive_twin_state(payload: TelemetryPayload) -> dict[str, Any]:
    state = _infer_state(payload)
    health = _infer_health(payload)
    position = {}
    if payload.gps is not None:
        position = {"lat": payload.gps.latitude, "lon": payload.gps.longitude}
    metrics = {}
    for field, (metric, _unit) in METRIC_MAP.items():
        v = getattr(payload, field, None)
        if v is not None:
            metrics[metric] = float(v)
    if payload.status:
        metrics["status"] = payload.status
    if payload.firmware:
        metrics["firmware"] = payload.firmware
    return {"state": state, "health": health, "position": position, "metrics": metrics}


def _infer_state(p: TelemetryPayload) -> str:
    if p.status:
        return p.status.lower()
    if p.speed is not None:
        return "moving" if p.speed > 1.0 else "idle"
    if p.door_status:
        return p.door_status.lower()
    return "unknown"


def _infer_health(p: TelemetryPayload) -> str:
    if p.battery is not None and p.battery < 15:
        return "degraded"
    if p.temperature is not None and (p.temperature < -20 or p.temperature > 60):
        return "critical"
    if p.failed_logins and p.failed_logins >= 5:
        return "at_risk"
    return "good"
