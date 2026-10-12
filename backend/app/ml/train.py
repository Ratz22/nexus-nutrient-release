"""
Day-2 upgraded trainer, now also recording training-domain coverage for
OOD detection. Three things a reviewer will specifically check for in a
"ML beats empirical estimation" paper, plus one operational addition:

1. GroupKFold on paper_id — random KFold leaks when multiple rows come
   from the same paper (shared baseline noise). This is close to
   mandatory for literature-mined datasets; mention it explicitly in
   your Methods section.
2. A hyperparameter-tuned comparison, not just defaults — Optuna tunes
   the top candidates so "XGBoost beat Linear Regression" isn't just
   "we tuned one and not the other."
3. An empirical kinetic baseline (bucket-mean lookup, the honest analogue
   of "look up a similar formulation in the literature by hand") — this
   is what Core Research Question #2 ("Can ML outperform empirical
   estimation?") is actually asking, and you need a non-ML number to beat.
4. feature_coverage.json — records the real min/max/percentile range of
   every numeric feature and the actual categories seen for every
   categorical feature, so a prediction later can be checked against
   real training coverage (see app/ml/ood.py) instead of silently
   extrapolating.

Usage:
    python -m app.ml.train --data data/processed/dataset.csv
    python -m app.ml.train --data data/processed/dataset.csv --trials 30
    python -m app.ml.train --data data/processed/dataset.csv --skip-tuning   # fast dev loop
"""
import argparse
import json
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
import shap
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import Pipeline

from app.ml.models import build_estimator, get_model_registry, get_tuning_search_space
from app.ml.preprocessing import (
    CATEGORICAL_COLUMNS,
    FEATURE_COLUMNS,
    GROUP_COLUMN,
    NUMERIC_COLUMNS,
    TARGET_COLUMN,
    build_preprocessor,
)

optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore", category=UserWarning)

# Only tune the models worth tuning time on within a one-day budget.
# Linear/SVR have little to gain; tree ensembles have the most upside.
TUNABLE_MODELS = {"random_forest", "xgboost", "lightgbm", "catboost"}


def make_cv(groups: pd.Series | None, n_splits: int = 5):
    if groups is not None and groups.nunique() >= n_splits:
        print(
            f"  Validation: GroupKFold by paper_id ({groups.nunique()} papers, {n_splits} folds). "
            "No paper appears in both training and testing."
        )
        return GroupKFold(n_splits=n_splits), groups
    print(
        "  [!] Validation: random KFold, NOT grouped by paper. "
        "These scores can be inflated by leakage and must not be published."
    )
    return KFold(n_splits=n_splits, shuffle=True, random_state=42), None


def cv_scores(pipeline: Pipeline, X: pd.DataFrame, y: pd.Series, cv, groups) -> dict:
    """Manual CV loop (not cross_val_predict) so we can also compute
    per-fold residuals for conformal intervals later."""
    fold_metrics = []
    all_residuals = []
    for train_idx, test_idx in cv.split(X, y, groups=groups):
        pipeline.fit(X.iloc[train_idx], y.iloc[train_idx])
        preds = pipeline.predict(X.iloc[test_idx])
        actual = y.iloc[test_idx]
        fold_metrics.append({
            "r2": r2_score(actual, preds),
            "rmse": float(np.sqrt(mean_squared_error(actual, preds))),
            "mae": float(mean_absolute_error(actual, preds)),
        })
        all_residuals.extend(np.abs(actual.values - preds))

    return {
        "r2": float(np.mean([m["r2"] for m in fold_metrics])),
        "r2_std": float(np.std([m["r2"] for m in fold_metrics])),
        "rmse": float(np.mean([m["rmse"] for m in fold_metrics])),
        "mae": float(np.mean([m["mae"] for m in fold_metrics])),
        "mape": float(np.mean(np.abs(np.array(all_residuals)) / np.clip(np.abs(y.mean()), 1e-9, None)) * 100),
        "residual_p90_abs": float(np.percentile(all_residuals, 90)),  # for conformal intervals
    }


def tune_model(name: str, X: pd.DataFrame, y: pd.Series, cv, groups, n_trials: int):
    """Optuna search over each model's space, scored by mean grouped-CV R2."""
    search_space_fn = get_tuning_search_space(name)

    def objective(trial: optuna.Trial) -> float:
        params = search_space_fn(trial)
        estimator = build_estimator(name, params)
        pipeline = Pipeline([("preprocess", build_preprocessor()), ("model", estimator)])
        scores = []
        for train_idx, test_idx in cv.split(X, y, groups=groups):
            pipeline.fit(X.iloc[train_idx], y.iloc[train_idx])
            preds = pipeline.predict(X.iloc[test_idx])
            scores.append(r2_score(y.iloc[test_idx], preds))
        return float(np.mean(scores))

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params, study.best_value


def empirical_baseline_metrics(X: pd.DataFrame, y: pd.Series, cv, groups) -> dict:
    """
    Non-ML baseline: predicts k as the mean k observed for rows sharing the
    same (coating_material, texture) bucket in the training fold — the
    honest analogue of 'look up a similar formulation in the literature
    and use its reported release constant,' which is what a researcher
    does today without this tool. This is the number your ML models need
    to beat to support Core Research Question #2.
    """
    bucket_cols = ["coating_material", "texture"]
    fold_metrics = []
    for train_idx, test_idx in cv.split(X, y, groups=groups):
        train_df = X.iloc[train_idx].copy()
        train_df["_y"] = y.iloc[train_idx].values
        bucket_means = train_df.groupby(bucket_cols)["_y"].mean()
        global_mean = train_df["_y"].mean()

        test_df = X.iloc[test_idx]
        preds = test_df.apply(
            lambda row: bucket_means.get((row["coating_material"], row["texture"]), global_mean),
            axis=1,
        )
        actual = y.iloc[test_idx]
        fold_metrics.append({
            "r2": r2_score(actual, preds),
            "rmse": float(np.sqrt(mean_squared_error(actual, preds))),
            "mae": float(mean_absolute_error(actual, preds)),
        })

    return {
        "r2": float(np.mean([m["r2"] for m in fold_metrics])),
        "rmse": float(np.mean([m["rmse"] for m in fold_metrics])),
        "mae": float(np.mean([m["mae"] for m in fold_metrics])),
        "method": "bucket-mean lookup (coating_material x texture) — empirical baseline, not ML",
    }


def main(data_path: str, model_dir: str, n_trials: int, skip_tuning: bool, cv_folds: int):
    df = pd.read_csv(data_path)
    missing = set(FEATURE_COLUMNS + [TARGET_COLUMN]) - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    groups_raw = df[GROUP_COLUMN] if GROUP_COLUMN in df.columns else None
    cv, groups = make_cv(groups_raw, n_splits=cv_folds)

    print(f"Dataset: {len(df)} rows" + (f", {groups_raw.nunique()} source papers" if groups is not None else ""))
    print("\n=== Empirical baseline (non-ML) ===")
    baseline = empirical_baseline_metrics(X, y, cv, groups)
    print(f"  R2={baseline['r2']:.3f}  RMSE={baseline['rmse']:.4f}  MAE={baseline['mae']:.4f}")

    registry = get_model_registry()
    leaderboard = {"empirical_baseline": baseline}
    fitted_pipelines = {}
    best_params_log = {}

    print("\n=== Model benchmark ===")
    for name, default_estimator in registry.items():
        t0 = time.time()
        if not skip_tuning and name in TUNABLE_MODELS:
            print(f"Tuning {name} ({n_trials} trials) ...")
            best_params, best_val = tune_model(name, X, y, cv, groups, n_trials)
            estimator = build_estimator(name, best_params)
            best_params_log[name] = best_params
            print(f"  tuned CV R2={best_val:.3f}  params={best_params}")
        else:
            estimator = default_estimator

        pipeline = Pipeline([("preprocess", build_preprocessor()), ("model", estimator)])
        metrics = cv_scores(pipeline, X, y, cv, groups)
        leaderboard[name] = metrics
        pipeline.fit(X, y)  # refit on full data for the saved artifact
        fitted_pipelines[name] = pipeline
        elapsed = time.time() - t0
        print(f"  {name}: R2={metrics['r2']:.3f}+/-{metrics['r2_std']:.3f}  RMSE={metrics['rmse']:.4f}  ({elapsed:.1f}s)")

    best_name = max(
        (k for k in leaderboard if k != "empirical_baseline"),
        key=lambda k: leaderboard[k]["r2"],
    )
    best_pipeline = fitted_pipelines[best_name]
    uplift = leaderboard[best_name]["r2"] - baseline["r2"]
    print(f"\nBest model: {best_name}  (R2={leaderboard[best_name]['r2']:.3f} vs empirical baseline "
          f"{baseline['r2']:.3f}, delta R2={uplift:+.3f})")

    Path(model_dir).mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, Path(model_dir) / "release_predictor_v1.joblib")
    joblib.dump({
        "name": best_name,
        "residual_p90_abs": leaderboard[best_name]["residual_p90_abs"],
    }, Path(model_dir) / "active_model_meta.joblib")

    background = X.sample(min(100, len(X)), random_state=42)
    transformed_bg = best_pipeline.named_steps["preprocess"].transform(background)
    explainer = shap.Explainer(best_pipeline.named_steps["model"].predict, transformed_bg)
    joblib.dump(explainer, Path(model_dir) / "shap_explainer.joblib")

    with open(Path(model_dir) / "metrics.json", "w") as f:
        json.dump(leaderboard, f, indent=2)
    with open(Path(model_dir) / "best_params.json", "w") as f:
        json.dump(best_params_log, f, indent=2)

    # Record what the model has actually seen, so a prediction later can be
    # checked against real training coverage instead of silently
    # extrapolating. This is the data an OOD/domain-warning check needs —
    # without it, "out of distribution" is just a guess.
    coverage = {"n_training_rows": len(df), "numeric": {}, "categorical": {}}
    for col in NUMERIC_COLUMNS:
        coverage["numeric"][col] = {
            "min": float(X[col].min()),
            "max": float(X[col].max()),
            "p01": float(X[col].quantile(0.01)),
            "p99": float(X[col].quantile(0.99)),
        }
    for col in CATEGORICAL_COLUMNS:
        coverage["categorical"][col] = sorted(X[col].dropna().unique().tolist())
    with open(Path(model_dir) / "feature_coverage.json", "w") as f:
        json.dump(coverage, f, indent=2)

    print(f"\nSaved model, SHAP explainer, metrics.json, best_params.json, feature_coverage.json to {model_dir}/")
    print("metrics.json (incl. empirical_baseline) is your paper's Results table.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/dataset.csv")
    parser.add_argument("--model-dir", default="models")
    parser.add_argument("--trials", type=int, default=25, help="Optuna trials per tunable model")
    parser.add_argument("--cv-folds", type=int, default=5)
    parser.add_argument("--skip-tuning", action="store_true", help="Use default hyperparams — fast dev loop")
    args = parser.parse_args()
    main(args.data, args.model_dir, args.trials, args.skip_tuning, args.cv_folds)