"""
Single source of truth for feature engineering. train.py and predict.py
BOTH import this so train/serve skew (the #1 way ML demos break in
production) can't happen.
"""
import pandas as pd

FEATURE_COLUMNS = [
    "particle_size_nm",
    "coating_material",
    "nutrient_type",
    "nutrient_loading_pct",
    "shell_thickness_nm",
    "ph",
    "moisture_pct",
    "temperature_c",
    "organic_carbon_pct",
    "texture",
    "salinity_ds_m",
    "rainfall_mm",
    "humidity_pct",
]

CATEGORICAL_COLUMNS = ["coating_material", "nutrient_type", "texture"]
NUMERIC_COLUMNS = [c for c in FEATURE_COLUMNS if c not in CATEGORICAL_COLUMNS]

TARGET_COLUMN = "release_constant_k"

# Present only in the raw literature dataset, never in an API request and
# never fed to the model as a feature — used solely to group rows from the
# same paper together so CV splits can't leak (see train.py's GroupKFold).
# If a paper reports 5 formulations, random KFold can put 4 in train and
# 1 in test — the model then "memorizes" that paper's baseline instead of
# generalizing. GroupKFold prevents that.
GROUP_COLUMN = "paper_id"


def flatten_request(formulation: dict, soil: dict, environment: dict) -> pd.DataFrame:
    """Turn the nested API request into the flat row shape the model expects."""
    row = {**formulation, **soil, **environment}
    return pd.DataFrame([row])[FEATURE_COLUMNS]


def build_preprocessor():
    """One-hot for categoricals, passthrough (scaled) for numerics.
    Tree ensembles don't need scaling, but keeping it makes swapping in
    SVR/linear baselines for the benchmark trivial.
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLUMNS),
            ("num", StandardScaler(), NUMERIC_COLUMNS),
        ]
    )
