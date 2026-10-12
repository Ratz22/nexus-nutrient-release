import io

import altair as alt
import httpx
import pandas as pd
import streamlit as st

from service_check import API_BASE_URL, connection_problem, explain_http_problem, require_backend
from theme import PALETTES, data_status_pill, friendly_error, get_active_theme, inject_theme, nexus_card, page_intro, sidebar_brand

TARGET = "release_constant_k"

FEATURE_INFO = {
    "particle_size_nm": ("Particle diameter", "nm", "Formulation"),
    "coating_material": ("Coating material", "category", "Formulation"),
    "nutrient_type": ("Nutrient", "category", "Formulation"),
    "nutrient_loading_pct": ("Nutrient loading", "% of particle mass", "Formulation"),
    "shell_thickness_nm": ("Coating thickness", "nm", "Formulation"),
    "ph": ("Soil pH", "pH units", "Soil"),
    "moisture_pct": ("Soil moisture", "%", "Soil"),
    "temperature_c": ("Temperature", "°C", "Environment"),
    "organic_carbon_pct": ("Soil organic carbon", "%", "Soil"),
    "texture": ("Soil texture", "category", "Soil"),
    "salinity_ds_m": ("Soil salinity", "dS/m", "Soil"),
    "rainfall_mm": ("Rainfall", "mm per month", "Environment"),
    "humidity_pct": ("Humidity", "%", "Environment"),
    TARGET: ("Release constant k (target)", "per day", "Target"),
    "paper_id": ("Source paper identifier", "text", "Provenance"),
    "doi": ("DOI of source paper", "text", "Provenance"),
}

st.set_page_config(page_title="Dataset - NEXUS", page_icon=None, layout="wide")
inject_theme()
sidebar_brand()
t = PALETTES[get_active_theme()]

st.markdown(
    """
    <div class="nexus-eyebrow">Data</div>
    <h1 style="margin-top:4px;">The dataset behind the engine</h1>
    """,
    unsafe_allow_html=True,
)
page_intro(
    "Shows the data the prediction engine learns from: where it came from, what each column means, how the "
    "values are spread, and every row, with filters and export.",
    "Use 'Browse rows' to filter and download. Go to 'Release Predictor' to test the engine on new inputs.",
)

require_backend("dataset")


def _style(chart, height=260):
    return (
        chart.properties(height=height, background="transparent")
        .configure_axis(labelColor=t["text_secondary"], titleColor=t["text_secondary"],
                        gridColor=t["border"], domainColor=t["border"])
        .configure_view(strokeWidth=0)
    )


def _get(path: str):
    try:
        r = httpx.get(f"{API_BASE_URL}/dataset/{path}", timeout=60)
    except httpx.HTTPError:
        return None, connection_problem()
    if r.status_code == 200:
        return r, None
    return None, explain_http_problem(r)


info_resp, err = _get("info")
if err:
    friendly_error(what="The dataset could not be opened.", why=err[0], next_step=err[1])
    st.stop()
info = info_resp.json()

raw_resp, err = _get("raw")
if err:
    friendly_error(what="The dataset rows could not be loaded.", why=err[0], next_step=err[1])
    st.stop()
df = pd.read_csv(io.BytesIO(raw_resp.content))

nexus_card(
    f"""<div class="nexus-eyebrow">Where this data comes from</div>
    {data_status_pill(not info['is_synthetic'])}
    <p style="margin-top:10px;">{info['provenance']}</p>
    <p style="color:{t['text_secondary']}; font-size:0.85rem; margin-top:6px;">
    File: {info['file']} &nbsp;·&nbsp; {info['n_rows']} rows &nbsp;·&nbsp; {info['n_columns']} columns
    &nbsp;·&nbsp; {info['n_source_papers']} source papers</p>"""
)

k1, k2, k3, k4 = st.columns(4)
for col, (label, value) in zip((k1, k2, k3, k4), [
    ("Rows", f"{info['n_rows']:,}"),
    ("Input features", str(info["n_features"])),
    ("Source papers", str(info["n_source_papers"]) if info["n_source_papers"] else "None (synthetic)"),
    ("Median release constant k", f"{df[TARGET].median():.3f} per day"),
]):
    with col:
        nexus_card(f'<div class="nexus-eyebrow">{label}</div><div class="nexus-stat-value">{value}</div>')

tab_overview, tab_dist, tab_rows, tab_dict = st.tabs(["Overview", "Distributions", "Browse rows", "Feature dictionary"])

with tab_overview:
    st.markdown("##### How fast does release happen across the dataset?")
    hist = _style(
        alt.Chart(df).mark_bar(color=t["green"], opacity=0.85).encode(
            x=alt.X(f"{TARGET}:Q", bin=alt.Bin(maxbins=30), title="Release constant k (per day)"),
            y=alt.Y("count()", title="Rows"),
        ))
    st.altair_chart(hist, theme=None, width="stretch")
    st.caption("Each bar counts the rows whose release constant falls in that range. Higher k means faster release.")

    if "coating_material" in df.columns:
        st.markdown("##### Average release speed by coating")
        by_coat = df.groupby("coating_material")[TARGET].agg(["mean", "count"]).reset_index()
        bars = _style(
            alt.Chart(by_coat).mark_bar(color=t["green"], cornerRadiusEnd=6).encode(
                x=alt.X("coating_material:N", sort="-y", title="Coating"),
                y=alt.Y("mean:Q", title="Average k (per day)"),
                tooltip=["coating_material", alt.Tooltip("mean:Q", format=".3f"), "count"],
            ))
        st.altair_chart(bars, theme=None, width="stretch")

    col_a, col_b = st.columns(2)
    with col_a:
        if "nutrient_type" in df.columns:
            st.markdown("##### Rows per nutrient")
            st.dataframe(df["nutrient_type"].value_counts().rename_axis("Nutrient").reset_index(name="Rows"),
                         width="stretch", hide_index=True)
    with col_b:
        if "texture" in df.columns:
            st.markdown("##### Rows per soil texture")
            st.dataframe(df["texture"].value_counts().rename_axis("Texture").reset_index(name="Rows"),
                         width="stretch", hide_index=True)

with tab_dist:
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    labels = {c: FEATURE_INFO.get(c, (c, "", ""))[0] for c in numeric_cols}
    choice = st.selectbox("Choose a column", numeric_cols, format_func=lambda c: labels[c], key="dist_col")
    s = df[choice].dropna()
    m1, m2, m3, m4 = st.columns(4)
    for col, (lab, val) in zip((m1, m2, m3, m4), [
        ("Minimum", f"{s.min():.4g}"), ("Median", f"{s.median():.4g}"),
        ("Mean", f"{s.mean():.4g}"), ("Maximum", f"{s.max():.4g}"),
    ]):
        with col:
            nexus_card(f'<div class="nexus-eyebrow">{lab}</div><div class="nexus-stat-value">{val}</div>')
    dist = _style(
        alt.Chart(df[[choice]].dropna()).mark_bar(color=t["green"], opacity=0.85).encode(
            x=alt.X(f"{choice}:Q", bin=alt.Bin(maxbins=30), title=labels[choice]),
            y=alt.Y("count()", title="Rows"),
        ))
    st.altair_chart(dist, theme=None, width="stretch")

with tab_rows:
    f1, f2, f3 = st.columns(3)
    coat_pick = f1.multiselect("Coating", sorted(df["coating_material"].dropna().unique()) if "coating_material" in df else [])
    nut_pick = f2.multiselect("Nutrient", sorted(df["nutrient_type"].dropna().unique()) if "nutrient_type" in df else [])
    tex_pick = f3.multiselect("Soil texture", sorted(df["texture"].dropna().unique()) if "texture" in df else [])
    view = df.copy()
    if coat_pick:
        view = view[view["coating_material"].isin(coat_pick)]
    if nut_pick:
        view = view[view["nutrient_type"].isin(nut_pick)]
    if tex_pick:
        view = view[view["texture"].isin(tex_pick)]
    st.caption(f"Showing {len(view):,} of {len(df):,} rows.")
    pretty = view.rename(columns={c: FEATURE_INFO.get(c, (c,))[0] for c in view.columns})
    st.dataframe(pretty, width="stretch", hide_index=True, height=420)
    st.download_button("Download these rows as CSV", view.to_csv(index=False).encode("utf-8"),
                       file_name="nexus_dataset_filtered.csv", mime="text/csv", key="dl_rows")

with tab_dict:
    rows = []
    for col in df.columns:
        name, unit, group = FEATURE_INFO.get(col, (col, "", "Other"))
        if pd.api.types.is_numeric_dtype(df[col]):
            seen = f"{df[col].min():.4g} to {df[col].max():.4g}"
        else:
            seen = ", ".join(sorted(map(str, df[col].dropna().unique()))[:8])
        rows.append({"Column": col, "Meaning": name, "Unit": unit, "Group": group, "Values seen": seen})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption("Values seen come from this file. A published dataset should also trace every value to a paper_id and DOI.")