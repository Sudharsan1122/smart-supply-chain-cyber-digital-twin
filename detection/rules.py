"""Phase 10 - Rule-based detection rules."""
from dataclasses import dataclass, field
from typing import Any, Callable

from detection.context import DetectionContext


@dataclass
class DetectionCandidate:
    rule_id: str
    title: str
    severity: str
    confidence: float
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)


_REGISTRY: dict[str, Callable] = {}


def register(rule_id):
    def deco(fn):
        _REGISTRY[rule_id] = fn
        return fn
    return deco


def all_rules():
    return dict(_REGISTRY)


@register("RULE-001")
def rule_speed(ctx: DetectionContext):
    if ctx.asset_type != "TRUCK" or ctx.payload_kind != "telemetry":
        return []
    speed = getattr(ctx.payload, "speed", None)
    if speed is None:
        return []
    if speed > 100:
        return [DetectionCandidate(
            rule_id="RULE-001", title=f"Overspeed on {ctx.asset_id}",
            severity="high", confidence=0.9,
            description=f"Speed {speed:.1f} km/h exceeds 100",
            evidence={"speed": speed, "threshold": 100},
        )]
    return []


@register("RULE-002")
def rule_temperature(ctx: DetectionContext):
    if ctx.payload_kind != "telemetry":
        return []
    temp = getattr(ctx.payload, "temperature", None)
    if temp is None:
        return []
    out = []
    if ctx.asset_type == "TRUCK" and temp > 8:
        out.append(DetectionCandidate(
            rule_id="RULE-002", title=f"Cold-chain breach on {ctx.asset_id}",
            severity="critical" if temp > 15 else "high", confidence=0.9,
            description=f"Temperature {temp:.1f}C exceeds 8C",
            evidence={"temperature": temp, "limit": 8},
        ))
    elif ctx.asset_type == "WAREHOUSE" and (temp > 40 or temp < -5):
        out.append(DetectionCandidate(
            rule_id="RULE-002", title=f"Warehouse temp anomaly on {ctx.asset_id}",
            severity="high", confidence=0.85,
            description=f"Warehouse temp {temp:.1f}C outside [-5, 40]",
            evidence={"temperature": temp},
        ))
    return out


@register("RULE-003")
def rule_geofence(ctx: DetectionContext):
    if ctx.asset_type != "TRUCK" or ctx.payload_kind != "telemetry":
        return []
    gps = getattr(ctx.payload, "gps", None)
    if gps is None:
        return []
    if not (6.0 <= gps.latitude <= 37.0 and 68.0 <= gps.longitude <= 98.0):
        return [DetectionCandidate(
            rule_id="RULE-003", title=f"Geo-fence violation on {ctx.asset_id}",
            severity="critical", confidence=0.95,
            description=f"Truck outside expected region",
            evidence={"lat": gps.latitude, "lon": gps.longitude},
        )]
    return []


@register("RULE-006")
def rule_auth_burst(ctx: DetectionContext):
    out = []
    if ctx.payload_kind == "telemetry":
        fl = getattr(ctx.payload, "failed_logins", None)
        if fl is not None and fl >= 5:
            out.append(DetectionCandidate(
                rule_id="RULE-006", title=f"Auth burst on {ctx.asset_id}",
                severity="high" if fl >= 10 else "medium", confidence=0.85,
                description=f"{fl} failed logins",
                evidence={"failed_logins": fl},
            ))
    elif ctx.payload_kind == "event":
        if getattr(ctx.payload, "event_type", None) == "AUTHENTICATION_ANOMALY":
            sev = getattr(ctx.payload, "severity", "medium")
            if sev in ("high", "critical"):
                out.append(DetectionCandidate(
                    rule_id="RULE-006", title=f"Auth anomaly on {ctx.asset_id}",
                    severity=sev, confidence=0.8,
                    description=getattr(ctx.payload, "description", "") or "Auth anomaly",
                    evidence={"event_type": "AUTHENTICATION_ANOMALY"},
                ))
    return out


@register("RULE-007")
def rule_config_tamper(ctx: DetectionContext):
    if ctx.payload_kind != "telemetry":
        return []
    fw = getattr(ctx.payload, "firmware", None)
    if not fw:
        return []
    prev = (ctx.twin_current.get("metrics") or {}).get("firmware")
    if prev and prev != fw:
        return [DetectionCandidate(
            rule_id="RULE-007", title=f"Firmware change on {ctx.asset_id}",
            severity="high", confidence=0.85,
            description=f"Firmware {prev} -> {fw}",
            evidence={"previous": prev, "current": fw},
        )]
    return []


@register("RULE-008")
def rule_heartbeat(ctx: DetectionContext):
    if ctx.payload_kind != "telemetry":
        return []
    status = getattr(ctx.payload, "status", None)
    if status != "OFFLINE":
        return []
    if ctx.asset_type not in ("VEHICLE_GATEWAY", "API_GATEWAY", "AUTH_SYSTEM", "DATABASE"):
        return []
    return [DetectionCandidate(
        rule_id="RULE-008", title=f"Heartbeat loss on {ctx.asset_id}",
        severity="high", confidence=0.9,
        description=f"{ctx.asset_type} OFFLINE",
        evidence={"status": status},
    )]


@register("RULE-009")
def rule_port_scan(ctx: DetectionContext):
    if ctx.payload_kind != "telemetry":
        return []
    dests = getattr(ctx.payload, "network_destinations", None) or []
    if len(dests) >= 5:
        return [DetectionCandidate(
            rule_id="RULE-009", title=f"Port scan on {ctx.asset_id}",
            severity="high", confidence=0.75,
            description=f"{len(dests)} destinations",
            evidence={"destinations": list(dests)[:10]},
        )]
    return []
