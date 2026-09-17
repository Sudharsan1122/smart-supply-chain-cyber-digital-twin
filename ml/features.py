"""Phase 22 - Feature extraction."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models as m

_BASE = ["level", "mean", "std", "range", "slope", "z_last", "delta_1", "delta_3"]

METRICS_BY_TYPE = {
    "TRUCK": ["speed", "temperature", "fuel", "battery"],
    "WAREHOUSE": ["temperature", "humidity", "occupancy", "power_consumption"],
    "SENSOR": ["temperature", "humidity"],
    "VEHICLE_GATEWAY": ["failed_logins", "api_calls", "unusual_api_calls"],
    "API_GATEWAY": ["api_calls", "unusual_api_calls"],
    "APPLICATION": ["api_calls", "unusual_api_calls"],
    "AUTH_SYSTEM": ["failed_logins", "auth_events"],
    "DATABASE": ["api_calls", "unusual_api_calls"],
    "SUPPLIER": [],
}


@dataclass
class FeatureBundle:
    asset_id: str
    asset_type: str
    feature_names: list[str]
    vector: np.ndarray
    raw_metrics: dict[str, list[float]] = field(default_factory=dict)

    @property
    def dimension(self):
        return len(self.vector)


def _series_features(values):
    if not values:
        return {k: 0.0 for k in _BASE}
    if len(values) == 1:
        v = values[0]
        return {"level": v, "mean": v, "std": 0.0, "range": 0.0,
                "slope": 0.0, "z_last": 0.0, "delta_1": 0.0, "delta_3": 0.0}
    arr = np.asarray(values, dtype=np.float64)
    mean = float(np.mean(arr))
    std = float(np.std(arr)) or 1e-6
    slope = float(np.polyfit(np.arange(len(arr)), arr, 1)[0]) if len(arr) >= 2 else 0.0
    return {
        "level": float(values[-1]), "mean": mean, "std": std,
        "range": float(np.max(arr) - np.min(arr)),
        "slope": slope,
        "z_last": float((values[-1] - mean) / std),
        "delta_1": float(values[-1] - values[-2]) if len(values) >= 2 else 0.0,
        "delta_3": float(values[-1] - values[-4]) if len(values) >= 4 else 0.0,
    }


async def extract_features(session, asset_id_code, asset_db_id, asset_type, window_seconds=60):
    metrics = METRICS_BY_TYPE.get(asset_type, [])
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
    feature_names, values_list = [], []
    raw = {}
    for metric in metrics:
        stmt = (select(m.Telemetry.value)
                .where(m.Telemetry.asset_id == asset_db_id)
                .where(m.Telemetry.metric == metric)
                .where(m.Telemetry.timestamp >= cutoff)
                .order_by(m.Telemetry.timestamp.asc()))
        vals = [float(v) for v in (await session.execute(stmt)).scalars().all() if v is not None]
        raw[metric] = vals
        sf = _series_features(vals)
        for name in _BASE:
            feature_names.append(f"{metric}__{name}")
            values_list.append(sf[name])
    vec = np.asarray(values_list, dtype=np.float64) if values_list else np.zeros(0)
    return FeatureBundle(asset_id=asset_id_code, asset_type=asset_type,
                         feature_names=feature_names, vector=vec, raw_metrics=raw)
