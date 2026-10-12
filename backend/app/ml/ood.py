"""
Training-domain coverage check. Not a statistical novelty-detection
model (that would need its own validation) — this is the honest,
simple version: for each numeric feature, is the input inside the
1st-99th percentile range actually observed in training? For each
categorical feature, was this exact category ever seen?

Deliberately conservative in its claims: this tells you whether an
input resembles training data on a per-feature basis, not whether the
model's prediction is "safe" in some deeper sense. A row can pass every
per-feature check and still sit in a combination of values the model
never saw jointly — mention that limitation wherever this is surfaced
to a researcher, not just here.
"""
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def load_coverage() -> dict | None:
    path = Path(settings.MODEL_DIR) / "feature_coverage.json"
    if not path.exists():
        return None
    import json
    with open(path) as f:
        return json.load(f)


def check_coverage(formulation: dict, soil: dict, environment: dict) -> dict:
    """Returns per-feature status plus an overall risk label.

    Status per numeric feature: "in_range" | "borderline" | "out_of_range"
      - in_range: within the observed 1st-99th percentile band
      - borderline: outside that band but within the absolute min/max seen
      - out_of_range: outside anything the model was ever trained on

    Status per categorical feature: "seen" | "unseen"
    """
    coverage = load_coverage()
    if coverage is None:
        return {
            "available": False,
            "overall_risk": "UNKNOWN",
            "features": {},
            "note": "No training coverage recorded yet — retrain to enable this check.",
        }

    row = {**formulation, **soil, **environment}
    features = {}
    risk_scores = []  # 0 = in_range/seen, 1 = borderline, 2 = out_of_range/unseen

    for col, bounds in coverage["numeric"].items():
        if col not in row:
            continue
        val = row[col]
        if bounds["p01"] <= val <= bounds["p99"]:
            status, score = "in_range", 0
        elif bounds["min"] <= val <= bounds["max"]:
            status, score = "borderline", 1
        else:
            status, score = "out_of_range", 2
        features[col] = {
            "value": val,
            "status": status,
            "training_range": [bounds["min"], bounds["max"]],
        }
        risk_scores.append(score)

    for col, seen_categories in coverage["categorical"].items():
        if col not in row:
            continue
        val = row[col]
        status = "seen" if val in seen_categories else "unseen"
        features[col] = {
            "value": val,
            "status": status,
            "training_categories": seen_categories,
        }
        risk_scores.append(0 if status == "seen" else 2)

    if not risk_scores:
        overall = "UNKNOWN"
    elif max(risk_scores) == 2 or risk_scores.count(1) >= 3:
        overall = "HIGH"
    elif 1 in risk_scores:
        overall = "MODERATE"
    else:
        overall = "LOW"

    return {
        "available": True,
        "overall_risk": overall,
        "features": features,
        "n_training_rows": coverage.get("n_training_rows"),
        "note": (
            "Per-feature coverage only — a combination of individually "
            "in-range values can still fall outside the region the model "
            "was actually trained on."
        ),
    }