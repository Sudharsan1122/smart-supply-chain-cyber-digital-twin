"""Analytics and timeline endpoints with dynamic window and filtering."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db

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
