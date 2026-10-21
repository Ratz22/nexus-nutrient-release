"""Fit zero-order, Higuchi, and first-order plateau release models to each real release curve.

Input : data/research/combined_real_release_observations.csv (default), or a path given as argument 1
Output: curve_inventory.csv and real_curve_fits.csv in the folder given as argument 2 (default data/research)
Run   : python scripts/fit_real_curves.py
        python scripts/fit_real_curves.py <input.csv> <output_folder>

Every value is used as recorded. Values above 100% are kept and counted, not clipped.
Curves with conflicting values at the same timepoint are excluded and listed, not averaged.
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "research" / "combined_real_release_observations.csv"
OUT_DIR = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data" / "research"

CURVE_KEY = ["source_doi", "experiment_id", "fertilizer_type", "environment_medium",
             "placement", "position_detail", "orthogonal_position",
             "temperature_condition", "moisture_treatment", "replicate_id"]
OPTIONAL_KEY_COLUMNS = ["placement", "position_detail", "orthogonal_position"]
MIN_TIMEPOINTS = 4


def zero_order(t, k):
    return k * t


def higuchi(t, k):
    return k * np.sqrt(t)


def first_order_plateau(t, qinf, k):
    return qinf * (1 - np.exp(-k * t))


# name: (function, parameter names, initial guess, (lower bounds, upper bounds))
MODELS = {
    "zero_order_linear": (zero_order, ["k"], [1.0], ([0], [np.inf])),
    "higuchi_sqrt_time": (higuchi, ["k"], [10.0], ([0], [np.inf])),
    "first_order_plateau": (first_order_plateau, ["qinf", "k"], [100.0, 0.05], ([0, 1e-6], [200, 10])),
}


def load():
    df = pd.read_csv(SRC, dtype=str)
    for c in OPTIONAL_KEY_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    for c in CURVE_KEY:
        if c not in df.columns:
            df[c] = ""
    df[OPTIONAL_KEY_COLUMNS] = df[OPTIONAL_KEY_COLUMNS].fillna("")
    df["t"] = pd.to_numeric(df["days_after_fertilization"], errors="coerce")
    df["y"] = pd.to_numeric(df["nitrogen_released_pct"], errors="coerce")
    unusable = df["t"].isna() | df["y"].isna()
    return df[~unusable].copy(), int(unusable.sum())


def fit_one(name, t, y):
    fn, names, p0, bounds = MODELS[name]
    n = len(t)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p, _ = curve_fit(fn, t, y, p0=p0, bounds=bounds, maxfev=20000)
    except (RuntimeError, ValueError):
        return {"n_points": n, "params_json": None, "rmse_pp": None, "mae_pp": None,
                "r2": None, "aic": None, "fit_status": "did_not_converge"}
    resid = y - fn(t, *p)
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    k = len(p)
    return {
        "n_points": n,
        "params_json": json.dumps(dict(zip(names, map(float, p)))),
        "rmse_pp": float(np.sqrt(ss_res / n)),
        "mae_pp": float(np.mean(np.abs(resid))),
        "r2": (1 - ss_res / ss_tot) if ss_tot > 0 else None,
        "aic": n * np.log(max(ss_res, 1e-12) / n) + 2 * k,
        "fit_status": "fit_completed",
    }


def main():
    df, n_unusable = load()
    print(f"Rows usable: {len(df)}; dropped (non-numeric time or release): {n_unusable}")

    inventory, fits = [], []
    for key, g in df.groupby(CURVE_KEY, dropna=False, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        meta = dict(zip(CURVE_KEY, key))
        curve_id = " | ".join("" if pd.isna(v) else str(v) for v in key)

        g = g.drop_duplicates(subset=["t", "y"]).sort_values("t")
        conflicting = g["t"].duplicated(keep=False).any()
        n_timepoints = int(g["t"].nunique())
        n_above_100 = int((g["y"] > 100).sum())

        if conflicting:
            status = "excluded_conflicting_values_at_same_time"
        elif n_timepoints < MIN_TIMEPOINTS:
            status = f"excluded_fewer_than_{MIN_TIMEPOINTS}_timepoints"
        else:
            status = "eligible"

        inventory.append({"curve_id": curve_id, **meta, "n_timepoints": n_timepoints,
                          "n_points_above_100pct": n_above_100, "status": status})
        if status != "eligible":
            continue

        t, y = g["t"].to_numpy(float), g["y"].to_numpy(float)
        for model in MODELS:
            fits.append({"curve_id": curve_id, **meta, "model": model, **fit_one(model, t, y)})

    inv = pd.DataFrame(inventory)
    fit_df = pd.DataFrame(fits)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inv.to_csv(OUT_DIR / "curve_inventory.csv", index=False)
    fit_df.to_csv(OUT_DIR / "real_curve_fits.csv", index=False)

    print("\nCurve eligibility:")
    print(inv["status"].value_counts().to_string())
    print(f"\nCurves with at least one value above 100%: {int((inv['n_points_above_100pct'] > 0).sum())}")
    print("\nFits per model (descriptive only, not a ranking):")
    for model, g in fit_df.groupby("model"):
        ok = g[g["fit_status"] == "fit_completed"]
        print(f"  {model}: fitted={len(ok)}, failed={len(g) - len(ok)}, "
              f"median R2={ok['r2'].median():.3f}, median RMSE={ok['rmse_pp'].median():.2f} pp")
    print(f"\nWrote {OUT_DIR / 'curve_inventory.csv'} and {OUT_DIR / 'real_curve_fits.csv'}")


if __name__ == "__main__":
    main()