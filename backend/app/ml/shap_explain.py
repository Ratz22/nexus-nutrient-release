from functools import lru_cache
from pathlib import Path

import joblib

from app.core.config import get_settings
from app.ml.predict import load_pipeline
from app.ml.preprocessing import flatten_request

settings = get_settings()


@lru_cache
def load_explainer():
    path = Path(settings.MODEL_DIR) / "shap_explainer.joblib"
    if not path.exists():
        raise FileNotFoundError(
            f"No SHAP explainer at {path}. Run `python -m app.ml.train` first."
        )
    return joblib.load(path)


def explain_prediction(formulation: dict, soil: dict, environment: dict) -> dict:
    pipeline = load_pipeline()
    explainer = load_explainer()
    row = flatten_request(formulation, soil, environment)
    transformed = pipeline.named_steps["preprocess"].transform(row)

    shap_values = explainer(transformed)
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    contributions = dict(zip(feature_names, shap_values.values[0].tolist()))

    top_drivers = sorted(contributions, key=lambda k: abs(contributions[k]), reverse=True)[:5]

    return {
        "model_used": pipeline.named_steps["model"].__class__.__name__,
        "base_value": float(shap_values.base_values[0]),
        "feature_contributions": contributions,
        "top_drivers": top_drivers,
    }
