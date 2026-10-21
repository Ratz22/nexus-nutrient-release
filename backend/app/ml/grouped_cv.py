"""Leave-one-source-out validation + calibrated prediction band.
Works with ANY sklearn-style model (XGBoost, CatBoost, Pipeline...). Does not touch your train.py.

Why: random train/test splits put points from the same paper in both sets and flatter the score.
Holding out whole papers shows how the model does on a paper it has never seen.

Example:
    from xgboost import XGBRegressor
    from sklearn.pipeline import make_pipeline
    metrics, detail = leave_source_out(
        df, features=FEATURE_COLS, target="cumulative_release_pct", group_col="source_id",
        make_model=lambda: make_pipeline(YOUR_PREPROCESSOR(), XGBRegressor(n_estimators=300)))
"""
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold


def leave_source_out(df: pd.DataFrame, features: Sequence[str], target: str, group_col: str,
                     make_model: Callable, n_splits: int = 5, coverage: float = 0.8):
    groups = df[group_col].astype(str).values
    n_splits = min(n_splits, len(set(groups)))
    if n_splits < 2:
        raise ValueError("Need at least 2 distinct sources for leave-source-out validation.")
    X, y = df[list(features)], df[target].astype(float).values
    pred = np.full(len(df), np.nan)
    for tr, te in GroupKFold(n_splits=n_splits).split(X, y, groups):
        model = make_model()
        model.fit(X.iloc[tr], y[tr])
        pred[te] = model.predict(X.iloc[te])

    resid = np.abs(y - pred)
    n = len(resid)
    q = min(1.0, np.ceil((n + 1) * coverage) / n)  # split-conformal quantile
    half_width = float(np.quantile(resid, q))
    metrics = {
        "validation": "leave-source-out (GroupKFold)",
        "n_splits": n_splits,
        "n_sources": int(len(set(groups))),
        "rmse": float(np.sqrt(np.mean((y - pred) ** 2))),
        "mae": float(mean_absolute_error(y, pred)),
        "r2": float(r2_score(y, pred)),
        f"band_half_width_{int(coverage*100)}": half_width,  # prediction +/- this covers ~coverage of unseen-paper points
    }
    detail = pd.DataFrame({group_col: groups, "actual": y, "predicted": pred, "abs_error": resid})
    return metrics, detail


def per_source_error(detail: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Which papers does the model struggle on? Sorted worst first."""
    return (detail.groupby(group_col).abs_error.agg(["mean", "max", "size"])
            .rename(columns={"mean": "mean_abs_error", "max": "max_abs_error", "size": "points"})
            .sort_values("mean_abs_error", ascending=False).reset_index())