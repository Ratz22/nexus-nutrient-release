import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingRegressor

from app.ml.grouped_cv import leave_source_out, per_source_error
from app.ml.kinetics import first_order, fit_release, time_to_release


def test_first_order_recovers_params():
    t = np.array([0.5, 1, 2, 4, 7, 10, 14, 21, 28])
    y = first_order(t, 90, 0.12) + np.random.default_rng(0).normal(0, 0.3, len(t))
    p = fit_release(t, y)["fits"]["first_order"]["params"]
    assert abs(p["qmax"] - 90) < 3 and abs(p["k"] - 0.12) < 0.02


def test_time_to_release_consistent():
    t80 = time_to_release("first_order", {"qmax": 100.0, "k": 0.1}, 80)
    assert abs(first_order(t80, 100, 0.1) - 80) < 1e-6


def test_leave_source_out_never_trains_on_heldout_source():
    rng = np.random.default_rng(1)
    rows = []
    for s in range(8):
        k = rng.uniform(0.05, 0.3)
        for t in [1, 3, 7, 14, 28, 42]:
            rows.append({"src": f"p{s}", "t": t, "k": k, "y": 100 * (1 - np.exp(-k * t))})
    df = pd.DataFrame(rows)
    m, d = leave_source_out(df, ["t", "k"], "y", "src", lambda: GradientBoostingRegressor(random_state=0))
    assert d.predicted.notna().all() and m["n_sources"] == 8 and m["r2"] > 0.5
    assert per_source_error(d, "src").shape[0] == 8


def test_needs_two_sources():
    df = pd.DataFrame({"src": ["a"] * 6, "t": range(6), "y": range(6)})
    with pytest.raises(ValueError):
        leave_source_out(df, ["t"], "y", "src", lambda: GradientBoostingRegressor())