"""SHAP-based explainability for ML anomaly detections."""
from typing import Any
import numpy as np

try:
    import shap
except ImportError:  # pragma: no cover
    shap = None


def explain_anomaly(
    model,
    X: np.ndarray,
    feature_names: list[str],
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Compute SHAP values for a single sample.

    Returns top_k contributing features with their SHAP values.
    """
    try:
        X_arr = np.asarray(X, dtype=np.float64)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        if shap is not None:
            explainer = shap.KernelExplainer(
                lambda x: -model.decision_function(x),
                np.zeros((1, X_arr.shape[1])),
            )
            shap_values = explainer.shap_values(X_arr, nsamples=100, silent=True)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            sv = np.asarray(shap_values, dtype=np.float64).reshape(-1)
        else:
            # Finite-difference marginal contribution on anomaly direction (-decision_function)
            base_pred = float(-model.decision_function(np.zeros((1, X_arr.shape[1])))[0])
            sv = np.zeros(X_arr.shape[1], dtype=np.float64)
            for j in range(X_arr.shape[1]):
                pert = np.zeros((1, X_arr.shape[1]), dtype=np.float64)
                pert[0, j] = X_arr[0, j]
                sv[j] = float(-model.decision_function(pert)[0]) - base_pred
            if len(sv) > 1:
                sv = sv - float(np.median(sv))

        # Sort by absolute contribution
        indices = np.argsort(np.abs(sv))[-top_k:][::-1]
        return {
            "top_features": [
                {
                    "name": feature_names[i],
                    "value": round(float(X_arr[0][i]), 4),
                    "shap_value": round(float(sv[i]), 6),
                    "impact": "increases" if sv[i] > 0 else "decreases",
                }
                for i in indices
            ]
        }
    except Exception as e:
        return {"error": str(e), "top_features": []}
