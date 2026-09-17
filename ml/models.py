"""Phase 22 - ML models."""
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM


class IsolationForestModel:
    name = "isolation_forest"

    def __init__(self, n_estimators=100, contamination=0.05, random_state=42):
        self.model = None
        self.hyperparams = {"n_estimators": n_estimators,
                            "contamination": contamination,
                            "random_state": random_state}
        self.metrics = None

    def fit(self, X):
        self.model = IsolationForest(**self.hyperparams)
        self.model.fit(X)
        return {"trained_samples": len(X)}

    def decision_function(self, X):
        return self.model.decision_function(X)

    def predict(self, X):
        return self.model.predict(X)

    def is_trained(self):
        return self.model is not None


class OneClassSVMModel:
    name = "one_class_svm"

    def __init__(self, nu=0.05, kernel="rbf", gamma="scale"):
        self.model = None
        self.hyperparams = {"nu": nu, "kernel": kernel, "gamma": gamma}
        self.metrics = None

    def fit(self, X):
        self.model = OneClassSVM(**self.hyperparams)
        self.model.fit(X)
        return {"trained_samples": len(X)}

    def decision_function(self, X):
        return self.model.decision_function(X)

    def predict(self, X):
        return self.model.predict(X)

    def is_trained(self):
        return self.model is not None


MODEL_CLASSES = {"isolation_forest": IsolationForestModel,
                 "one_class_svm": OneClassSVMModel}
