import csv
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.core.config import get_settings
from app.ml.preprocessing import FEATURE_COLUMNS, TARGET_COLUMN

router = APIRouter()
settings = get_settings()

def _csv_rows():
    path = Path(settings.DATASET_PATH)
    if not path.is_file():
        raise HTTPException(503, detail=f"Dataset not found: {path}")
    try:
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames or []
            rows = list(reader)
        return path, columns, rows
    except (OSError, csv.Error) as exc:
        raise HTTPException(500, detail=f"Dataset read failed: {exc}")

@router.get("/info")
def get_dataset_info():
    path, columns, rows = _csv_rows()
    return {
        "file": str(path),
        "n_rows": len(rows),
        "n_columns": len(columns),
        "n_features": len(FEATURE_COLUMNS),
        "n_source_papers": 0,
        "is_synthetic": True,
        "provenance": "Synthetic prototype dataset; not validated against real experimental observations."
    }

@router.get("/raw")
def get_dataset_raw():
    path = Path(settings.DATASET_PATH)
    if not path.is_file():
        raise HTTPException(503, detail=f"Dataset not found: {path}")
    return Response(path.read_bytes(), media_type="text/csv")

@router.get("/schema")
def get_schema():
    return {"features": FEATURE_COLUMNS, "target": TARGET_COLUMN}

@router.get("/models/leaderboard")
def get_leaderboard():
    path = Path(settings.MODEL_DIR) / "metrics.json"
    if not path.exists():
        raise HTTPException(status_code=503, detail="No trained models yet. Run train.py.")
    with path.open(encoding="utf-8") as f:
        return json.load(f)
