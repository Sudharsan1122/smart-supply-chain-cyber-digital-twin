"""Analytics and timeline endpoints with dynamic window and filtering."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import models as m
from database.db import get_db
from digital_twin.graph import twin_graph

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/timeline")
async def get_timeline(
    window_minutes: int = Query(default=30, ge=5, le=120),
    severity: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return per-minute counts of telemetry, detections, iocs, triage, and top asset risk history."""
    q_timeline = text(f"""
        WITH minutes AS (
            SELECT generate_series(
                date_trunc('minute', now() - interval '{window_minutes} minutes'),
                date_trunc('minute', now()),
                interval '1 minute'
            ) AS minute
        ),
        tel AS (
            SELECT date_trunc('minute', t.timestamp) AS minute, count(*) AS cnt
            FROM telemetry t
            JOIN assets a ON t.asset_id = a.id
            WHERE t.timestamp >= now() - interval '{window_minutes} minutes'
              AND (CAST(:asset_type AS text) IS NULL OR a.asset_type = CAST(:asset_type AS text))
            GROUP BY 1
        ),
        det AS (
            SELECT date_trunc('minute', d.detected_at) AS minute, count(*) AS cnt
            FROM detections d
            JOIN assets a ON d.asset_id = a.id
            WHERE d.detected_at >= now() - interval '{window_minutes} minutes'
              AND (CAST(:severity AS text) IS NULL OR d.severity = CAST(:severity AS text))
              AND (CAST(:asset_type AS text) IS NULL OR a.asset_type = CAST(:asset_type AS text))
            GROUP BY 1
        ),
        ioc AS (
            SELECT date_trunc('minute', last_seen) AS minute, count(*) AS cnt
            FROM iocs
            WHERE last_seen >= now() - interval '{window_minutes} minutes'
            GROUP BY 1
        ),
        tri AS (
            SELECT date_trunc('minute', tr.created_at) AS minute, count(*) AS cnt
            FROM triage tr
            JOIN detections d ON tr.detection_id = d.id
            JOIN assets a ON d.asset_id = a.id
            WHERE tr.created_at >= now() - interval '{window_minutes} minutes'
              AND (CAST(:severity AS text) IS NULL OR d.severity = CAST(:severity AS text))
              AND (CAST(:asset_type AS text) IS NULL OR a.asset_type = CAST(:asset_type AS text))
            GROUP BY 1
        )
        SELECT 
            to_char(m.minute, 'HH24:MI') as bucket,
            COALESCE(tel.cnt, 0) as telemetry,
            COALESCE(det.cnt, 0) as detections,
            COALESCE(ioc.cnt, 0) as iocs,
            COALESCE(tri.cnt, 0) as triage
        FROM minutes m
        LEFT JOIN tel ON m.minute = tel.minute
        LEFT JOIN det ON m.minute = det.minute
        LEFT JOIN ioc ON m.minute = ioc.minute
        LEFT JOIN tri ON m.minute = tri.minute
        ORDER BY m.minute;
    """)

    params: dict[str, Any] = {
        "severity": severity.lower() if severity else None,
        "asset_type": asset_type.upper() if asset_type else None,
    }

    timeline_rows = (await session.execute(q_timeline, params)).mappings().all()
    timestamps = [r["bucket"] for r in timeline_rows]
    telemetry_counts = [int(r["telemetry"]) for r in timeline_rows]
    detections_counts = [int(r["detections"]) for r in timeline_rows]
    iocs_counts = [int(r["iocs"]) for r in timeline_rows]
    triage_counts = [int(r["triage"]) for r in timeline_rows]

    # Query top 5 assets by latest risk score, filtered by asset_type if requested
    q_top_assets = text("""
        SELECT a.asset_id
        FROM (
            SELECT DISTINCT ON (asset_id) asset_id, score, scored_at
            FROM risk_scores
            ORDER BY asset_id, scored_at DESC
        ) latest
        JOIN assets a ON latest.asset_id = a.id
        WHERE (CAST(:asset_type AS text) IS NULL OR a.asset_type = CAST(:asset_type AS text))
        ORDER BY latest.score DESC
        LIMIT 5;
    """)
    top_assets = [r[0] for r in (await session.execute(q_top_assets, {"asset_type": params["asset_type"]})).all()]

    risk_series: dict[str, list[float]] = {asset: [0.0] * len(timestamps) for asset in top_assets}

    if top_assets:
        q_risk_hist = text(f"""
            SELECT a.asset_id, to_char(date_trunc('minute', r.scored_at), 'HH24:MI') as bucket, round(avg(r.score)::numeric, 2) as avg_score
            FROM risk_scores r
            JOIN assets a ON r.asset_id = a.id
            WHERE a.asset_id = ANY(:assets) AND r.scored_at >= now() - interval '{window_minutes} minutes'
            GROUP BY a.asset_id, date_trunc('minute', r.scored_at)
            ORDER BY date_trunc('minute', r.scored_at);
        """)
        hist_rows = (await session.execute(q_risk_hist, {"assets": top_assets})).mappings().all()

        bucket_idx = {b: idx for idx, b in enumerate(timestamps)}
        last_known: dict[str, float] = {asset: 0.0 for asset in top_assets}

        for h in hist_rows:
            asset = h["asset_id"]
            bucket = h["bucket"]
            if bucket in bucket_idx and asset in risk_series:
                idx = bucket_idx[bucket]
                val = float(h["avg_score"])
                risk_series[asset][idx] = val
                last_known[asset] = val

        for asset in top_assets:
            curr = 0.0
            for idx in range(len(timestamps)):
                if risk_series[asset][idx] > 0.0:
                    curr = risk_series[asset][idx]
                elif curr > 0.0:
                    risk_series[asset][idx] = curr

    return {
        "window_minutes": window_minutes,
        "severity": severity,
        "asset_type": asset_type,
        "timestamps": timestamps,
        "telemetry": telemetry_counts,
        "detections": detections_counts,
        "iocs": iocs_counts,
        "triage": triage_counts,
        "risk_history": {
            "assets": top_assets,
            "series": risk_series,
        },
    }


@router.get("/playback")
async def playback(
    from_minutes_ago: int = Query(default=30, ge=1, le=120),
    interval_seconds: int = Query(default=60, ge=1, le=3600),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return time-series of bucketed truck positions, detections, and events for playback."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=from_minutes_ago)

    # 1. Get all position telemetry in window
    stmt = (
        select(m.Telemetry)
        .where(m.Telemetry.metric == "position")
        .where(m.Telemetry.timestamp >= cutoff)
        .order_by(m.Telemetry.timestamp.asc())
    )
    positions = (await session.execute(stmt)).scalars().all()

    raw_by_truck: dict[str, list[tuple[datetime, float, float]]] = {}
    all_ts: list[datetime] = []

    for p in positions:
        asset_code = twin_graph.asset_id_for(p.asset_id)
        if not asset_code or not asset_code.startswith("TRUCK-"):
            continue
        payload = p.payload or {}
        if "lat" not in payload or "lon" not in payload:
            continue
        lat = float(payload["lat"])
        lon = float(payload["lon"])
        # Filter out non-India coordinates
        if not (6.0 <= lat <= 37.0 and 68.0 <= lon <= 98.0):
            continue
        raw_by_truck.setdefault(asset_code, []).append((p.timestamp, lat, lon))
        all_ts.append(p.timestamp)

    timestamps: list[str] = []
    trucks: dict[str, list[dict[str, Any]]] = {}

    if all_ts:
        t_min = min(all_ts)
        t_max = max(all_ts)
        span_sec = max(1.0, (t_max - t_min).total_seconds())
        # Adaptive bucket step: target up to ~90 frames, respecting interval_seconds upper bound
        step_sec = max(2, min(interval_seconds, max(2, int(span_sec / 90))))

        bucket_map: dict[int, datetime] = {}
        truck_bucket_pos: dict[str, dict[int, tuple[float, float]]] = {
            k: {} for k in raw_by_truck
        }

        for asset_code, pts in raw_by_truck.items():
            for ts, lat, lon in pts:
                b_key = int(ts.timestamp()) // step_sec
                bucket_map[b_key] = ts
                truck_bucket_pos[asset_code][b_key] = (lat, lon)

        sorted_keys = sorted(bucket_map.keys())
        timestamps = [bucket_map[k].isoformat() for k in sorted_keys]

        for asset_code, pts in raw_by_truck.items():
            aligned: list[dict[str, Any]] = []
            last_lat, last_lon = pts[0][1], pts[0][2]
            b_pos = truck_bucket_pos[asset_code]
            for idx, k in enumerate(sorted_keys):
                if k in b_pos:
                    last_lat, last_lon = b_pos[k]
                aligned.append({
                    "t": timestamps[idx],
                    "lat": round(last_lat, 6),
                    "lon": round(last_lon, 6),
                })
            trucks[asset_code] = aligned

    # 2. Get security events in window
    stmt_ev = (
        select(m.SecurityEvent)
        .where(m.SecurityEvent.timestamp >= cutoff)
        .order_by(m.SecurityEvent.timestamp.asc())
    )
    events_raw = (await session.execute(stmt_ev)).scalars().all()
    events: list[dict[str, Any]] = []
    for e in events_raw:
        asset_code = twin_graph.asset_id_for(e.asset_id)
        parents = twin_graph.direct_parents(asset_code) if asset_code else []
        parent_truck = next((p for p in parents if p.startswith("TRUCK-")), None)
        events.append({
            "t": e.timestamp.isoformat(),
            "kind": "event",
            "asset": asset_code,
            "parent_asset": parent_truck,
            "severity": e.severity,
            "title": f"{e.event_type} ({e.severity})",
        })

    # 3. Get detections in window
    stmt_det = (
        select(m.Detection)
        .where(m.Detection.detected_at >= cutoff)
        .order_by(m.Detection.detected_at.asc())
    )
    dets_raw = (await session.execute(stmt_det)).scalars().all()
    for d in dets_raw:
        asset_code = twin_graph.asset_id_for(d.asset_id)
        parents = twin_graph.direct_parents(asset_code) if asset_code else []
        parent_truck = next((p for p in parents if p.startswith("TRUCK-")), None)
        events.append({
            "t": d.detected_at.isoformat(),
            "kind": "detection",
            "asset": asset_code,
            "parent_asset": parent_truck,
            "severity": d.severity,
            "title": f"{d.rule_id}: {d.description}",
        })

    # 4. Get high risk jumps in window
    stmt_risk = (
        select(m.RiskScore)
        .where(m.RiskScore.scored_at >= cutoff)
        .where(m.RiskScore.score >= 50.0)
        .order_by(m.RiskScore.scored_at.asc())
        .limit(200)
    )
    risks_raw = (await session.execute(stmt_risk)).scalars().all()
    seen_risk_buckets: set[tuple[str, int]] = set()
    for r in risks_raw:
        asset_code = twin_graph.asset_id_for(r.asset_id)
        if not asset_code:
            continue
        b_min = int(r.scored_at.timestamp()) // 60
        if (asset_code, b_min) in seen_risk_buckets:
            continue
        seen_risk_buckets.add((asset_code, b_min))
        parents = twin_graph.direct_parents(asset_code)
        parent_truck = next((p for p in parents if p.startswith("TRUCK-")), None)
        events.append({
            "t": r.scored_at.isoformat(),
            "kind": "risk_jump",
            "asset": asset_code,
            "parent_asset": parent_truck,
            "score": round(float(r.score), 1),
            "title": f"Risk score {round(float(r.score), 1)} on {asset_code}",
        })

    events.sort(key=lambda x: x["t"])

    return {
        "window_from": cutoff.isoformat(),
        "window_to": now.isoformat(),
        "timestamps": timestamps,
        "trucks": trucks,
        "events": events,
    }
