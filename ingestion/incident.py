"""Phase 7 - Incident candidate."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class IncidentCandidate:
    rule_id: str
    title: str
    severity: str
    window_start: datetime
    window_end: datetime
    root_asset_id: str
    confidence: float = 0.5
    description: str | None = None
    telemetry_ids: list[int] = field(default_factory=list)
    event_ids: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
