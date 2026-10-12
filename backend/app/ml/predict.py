"""
Loads the trained pipeline once (module-level cache) and serves both a
point prediction (release constant k) and a full release curve.

Uncertainty: train.py stores residual_p90_abs — the 90th percentile of
absolute CV residuals on held-out folds. This is a split-conformal-style
interval: it's not a model's internal confidence (which is often
overconfident), it's "how wrong was this model on data it didn't train
on, historically." +/- that value around k gives a distribution-free,
90%-ish coverage interval. Simple, defensible in a paper, no extra
training cost. A tighter true conformal implementation would hold out a
dedicated calibration set instead of reusing CV residuals — worth
upgrading to if you have time on Day 4, not essential for the MVP.
"""
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from app.core.config import get_settings
from app.ml.ood import check_coverage
from app.ml.preprocessing import flatten_request

settings = get_settings()


@lru_cache
def load_pipeline():
    path = Path(settings.MODEL_DIR) / settings.ACTIVE_MODEL_NAME
    if not path.exists():
        raise FileNotFoundError(
            f"No trained model at {path}. Run `python -m app.ml.train` first."
        )
    return joblib.load(path)


@lru_cache
def load_model_meta() -> dict:
    meta_path = Path(settings.MODEL_DIR) / "active_model_meta.joblib"
    if meta_path.exists():
        return joblib.load(meta_path)
    return {"name": "unknown", "residual_p90_abs": 0.0}


def generate_release_curve(k: float, k_lower: float, k_upper: float, days: int = 30) -> list[dict]:
    """First-order release model: release% = 100 * (1 - e^(-k*t)),
    evaluated at k, k_lower, k_upper so the frontend can shade a band."""
    t = np.arange(0, days + 1)

    def curve_for(k_val):
        return 100 * (1 - np.exp(-max(k_val, 1e-6) * t))

    mid = curve_for(k)
    lower = curve_for(k_lower)
    upper = curve_for(k_upper)

    return [
        {
            "day": int(day),
            "release_pct": round(float(m), 2),
            "release_pct_lower": round(float(lo), 2),
            "release_pct_upper": round(float(hi), 2),
        }
        for day, m, lo, hi in zip(t, mid, lower, upper)
    ]


def predict_release(formulation: dict, soil: dict, environment: dict) -> dict:
    pipeline = load_pipeline()
    meta = load_model_meta()
    row = flatten_request(formulation, soil, environment)

    raw_k = float(pipeline.predict(row)[0])
    # A release rate cannot be negative. When a model extrapolates below zero the
    # input is far outside what it learned from; flag it instead of showing nonsense.
    estimate_valid = raw_k > 0
    k = max(raw_k, 1e-6)
    margin = float(meta.get("residual_p90_abs", 0.0))
    k_lower = max(k - margin, 1e-6)
    k_upper = k + margin

    curve = generate_release_curve(k, k_lower, k_upper)
    coverage = check_coverage(formulation, soil, environment)

    return {
        "model_used": meta.get("name", "unknown"),
        "release_curve": curve,
        "release_constant_k": round(k, 5),
        "raw_release_constant_k": round(raw_k, 5),
        "estimate_valid": estimate_valid,
        "release_constant_k_interval": [round(k_lower, 5), round(k_upper, 5)],
        "predicted_r2_confidence": _load_active_model_r2(meta.get("name")),
        "domain_coverage": coverage,
    }


def _load_active_model_r2(model_name: str | None) -> float:
    import json
    metrics_path = Path(settings.MODEL_DIR) / "metrics.json"
    if not metrics_path.exists() or not model_name:
        return 0.0
    with open(metrics_path) as f:
        metrics = json.load(f)
    return round(metrics.get(model_name, {}).get("r2", 0.0), 3)