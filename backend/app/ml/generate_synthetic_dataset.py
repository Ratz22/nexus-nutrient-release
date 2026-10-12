"""
Generates a physically-plausible synthetic dataset so you can run the
FULL pipeline (train -> SHAP -> API -> frontend) on day 1, before your
literature-mined dataset is ready. Swap this file's output for the real
data/processed/dataset.csv the moment Sprint-4 dataset work is done —
nothing else in the codebase needs to change, since it's shaped by the
same FEATURE_COLUMNS / TARGET_COLUMN contract.

    python -m app.ml.generate_synthetic_dataset --n 800
"""
import argparse

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

COATINGS = ["chitosan", "alginate", "silica", "starch", "PLA", "zeolite"]
NUTRIENTS = ["N", "P", "K", "Zn", "Fe", "Cu"]
TEXTURES = ["sandy", "loamy", "clay"]


def generate(n: int) -> pd.DataFrame:
    df = pd.DataFrame({
        "particle_size_nm": RNG.uniform(20, 400, n),
        "coating_material": RNG.choice(COATINGS, n),
        "nutrient_type": RNG.choice(NUTRIENTS, n),
        "nutrient_loading_pct": RNG.uniform(2, 40, n),
        "shell_thickness_nm": RNG.uniform(5, 100, n),
        "ph": RNG.uniform(4.5, 8.5, n),
        "moisture_pct": RNG.uniform(10, 80, n),
        "temperature_c": RNG.uniform(10, 40, n),
        "organic_carbon_pct": RNG.uniform(0.2, 4.0, n),
        "texture": RNG.choice(TEXTURES, n),
        "salinity_ds_m": RNG.uniform(0, 4, n),
        "rainfall_mm": RNG.uniform(0, 300, n),
        "humidity_pct": RNG.uniform(20, 95, n),
    })

    # Plausible ground truth: thinner shell, smaller particle, higher
    # moisture/temperature/rainfall -> faster release (higher k).
    # Higher organic carbon and clay-like texture slow it down (adsorption).
    texture_factor = df["texture"].map({"clay": -0.02, "loamy": 0.0, "sandy": 0.02})
    coating_factor = df["coating_material"].map({
        "chitosan": 0.01, "alginate": 0.0, "silica": -0.01,
        "starch": 0.02, "PLA": -0.015, "zeolite": -0.02,
    })

    k = (
        0.15
        - 0.0004 * df["shell_thickness_nm"]
        + 0.0003 * df["particle_size_nm"] * -1
        + 0.002 * df["moisture_pct"]
        + 0.001 * df["temperature_c"]
        + 0.0005 * df["rainfall_mm"]
        - 0.01 * df["organic_carbon_pct"]
        - 0.005 * df["salinity_ds_m"]
        + texture_factor
        + coating_factor
        + RNG.normal(0, 0.01, n)
    )
    df["release_constant_k"] = np.clip(k, 0.005, 0.5)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=800)
    parser.add_argument("--out", default="data/processed/dataset.csv")
    args = parser.parse_args()
    df = generate(args.n)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} synthetic rows to {args.out}")
