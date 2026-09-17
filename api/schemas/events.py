"""Security event schemas."""
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


EventType = Literal[
    "NETWORK_ANOMALY", "DEVICE_ANOMALY", "AUTHENTICATION_ANOMALY",
    "APPLICATION_ANOMALY", "TOPOLOGY_DEVIATION", "OPERATIONAL_ANOMALY",
    "SECURITY_STATE_CHANGE", "INTRUSION_ATTEMPT", "MALWARE_DETECTED",
    "DATA_EXFILTRATION", "CONFIG_CHANGE",
]
Severity = Literal["info", "low", "medium", "high", "critical"]


class EventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(..., min_length=1, max_length=64)
    event_type: EventType
    severity: Severity = "info"
    description: str | None = None
    source: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)


class EventResponse(BaseModel):
    success: bool
    event_id: int | None = None
    asset_id: str
    event_type: str
    severity: str
    timestamp: datetime
    message: str
