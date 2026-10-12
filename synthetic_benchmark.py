
"""
NEXUS — Synthetic Data Benchmark
FOR DEMONSTRATION ONLY.
Results are not experimental validation.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import GroupShuffleSplit, GroupKFold, cross_validate
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.svm import SVR

# --------------------------------------------------
# 1. SETTINGS
# --------------------------------------------------

SEED = 42
N_FORMULATIONS = 500
TIME_POINTS = 6

OUTPUT = Path("nexus_benchmark_results")
OUTPUT.mkdir(exist_ok=True)

rng = np.random.default_rng(SEED)


# --------------------------------------------------
# 2. GENERATE SYNTHETIC DATA
# --------------------------------------------------

rows = []

coatings = ["Chitosan", "Alginate", "Starch", "Polymer blend"]
nutrients = ["Nitrogen", "Phosphorus", "Potassium"]

coating_effect = {
    "Chitosan": 0.00,
    "Alginate": 0.16,
    "Starch": 0.27,
    "Polymer blend": 0.11,
}

nutrient_effect = {
    "Nitrogen": 0.08,
    "Phosphorus": 0.18,
    "Potassium": 0.12,
}

for i in range(N_FORMULATIONS):

    coating = rng.choice(coatings)
    nutrient = rng.choice(nutrients)

    particle_size = rng.uniform(20, 500)
    thickness = rng.uniform(2, 80)
    loading = rng.uniform(10, 60)
    soil_ph = rng.uniform(4.5, 8.5)
    temperature = rng.uniform(10, 40)
    moisture = rng.uniform(10, 80)
    organic_carbon = rng.uniform(0.2, 5.0)
    clay = rng.uniform(5, 60)

    # Artificial relationship for testing the ML pipeline.
    # These coefficients are NOT experimentally derived.

    log_k = (
        -2.45
        + 0.018 * (temperature - 25)
        + 0.012 * (moisture - 45)
        - 0.010 * (thickness - 40)
        - 0.0018 * (particle_size - 250)
        + 0.018 * (loading - 35)
        + coating_effect[coating]
        + nutrient_effect[nutrient]
        - 0.035 * abs(soil_ph - 6.5)
        + rng.normal(0, 0.10)
    )

    k = np.clip(np.exp(log_k), 0.002, 0.35)

    max_release = np.clip(
        92 - 0.10 * thickness
        + 0.10 * loading
        - 0.025 * particle_size
        + rng.normal(0, 3),
        35, 98
    )

    for time in np.linspace(1, 30, TIME_POINTS):

        release = max_release * (1 - np.exp(-k * time))
        release += rng.normal(0, 2)
        release = np.clip(release, 0, 100)

        rows.append({
            "formulation_id": f"F{i:04d}",
            "nutrient": nutrient,
            "coating": coating,
            "particle_size_nm": particle_size,
            "coating_thickness_um": thickness,
            "nutrient_loading_percent": loading,
            "soil_ph": soil_ph,
            "temperature_c": temperature,
            "soil_moisture_percent": moisture,
            "organic_carbon_percent": organic_carbon,
            "clay_percent": clay,
            "time_days": time,
            "release_percent": release,
        })

df = pd.DataFrame(rows)

df.to_csv(
    OUTPUT / "synthetic_dataset.csv",
    index=False
)

print("Synthetic observations:", len(df))
print("Unique formulations:", df["formulation_id"].nunique())


# --------------------------------------------------
# 3. PREPARE FEATURES AND TARGET
# --------------------------------------------------

target = "release_percent"
group = "formulation_id"

categorical = ["nutrient", "coating"]

numeric = [
    "particle_size_nm",
    "coating_thickness_um",
    "nutrient_loading_percent",
    "soil_ph",
    "temperature_c",
    "soil_moisture_percent",
    "organic_carbon_percent",
    "clay_percent",
    "time_days",
]

features = categorical + numeric

# Hold out entire formulations to avoid leakage
splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=SEED
)

train_idx, test_idx = next(
    splitter.split(
        df[features],
        df[target],
        groups=df[group]
    )
)

train = df.iloc[train_idx]
test = df.iloc[test_idx]

X_train = train[features]
y_train = train[target]

X_test = test[features]
y_test = test[target]


# --------------------------------------------------
# 4. PREPROCESSING
# --------------------------------------------------

def make_preprocessor(scale=False):

    numeric_steps = [
        ("imputer", SimpleImputer(strategy="median"))
    ]

    if scale:
        numeric_steps.append(
            ("scaler", StandardScaler())
        )

    numeric_pipe = Pipeline(numeric_steps)

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(
            strategy="most_frequent"
        )),
        ("onehot", OneHotEncoder(
            handle_unknown="ignore"
        )),
    ])

    return ColumnTransformer([
        ("numeric", numeric_pipe, numeric),
        ("categorical", categorical_pipe, categorical),
    ])


# --------------------------------------------------
# 5. TRAIN AND COMPARE MODELS
# --------------------------------------------------

models = {
    "Linear Regression": Pipeline([
        ("prep", make_preprocessor(scale=True)),
        ("model", LinearRegression()),
    ]),

    "Random Forest": Pipeline([
        ("prep", make_preprocessor()),
        ("model", RandomForestRegressor(
            n_estimators=200,
            min_samples_leaf=2,
            random_state=SEED,
            n_jobs=-1,
        )),
    ]),

    "SVR": Pipeline([
        ("prep", make_preprocessor(scale=True)),
        ("model", SVR(
            C=15,
            epsilon=1.5,
            kernel="rbf",
        )),
    ]),

    "Gradient Boosting": Pipeline([
        ("prep", make_preprocessor()),
        ("model", HistGradientBoostingRegressor(
            max_iter=180,
            learning_rate=0.08,
            random_state=SEED,
        )),
    ]),
}

results = []
predictions = {}

for name, model in models.items():

    model.fit(X_train, y_train)
    predicted = model.predict(X_test)

    predictions[name] = predicted


results.append({
    "Model": name,
    "R2": r2_score(y_test, predicted),
    "R2_percent": r2_score(y_test, predicted) * 100,
    "RMSE": np.sqrt(
        mean_squared_error(y_test, predicted)
    ),
    "MAE": mean_absolute_error(
        y_test, predicted
    ),
    "MAPE_percent": np.mean(
        np.abs((y_test - predicted) / y_test)
    ) * 100,
})


metrics = pd.DataFrame(results)
metrics = metrics.sort_values("RMSE")

metrics.to_csv(
    OUTPUT / "model_metrics.csv",
    index=False
)

print("\nMODEL COMPARISON — SYNTHETIC DATA")
print(metrics.round(3).to_string(index=False))


# --------------------------------------------------
# 6. GROUPED CROSS-VALIDATION
# --------------------------------------------------

cv = GroupKFold(n_splits=5)
cv_results = []

for name, model in models.items():

    scores = cross_validate(
        model,
        X_train,
        y_train,
        groups=train[group],
        cv=cv,
        scoring={
            "r2": "r2",
            "rmse": "neg_root_mean_squared_error",
            "mae": "neg_mean_absolute_error",
        },
        n_jobs=1,
    )

    cv_results.append({
        "Model": name,
        "Mean CV R2": scores["test_r2"].mean(),
        "Mean CV RMSE": -scores["test_rmse"].mean(),
        "Mean CV MAE": -scores["test_mae"].mean(),
    })

cv_df = pd.DataFrame(cv_results)

cv_df.to_csv(
    OUTPUT / "cross_validation_metrics.csv",
    index=False
)

print("\nGROUPED CROSS-VALIDATION")
print(cv_df.round(3).to_string(index=False))


# --------------------------------------------------
# 7. CHART: MODEL COMPARISON
# --------------------------------------------------

plot_data = metrics.sort_values("RMSE")

plt.figure(figsize=(9, 5))

plt.barh(
    plot_data["Model"],
    plot_data["RMSE"]
)

plt.xlabel("RMSE (release percentage points)")
plt.title("NEXUS Model Comparison — Synthetic Data")
plt.gca().invert_yaxis()
plt.tight_layout()

plt.savefig(
    OUTPUT / "model_comparison.png",
    dpi=200
)

plt.close()


# --------------------------------------------------
# 8. CHART: OBSERVED VS PREDICTED
# --------------------------------------------------

best_model = metrics.iloc[0]["Model"]
best_predictions = predictions[best_model]

plt.figure(figsize=(6, 6))

plt.scatter(
    y_test,
    best_predictions,
    alpha=0.6
)

low = min(y_test.min(), best_predictions.min())
high = max(y_test.max(), best_predictions.max())

plt.plot(
    [low, high],
    [low, high],
    linestyle="--"
)

plt.xlabel("Synthetic Observed Release (%)")
plt.ylabel("Predicted Release (%)")

plt.title(
    f"{best_model}\n"
    "Synthetic Hold-Out Data Only"
)

plt.tight_layout()

plt.savefig(
    OUTPUT / "observed_vs_predicted.png",
    dpi=200
)

plt.close()


# --------------------------------------------------
# 9. SAVE TEST PREDICTIONS
# --------------------------------------------------

test_output = test[
    ["formulation_id", "time_days", target]
].copy()

test_output["predicted_release"] = best_predictions

test_output.to_csv(
    OUTPUT / "test_predictions.csv",
    index=False
)


# --------------------------------------------------
# 10. FINISH
# --------------------------------------------------

print("\nBEST MODEL ON SYNTHETIC TEST DATA:")
print(best_model)

print("\nFiles saved in:", OUTPUT.resolve())

print("""
IMPORTANT:
These results demonstrate the ML workflow on generated data.
They do not establish accuracy on real nanofertilizers.
Use experimentally measured, source-traceable data for
scientific performance claims.
""")
