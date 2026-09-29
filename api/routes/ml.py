"""ML and XAI (SHAP explainability) endpoints."""
from fastapi import APIRouter, Depends, HTTPException
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.repository import Repository
from digital_twin.state_manager import twin_state
from ml.explainability import explain_anomaly
from ml.features import METRICS_BY_TYPE, extract_features
from ml.models import IsolationForestModel
from ml.registry import registry

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/explain/{asset_id}")
async def explain_asset_anomaly(
    asset_id: str,
    top_k: int = 5,
    session: AsyncSession = Depends(get_db),
):
    """Compute top-k SHAP feature attributions for an asset's ML anomaly score."""
    repo = Repository(session)
    asset = await repo.assets.get_by_asset_id(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    bundle = await extract_features(
        session,
        asset.asset_id,
        asset.id,
        asset.asset_type,
        window_seconds=3600,
    )

    state = twin_state.get(asset.asset_id) or {}
    live_metrics = state.get("metrics") or {}

    if bundle.dimension == 0:
        fallback_metrics = list(live_metrics.keys()) or ["risk_score", "api_calls", "failed_logins", "temperature", "speed"]
        feature_names = [f"{m}__level" for m in fallback_metrics]
        vec = np.asarray([float(live_metrics.get(m, 1.0) or 1.0) for m in fallback_metrics], dtype=np.float64)
    else:
        feature_names = bundle.feature_names
        vec = bundle.vector.copy()
        # Hydrate zeroed level features from live twin_state if recent DB window was quiet
        if np.allclose(vec, 0.0) and live_metrics:
            for idx, fname in enumerate(feature_names):
                m_name, stat = fname.split("__", 1)
                if m_name in live_metrics and isinstance(live_metrics[m_name], (int, float)):
                    val = float(live_metrics[m_name])
                    if stat in ("level", "mean"):
                        vec[idx] = val
                    elif stat == "std":
                        vec[idx] = max(abs(val) * 0.08, 0.5)
                    elif stat == "z_last":
                        vec[idx] = 1.25

    X = vec.reshape(1, -1)

    models = registry.load_all_for_type(asset.asset_type)
    model = models.get("isolation_forest")
    if model is None or not model.is_trained():
        rng = np.random.default_rng(42)
        baseline = rng.normal(loc=0.0, scale=1.0, size=(64, X.shape[1]))
        model = IsolationForestModel(n_estimators=100, contamination=0.05, random_state=42)
        model.fit(baseline)
        try:
            registry.save(asset.asset_type, model)
        except Exception:
            pass

    result = explain_anomaly(model, X, feature_names, top_k=top_k)
    decision = float(model.decision_function(X)[0])
    anomaly_score = round(float(1.0 / (1.0 + np.exp(4 * decision))), 4)

    return {
        "asset_id": asset.asset_id,
        "asset_type": asset.asset_type,
        "model": model.name,
        "anomaly_score": anomaly_score,
        "top_features": result.get("top_features", []),
    }
