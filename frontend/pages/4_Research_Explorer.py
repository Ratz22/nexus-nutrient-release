import html

import httpx
import streamlit as st
import json
from pathlib import Path

import pandas as pd
from report_pdf import VERIFIED_SOURCES

from service_check import API_BASE_URL, connection_problem, explain_http_problem
from theme import PALETTES, friendly_error, get_active_theme, inject_theme, nexus_card, page_intro, sidebar_brand

st.set_page_config(page_title="Research Explorer - NEXUS", page_icon=None, layout="wide")
inject_theme()
sidebar_brand()
t = PALETTES[get_active_theme()]

st.markdown(
    """
    <div class="nexus-eyebrow">Research Library</div>
    <h1 style="margin-top:4px;">Find published research</h1>
    """,
    unsafe_allow_html=True,
)
page_intro(
    "Searches published papers through OpenAlex, with Crossref as a backup, so you can ground your ideas in "
    "verifiable sources. Results show real titles, authors, DOIs and citation counts. Nothing is AI-written.",
    "Found a useful paper? Open its DOI to read it, then test the idea in 'Release Predictor'.",
)

c1, c2 = st.columns([4, 1])
query = c1.text_input("Search topic", placeholder="e.g. chitosan nitrogen controlled release",
                      label_visibility="collapsed", key="lit_query")
limit = c2.selectbox("Results", [5, 10, 15, 25], index=1, label_visibility="collapsed", key="lit_limit")

if st.button("Search papers", key="lit_search", type="primary"):
    q = query.strip()
    if len(q) < 3:
        st.session_state["lit_results"] = {"q": q, "error": ("Type at least three characters to search.", "")}
    else:
        try:
            with st.spinner("Searching published literature..."):
                resp = httpx.get(f"{API_BASE_URL}/literature", params={"q": q, "limit": limit}, timeout=150)
            if resp.status_code == 200:
                st.session_state["lit_results"] = {"q": q, "papers": resp.json()}
            else:
                st.session_state["lit_results"] = {"q": q, "error": explain_http_problem(resp)}
        except httpx.HTTPError:
            st.session_state["lit_results"] = {"q": q, "error": connection_problem()}

res = st.session_state.get("lit_results")


def _card(p: dict, badge: str, note: str = ""):
    title = html.escape(p.get("title") or "Untitled")
    url = html.escape(p.get("url") or f"https://doi.org/{p.get('doi', '')}")
    authors_list = p.get("authors") or []
    authors = html.escape(", ".join(authors_list[:6]) + (" et al." if len(authors_list) > 6 else "")) or "Authors listed at the DOI"
    venue = html.escape(p.get("venue") or "Venue listed at the DOI")
    year = html.escape(str(p.get("year") or "n.d."))
    cites = p.get("citations")
    cite_txt = f" &nbsp;·&nbsp; cited {cites} times" if cites is not None else ""
    doi = html.escape(p.get("doi") or "no DOI listed")
    abstract = p.get("abstract")
    abstract_html = (
        f'<details style="margin-top:10px;"><summary style="color:{t["green"]}; cursor:pointer; font-size:0.85rem;">'
        f'Read the abstract</summary><p style="color:{t["text_secondary"]}; font-size:0.88rem; margin-top:6px; line-height:1.55;">'
        f'{html.escape(abstract)}</p></details>'
        if abstract else ""
    )
    note_html = (f'<div style="color:{t["text_secondary"]}; font-size:0.8rem; margin-top:6px;">{note}</div>' if note else "")
    nexus_card(
        f"""<div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start;">
            <div style="font-weight:700; font-size:1.05rem; line-height:1.35;">
                <a href="{url}" target="_blank" style="color:{t['text']}; text-decoration:none;">{title}</a></div>
            <span class="nexus-pill nexus-pill-ready" style="white-space:nowrap;">{html.escape(badge)}</span></div>
        <div style="color:{t['text_secondary']}; font-size:0.85rem; margin-top:6px;">
            {authors} &nbsp;·&nbsp; {venue}, {year}{cite_txt}</div>
        <div style="color:{t['text_secondary']}; font-size:0.8rem; margin-top:4px;">DOI: {doi}</div>
        {note_html}{abstract_html}"""
    )


def _verified_section():
    st.markdown("##### Verified source studies")
    st.caption("These DOIs were checked for the planned literature dataset. They work without a live connection.")
    for item in VERIFIED_SOURCES:
        _card(
            {"title": item["title"], "authors": item["authors"], "year": item["year"],
             "venue": item["venue"], "doi": item["doi"], "url": f"https://doi.org/{item['doi']}"},
            badge="Verified DOI",
            note="Values are not yet extracted into the training data.",
        )


if res is None:
    nexus_card(
        f"""<div class="nexus-eyebrow">Try a search</div>
        <p style="color:{t['text_secondary']};">Examples: <em>chitosan nitrogen controlled release</em>,
        <em>silica coated urea nanoparticles</em>, <em>nano fertilizer release kinetics soil</em>.</p>"""
    )
    _verified_section()
elif res.get("error"):
    why, next_step = res["error"]
    friendly_error(
        what="Live paper search is unavailable right now.",
        why=why,
        next_step=(next_step + " " if next_step else "") + "The verified source studies below still work.",
    )
    _verified_section()
else:
    papers = res["papers"]
    st.markdown(f"**{len(papers)} papers** for “{html.escape(res['q'])}”")
    if not papers:
        nexus_card(
            """<div class="nexus-eyebrow">No papers found</div>
            <p>Try fewer or broader keywords, or a different spelling.</p>"""
        )
    for p in papers:
        _card(p, badge=p.get("source") or "Live")


# ── NEXUS Experimental Data Explorer ──────────────────────────
st.divider()
st.markdown("## Experimental Data Explorer")
st.caption(
    "Exploration of published nutrient-release measurements. "
    "These results are separate from the synthetic-data ML predictor."
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DIR = PROJECT_ROOT / "data" / "research"

observations_path = RESEARCH_DIR / "combined_real_release_observations.csv"
fits_path = RESEARCH_DIR / "combined_exploratory_kinetic_fits.csv"
audit_path = RESEARCH_DIR / "combined_dataset_audit.json"

if not observations_path.exists() or not fits_path.exists():
    st.warning(
        "Research files were not found in data/research. "
        "Copy the published-data CSV files into that folder."
    )
else:
    try:
        observations = pd.read_csv(observations_path)
        fits = pd.read_csv(fits_path)

        # Standardize the fields used in the interface.
        required = {
            "paper_id",
            "days_after_fertilization",
            "nitrogen_released_pct",
            "fertilizer_type",
        }
        missing = required - set(observations.columns)

        if missing:
            st.error(f"Observation file is missing columns: {sorted(missing)}")
        else:
            observations["days_after_fertilization"] = pd.to_numeric(
                observations["days_after_fertilization"], errors="coerce"
            )
            observations["nitrogen_released_pct"] = pd.to_numeric(
                observations["nitrogen_released_pct"], errors="coerce"
            )
            observations = observations.dropna(
                subset=["days_after_fertilization", "nitrogen_released_pct"]
            )

            # Summary statistics describe the available observations,
            # not independent model-validation performance.
            m1, m2, m3 = st.columns(3)
            m1.metric("Published observations", f"{len(observations):,}")
            m2.metric("Source studies", observations["paper_id"].nunique())
            m3.metric("Fertilizer labels", observations["fertilizer_type"].nunique())

            if audit_path.exists():
                with st.expander("Data provenance and limitations"):
                    with open(audit_path, encoding="utf-8") as f:
                        audit = json.load(f)

                    st.write(audit.get("purpose", ""))
                    for source in audit.get("sources", []):
                        st.markdown(
                            f"- **{source.get('paper_id', 'Unknown DOI')}** — "
                            f"{source.get('source', 'Source not specified')}: "
                            f"{source.get('rows', '?')} rows"
                        )

                    st.markdown("**Limitations recorded in the audit**")
                    for limitation in audit.get("critical_limitations", []):
                        st.markdown(f"- {limitation}")

            st.markdown("### Explore observed release")

            paper_options = sorted(
                observations["paper_id"].dropna().astype(str).unique()
            )
            selected_paper = st.selectbox(
                "Source study (DOI)",
                paper_options,
                key="exp_paper",
            )

            paper_data = observations[
                observations["paper_id"].astype(str) == selected_paper
            ].copy()

            fertilizer_options = sorted(
                paper_data["fertilizer_type"].dropna().astype(str).unique()
            )
            selected_fertilizer = st.selectbox(
                "Fertilizer formulation",
                fertilizer_options,
                key="exp_fertilizer",
            )

            curve_data = paper_data[
                paper_data["fertilizer_type"].astype(str) == selected_fertilizer
            ].copy()

            # Narrow to one experimental condition where these fields exist.
            condition_columns = [
                "experiment_id",
                "temperature_condition",
                "placement",
                "position_detail",
                "moisture_treatment",
            ]
            available_conditions = [
                c for c in condition_columns if c in curve_data.columns
            ]

            for col in available_conditions:
                values = sorted(
                    curve_data[col].fillna("Not specified").astype(str).unique()
                )
                if len(values) > 1:
                    selected_value = st.selectbox(
                        col.replace("_", " ").title(),
                        values,
                        key=f"exp_{col}",
                    )
                    curve_data = curve_data[
                        curve_data[col].fillna("Not specified").astype(str)
                        == selected_value
                    ]

            if curve_data.empty:
                st.info("No observations match this selection.")
            else:
                # Multiple replicate observations at the same time are
                # shown as a mean; raw rows remain in the CSV.
                plotted = (
                    curve_data.groupby("days_after_fertilization", as_index=False)
                    ["nitrogen_released_pct"]
                    .agg(["mean", "count"])
                    .reset_index()
                )

                plotted.columns = [
                    "days_after_fertilization",
                    "mean_release_pct",
                    "observation_count",
                ]
                plotted = plotted.sort_values("days_after_fertilization")

                st.line_chart(
                    plotted.set_index("days_after_fertilization")[
                        ["mean_release_pct"]
                    ],
                    y_label="Nitrogen released (%)",
                    x_label="Days after fertilization",
                )

                st.caption(
                    "The line shows the mean of available observations at each time "
                    "point for the selected conditions. It is not an ML prediction."
                )

                with st.expander("View plotted observations"):
                    st.dataframe(plotted, use_container_width=True)

                with st.expander("View source records"):
                    display_columns = [
                        c for c in [
                            "paper_id",
                            "source_doi",
                            "experiment_id",
                            "fertilizer_type",
                            "days_after_fertilization",
                            "nitrogen_released_pct",
                            "temperature_condition",
                            "placement",
                            "replicate_id",
                            "source_note",
                        ] if c in curve_data.columns
                    ]
                    st.dataframe(
                        curve_data[display_columns],
                        use_container_width=True,
                    )

            st.markdown("### Kinetic model comparison")
            st.caption(
                "Exploratory fits to observed curves. Fit statistics are not "
                "prediction scores on unseen experiments."
            )

            if "fit_status" in fits.columns:
                successful_fits = fits[
                    fits["fit_status"].astype(str).str.lower().eq("success")
                ].copy()
            else:
                successful_fits = fits.copy()

            metric_columns = [
                "paper_id",
                "fertilizer_type",
                "model",
                "n_timepoints",
                "r2_curve_fit",
                "rmse_pct_points",
                "mae_pct_points",
                "aic",
                "interpretation",
            ]
            metric_columns = [
                c for c in metric_columns if c in successful_fits.columns
            ]

            if metric_columns:
                if "paper_id" in successful_fits.columns:
                    successful_fits = successful_fits[
                        successful_fits["paper_id"].astype(str) == selected_paper
                    ]
                if "fertilizer_type" in successful_fits.columns:
                    successful_fits = successful_fits[
                        successful_fits["fertilizer_type"].astype(str)
                        == selected_fertilizer
                    ]

                st.dataframe(
                    successful_fits[metric_columns],
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "Download filtered fit results (CSV)",
                    data=successful_fits[metric_columns].to_csv(index=False),
                    file_name="nexus_filtered_kinetic_fits.csv",
                    mime="text/csv",
                )
            else:
                st.info("No recognized kinetic-fit metric columns were found.")

    except (OSError, ValueError, KeyError, pd.errors.ParserError) as exc:
        st.error(f"Could not load the experimental research data: {exc}")
