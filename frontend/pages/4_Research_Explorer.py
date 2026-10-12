import html

import httpx
import streamlit as st

from report_pdf import VERIFIED_SOURCES
from service_check import require_backend
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