# NEXUS: Nutrient Release Intelligence (ML-NanoFertRelease)

A computational framework for estimating how fast a nano-fertilizer releases its nutrient, built from published release data. The system has a FastAPI backend, a Streamlit frontend, and a benchmark of several regression models compared against a non-ML baseline.

> **Status: research prototype. Not validated for publication yet.**
> The current model metrics were produced with random cross-validation, not grouped by source paper, so they can be inflated by leakage. See [Known issues](#known-issues).

## Project layout

backend/
  app/
    main.py              FastAPI app
    api/v1/              API routes (predict, explain, dataset, external, fit)
    core/config.py       settings (paths, API prefix)
    ml/                  training, models, preprocessing, prediction, OOD check, SHAP
    services/            SoilGrids, NASA POWER, literature lookup
    schemas/             request/response models
  tests/                 pytest suite
frontend/
  Home.py                Streamlit entry point
  pages/                 Release Predictor, Explainability, Model Benchmark,
                         Research Explorer, Report Export, Synthetic Dataset, Fit My Data
data/
  processed/dataset.csv  training dataset (400 rows)
  raw/                   literature template and source files
models/                  trained model, SHAP explainer, metrics.json
nexus_benchmark_results/ earlier benchmark outputs (provenance under review)
```

## Setup

From the project root, in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pip install -r frontend\requirements.txt
```

## Run

Start the backend from the `backend` folder. Launching from the project root breaks the `app.` imports.

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

In a second terminal, start the frontend:

```powershell
cd frontend
streamlit run Home.py
```

The app opens at http://localhost:8501. If a page says the backend is unreachable, the backend isn't running on port 8000.

## Train the model

From the `backend` folder:

```powershell
python -m app.ml.train --data ..\data\processed\dataset.csv --skip-tuning
```

This writes `models/release_predictor_v1.joblib`, `shap_explainer.joblib`, `metrics.json`, `best_params.json`, and `feature_coverage.json`. Without `--skip-tuning`, Optuna tunes the tree-based models, which is slower.

Check a dataset before training:

```powershell
python -m app.ml.validate_dataset --data ..\data\processed\dataset.csv
```

## Tests

```powershell
cd backend
pytest -q
```

## Methods in brief

- **Target:** `release_constant_k`, the first-order release rate.
- **Features:** 13 formulation, soil, and environment inputs (see `backend/app/ml/preprocessing.py`).
- **Models compared:** linear regression, random forest, SVR, XGBoost, LightGBM, CatBoost.
- **Baseline:** bucket-mean lookup by coating material and soil texture. This is the non-ML number a model has to beat.
- **Validation:** intended to be grouped by source paper (`paper_id`) using GroupKFold, so no paper appears in both training and test folds. Falls back to random KFold when there are fewer than 5 distinct papers. The training script prints a warning when this happens.
- **Uncertainty:** the 90th percentile of absolute held-out residuals, stored as `residual_p90_abs`. This is a rough interval, not a calibrated one.
- **Explainability:** SHAP values for the saved model.

## Known issues

1. **Validation is not grouped by paper in the current results.** The training run printed `random KFold, NOT grouped by paper`, so `models/metrics.json` must not be cited as results. Fixing this needs at least 5 distinct `paper_id` values in `dataset.csv`.
2. **Hyperparameters are untuned in the current results.** `models/best_params.json` is empty, so the tree models ran with default settings.
3. **Dataset provenance is incomplete.** Not every row's `doi` has been checked against its source paper.
4. **`nexus_benchmark_results/` has no traceable source script.** Its model names don't match `models.py`, and `synthetic_benchmark.py` wasn't found. Don't cite these results until their origin is confirmed.
5. **The `dataset` page needs the `/dataset/info` and `/dataset/raw` routes** to load. See `backend/app/api/v1/endpoints/dataset_export.py`.

## Not part of the deployed system

- `nexus-web/` is a separate React prototype. The Streamlit frontend is the supported UI.
- `fetch_datasets.py` downloads candidate source files. Its outputs are not used for training until they've been checked and added to `data/processed/dataset.csv`.

## Disclaimer

Predictions are research estimates from published laboratory data. They are not agronomic, regulatory, or safety advice. Validate in your own conditions before any field or commercial use. See `DISCLAIMER.md`.

## License

Not yet chosen. See `LICENSE` once it's finalized.