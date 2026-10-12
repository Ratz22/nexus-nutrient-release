import os

import httpx
import streamlit as st

from theme import PALETTES, data_status_pill, get_active_theme, hero_art, inject_theme, nexus_card, page_intro, sidebar_brand

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
IS_REAL_DATA = False  # flip to True once the synthetic dataset is replaced

st.set_page_config(page_title="NEXUS - Nutrient Release Intelligence", page_icon=None, layout="wide")
inject_theme()
sidebar_brand()
t = PALETTES[get_active_theme()]

left, right = st.columns([3, 2], vertical_alignment="center")
with left:
    st.markdown(
        f"""
        <div style="font-size:0.85rem; font-weight:700; color:{t['green']}; letter-spacing:0.1em; text-transform:uppercase;">
            NEXUS &nbsp;·&nbsp; Nutrient Release Intelligence
        </div>
        <h1 style="font-size:2.9rem; line-height:1.08; margin:10px 0 0 0;">
            Know how a nano-fertilizer will behave, before you make it.
        </h1>
        <p style="color:{t['text_secondary']}; font-size:1.08rem; max-width:560px; margin-top:14px; line-height:1.55;">
            NEXUS estimates how quickly a fertilizer releases its nutrients in your soil and climate,
            tells you how far to trust the answer, and explains what drove it.
        </p>
        """,
        unsafe_allow_html=True,
    )
    b1, b2, b3 = st.columns(3)
    if b1.button("Start a prediction", key="hero_predict", width="stretch"):
        st.switch_page("pages/1_Release_Predictor.py")
    if b2.button("Browse papers", key="hero_papers", width="stretch"):
        st.switch_page("pages/4_Research_Explorer.py")
    if b3.button("View the dataset", key="hero_dataset", width="stretch"):
        st.switch_page("pages/6_Synthetic_Dataset.py")
with right:
    hero_art(height=250)

st.markdown("<br>", unsafe_allow_html=True)
page_intro(
    "NEXUS is a planning tool for researchers. It helps you decide which nano-fertilizer designs are "
    "worth testing in the lab, so fewer experiments are wasted.",
    "Start a prediction, browse published papers, or view the dataset the engine learns from. "
    "Every page opens with a short note like this one saying what it is for.",
)

try:
    backend_ready = httpx.get(f"{API_BASE_URL}/dataset/models/leaderboard", timeout=5).status_code == 200
except httpx.HTTPError:
    backend_ready = False

status_text = (
    "The prediction engine is running and ready to use."
    if backend_ready
    else "The prediction engine is not running or has not been trained yet."
)
nexus_card(
    f"""
    <div class="nexus-eyebrow">System status</div>
    {data_status_pill(IS_REAL_DATA)}
    <p style="margin-top:10px;">{status_text}</p>
    <p style="color:{t['text_secondary']}; font-size:0.9rem; margin-top:4px;">
        The engine currently learns from synthetic practice data, not published experiments.
        The workflow is real, but the numbers are for demonstration only. Replacing that data with
        source-traceable experiments is the next milestone.
    </p>
    """
)

st.markdown("### Why this matters")
w1, w2, w3 = st.columns(3)
with w1:
    nexus_card(
        f"""<div class="nexus-eyebrow">The problem</div>
        <div style="font-weight:700; font-size:1.05rem;">Fertilizer is wasted</div>
        <p style="color:{t['text_secondary']}; font-size:0.9rem; margin-top:6px;">
        Conventional fertilizers can lose a large share of their nutrients to leaching, runoff and the air
        before crops use them. Controlled-release designs aim to match release to what plants need.</p>"""
    )
with w2:
    nexus_card(
        f"""<div class="nexus-eyebrow">The bottleneck</div>
        <div style="font-weight:700; font-size:1.05rem;">Testing is slow</div>
        <p style="color:{t['text_secondary']}; font-size:0.9rem; margin-top:6px;">
        Choosing a coating, particle size and loading usually means many weeks of trials, repeated for
        every soil and climate of interest.</p>"""
    )
with w3:
    nexus_card(
        f"""<div class="nexus-eyebrow">What NEXUS does</div>
        <div style="font-weight:700; font-size:1.05rem;">Shortlists before the lab</div>
        <p style="color:{t['text_secondary']}; font-size:0.9rem; margin-top:6px;">
        It estimates release for a design, flags inputs beyond what it knows, and shows what mattered most,
        so only the best candidates reach the bench.</p>"""
    )

st.markdown("### How it works")
h1, h2, h3 = st.columns(3)
steps = [
    ("1", "Describe", "Enter your nano-fertilizer and soil, upload a soil spreadsheet, or look the soil up by location."),
    ("2", "Predict", "Get a plain-language answer, a release curve, and a confidence level."),
    ("3", "Understand", "See what influenced the estimate, check the papers, and download a PDF report."),
]
for col, (num, title, text) in zip((h1, h2, h3), steps):
    with col:
        nexus_card(
            f"""<div style="display:flex; align-items:center; gap:12px;">
                <div style="width:34px; height:34px; border-radius:50%; background:{t['green_tint']};
                     color:{t['green']}; font-weight:800; display:flex; align-items:center; justify-content:center;">{num}</div>
                <div style="font-weight:700; font-size:1.05rem;">{title}</div></div>
                <p style="color:{t['text_secondary']}; font-size:0.9rem; margin-top:10px;">{text}</p>"""
        )

st.markdown("### Where the project stands")
r1, r2, r3 = st.columns(3)
roadmap = [
    ("Now", "Working prototype", "warning",
     "The full pipeline runs from input to report. It currently uses synthetic practice data."),
    ("Next", "Real experimental data", "green",
     "Published release experiments with a paper and DOI attached to every value, validated by holding out whole papers."),
    ("Then", "Lab validation", "green",
     "Test predictions against partner-lab experiments, and add a saved-experiment archive."),
]
for col, (tag, title, tone, text) in zip((r1, r2, r3), roadmap):
    with col:
        nexus_card(
            f"""<span class="nexus-pill" style="background-color:{t[tone + '_tint']}; color:{t[tone]};">{tag}</span>
            <div style="font-weight:700; font-size:1.05rem; margin-top:10px;">{title}</div>
            <p style="color:{t['text_secondary']}; font-size:0.9rem; margin-top:6px;">{text}</p>"""
        )

st.markdown(
    f"""<p style="color:{t['text_secondary']}; font-size:0.78rem; margin-top:24px;">
    Connected to prediction server at <code>{API_BASE_URL}</code></p>""",
    unsafe_allow_html=True,
)