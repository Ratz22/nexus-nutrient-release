"""Classical release-kinetics fitting. Fully interpretable: gives parameters + best model by AIC."""
import numpy as np
from scipy.optimize import brentq, curve_fit


def first_order(t, qmax, k):
    return qmax * (1 - np.exp(-k * t))


def higuchi(t, k):
    return k * np.sqrt(t)


def korsmeyer_peppas(t, k, n):
    return k * np.power(t, n)


def weibull(t, qmax, a, b):
    return qmax * (1 - np.exp(-np.power(t, b) / a))


MODELS = {
    "first_order": (first_order, ["qmax", "k"], [100, 0.1], ([0, 1e-6], [100, 10])),
    "higuchi": (higuchi, ["k"], [10], ([0], [1000])),
    "korsmeyer_peppas": (korsmeyer_peppas, ["k", "n"], [10, 0.5], ([0, 0.05], [1000, 2])),
    "weibull": (weibull, ["qmax", "a", "b"], [100, 10, 1], ([0, 1e-3, 0.05], [100, 1e4, 5])),
}


def _aic(y, y_hat, k):
    n = len(y)
    rss = max(float(np.sum((y - y_hat) ** 2)), 1e-12)
    return n * np.log(rss / n) + 2 * k


def fit_release(t, y):
    t, y = np.asarray(t, float), np.asarray(y, float)
    if len(t) < 4:
        raise ValueError("Need at least 4 time points to fit release kinetics.")
    fits = {}
    for name, (fn, names, p0, bounds) in MODELS.items():
        try:
            p, _ = curve_fit(fn, t, y, p0=p0, bounds=bounds, maxfev=20000)
            yh = fn(t, *p)
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            fits[name] = {
                "params": dict(zip(names, map(float, p))),
                "r2": float(1 - np.sum((y - yh) ** 2) / ss_tot) if ss_tot > 0 else None,
                "aic": float(_aic(y, yh, len(p))),
            }
        except (RuntimeError, ValueError):
            fits[name] = {"error": "did not converge"}
    ok = {k: v for k, v in fits.items() if "aic" in v}
    best = min(ok, key=lambda k: ok[k]["aic"]) if ok else None
    return {"best_model": best, "fits": fits}


def predict(model_name, params, t):
    return MODELS[model_name][0](np.asarray(t, float), *params.values())


def time_to_release(model_name, params, target_pct=80.0, t_max=1000.0):
    """Days to reach target % release under a fitted model, or None if never reached."""
    f = lambda t: predict(model_name, params, t) - target_pct
    if f(1e-6) >= 0:
        return 0.0
    if f(t_max) < 0:
        return None
    return float(brentq(f, 1e-6, t_max))