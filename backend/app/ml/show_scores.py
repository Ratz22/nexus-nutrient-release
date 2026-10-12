"""
Prints the model scores in plain language, with a clear statement of
whether they can be trusted.

Run (after training):
    python -m app.ml.show_scores --data data/processed/dataset.csv
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from app.core.config import get_settings
from app.ml.preprocessing import GROUP_COLUMN

NAMES = {
    "linear_regression": "Linear regression",
    "random_forest": "Random forest",
    "svr": "Support vector regression",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "catboost": "CatBoost",
    "empirical_baseline": "Simple look-up rule (baseline)",
}


def main():
    settings = get_settings()
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/dataset.csv")
    parser.add_argument("--model-dir", default=settings.MODEL_DIR)
    args = parser.parse_args()

    metrics_path = Path(args.model_dir) / "metrics.json"
    if not metrics_path.exists():
        print("No scores found. Train the model first: python -m app.ml.train")
        return
    metrics = json.loads(metrics_path.read_text())

    try:
        data = pd.read_csv(args.data)
        n_rows = len(data)
        n_papers = data[GROUP_COLUMN].nunique() if GROUP_COLUMN in data.columns else 0
    except FileNotFoundError:
        n_rows, n_papers = 0, 0

    grouped = n_papers >= 5

    rows = []
    for key, m in metrics.items():
        rows.append({
            "Method": NAMES.get(key, key),
            "R2 (higher is better)": round(m["r2"], 3),
            "R2 spread across folds": round(m.get("r2_std", 0.0), 3),
            "MAE (lower is better)": round(m["mae"], 4),
            "RMSE (lower is better)": round(m["rmse"], 4),
        })
    table = pd.DataFrame(rows).sort_values("R2 (higher is better)", ascending=False)

    models_only = table[table["Method"] != NAMES["empirical_baseline"]]
    best = models_only.iloc[0]
    baseline_row = table[table["Method"] == NAMES["empirical_baseline"]]
    baseline_r2 = float(baseline_row["R2 (higher is better)"].iloc[0]) if not baseline_row.empty else None

    print("=" * 72)
    print("NEXUS MODEL SCORES")
    print("=" * 72)
    print(f"Dataset rows:      {n_rows}")
    print(f"Source papers:     {n_papers}")
    if grouped:
        print("Validation:        grouped by paper (no paper appears in both training and testing)")
    else:
        print("Validation:        NOT grouped by paper (random splits)")
    print()
    print(table.to_string(index=False))
    print()
    print(f"Best method: {best['Method']} (R2 = {best['R2 (higher is better)']})")
    if baseline_r2 is not None:
        gap = best["R2 (higher is better)"] - baseline_r2
        print(f"Gain over the simple look-up rule: {gap:+.3f} R2")
    print()
    print("HOW TO READ THIS")
    print("  R2 = share of the variation in release speed the method explains on unseen data.")
    print("  MAE and RMSE = typical size of the error, in the release constant (per day).")
    print()
    print("STATUS")
    if n_papers == 0:
        print("  NOT PUBLISHABLE. No paper identifiers were found, so the scores cannot be")
        print("  checked for leakage. Use real literature data with paper_id.")
    elif not grouped:
        print("  NOT PUBLISHABLE. Fewer than 5 papers, so grouped validation is not reliable.")
    elif n_papers < 10:
        print("  PRELIMINARY. Grouped validation is in place, but more papers are needed.")
    else:
        print("  CANDIDATE RESULT. Needs supervisor review before any claim is made.")
    print()
    print("Reminder: if the training data is synthetic (the default for this prototype),")
    print("these scores show that the workflow works. They are NOT scientific findings.")
    print("=" * 72)


if __name__ == "__main__":
    main()