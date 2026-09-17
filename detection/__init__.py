"""Detection package."""
from detection.engine import run_detection
from detection.risk import score_asset, score_all_assets
__all__ = ["run_detection", "score_asset", "score_all_assets"]
