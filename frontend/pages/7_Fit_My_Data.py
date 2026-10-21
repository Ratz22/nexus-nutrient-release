"""Fit your own lab release data to standard kinetic models (calls POST /fit on the backend)."""
import io
import os

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")  # change if your backend prefix differs

NAMES = {
    "first_order": "Steady fade-out (first-order)",
    "higuchi": "Diffusion-controlled (Higuchi)",
    "korsmeyer_peppas": "Mixed diffusion + swelling (Korsmeyer-Peppas)",
    "weibull": "Flexible S-shaped curve (Weibull)",
}
SAMPLE = "time_days,release_pct\n1,12\n2,22\n4,38\n7,55\n10,66\n14,78\n21,88\n28,93"

st.title("Fit your own lab results")
st.caption("Paste or upload time (days) and % released. We fit four standard release models and show which describes your data best.")

up = st.file_uploader("CSV: time in days, release in %", type="csv")
text = st.text_area("...or paste here", value="" if up else SAMPLE, height=170)
try:
    df = pd.read_csv(up if up else io.StringIO(text)).iloc[:, :2].apply(pd.to_numeric, errors="coerce").dropna()
except Exception as e:
    st.error(f"Could not read that data: {e}"); st.stop()
df.columns = ["t", "y"]

try:
    r = requests.post(f"{API}/fit", json={"time_days": df.t.tolist(), "release_pct": df.y.tolist()}, timeout=30)
except requests.RequestException:
    st.error(f"Backend not reachable at {API}. Start it, or set API_BASE_URL."); st.stop()
if r.status_code != 200:
    st.error(r.json().get("detail", "Fit failed.")); st.stop()

res = r.json()
best = res.get("best_model")
if not best:
    st.error("No model fit this data. Check units and that release rises with time."); st.stop()
t80 = res.get("t80_days")
st.success(f"Best fit: {NAMES[best]} · R² = {res['fits'][best]['r2']:.3f} · "
           f"80% released at {'about %.1f days' % t80 if t80 else 'beyond the model range'}")

fig = go.Figure(go.Scatter(x=df.t, y=df.y, mode="markers", name="Your data", marker=dict(size=9)))
for name, c in res["curves"].items():
    fig.add_trace(go.Scatter(x=c["t"], y=c["y"], name=NAMES[name], line=dict(width=4 if name == best else 1.5)))
fig.update_layout(height=420, xaxis_title="Days", yaxis_title="Released (%)", yaxis_range=[0, 105])
st.plotly_chart(fig)

table = pd.DataFrame([{"Model": NAMES[k], "R²": v.get("r2"), "AIC (lower = better)": v.get("aic"),
                       "Parameters": str(v.get("params", v.get("error")))} for k, v in res["fits"].items()])
st.dataframe(table, hide_index=True)
st.caption(res["disclaimer"])