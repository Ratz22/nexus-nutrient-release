# ML-NanoFertRelease

Interpretable ML platform to predict nano-fertilizer nutrient release —
capstone research paper + deployable MVP, one codebase.

## Architecture

```
                    ┌─────────────────────────┐
                    │   Streamlit frontend     │
                    │  (5 pages, simple UX)    │
                    └───────────┬─────────────┘
                                │ REST (httpx)
                    ┌───────────▼─────────────┐
                    │      FastAPI backend      │
                    │  /predict  /explain        │
                    │  /soil  /weather  /literature
                    │  /dataset/schema  /leaderboard
                    └───┬───────────┬──────────┘
                        │           │
            ┌───────────▼──┐   ┌────▼─────────────────┐
            │ ML pipeline   │   │  External global APIs │
            │ (sklearn +    │   │  SoilGrids (ISRIC)     │
            │  XGB/LGBM/    │   │  NASA POWER            │
            │  CatBoost +   │   │  Semantic Scholar       │
            │  SHAP)        │   └────────────────────────┘
            └───────────────┘
```

Why this stack: FastAPI + Streamlit is the fastest path to a *working,
deployed* research tool in a week, without sacrificing rigor — the API
is fully decoupled, so you (or a future teammate) can swap the frontend
for React/Next.js later with zero backend changes.

## What makes this "not just another fertilizer-prediction script"

1. **Train/serve consistency by construction** — `preprocessing.py` is
   the single source of truth for features; training and inference both
   import it, so they can never silently drift apart.
2. **Real global data, not manual entry** — `/soil` and `/weather`
   auto-fill formulation forms from any lat/lon via ISRIC SoilGrids and
   NASA POWER (both free, keyless, planet-wide).
3. **Research tool, not just a calculator** — `/literature` gives live
   Semantic Scholar search inside the app, so it doubles as a lit-review
   aid while you write the paper.
4. **Explainability is a first-class endpoint**, not an afterthought —
   `/explain` returns SHAP values with a precomputed background sample so
   it's fast enough for interactive use.
5. **Runnable on day 1** — `generate_synthetic_dataset.py` produces a
   physically-plausible dataset so the *entire* pipeline (train → SHAP →
   API → frontend) works before your literature-mined dataset exists.
   Swap the CSV later; nothing else changes.

## Quickstart (local, no Docker)

```bash
# from the repo root
pip install -r backend/requirements.txt --break-system-packages
pip install -r frontend/requirements.txt --break-system-packages

# 1. generate a placeholder dataset (skip once you have the real one)
PYTHONPATH=backend python -m app.ml.generate_synthetic_dataset --n 800

# 2. train + benchmark all 6 models, save the best + its SHAP explainer
PYTHONPATH=backend python -m app.ml.train

# 3. run the API
uvicorn app.main:app --app-dir backend --reload --port 8000

# 4. in a second terminal, run the frontend
cd frontend && streamlit run app.py
```

Visit `http://localhost:8501`. API docs (auto-generated) at
`http://localhost:8000/docs`.

## Quickstart (Docker)

```bash
docker compose up --build
```

Backend: `localhost:8000` · Frontend: `localhost:8501`.
Run training once inside the backend container the first time:
```bash
docker compose exec backend python -m app.ml.generate_synthetic_dataset --n 800
docker compose exec backend python -m app.ml.train
```

## Repo layout

```
backend/
  app/
    core/config.py          # env-driven settings
    schemas/formulation.py  # API contract = dataset schema
    ml/
      preprocessing.py      # shared feature contract (train + serve)
      models.py             # 6-model registry (Linear/RF/SVR/XGB/LGBM/CatBoost)
      train.py              # benchmark + save best model + SHAP explainer
      predict.py            # inference + release-curve generation
      shap_explain.py       # SHAP explanation endpoint logic
      generate_synthetic_dataset.py
    services/
      soilgrids.py          # global soil data (ISRIC)
      nasa_power.py         # global weather data (NASA)
      semantic_scholar.py   # literature search
    api/v1/endpoints/       # predict, explain, external, dataset
    main.py                 # FastAPI app
  tests/
frontend/
  app.py                    # landing page
  pages/
    1_Release_Predictor.py
    2_Explainability.py
    3_Model_Benchmark.py
    4_Research_Explorer.py
    5_Report_Export.py
data/
  raw/                      # drop literature-extracted CSVs here
  processed/dataset.csv     # final training data (schema in ml/preprocessing.py)
models/                     # trained pipeline + SHAP explainer + metrics.json (generated)
```

## One-week build plan

| Day | Focus | Deliverable |
|---|---|---|
| 1 | Repo up, synthetic pipeline runs end-to-end | You are here — everything above already works |
| 2 | Literature dataset extraction (Sprint 6 of your matrix) | `data/processed/dataset.csv` replaces the synthetic one |
| 3 | Retrain on real data, inspect SHAP, tune hyperparameters | Real `metrics.json`, chosen best model |
| 4 | Polish frontend UX — units, tooltips, input validation ranges from literature | Demo-ready predictor + explainability pages |
| 5 | Report export polish + literature explorer tuned to your keywords | Full MVP feature-complete |
| 6 | Deploy (Render/Railway for backend, Streamlit Community Cloud for frontend) | Public URL you can put in the paper/demo |
| 7 | Write up Methods + Results sections straight from `metrics.json` and SHAP plots | Paper draft sections done |

## Extending

- **Swap in a real feature (e.g. cation exchange capacity)**: add it to
  `FormulationInput`/`SoilInput` in `schemas/formulation.py` **and**
  `FEATURE_COLUMNS` in `ml/preprocessing.py` — that's the only place
  the contract lives.
- **Add a 7th model**: one line in `ml/models.py`'s registry.
- **Batch prediction from CSV**: add an endpoint that loops
  `predict_release()` over uploaded rows — the function already accepts
  plain dicts, no refactor needed.
