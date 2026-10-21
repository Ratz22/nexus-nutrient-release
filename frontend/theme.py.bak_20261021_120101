"""
NEXUS design system, v4.

What's new vs v3:
  - Glass look: translucent cards + backdrop blur sitting on soft
    gradient "light blobs". Glass only reads as glass when there is
    something colourful behind it to blur, so the blobs are the point.
  - page_intro(): every page says what it is for and where to go next.
  - verdict_card(): a plain-language answer for non-ML scientists.
  - hero_art(): a small animated seedling + nanoparticle illustration.

Honest constraint (unchanged): Streamlit's native chrome is fixed by
.streamlit/config.toml at server start. The dark/light toggle repaints
everything we style ourselves; a couple of native internals (dropdown
panel, dataframe grid) stay on the config.toml theme.
"""
import math

import streamlit as st

PALETTES = {
    "light": {
        "bg": "#F5F5F7",
        "card": "#FFFFFF",
        "card_glass": "rgba(255,255,255,0.72)",
        "text": "#1D1D1F",
        "text_secondary": "#6E6E73",
        "border": "rgba(0,0,0,0.07)",
        "green": "#2F7D4A",
        "green_tint": "rgba(47,125,74,0.10)",
        "warning": "#B35C00",
        "warning_tint": "rgba(179,92,0,0.10)",
        "danger": "#B3261E",
        "danger_tint": "rgba(179,38,30,0.10)",
        "shadow": "rgba(0,0,0,0.05)",
        "shadow_hover": "rgba(47,125,74,0.18)",
        "input_bg": "#FFFFFF",
        "scrollbar": "#D1D1D6",
        "blob1": "rgba(47,125,74,0.16)",
        "blob2": "rgba(90,170,200,0.12)",
        "blob3": "rgba(214,190,90,0.10)",
    },
    "dark": {
        "bg": "#000000",
        "card": "#1C1C1E",
        "card_glass": "rgba(28,28,30,0.62)",
        "text": "#F5F5F7",
        "text_secondary": "#98989D",
        "border": "rgba(255,255,255,0.09)",
        "green": "#4CAF72",
        "green_tint": "rgba(76,175,114,0.14)",
        "warning": "#FFB454",
        "warning_tint": "rgba(255,159,10,0.14)",
        "danger": "#FF6B61",
        "danger_tint": "rgba(255,107,97,0.14)",
        "shadow": "rgba(0,0,0,0.5)",
        "shadow_hover": "rgba(76,175,114,0.28)",
        "input_bg": "#1C1C1E",
        "scrollbar": "#3A3A3C",
        "blob1": "rgba(76,175,114,0.22)",
        "blob2": "rgba(60,130,190,0.16)",
        "blob3": "rgba(200,170,60,0.10)",
    },
}


def get_active_theme() -> str:
    return st.session_state.get("nexus_theme", "light")


def _set_theme(name: str):
    st.session_state["nexus_theme"] = name


def _t() -> dict:
    return PALETTES[get_active_theme()]


def inject_theme():
    t = _t()
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        * {{
            transition: background-color 0.18s ease, color 0.18s ease,
                        border-color 0.18s ease, box-shadow 0.25s ease, transform 0.25s ease;
        }}

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        /* Soft light blobs behind everything: this is what the glass cards blur against */
        .stApp {{
            background-color: {t['bg']};
            background-image:
                radial-gradient(ellipse 55% 45% at 8% 6%, {t['blob1']} 0%, transparent 70%),
                radial-gradient(ellipse 50% 45% at 95% 20%, {t['blob2']} 0%, transparent 70%),
                radial-gradient(ellipse 60% 50% at 70% 100%, {t['blob3']} 0%, transparent 70%);
            background-attachment: fixed;
        }}

        [data-testid="stHeader"] {{ background-color: transparent !important; }}

        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: {t['scrollbar']}; border-radius: 10px; }}

        .block-container {{
            max-width: 1180px;
            margin: 0 auto;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }}

        h1, h2, h3, h4, h5 {{
            color: {t['text']} !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }}
        h1 {{ font-weight: 800 !important; letter-spacing: -0.03em; }}
        h3 {{ margin-top: 2.2rem !important; margin-bottom: 0.8rem !important; font-size: 1.15rem !important; }}

        p, span, label, .stMarkdown {{ color: {t['text']}; }}
        [data-testid="stCaptionContainer"] {{ color: {t['text_secondary']} !important; }}

        /* --- Sidebar (glass) --- */
        section[data-testid="stSidebar"] {{
            background-color: {t['card_glass']};
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border-right: 1px solid {t['border']};
        }}
        section[data-testid="stSidebar"] > div {{ padding-top: 1.2rem; }}

        [data-testid="stSidebarNav"] ul {{ padding: 0 10px; }}
        [data-testid="stSidebarNav"] li {{ margin-bottom: 2px; }}
        [data-testid="stSidebarNav"] a {{
            border-radius: 10px;
            padding: 8px 14px !important;
            font-weight: 500;
            color: {t['text']} !important;
        }}
        [data-testid="stSidebarNav"] a:hover {{ background-color: {t['green_tint']}; }}
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background-color: {t['green_tint']};
            font-weight: 600;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"] span {{ color: {t['green']} !important; }}

        /* --- Glass cards --- */
        .nexus-card {{
            background-color: {t['card_glass']};
            backdrop-filter: blur(16px) saturate(140%);
            -webkit-backdrop-filter: blur(16px) saturate(140%);
            border: 1px solid {t['border']};
            border-radius: 22px;
            padding: 24px 28px;
            margin-bottom: 16px;
            box-shadow: 0 2px 10px {t['shadow']};
        }}
        .nexus-card:hover {{
            box-shadow: 0 10px 34px {t['shadow_hover']};
            transform: translateY(-2px);
        }}

        .nexus-eyebrow {{
            color: {t['text_secondary']};
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 4px;
        }}
        .nexus-stat-value {{ color: {t['text']}; font-size: 1.6rem; font-weight: 700; }}
        .nexus-stat-label {{ color: {t['text_secondary']}; font-size: 0.85rem; }}

        .nexus-pill {{
            display: inline-block;
            padding: 3px 12px;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .nexus-pill-placeholder {{ background-color: {t['warning_tint']}; color: {t['warning']}; }}
        .nexus-pill-ready {{ background-color: {t['green_tint']}; color: {t['green']}; }}

        /* --- Glowing buttons --- */
        .stButton > button, .stDownloadButton > button {{
            background: linear-gradient(135deg, {t['green']} 0%, {t['green']} 100%);
            color: white;
            border-radius: 14px;
            border: none;
            font-weight: 600;
            padding: 0.6rem 1.3rem;
            box-shadow: 0 4px 14px {t['shadow_hover']};
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            filter: brightness(1.08);
            color: white;
            box-shadow: 0 6px 22px {t['shadow_hover']};
            transform: translateY(-1px);
        }}
        .stButton > button:active {{ transform: scale(0.98); }}

        /* --- Inputs --- */
        .stTextInput input, .stNumberInput input, .stTextArea textarea {{
            background-color: {t['input_bg']} !important;
            color: {t['text']} !important;
            border: 1px solid {t['border']} !important;
            border-radius: 12px !important;
        }}
        [data-baseweb="select"] > div {{
            background-color: {t['input_bg']} !important;
            border-color: {t['border']} !important;
            color: {t['text']} !important;
            border-radius: 12px !important;
        }}
        [data-testid="stSlider"] [role="slider"] {{ background-color: {t['green']} !important; }}
        [data-testid="stFileUploader"] section {{
            background-color: {t['card_glass']} !important;
            border: 1.5px dashed {t['green']} !important;
            border-radius: 16px !important;
        }}

        [data-testid="stExpander"] {{
            background-color: {t['card_glass']};
            border: 1px solid {t['border']};
            border-radius: 16px;
        }}
        hr {{ border-color: {t['border']} !important; }}

        /* --- Bordered input groups (st.container(border=True)) --- */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 22px !important;
            border-color: {t['border']} !important;
            background-color: {t['card_glass']};
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
        }}

        /* --- Result pop-up (st.dialog) --- */
        [data-testid="stDialog"] {{
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }}
        [data-testid="stDialog"] [role="dialog"] {{
            background-color: {t['card']} !important;
            border: 1px solid {t['border']};
            border-radius: 26px;
            box-shadow: 0 24px 80px {t['shadow_hover']};
        }}

        /* --- Hero art animation --- */
        @keyframes nexus-float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-9px); }}
        }}
        @keyframes nexus-pulse {{
            0%, 100% {{ opacity: 0.35; }}
            50% {{ opacity: 1; }}
        }}
        .nexus-float {{ animation: nexus-float 6s ease-in-out infinite; }}
        .nexus-dot {{ animation: nexus-pulse 3s ease-in-out infinite; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand():
    t = _t()
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 16px 14px 8px 14px; margin-top: 12px; border-top: 1px solid {t['border']};">
                <div style="font-weight:700; font-size:0.85rem; color:{t['green']}; letter-spacing:0.04em;">NEXUS</div>
                <div style="color:{t['text_secondary']}; font-size:0.72rem; margin-top:2px;">
                    Nutrient Release Intelligence · prototype
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        current = get_active_theme()
        label = "Switch to dark" if current == "light" else "Switch to light"
        if st.button(label, key="nexus_theme_toggle", width="stretch"):
            _set_theme("dark" if current == "light" else "light")
            st.rerun()


def page_intro(what_it_is: str, where_next: str):
    """Plain-language header every page opens with: what is this page for,
    and where should the reader go after it. Written for someone who has
    never heard of machine learning."""
    t = _t()
    st.markdown(
        f"""
        <div class="nexus-card" style="padding:16px 22px; background-color:{t['green_tint']};">
            <p style="margin:0; font-size:0.9rem;"><strong>What this page is for:</strong> {what_it_is}</p>
            <p style="margin:6px 0 0 0; font-size:0.85rem; color:{t['text_secondary']};"><strong>Where to go next:</strong> {where_next}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def release_speed_summary(k: float) -> dict:
    """Translate the release constant k (per day) into things a scientist
    thinks in: days to 50% / 90% release, and a speed label.
    First-order model: release(t) = 1 - exp(-k t)  =>  t_p = -ln(1-p)/k."""
    if not k or k <= 0:
        return {"d50": None, "d90": None, "speed": "unknown"}
    d50 = math.log(2) / k
    d90 = math.log(10) / k
    if d90 <= 14:
        speed = "fast"
    elif d90 <= 45:
        speed = "moderate"
    else:
        speed = "slow, sustained"
    return {"d50": d50, "d90": d90, "speed": speed}


def _fmt_days(d):
    if d is None:
        return "n/a"
    if d > 365:
        return "more than a year"
    return f"{d:.0f} days" if d >= 10 else f"{d:.1f} days"


def confidence_label(r2: float, risk: str) -> tuple[str, str]:
    """Combine how well the model validated (R2) with whether this input
    resembles its training data (risk) into one plain label.
    Returns (label, palette key). The weaker of the two signals wins."""
    if risk == "HIGH" or r2 < 0.5:
        return "Low", "danger"
    if risk in ("MODERATE", "UNKNOWN") or r2 < 0.8:
        return "Moderate", "warning"
    return "High", "green"


def verdict_content(k: float, r2: float, risk: str, flagged: list, is_real_data: bool = False,
                    estimate_valid: bool = True) -> dict:
    """All the words of the verdict in one place, so the card and the
    pop-up say exactly the same thing."""
    s = release_speed_summary(k) if estimate_valid else {"d50": None, "d90": None, "speed": "unknown"}
    label, tone = confidence_label(r2, risk)

    if not estimate_valid:
        label, tone = "Low", "danger"
        headline = "No usable estimate for this input"
        detail = (
            "The model's calculation went below zero, which is physically impossible. This happens when an "
            "input is far outside anything it has learned from"
            + (f" ({', '.join(flagged)})" if flagged else "")
            + "."
        )
        next_step = "Choose values closer to the range the model knows, or test this design in the lab instead."
    elif risk == "HIGH":
        headline = "Treat this result with caution"
        detail = (
            "This formulation uses values the model has rarely or never seen"
            + (f" ({', '.join(flagged)})" if flagged else "")
            + ". Read the numbers below as a rough guess, not a forecast."
        )
        next_step = "Run a small lab trial before relying on this estimate."
    elif risk == "MODERATE":
        headline = "A reasonable estimate, worth a lab check"
        detail = "Some inputs sit near the edge of what the model has learned from."
        next_step = "Use this to shortlist formulations, then confirm the best ones in the lab."
    elif risk == "UNKNOWN":
        headline = "Estimate available, reliability unchecked"
        detail = "The system could not compare this input with its training data."
        next_step = "Retrain the model to enable the reliability check."
    else:
        headline = "This formulation looks well within the model's experience"
        detail = "The inputs closely resemble the conditions the model learned from."
        next_step = "Good for planning. Confirm the final choice with a lab experiment."

    speed_line = ""
    if s["d90"] is not None:
        speed_line = (
            f"Expected release pace: <strong>{s['speed']}</strong>. About half of the nutrient "
            f"is released by <strong>{_fmt_days(s['d50'])}</strong> and about 90% by "
            f"<strong>{_fmt_days(s['d90'])}</strong>."
        )

    caveat = (
        ""
        if is_real_data
        else "Prototype notice: the model currently learns from synthetic practice data, "
        "not published experiments, so treat every number here as a demonstration."
    )
    return {
        "headline": headline,
        "detail": detail,
        "next_step": next_step,
        "speed_line": speed_line,
        "confidence": label,
        "tone": tone,
        "caveat": caveat,
        "d50": s["d50"],
        "d90": s["d90"],
    }


def verdict_card(k: float, r2: float, risk: str, flagged: list, is_real_data: bool = False,
                 estimate_valid: bool = True):
    """The first thing a non-ML scientist sees after a prediction."""
    t = _t()
    v = verdict_content(k, r2, risk, flagged, is_real_data, estimate_valid)
    color = t[v["tone"]]
    caveat_html = (
        f'<p style="margin-top:12px; font-size:0.78rem; color:{t["text_secondary"]};">{v["caveat"]}</p>'
        if v["caveat"] else ""
    )
    st.markdown(
        f"""
        <div class="nexus-card" style="border:1px solid {color}; padding:30px 32px;
             box-shadow: 0 12px 40px {t['shadow_hover']};">
            <div class="nexus-eyebrow">The short answer</div>
            <div style="font-size:1.5rem; font-weight:800; color:{color}; line-height:1.25;">{v['headline']}</div>
            <p style="margin-top:10px; font-size:0.97rem; line-height:1.55;">{v['detail']}</p>
            <p style="margin-top:8px; font-size:0.97rem; line-height:1.55;">{v['speed_line']}</p>
            <div style="display:flex; gap:28px; margin-top:16px; flex-wrap:wrap;">
                <div>
                    <div style="color:{t['text_secondary']}; font-size:0.75rem;">Confidence in this estimate</div>
                    <div style="color:{color}; font-weight:700; font-size:1.15rem;">{v['confidence']}</div>
                </div>
                <div>
                    <div style="color:{t['text_secondary']}; font-size:0.75rem;">Suggested next step</div>
                    <div style="font-weight:600; font-size:0.95rem;">{v['next_step']}</div>
                </div>
            </div>
            {caveat_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_art(height: int = 210):
    """Small agriculture-themed illustration: a seedling in soil with
    drifting nanoparticles and a soft glow. Pure inline SVG + CSS."""
    t = _t()
    g = t["green"]
    st.markdown(
        f"""
        <div class="nexus-float" style="display:flex; justify-content:center;">
        <svg viewBox="0 0 320 220" height="{height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Seedling with nutrient particles">
          <defs>
            <radialGradient id="glow" cx="50%" cy="55%" r="55%">
              <stop offset="0%" stop-color="{g}" stop-opacity="0.35"/>
              <stop offset="100%" stop-color="{g}" stop-opacity="0"/>
            </radialGradient>
            <linearGradient id="leaf" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="{g}" stop-opacity="0.95"/>
              <stop offset="100%" stop-color="{g}" stop-opacity="0.55"/>
            </linearGradient>
          </defs>
          <circle cx="160" cy="110" r="105" fill="url(#glow)"/>
          <path d="M60 178 Q160 150 260 178 L260 200 Q160 214 60 200 Z" fill="{g}" fill-opacity="0.22"/>
          <path d="M160 178 C160 150 158 128 160 100" stroke="{g}" stroke-width="4" fill="none" stroke-linecap="round"/>
          <path d="M160 128 C130 128 112 110 108 88 C134 88 156 100 160 128 Z" fill="url(#leaf)"/>
          <path d="M160 108 C190 106 208 88 212 66 C186 66 164 80 160 108 Z" fill="url(#leaf)"/>
          <circle class="nexus-dot" cx="86" cy="70" r="5" fill="{g}"/>
          <circle class="nexus-dot" cx="238" cy="104" r="4" fill="{g}" style="animation-delay:0.8s"/>
          <circle class="nexus-dot" cx="220" cy="40" r="3" fill="{g}" style="animation-delay:1.6s"/>
          <circle class="nexus-dot" cx="110" cy="150" r="3.5" fill="{g}" style="animation-delay:2.2s"/>
          <circle class="nexus-dot" cx="64" cy="118" r="2.5" fill="{g}" style="animation-delay:1.1s"/>
        </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )


FEATURE_LABELS = {
    "particle_size_nm": "Particle size",
    "shell_thickness_nm": "Shell thickness",
    "nutrient_loading_pct": "Nutrient loading",
    "ph": "Soil pH",
    "moisture_pct": "Soil moisture",
    "temperature_c": "Temperature",
    "organic_carbon_pct": "Soil organic carbon",
    "salinity_ds_m": "Soil salinity",
    "rainfall_mm": "Rainfall",
    "humidity_pct": "Humidity",
    "coating_material": "Coating material",
    "nutrient_type": "Nutrient type",
    "texture": "Soil texture",
}
_CATEGORICAL_BASES = ("coating_material", "nutrient_type", "texture")


def base_feature(raw: str) -> str:
    """'cat__coating_material_chitosan' -> 'coating_material'; 'num__ph' -> 'ph'."""
    name = raw.replace("num__", "").replace("cat__", "")
    for base in _CATEGORICAL_BASES:
        if name.startswith(base + "_"):
            return base
    return name


def friendly_feature_name(raw: str) -> str:
    return FEATURE_LABELS.get(base_feature(raw), base_feature(raw).replace("_", " ").capitalize())


def nexus_card(html: str):
    st.markdown(f'<div class="nexus-card">{html}</div>', unsafe_allow_html=True)


def data_status_pill(is_real_data: bool) -> str:
    if is_real_data:
        return '<span class="nexus-pill nexus-pill-ready">Peer-reviewed data</span>'
    return '<span class="nexus-pill nexus-pill-placeholder">Synthetic placeholder data</span>'


def friendly_error(what: str, why: str, next_step: str):
    t = _t()
    st.markdown(
        f"""
        <div class="nexus-card" style="border-left: 4px solid {t['warning']};">
            <div class="nexus-eyebrow" style="color:{t['warning']};">Something needs attention</div>
            <p style="margin:4px 0 2px 0;"><strong>What happened:</strong> {what}</p>
            <p style="margin:2px 0;"><strong>Why:</strong> {why}</p>
            <p style="margin:2px 0 0 0;"><strong>What you can do:</strong> {next_step}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )