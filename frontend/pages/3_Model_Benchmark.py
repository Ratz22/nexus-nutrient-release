import os

import altair as alt
import httpx
import pandas as pd
import streamlit as st
from service_check import require_backend
from theme import (
    PALETTES,
    data_status_pill,
    friendly_error,
    get_active_theme,
    inject_theme,
    nexus_card,
    page_intro,
    sidebar_brand,
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
IS_REAL_DATA = False  # flip to True once the synthetic dataset is replaced

NAMES = {
    "linear_regression": "Linear regression",
    "random_forest": "Random forest",
    "svr": "Support vector regression",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "catboost": "CatBoost",
    "empirical_baseline": "Simple look-up rule (baseline)",
}

st.set_page_config(page_title="Model Benchmark - NEXUS", page_icon=None, layout="wide")
inject_theme()
sidebar_brand()
require_backend()
t = PALETTES[get_active_theme()]

st.markdown(
    """
    <div class="nexus-eyebrow">Model Lab</div>
    <h1 style="margin-top:4px;">How trustworthy is the engine?</h1>
    """,
    unsafe_allow_html=True,
)
page_intro(
    "Compares several prediction methods against a simple rule of thumb, so you can see whether the AI "
    "genuinely beats what a researcher could do by looking values up.",
    "If you only care about your own formulation, go to 'Release Predictor'. This page is mainly for "
    "judging how far to trust the engine, and for your methods section.",
)

pill = data_status_pill(IS_REAL_DATA)
data_note = (
    "These scores come from synthetic practice data. They show that the testing machinery works; they "
    "are not evidence that the engine predicts real fertilizers well."
    if not IS_REAL_DATA
    else "These scores come from published experimental data."
)
nexus_card(
    f"""<div class="nexus-eyebrow">What the scores are based on</div>{pill}
    <p style="color:{t['text_secondary']}; font-size:0.9rem; margin-top:8px;">{data_note}</p>"""
)

try:
    resp = httpx.get(f"{API_BASE_URL}/dataset/models/leaderboard", timeout=15)
    if resp.status_code == 503:
        nexus_card(
            """<div class="nexus-eyebrow">Not trained yet</div>
            <p>The engine has not been trained, so there are no scores to show. Ask whoever runs the system to train it.</p>"""
        )
        st.stop()
    resp.raise_for_status()
    leaderboard = resp.json()
except Exception:
    friendly_error(
        what="We could not load the model scores.",
        why="The prediction server did not respond correctly.",
        next_step="Make sure the backend is running and the model has been trained, then reload this page.",
    )
    st.stop()

df = pd.DataFrame(leaderboard).T
baseline = df.loc["empirical_baseline"] if "empirical_baseline" in df.index else None
models = df.drop(index="empirical_baseline", errors="ignore").sort_values("r2", ascending=False)

best_key = models.index[0]
best = models.iloc[0]
best_pct = max(best["r2"], 0) * 100

if baseline is not None:
    base_pct = max(baseline["r2"], 0) * 100
    beats = best["r2"] > baseline["r2"]
    compare = (
        f"A simple look-up rule (average of similar past cases) explains about {base_pct:.0f}%. "
        + ("The engine does clearly better." if beats and best["r2"] - baseline["r2"] > 0.05
           else "The engine is not clearly better than the simple rule, so it adds little here.")
    )
else:
    compare = ""

nexus_card(
    f"""<div class="nexus-eyebrow">The short answer</div>
    <div style="font-size:1.4rem; font-weight:800; color:{t['green']};">Best method: {NAMES.get(best_key, best_key)}</div>
    <p style="font-size:1rem; line-height:1.55; margin-top:8px;">On cases it had not seen during training, it explains
    about <strong>{best_pct:.0f}%</strong> of the differences in release speed. {compare}</p>
    <p style="color:{t['text_secondary']}; font-size:0.82rem; margin-top:8px;">
    Every score here is measured on held-out data: each method is repeatedly trained on part of the data and
    tested on rows it never saw.</p>"""
)

st.markdown("##### Accuracy of each method")
plot_df = pd.DataFrame(
    {
        "Method": [NAMES.get(k, k) for k in df.index],
        "Accuracy": [max(float(v), 0.0) * 100 for v in df["r2"]],
        "Kind": ["Baseline" if k == "empirical_baseline" else "AI model" for k in df.index],
    }
)
order = plot_df.sort_values("Accuracy", ascending=False)["Method"].tolist()
chart = (
    alt.Chart(plot_df)
    .mark_bar(cornerRadiusEnd=6, height=22)
    .encode(
        y=alt.Y("Method:N", sort=order, title=None),
        x=alt.X("Accuracy:Q", title="Share of differences explained (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color(
            "Kind:N",
            scale=alt.Scale(domain=["AI model", "Baseline"], range=[t["green"], t["text_secondary"]]),
            legend=alt.Legend(title=None, orient="bottom"),
        ),
        tooltip=["Method", alt.Tooltip("Accuracy:Q", format=".1f")],
    )
    .properties(height=max(200, 38 * len(plot_df)), background="transparent")
    .configure_axis(labelColor=t["text_secondary"], titleColor=t["text_secondary"], gridColor=t["border"], domainColor=t["border"])
    .configure_legend(labelColor=t["text_secondary"])
    .configure_view(strokeWidth=0)
)
st.altair_chart(chart, theme=None)
st.caption("Longer bar = better. Grey is the simple look-up rule the AI has to beat.")

with st.expander("Full score table (for your methods section)"):
    table = df.copy()
    table.index = [NAMES.get(k, k) for k in table.index]
    rename = {
        "r2": "R² (higher is better)",
        "r2_std": "R² spread across folds",
        "rmse": "RMSE (lower is better)",
        "mae": "MAE (lower is better)",
        "mape": "MAPE %",
    }
    cols = [c for c in rename if c in table.columns]
    table = table[cols].rename(columns=rename).round(4)
    st.dataframe(table, width="stretch")
    st.caption(
        "R² is the share of variation explained. MAE and RMSE are average and root-mean-square errors in the "
        "release constant (per day). Scores come from k-fold cross-validation; when the dataset carries a paper "
        "identifier, folds are split by paper so results from one study never appear in both training and testing."
    )

n1, _, _ = st.columns([1, 1, 1])
if n1.button("Try the Release Predictor", key="to_predictor", width="stretch"):
    st.switch_page("pages/1_Release_Predictor.py")