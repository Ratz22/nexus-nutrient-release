import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.ml.preprocessing import FEATURE_COLUMNS, TARGET_COLUMN

router = APIRouter()
settings = get_settings()


@router.get("/schema")
def get_schema():
    """So the frontend form always matches what the model was trained on —
    single source of truth, no hardcoded field lists drifting out of sync."""
    return {"features": FEATURE_COLUMNS, "target": TARGET_COLUMN}


@router.get("/models/leaderboard")
def get_leaderboard():
    """Powers the 'Model Benchmark' page — real CV metrics from train.py."""
    path = Path(settings.MODEL_DIR) / "metrics.json"
    if not path.exists():
        raise HTTPException(status_code=503, detail="No trained models yet. Run train.py.")
    with open(path) as f:
        return json.load(f)
