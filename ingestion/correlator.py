"""Phase 7 - Correlation engine."""
from __future__ import annotations
import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import models as m
from digital_twin.graph import twin_graph
from ingestion.incident import IncidentCandidate, now_utc

logger = logging.getLogger(__name__)
DEFAULT_WINDOW_SECONDS = 120


async def _recent_telemetry(session, asset_db_id, window_seconds):
    cutoff = now_utc() - timedelta(seconds=window_seconds)
    stmt = (select(m.Telemetry).where(m.Telemetry.asset_id == asset_db_id)
            .where(m.Telemetry.timestamp >= cutoff)
            .order_by(m.Telemetry.timestamp.desc()))
    return list((await session.execute(stmt)).scalars().all())


async def _recent_events(session, asset_db_id, window_seconds):
    cutoff = now_utc() - timedelta(seconds=window_seconds)
    stmt = (select(m.SecurityEvent).where(m.SecurityEvent.asset_id == asset_db_id)
            .where(m.SecurityEvent.timestamp >= cutoff)
            .order_by(m.SecurityEvent.timestamp.desc()))
    return list((await session.execute(stmt)).scalars().all())


async def correlate(session: AsyncSession, asset_id: str,
                    window_seconds: int = DEFAULT_WINDOW_SECONDS) -> list[IncidentCandidate]:
    if not twin_graph.has_node(asset_id):
        return []
    db_id = twin_graph.db_id_for(asset_id)
    node = twin_graph.graph.nodes[asset_id]
    asset_type = node["asset_type"]

    tel = await _recent_telemetry(session, db_id, window_seconds)
    events = await _recent_events(session, db_id, window_seconds)

    candidates = []

    # R001 - Cold chain breach
    if asset_type == "TRUCK":
        high = [t for t in tel if t.metric == "temperature" and t.value and t.value > 8.0]
        if high:
            candidates.append(IncidentCandidate(
                rule_id="R001", title=f"Cold-chain breach on {asset_id}",
                severity="high", confidence=0.8,
                window_start=min(t.timestamp for t in high),
                window_end=max(t.timestamp for t in high),
                root_asset_id=asset_id,
                description=f"{len(high)} temp readings above 8C",
                telemetry_ids=[t.id for t in high],
            ))

    # R002 - Unauthorized warehouse entry
    if asset_type == "WAREHOUSE":
        doors = [t for t in tel if t.metric == "door_status"
                 and (t.payload or {}).get("status") == "OPEN"]
        if doors:
            high_events = [e for e in events if e.severity in ("medium", "high", "critical")]
            conf = 0.85 if high_events else 0.55
            sev = "high" if high_events else "medium"
            all_ts = [d.timestamp for d in doors] + [e.timestamp for e in high_events]
            candidates.append(IncidentCandidate(
                rule_id="R002", title=f"Unauthorized entry on {asset_id}",
                severity=sev, confidence=conf,
                window_start=min(all_ts), window_end=max(all_ts),
                root_asset_id=asset_id,
                telemetry_ids=[d.id for d in doors],
                event_ids=[e.id for e in high_events],
            ))

    # R003 - Auth failure storm
    bursts = [t for t in tel if t.metric == "failed_logins" and (t.value or 0) >= 5]
    auth_events = [e for e in events if e.event_type == "AUTHENTICATION_ANOMALY"]
    if bursts or auth_events:
        all_ts = [t.timestamp for t in bursts] + [e.timestamp for e in auth_events]
        candidates.append(IncidentCandidate(
            rule_id="R003", title=f"Auth failure storm on {asset_id}",
            severity="high" if auth_events else "medium",
            confidence=0.9 if (bursts and auth_events) else 0.7,
            window_start=min(all_ts), window_end=max(all_ts),
            root_asset_id=asset_id,
            telemetry_ids=[t.id for t in bursts],
            event_ids=[e.id for e in auth_events],
        ))

    # R006 - Gateway compromise
    if asset_type == "VEHICLE_GATEWAY":
        dev_events = [e for e in events if e.event_type in ("DEVICE_ANOMALY", "NETWORK_ANOMALY")]
        if dev_events:
            candidates.append(IncidentCandidate(
                rule_id="R006", title=f"Edge gateway compromise on {asset_id}",
                severity=max(e.severity for e in dev_events),
                confidence=0.85,
                window_start=min(e.timestamp for e in dev_events),
                window_end=max(e.timestamp for e in dev_events),
                root_asset_id=asset_id,
                telemetry_ids=[t.id for t in tel[-5:]],
                event_ids=[e.id for e in dev_events],
            ))

    return candidates
