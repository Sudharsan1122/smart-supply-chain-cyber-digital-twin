"""Phase 10 - Detection context."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.events import EventPayload
from api.schemas.telemetry import TelemetryPayload
from database import models as m
from digital_twin.graph import twin_graph
from digital_twin.state_manager import twin_state

HISTORY_WINDOW_SECONDS = 300


@dataclass
class DetectionContext:
    payload: Any
    payload_kind: str
    asset_id: str
    asset_type: str
    asset_db_id: int
    now: datetime
    twin_current: dict = field(default_factory=dict)
    recent_telemetry: list = field(default_factory=list)
    recent_events: list = field(default_factory=list)
    neighbors: dict = field(default_factory=dict)
    validation_flags: list = field(default_factory=list)


async def build_context(session: AsyncSession, payload, validation_flags=None) -> DetectionContext:
    kind = "telemetry" if isinstance(payload, TelemetryPayload) else "event"
    asset_id = payload.asset_id
    node = twin_graph.graph.nodes[asset_id]
    db_id = twin_graph.db_id_for(asset_id)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=HISTORY_WINDOW_SECONDS)

    stmt_t = (select(m.Telemetry).where(m.Telemetry.asset_id == db_id)
              .where(m.Telemetry.timestamp >= cutoff)
              .order_by(m.Telemetry.timestamp.desc()).limit(50))
    recent_tel = list((await session.execute(stmt_t)).scalars().all())

    stmt_e = (select(m.SecurityEvent).where(m.SecurityEvent.asset_id == db_id)
              .where(m.SecurityEvent.timestamp >= cutoff)
              .order_by(m.SecurityEvent.timestamp.desc()).limit(50))
    recent_ev = list((await session.execute(stmt_e)).scalars().all())

    return DetectionContext(
        payload=payload, payload_kind=kind, asset_id=asset_id,
        asset_type=node["asset_type"], asset_db_id=db_id, now=now,
        twin_current=twin_state.get(asset_id) or {},
        recent_telemetry=recent_tel, recent_events=recent_ev,
        neighbors={"children": twin_graph.direct_children(asset_id),
                   "parents": twin_graph.direct_parents(asset_id)},
        validation_flags=list(validation_flags or []),
    )
