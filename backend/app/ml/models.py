"""
Every candidate from the master reference doc's model list, in one
registry — plus build_estimator()/get_tuning_search_space() so train.py
can Optuna-tune each one without a big if/elif chain. Add a 7th model
by adding one entry to REGISTRY_FACTORY and (if you want it tuned) one
to SEARCH_SPACES.
"""
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None

try:
    from lightgbm import LGBMRegressor
except ImportError:
    LGBMRegressor = None

try:
    from catboost import CatBoostRegressor
except ImportError:
    CatBoostRegressor = None


# name -> (estimator class, fixed kwargs always applied regardless of tuning)
REGISTRY_FACTORY = {
    "linear_regression": (LinearRegression, {}),
    "random_forest": (RandomForestRegressor, {"random_state": 42, "n_jobs": -1}),
    "svr": (SVR, {"kernel": "rbf"}),
}
if XGBRegressor is not None:
    REGISTRY_FACTORY["xgboost"] = (XGBRegressor, {"random_state": 42, "n_jobs": -1})
if LGBMRegressor is not None:
    REGISTRY_FACTORY["lightgbm"] = (LGBMRegressor, {"random_state": 42, "verbosity": -1})
if CatBoostRegressor is not None:
    REGISTRY_FACTORY["catboost"] = (CatBoostRegressor, {"random_state": 42, "verbose": False})


# Sensible, untuned defaults — used when --skip-tuning is passed.
DEFAULT_PARAMS = {
    "random_forest": {"n_estimators": 300, "max_depth": None},
    "svr": {"C": 10, "epsilon": 0.01},
    "xgboost": {"n_estimators": 400, "learning_rate": 0.05, "max_depth": 6},
    "lightgbm": {"n_estimators": 400, "learning_rate": 0.05},
    "catboost": {"iterations": 400, "learning_rate": 0.05, "depth": 6},
}


def build_estimator(name: str, params: dict):
    """Construct a fresh, unfitted estimator instance with given hyperparams
    merged over the fixed kwargs. Called once per CV fold during tuning and
    once for the final refit, so it must be side-effect-free."""
    cls, fixed_kwargs = REGISTRY_FACTORY[name]
    return cls(**fixed_kwargs, **params)


def get_model_registry() -> dict:
    """Default (untuned) instances — the starting point train.py falls back
    to for non-tunable models (linear_regression) and when --skip-tuning."""
    registry = {}
    for name in REGISTRY_FACTORY:
        params = DEFAULT_PARAMS.get(name, {})
        registry[name] = build_estimator(name, params)
    return registry


def get_tuning_search_space(name: str):
    """Returns a function(trial) -> params dict for Optuna. Ranges are kept
    deliberately modest to fit a one-day compute budget — widen them if you
    have more than ~25 trials/model to spend."""
    return SEARCH_SPACES[name]


def _rf_space(trial):
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 600, step=50),
        "max_depth": trial.suggest_int("max_depth", 3, 20),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 8),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
    }


def _xgb_space(trial):
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 600, step=50),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10, log=True),
    }


def _lgbm_space(trial):
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 600, step=50),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
    }


def _catboost_space(trial):
    return {
        "iterations": trial.suggest_int("iterations", 100, 600, step=50),
        "depth": trial.suggest_int("depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
    }


SEARCH_SPACES = {
    "random_forest": _rf_space,
    "xgboost": _xgb_space,
    "lightgbm": _lgbm_space,
    "catboost": _catboost_space,
}