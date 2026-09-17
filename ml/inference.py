"""Phase 22 - ML inference."""
import numpy as np
from dataclasses import dataclass
from ml.registry import registry


@dataclass
class AnomalyResult:
    is_anomaly: bool
    aggregate_score: float
    per_model: dict
    reason: str


def score_bundle(bundle):
    models = registry.load_all_for_type(bundle.asset_type)
    if not models or bundle.dimension == 0:
        return AnomalyResult(False, 0.0, {}, "no_models")
    X = bundle.vector.reshape(1, -1)
    per_model = {}
    scores = []
    any_flagged = False
    for name, model in models.items():
        try:
            if not model.is_trained():
                continue
            decision = float(model.decision_function(X)[0])
            label = int(model.predict(X)[0])
            score = float(1.0 / (1.0 + np.exp(4 * decision)))
            per_model[name] = {"decision": round(decision, 4),
                               "score": round(score, 4),
                               "flagged": label == -1}
            scores.append(score)
            if label == -1:
                any_flagged = True
        except Exception:
            continue
    agg = float(np.mean(scores)) if scores else 0.0
    return AnomalyResult(any_flagged, round(agg, 4), per_model,
                         "ml_anomaly" if any_flagged else "ml_normal")


def anomaly_to_detection(bundle, result, min_score=0.65):
    if not result.is_anomaly or result.aggregate_score < min_score:
        return None
    if result.aggregate_score >= 0.9:
        sev = "critical"
    elif result.aggregate_score >= 0.8:
        sev = "high"
    elif result.aggregate_score >= 0.7:
        sev = "medium"
    else:
        sev = "low"
    return {"rule_id": "ML-ANOMALY", "model_version": "ml-v1",
            "severity": sev, "confidence": result.aggregate_score,
            "description": f"ML anomaly on {bundle.asset_id} (score={result.aggregate_score:.2f})",
            "evidence": result.per_model}
