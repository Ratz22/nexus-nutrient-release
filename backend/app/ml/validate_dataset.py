"""
Checks a literature dataset BEFORE training.

Run:
    python -m app.ml.validate_dataset --data data/raw/literature.csv

Exit code 0 = ready to train. Exit code 1 = fix the errors first.
"""
import argparse
import sys

import pandas as pd

from app.ml.preprocessing import FEATURE_COLUMNS, GROUP_COLUMN, TARGET_COLUMN

REQUIRED_EXTRA = ["doi"]

ALLOWED = {
    "coating_material": ["chitosan", "alginate", "silica", "starch", "PLA", "zeolite"],
    "nutrient_type": ["N", "P", "K", "Zn", "Fe", "Cu"],
    "texture": ["sandy", "loamy", "clay"],
}

RANGES = {
    "particle_size_nm": (1, 10000),
    "shell_thickness_nm": (0.1, 1000),
    "nutrient_loading_pct": (0, 100),
    "ph": (0, 14),
    "moisture_pct": (0, 100),
    "temperature_c": (-10, 60),
    "organic_carbon_pct": (0, 100),
    "salinity_ds_m": (0, 100),
    "rainfall_mm": (0, 5000),
    "humidity_pct": (0, 100),
}

MIN_PAPERS = 3
RECOMMENDED_PAPERS = 10
MIN_ROWS = 50


def check(df: pd.DataFrame):
    errors, warnings = [], []

    required = FEATURE_COLUMNS + [GROUP_COLUMN, TARGET_COLUMN] + REQUIRED_EXTRA
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append("The file is missing these required columns: " + ", ".join(missing) + ".")
        return errors, warnings
    if df.empty:
        errors.append("The file has a header but no data rows.")
        return errors, warnings

    n_rows = len(df)

    empty_features = [c for c in FEATURE_COLUMNS if df[c].isna().any()]
    if empty_features:
        errors.append("Some rows are empty in these columns: " + ", ".join(empty_features) + ". Fill them or remove those rows.")

    paper_blank = df[GROUP_COLUMN].isna() | (df[GROUP_COLUMN].astype(str).str.strip() == "")
    if paper_blank.any():
        errors.append(f"{int(paper_blank.sum())} row(s) have no paper_id. Every row must name its source paper.")

    doi_blank = df["doi"].isna() | (df["doi"].astype(str).str.strip() == "")
    if doi_blank.any():
        errors.append(f"{int(doi_blank.sum())} row(s) have no DOI. Every value must be traceable to a source.")

    for col, allowed in ALLOWED.items():
        found = set(df[col].dropna().astype(str).str.strip())
        bad = sorted(found - set(allowed))
        if bad:
            errors.append(f"Unknown {col} value(s): {', '.join(bad)}. Allowed values: {', '.join(allowed)}.")

    for col, (lo, hi) in RANGES.items():
        num = pd.to_numeric(df[col], errors="coerce")
        not_numbers = num.isna() & df[col].notna()
        if not_numbers.any():
            errors.append(f"{col}: {int(not_numbers.sum())} value(s) are not numbers.")
        out = (num < lo) | (num > hi)
        if out.any():
            errors.append(f"{col}: {int(out.sum())} value(s) fall outside the expected range {lo} to {hi}. Check the units.")

    k = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
    if k.isna().any() or (k <= 0).any():
        errors.append("release_constant_k must be a positive number in every row.")

    if "cumulative_release_pct" in df.columns:
        cr = pd.to_numeric(df["cumulative_release_pct"], errors="coerce")
        if ((cr < 0) | (cr > 100)).any():
            errors.append("cumulative_release_pct must be between 0 and 100.")

    n_papers = df[GROUP_COLUMN].nunique()
    if n_papers < MIN_PAPERS:
        errors.append(
            f"Only {n_papers} distinct paper(s) found. At least {MIN_PAPERS} are needed "
            "for paper-grouped validation."
        )
    elif n_papers < RECOMMENDED_PAPERS:
        warnings.append(
            f"{n_papers} papers found. Scores are possible but fragile; "
            f"{RECOMMENDED_PAPERS} or more papers are recommended."
        )

    if n_rows < MIN_ROWS:
        warnings.append(f"Only {n_rows} rows. Models trained on this few rows will not generalise well.")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/raw/literature.csv")
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.data)
    except FileNotFoundError:
        print(f"File not found: {args.data}")
        sys.exit(1)
    except Exception as e:
        print(f"Could not read {args.data} as a CSV file: {e}")
        sys.exit(1)

    errors, warnings = check(df)

    print(f"Checked {args.data}: {len(df)} rows, {df[GROUP_COLUMN].nunique() if GROUP_COLUMN in df.columns else 0} papers.")
    print()
    if errors:
        print("ERRORS (must fix before training):")
        for e in errors:
            print("  - " + e)
    if warnings:
        print("WARNINGS (read these):")
        for w in warnings:
            print("  - " + w)
    if not errors and not warnings:
        print("No problems found.")

    print()
    if errors:
        print("RESULT: NOT READY. Fix the errors above and run this again.")
        sys.exit(1)
    print("RESULT: READY. You can now run: python -m app.ml.train --data " + args.data)
    sys.exit(0)


if __name__ == "__main__":
    main()