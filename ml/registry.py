"""Phase 22 - Model registry."""
import json, logging
from pathlib import Path
import joblib
from config.settings import settings
from ml.models import MODEL_CLASSES

logger = logging.getLogger(__name__)


class ModelRegistry:
    def __init__(self, artifacts_dir=None):
        self.dir = Path(artifacts_dir or settings.ml_artifacts_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}

    def _paths(self, asset_type, model_name):
        base = f"{asset_type}__{model_name}"
        return self.dir / f"{base}.joblib", self.dir / f"{base}.json"

    def save(self, asset_type, model):
        mp, meta_p = self._paths(asset_type, model.name)
        joblib.dump(model, mp)
        meta = {"asset_type": asset_type, "model_name": model.name,
                "hyperparams": model.hyperparams}
        meta_p.write_text(json.dumps(meta, indent=2))
        self._cache[(asset_type, model.name)] = model

    def load(self, asset_type, model_name):
        key = (asset_type, model_name)
        if key in self._cache:
            return self._cache[key]
        mp, _ = self._paths(asset_type, model_name)
        if not mp.exists():
            return None
        try:
            model = joblib.load(mp)
            self._cache[key] = model
            return model
        except Exception:
            return None

    def load_all_for_type(self, asset_type):
        out = {}
        for name in MODEL_CLASSES:
            m = self.load(asset_type, name)
            if m:
                out[name] = m
        return out

    def list_available(self):
        out = []
        for p in sorted(self.dir.glob("*.json")):
            try:
                out.append(json.loads(p.read_text()))
            except Exception:
                pass
        return out


registry = ModelRegistry()
