import json
import os

import httpx
import pandas as pd
import streamlit as st
from service_check import require_backend
from theme import (
    PALETTES,
    base_feature,
    friendly_error,
    friendly_feature_name,
    get_active_theme,
    inject_theme,
    nexus_card,
    page_intro,
    sidebar_brand,
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Explainability - NEXUS", page_icon=None, layout="wide")
inject_theme()
sidebar_brand()
require_backend()
t = PALETTES[get_active_theme()]

st.markdown(
    """
    <div class="nexus-eyebrow">Research Lab</div>
    <h1 style="margin-top:4px;">What influenced this result?</h1>
    """,
    unsafe_allow_html=True,
)
page_intro(
    "Shows which of your inputs the model leaned on most when it made its estimate, and whether each "
    "one pushed the release faster or slower.",
    "Go back to 'Release Predictor' to change an input and compare, or open 'Report Export' to save "
    "this experiment as a PDF.",
)

payload = st.session_state.get("last_prediction")
if not payload:
    nexus_card(
        """<div class="nexus-eyebrow">Nothing to explain yet</div>
        <p>Run a prediction first, then come back here.</p>"""
    )
    if st.button("Go to Release Predictor", key="to_predictor", width="stretch"):
        st.switch_page("pages/1_Release_Predictor.py")
    st.stop()

# Fetch once per distinct prediction, so the page just shows the answer.
key = json.dumps(payload, sort_keys=True)
if st.session_state.get("explain_key") != key:
    try:
        with st.spinner("Working out what mattered most..."):
            resp = httpx.post(f"{API_BASE_URL}/explain", json=payload, timeout=60)
            resp.raise_for_status()
            st.session_state["explain_result"] = resp.json()
            st.session_state["explain_key"] = key
    except Exception:
        friendly_error(
            what="We could not work out what influenced this result.",
            why="The explanation service did not respond.",
            next_step="Make sure the backend is running and the model has been trained, then reload this page.",
        )
        st.stop()

result = st.session_state["explain_result"]
flat = {**payload["formulation"], **payload["soil"], **payload["environment"]}

# Group the model's internal pieces back into the inputs a researcher recognises
grouped: dict[str, float] = {}
for raw, val in result["feature_contributions"].items():
    base = base_feature(raw)
    grouped[base] = grouped.get(base, 0.0) + float(val)

ranked = sorted(grouped.items(), key=lambda kv: abs(kv[1]), reverse=True)
total = sum(abs(v) for _, v in ranked) or 1.0
top = ranked[:5]

lead_name, lead_val = ranked[0]
direction = "faster" if lead_val > 0 else "slower"
second = ranked[1] if len(ranked) > 1 else None

summary = (
    f"The biggest influence was <strong>{friendly_feature_name(lead_name).lower()}</strong>"
    f" (your value: {flat.get(lead_name)}). In the data the model learned from, a value like this "
    f"is associated with <strong>{direction}</strong> release."
)
if second:
    d2 = "faster" if second[1] > 0 else "slower"
    summary += (
        f" Next came <strong>{friendly_feature_name(second[0]).lower()}</strong> "
        f"(your value: {flat.get(second[0])}), associated with {d2} release."
    )

nexus_card(
    f"""<div class="nexus-eyebrow">The short version</div>
    <p style="font-size:1.02rem; line-height:1.6; margin-top:6px;">{summary}</p>
    <p style="color:{t['text_secondary']}; font-size:0.85rem; margin-top:10px;">
    These are patterns the model found in its training data. They are hints about what to test,
    not proof that one thing causes another.</p>"""
)

st.markdown("##### The five biggest influences")
for name, val in top:
    share = abs(val) / total * 100
    faster = val > 0
    color = t["green"] if faster else t["warning"]
    word = "tends to speed up release" if faster else "tends to slow release"
    st.markdown(
        f"""
        <div class="nexus-card" style="padding:16px 22px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:baseline; gap:12px; flex-wrap:wrap;">
                <div><span style="font-weight:700;">{friendly_feature_name(name)}</span>
                     <span style="color:{t['text_secondary']}; font-size:0.85rem;"> &nbsp;your value: {flat.get(name)}</span></div>
                <div style="color:{color}; font-weight:600; font-size:0.88rem;">{word}</div>
            </div>
            <div style="background:{t['border']}; border-radius:8px; height:9px; margin-top:10px;">
                <div style="background:{color}; width:{max(share, 2):.0f}%; height:9px; border-radius:8px;"></div>
            </div>
            <div style="color:{t['text_secondary']}; font-size:0.75rem; margin-top:5px;">about {share:.0f}% of the total influence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(
    "Green bars: inputs the model links with faster release. Amber bars: inputs it links with slower release. "
    "If you want a different release pace, the inputs at the top are the most promising ones to test in the lab."
)

with st.expander("Raw model numbers (for your methods section)"):
    table = pd.DataFrame(
        [{"Input": friendly_feature_name(n), "Your value": str(flat.get(n)), "Contribution to k": round(v, 5)} for n, v in ranked]
    )
    st.dataframe(table, width="stretch", hide_index=True)
    st.caption(
        "Contributions are SHAP values on the release-constant scale, summed across the encoded pieces of "
        f"each input. Baseline prediction: {round(result['base_value'], 4)}. SHAP describes what the model "
        "learned, not physical cause and effect."
    )

n1, n2, _ = st.columns([1, 1, 1])
if n1.button("Change inputs and compare", key="back_predictor", width="stretch"):
    st.switch_page("pages/1_Release_Predictor.py")
if n2.button("Download a summary report", key="to_report", width="stretch"):
    st.switch_page("pages/5_Report_Export.py")