import os

import altair as alt
import httpx
import pandas as pd
import streamlit as st
from service_check import require_backend
from soil_upload import LABELS as SOIL_LABELS
from soil_upload import TEMPLATE_CSV, parse_soil_csv
from theme import (
    PALETTES,
    friendly_error,
    friendly_feature_name,
    get_active_theme,
    inject_theme,
    nexus_card,
    page_intro,
    sidebar_brand,
    verdict_card,
    verdict_content,
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
IS_REAL_DATA = False  # flip to True once the synthetic dataset is replaced
TEXTURES = ["sandy", "loamy", "clay"]
COATINGS = ["chitosan", "alginate", "silica", "starch", "PLA", "zeolite"]
NUTRIENTS = ["N", "P", "K", "Zn", "Fe", "Cu"]

st.set_page_config(page_title="Release Predictor - NEXUS", page_icon=None, layout="wide")
inject_theme()
sidebar_brand()
require_backend()
st.markdown(
    """
    <div class="nexus-eyebrow">Research Lab</div>
    <h1 style="margin-top:4px;">Release Predictor</h1>
    <p style="color:#6E6E73; max-width:720px;">
        Describe a nano-fertilizer and the soil it will sit in. NEXUS estimates how quickly
        the nutrient will be released, and tells you how far to trust the answer.
    </p>
    """,
    unsafe_allow_html=True,
)
page_intro(
    "Estimate how fast a nano-fertilizer releases its nutrient in a given soil and climate, "
    "before you spend weeks testing it in the lab.",
    "Fill in the three boxes and press Predict. Then open 'Explainability' to see what influenced "
    "the result, or 'Report Export' to download a PDF.",
)


def _bump():
    """Give every soil and weather widget fresh keys, so pre-filled values actually appear.
    Streamlit keeps a widget's value under its key and ignores new defaults for an existing key."""
    st.session_state["prefill_ver"] = st.session_state.get("prefill_ver", 0) + 1


def _fetch(path: str, lat: float, lon: float):
    """Returns (data, None) on success or (None, plain-language reason) on failure."""
    try:
        r = httpx.get(f"{API_BASE_URL}/{path}", params={"lat": lat, "lon": lon}, timeout=150)
    except httpx.HTTPError:
        return None, "the prediction server could not be reached. Is the backend running?"
    if r.status_code == 200:
        return r.json(), None
    try:
        return None, str(r.json().get("detail", "the service returned an error"))
    except ValueError:
        return None, "the service returned an error"


@st.dialog("Your result", width="large")
def show_result_dialog(content: dict):
    t = PALETTES[get_active_theme()]
    color = t[content["tone"]]

    def _days(d):
        if d is None:
            return None
        if d > 365:
            return ">365"
        return f"{d:.0f}" if d >= 10 else f"{d:.1f}"

    tiles = ""
    for value, label in ((_days(content["d50"]), "days to release half"),
                         (_days(content["d90"]), "days to release 90%")):
        if value is not None:
            tiles += (
                f'<div style="flex:1; min-width:130px; border:1px solid {t["border"]}; border-radius:18px; padding:16px;">'
                f'<div style="font-size:1.9rem; font-weight:800; color:{t["green"]};">{value}</div>'
                f'<div style="font-size:0.78rem; color:{t["text_secondary"]};">{label}</div></div>'
            )
    tiles += (
        f'<div style="flex:1; min-width:130px; border:1px solid {color}; border-radius:18px; padding:16px;">'
        f'<div style="font-size:1.9rem; font-weight:800; color:{color};">{content["confidence"]}</div>'
        f'<div style="font-size:0.78rem; color:{t["text_secondary"]};">confidence</div></div>'
    )
    caveat = (
        f'<p style="margin-top:14px; font-size:0.78rem; color:{t["text_secondary"]};">{content["caveat"]}</p>'
        if content["caveat"] else ""
    )
    st.markdown(
        f"""
        <div style="text-align:center; padding: 4px 6px 0 6px;">
            <div style="font-size:0.78rem; font-weight:600; letter-spacing:0.08em; text-transform:uppercase;
                        color:{t['text_secondary']};">The short answer</div>
            <div style="font-size:1.7rem; font-weight:800; color:{color}; line-height:1.2; margin-top:6px;">
                {content['headline']}
            </div>
            <p style="margin-top:12px; font-size:1rem; line-height:1.55;">{content['detail']}</p>
            <div style="display:flex; gap:12px; justify-content:center; margin-top:20px; flex-wrap:wrap;">{tiles}</div>
            <p style="margin-top:20px; font-size:0.95rem;"><strong>Suggested next step:</strong> {content['next_step']}</p>
            {caveat}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Got it", key="close_dialog", width="stretch"):
        st.rerun()


# ------------------------------------------------------------ prefill state
ver = st.session_state.get("prefill_ver", 0)
prefill = {**st.session_state.get("prefill_location", {}), **st.session_state.get("prefill_csv", {})}


def pv(field, default):
    return prefill.get(field, default)


def wk(name: str) -> str:
    return f"{name}_{ver}"


# ------------------------------------------------------------ step 1
with st.container(border=True):
    st.markdown("##### 1 · Your nano-fertilizer")
    f1, f2, f3 = st.columns(3)
    particle_size_nm = f1.number_input("Particle size (nm)", min_value=1.0, value=120.0,
                                       help="Diameter of a single particle, in nanometres.")
    coating_material = f2.selectbox("Coating material", COATINGS,
                                    help="The outer layer that slows down how fast the nutrient escapes.")
    nutrient_type = f3.selectbox("Nutrient", NUTRIENTS,
                                 help="The nutrient carried inside the particle (N = nitrogen, P = phosphorus, K = potassium).")
    f4, f5 = st.columns(2)
    nutrient_loading_pct = f4.slider("Nutrient loading (%)", 0.0, 100.0, 15.0,
                                     help="Share of the particle that is actual nutrient.")
    shell_thickness_nm = f5.number_input("Coating thickness (nm)", min_value=1.0, value=30.0,
                                         help="Thickness of the outer shell. Thicker shells usually release more slowly.")

# ------------------------------------------------------------ step 2
with st.container(border=True):
    st.markdown("##### 2 · Your soil")
    st.caption("Upload your lab spreadsheet, look the soil up from a location, or type values in directly.")
    up_col, loc_col = st.columns(2)

    with up_col:
        uploaded = st.file_uploader("Upload soil results (CSV)", type=["csv"], key="soil_csv_file",
                                    help="One row per sample. Several samples are averaged.")
        st.download_button("Download a blank template", TEMPLATE_CSV,
                           file_name="nexus_soil_template.csv", mime="text/csv", key="soil_template")

        if uploaded is not None:
            sig = f"{uploaded.name}-{uploaded.size}"
            if st.session_state.get("csv_sig") != sig:
                parsed = parse_soil_csv(uploaded.getvalue())
                st.session_state.update(
                    csv_sig=sig,
                    csv_report=parsed,
                    prefill_csv={} if parsed["error"] else parsed["values"],
                )
                _bump()
                st.rerun()
        elif st.session_state.get("csv_sig"):
            st.session_state.update(csv_sig=None, csv_report=None, prefill_csv={})
            _bump()
            st.rerun()

        report = st.session_state.get("csv_report")
        if report and report["error"]:
            friendly_error(
                what="We could not use that spreadsheet.",
                why=report["error"],
                next_step="Download the blank template, paste your values into it, and upload it again.",
            )
        elif report:
            found = ", ".join(SOIL_LABELS[f] for f in report["found"])
            st.success(f"Read {report['n_samples']} sample(s). Filled in: {found}.")
            if report["missing"]:
                st.info("Not in your file, so fill these in by hand: "
                        + ", ".join(SOIL_LABELS[f] for f in report["missing"]) + ".")
            for note in report["notes"]:
                st.warning(note)

    with loc_col:
        st.markdown("**Or look it up from a location**")
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude", value=23.2599, format="%.4f", key="lat")
        lon = c2.number_input("Longitude", value=77.4126, format="%.4f", key="lon")
        if st.button("Fetch soil and climate data", key="fetch_location", width="stretch"):
            with st.spinner("Asking the global soil and climate databases..."):
                soil, soil_err = _fetch("soil", lat, lon)
                weather, weather_err = _fetch("weather", lat, lon)
            merged, ok, problems = {}, [], []
            if soil:
                merged.update({k: soil[k] for k in ("ph", "organic_carbon_pct", "texture") if k in soil})
                ok.append("soil properties (ISRIC SoilGrids)")
            else:
                problems.append(f"Soil: {soil_err}")
            if weather:
                merged.update({k: weather[k] for k in ("rainfall_mm", "humidity_pct", "temperature_c") if k in weather})
                ok.append("climate averages (NASA POWER)")
            else:
                problems.append(f"Climate: {weather_err}")
            st.session_state.update(prefill_location=merged, fetch_report={"ok": ok, "problems": problems})
            _bump()
            st.rerun()

        fetch_report = st.session_state.get("fetch_report")
        if fetch_report:
            if fetch_report["ok"]:
                st.success("Filled in from " + " and ".join(fetch_report["ok"]) + ". Change anything you like.")
            for problem in fetch_report["problems"]:
                st.warning(problem)

    s1, s2, s3 = st.columns(3)
    ph = s1.slider("Soil pH", 0.0, 14.0, float(pv("ph", 6.5)), key=wk("ph"),
                   help="Acidity of the soil. 7 is neutral.")
    moisture_pct = s2.slider("Soil moisture (%)", 0.0, 100.0, float(pv("moisture_pct", 40.0)), key=wk("moisture"))
    temperature_c = s3.number_input("Temperature (°C)", value=float(pv("temperature_c", 25.0)), key=wk("temp"))
    s4, s5, s6 = st.columns(3)
    organic_carbon_pct = s4.number_input("Organic carbon (%)", value=float(pv("organic_carbon_pct", 1.2)),
                                         min_value=0.0, max_value=100.0, key=wk("oc"),
                                         help="Organic matter in the soil. It can hold on to nutrients.")
    texture_default = pv("texture", "loamy")
    texture = s5.selectbox("Soil texture", TEXTURES,
                           index=TEXTURES.index(texture_default) if texture_default in TEXTURES else 1,
                           key=wk("texture"), help="Sandy soils drain quickly; clay soils hold water.")
    salinity_ds_m = s6.number_input("Salinity (dS/m)", value=float(pv("salinity_ds_m", 0.5)),
                                    min_value=0.0, key=wk("salinity"))

# ------------------------------------------------------------ step 3
with st.container(border=True):
    st.markdown("##### 3 · Weather")
    e1, e2 = st.columns(2)
    rainfall_mm = e1.number_input("Rainfall (mm per month)", value=float(pv("rainfall_mm", 80.0)),
                                  min_value=0.0, key=wk("rain"),
                                  help="Monthly rainfall. Fetched values are approximated from long-term averages.")
    humidity_pct = e2.slider("Humidity (%)", 0.0, 100.0, float(pv("humidity_pct", 60.0)), key=wk("humid"))

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------ predict
if st.button("Predict release", type="primary", width="stretch", key="predict"):
    payload = {
        "formulation": {
            "particle_size_nm": particle_size_nm,
            "coating_material": coating_material,
            "nutrient_type": nutrient_type,
            "nutrient_loading_pct": nutrient_loading_pct,
            "shell_thickness_nm": shell_thickness_nm,
        },
        "soil": {
            "ph": ph,
            "moisture_pct": moisture_pct,
            "temperature_c": temperature_c,
            "organic_carbon_pct": organic_carbon_pct,
            "texture": texture,
            "salinity_ds_m": salinity_ds_m,
        },
        "environment": {"rainfall_mm": rainfall_mm, "humidity_pct": humidity_pct},
    }
    try:
        resp = httpx.post(f"{API_BASE_URL}/predict", json=payload, timeout=60)
        if resp.status_code == 503:
            friendly_error(
                what="The prediction engine has not been trained yet.",
                why="No trained model was found on the server.",
                next_step="Ask whoever runs the system to train the model, then try again.",
            )
        elif resp.status_code != 200:
            friendly_error(
                what="The prediction could not be completed.",
                why="The prediction server returned an error.",
                next_step="Check the backend terminal for the message, then press Predict again.",
            )
        else:
            st.session_state["last_prediction"] = payload
            st.session_state["last_result"] = resp.json()
            st.session_state["show_result_dialog"] = True
    except httpx.HTTPError:
        friendly_error(
            what="The prediction could not be completed.",
            why="The prediction server could not be reached.",
            next_step="Make sure the backend is running, then press Predict again.",
        )

# ------------------------------------------------------------ results
result = st.session_state.get("last_result")
if result:
    coverage = result.get("domain_coverage", {})
    risk = coverage.get("overall_risk", "UNKNOWN")
    flagged = [
        f"{friendly_feature_name(name)}: {info['value']}"
        for name, info in coverage.get("features", {}).items()
        if info.get("status") in ("borderline", "out_of_range", "unseen")
    ]
    valid = result.get("estimate_valid", True)
    content = verdict_content(result["release_constant_k"], result["predicted_r2_confidence"],
                              risk, flagged, IS_REAL_DATA, valid)

    if st.session_state.pop("show_result_dialog", False):
        show_result_dialog(content)

    st.markdown("### Result")
    verdict_card(result["release_constant_k"], result["predicted_r2_confidence"], risk, flagged,
                 IS_REAL_DATA, valid)

    if not valid:
        nexus_card(
            """<div class="nexus-eyebrow">No release curve</div>
            <p>A release curve is only drawn when the model produces a physically possible rate.
            Adjust the flagged inputs and predict again.</p>"""
        )
    else:
        st.markdown("##### How the nutrient is released over time")
        t = PALETTES[get_active_theme()]
        curve_df = pd.DataFrame(result["release_curve"])
        base = alt.Chart(curve_df).encode(x=alt.X("day:Q", title="Days after application"))
        band = base.mark_area(opacity=0.18, color=t["green"]).encode(
            y=alt.Y("release_pct_lower:Q", title="Nutrient released (%)", scale=alt.Scale(domain=[0, 100])),
            y2="release_pct_upper:Q",
        )
        line = base.mark_line(color=t["green"], strokeWidth=3).encode(y="release_pct:Q")
        guides = alt.Chart(pd.DataFrame({"y": [50, 90]})).mark_rule(
            strokeDash=[4, 4], color=t["text_secondary"], opacity=0.5
        ).encode(y="y:Q")
        chart = (
            (band + line + guides)
            .properties(height=320, background="transparent")
            .configure_axis(labelColor=t["text_secondary"], titleColor=t["text_secondary"],
                            gridColor=t["border"], domainColor=t["border"], tickColor=t["border"])
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(chart, theme=None)
        st.caption("Solid line: expected release. Shaded band: the range the estimate could plausibly "
                   "fall in, based on error on held-out data. Dashed lines mark 50% and 90%.")

    with st.expander("Technical details (for your methods section)"):
        k_lo, k_hi = result["release_constant_k_interval"]
        st.markdown(
            f"- **Model:** {result['model_used'].replace('_', ' ')}\n"
            f"- **Validation score (R²):** {result['predicted_r2_confidence']}\n"
            + (
                f"- **Release constant k:** {result['release_constant_k']} per day "
                f"(90% band {k_lo} to {k_hi}); release modelled as 100 × (1 − e^(−k·t))\n"
                if valid else
                f"- **Release constant k:** not valid. The model extrapolated to "
                f"{result.get('raw_release_constant_k')}, which is below zero.\n"
            )
            + f"- **Training rows behind the reliability check:** {coverage.get('n_training_rows', 'unknown')}"
        )
        rows = []
        for name, info in coverage.get("features", {}).items():
            rng = info.get("training_range")
            seen = ", ".join(info["training_categories"]) if info.get("training_categories") else ""
            rows.append({
                "Input": friendly_feature_name(name),
                "Your value": str(info["value"]),
                "Range in training data": f"{rng[0]:.3g} to {rng[1]:.3g}" if rng else seen,
                "Check": {"in_range": "Within range", "borderline": "Near the edge",
                          "out_of_range": "Outside range", "seen": "Seen before",
                          "unseen": "Never seen"}.get(info["status"], info["status"]),
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption(coverage.get("note", ""))

    st.markdown("##### Where to next?")
    n1, n2, _ = st.columns(3)
    if n1.button("See what influenced this result", key="go_explain", width="stretch"):
        st.switch_page("pages/2_Explainability.py")
    if n2.button("Download a PDF report", key="go_report", width="stretch"):
        st.switch_page("pages/5_Report_Export.py")