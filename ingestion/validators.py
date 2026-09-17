"""Phase 7 - Field validation + anomaly flagging."""
from dataclasses import dataclass, field
from typing import Any
from api.schemas.telemetry import TelemetryPayload


@dataclass
class ValidationResult:
    ok: bool
    flags: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


ASSET_RANGES = {
    "TRUCK": {"speed": (0, 120), "temperature": (-25, 30), "fuel": (0, 100), "battery": (0, 100)},
    "WAREHOUSE": {"temperature": (-5, 40), "humidity": (0, 100), "occupancy": (0, 5000), "power_consumption": (0, 500)},
    "SENSOR": {"temperature": (-30, 60), "humidity": (0, 100)},
    "VEHICLE_GATEWAY": {"failed_logins": (0, 100), "api_calls": (0, 100_000)},
    "API_GATEWAY": {"api_calls": (0, 10_000_000), "unusual_api_calls": (0, 1_000_000)},
    "AUTH_SYSTEM": {"failed_logins": (0, 10_000), "auth_events": (0, 100_000)},
    "DATABASE": {"api_calls": (0, 10_000_000), "unusual_api_calls": (0, 1_000_000)},
}


def validate(payload: TelemetryPayload) -> ValidationResult:
    flags = []
    reasons = []
    meta = {}
    ranges = ASSET_RANGES.get(payload.asset_type, {})

    for field_name, (lo, hi) in ranges.items():
        v = getattr(payload, field_name, None)
        if v is None:
            continue
        if not (lo <= v <= hi):
            reasons.append(f"{field_name}={v} outside [{lo}, {hi}]")

    if reasons:
        return ValidationResult(ok=False, reasons=reasons)

    if payload.battery is not None and payload.battery < 15:
        flags.append("low_battery")
    if payload.fuel is not None and payload.fuel < 10:
        flags.append("low_fuel")
    if payload.temperature is not None:
        if payload.temperature <= -20 or payload.temperature >= 55:
            flags.append("extreme_temperature")
        elif payload.temperature >= 8 and payload.asset_type == "TRUCK":
            flags.append("cold_chain_breach")
    if payload.door_status == "OPEN":
        flags.append("door_open")
    if payload.failed_logins and payload.failed_logins >= 5:
        flags.append("failed_login_burst")
    if payload.unusual_api_calls and payload.unusual_api_calls >= 100:
        flags.append("unusual_api_burst")
    if payload.firmware and payload.firmware.startswith("v1."):
        flags.append("outdated_firmware")

    return ValidationResult(ok=True, flags=flags, metadata=meta)
