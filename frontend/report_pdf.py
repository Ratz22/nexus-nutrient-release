"""
NEXUS research report (PDF), built with ReportLab platypus so the layout
flows across pages. All user-supplied and API-supplied text is cleaned and
XML-escaped before it reaches a Paragraph, so nothing typed into the form
or returned by a literature service can inject markup.
"""
import io
import re
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from theme import friendly_feature_name, verdict_content

GREEN = colors.HexColor("#2F7D4A")
GREEN_LIGHT = colors.HexColor("#E8F5EC")
TEXT = colors.HexColor("#1D1D1F")
MUTED = colors.HexColor("#6E6E73")
LINE = colors.HexColor("#E5E5E7")
PANEL = colors.HexColor("#F5F5F7")
WARN = colors.HexColor("#B35C00")
WARN_LIGHT = colors.HexColor("#FFF4E5")
DANGER = colors.HexColor("#B3261E")
DANGER_LIGHT = colors.HexColor("#FBE9E7")

TONES = {
    "green": (GREEN, GREEN_LIGHT, "#2F7D4A"),
    "warning": (WARN, WARN_LIGHT, "#B35C00"),
    "danger": (DANGER, DANGER_LIGHT, "#B3261E"),
}

STATUS = {
    "in_range": ("Within range", "#2F7D4A"),
    "borderline": ("Near the edge", "#B35C00"),
    "out_of_range": ("Outside range", "#B3261E"),
    "seen": ("Seen in training", "#2F7D4A"),
    "unseen": ("Never seen", "#B3261E"),
}

NUTRIENT_NAMES = {"N": "nitrogen", "P": "phosphorus", "K": "potassium",
                  "Zn": "zinc", "Fe": "iron", "Cu": "copper"}

# Source studies named in data/raw/literature_template.csv. Fields that could
# not be confirmed from the publisher or search-indexed abstract say "see DOI".
VERIFIED_SOURCES = [
    {"title": "Preparation of NPK nanofertilizer based on chitosan nanoparticles and its effect on biophysical characteristics and growth of coffee in green house",
     "authors": ["Ngoc Minh Ha", "Thi Huyen Nguyen", "San-Lang Wang", "Anh Dzung Nguyen"],
     "year": "2019", "venue": "Research on Chemical Intermediates", "doi": "10.1007/s11164-018-3630-7"},
    {"title": "Urea-Lignin/Chitosan Nanocomposite as Slow-Release Nanofertilizer",
     "authors": [], "year": "2023", "venue": "ACS Agricultural Science & Technology",
     "doi": "10.1021/acsagscitech.2c00334"},
    {"title": "Coated NPK Fertilizer Based on Citric Acid-Crosslinked Chitosan/Alginate Encapsulant",
     "authors": [], "year": "see DOI", "venue": "Journal of Ecological Engineering",
     "doi": "10.12911/22998993/113418"},
]


def _c(text) -> str:
    """Make text safe for the built-in PDF fonts."""
    text = "" if text is None else str(text)
    for fancy, plain in {"\u2014": "-", "\u2013": "-", "\u2019": "'", "\u2018": "'",
                         "\u201c": '"', "\u201d": '"', "\u2212": "-", "\u00b7": "-",
                         "\u2022": "-", "\u00b2": "2", "\u00b0": " deg"}.items():
        text = text.replace(fancy, plain)
    return text.encode("latin-1", "replace").decode("latin-1")


def _fmt_val(v) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    return _c(v)


def _fmt_days(d) -> str:
    if d is None:
        return "n/a"
    if d > 365:
        return "over 1 year"
    return f"{d:.0f}" if d >= 10 else f"{d:.1f}"


def _styles() -> dict:
    return {
        "kicker": ParagraphStyle("kicker", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=GREEN),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=TEXT, spaceAfter=3),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=GREEN,
                             spaceBefore=14, spaceAfter=6, keepWithNext=1),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=TEXT),
        "bodybold": ParagraphStyle("bodybold", fontName="Helvetica-Bold", fontSize=9.5, leading=13.5, textColor=TEXT),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED),
        "italic": ParagraphStyle("italic", fontName="Helvetica-Oblique", fontSize=8, leading=11, textColor=MUTED),
        "kpi_val": ParagraphStyle("kpi_val", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=GREEN),
        "kpi_lab": ParagraphStyle("kpi_lab", fontName="Helvetica", fontSize=7.5, leading=10, textColor=MUTED),
        "ref": ParagraphStyle("ref", fontName="Helvetica", fontSize=8.2, leading=11, textColor=TEXT,
                              leftIndent=16, firstLineIndent=-16, spaceAfter=5),
    }


def _p(text, style):
    return Paragraph(escape(_c(text)), style)


def _decorate(canvas, doc, first: bool, note: str):
    w, h = A4
    canvas.saveState()
    if first:
        canvas.setFillColor(GREEN)
        canvas.rect(0, h - 14 * mm, w, 14 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(20 * mm, h - 9 * mm, "NEXUS  |  NUTRIENT RELEASE INTELLIGENCE")
    else:
        canvas.setStrokeColor(LINE)
        canvas.line(20 * mm, h - 13 * mm, w - 20 * mm, h - 13 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(20 * mm, h - 10 * mm, "NEXUS  |  Prototype prediction report")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(20 * mm, 12 * mm, _c(note))
    canvas.drawRightString(w - 20 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _verdict_box(v, width):
    fg, bg, _ = TONES[v["tone"]]
    s = _styles()
    head = ParagraphStyle("verdict_head", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=fg)
    body = [_p(v["headline"], head), Spacer(1, 4), _p(v["detail"], s["body"])]
    if v["speed_line"]:
        body += [Spacer(1, 3), _p(re.sub(r"<[^>]+>", "", v["speed_line"]), s["body"])]
    body += [Spacer(1, 4), _p(f"Confidence in this estimate: {v['confidence']}.   "
                              f"Suggested next step: {v['next_step']}", s["small"])]
    t = Table([[body]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 4, fg),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def _kpi_row(items, width):
    s = _styles()
    cells = [[Paragraph(f'<font color="{hexcolor}">{escape(_c(value))}</font>', s["kpi_val"]),
              _p(label, s["kpi_lab"])]
             for value, label, hexcolor in items]
    col = width / len(items)
    t = Table([cells], colWidths=[col] * len(items))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("GRID", (0, 0), (-1, -1), 4, colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _release_chart(curve, width):
    days = max(p["day"] for p in curve)
    d = Drawing(width, 210)
    lp = LinePlot()
    lp.x, lp.y, lp.width, lp.height = 40, 30, width - 60, 150
    lp.data = [
        [(p["day"], p["release_pct"]) for p in curve],
        [(p["day"], p["release_pct_lower"]) for p in curve],
        [(p["day"], p["release_pct_upper"]) for p in curve],
    ]
    lp.lines[0].strokeColor = GREEN
    lp.lines[0].strokeWidth = 2.2
    for i in (1, 2):
        lp.lines[i].strokeColor = MUTED
        lp.lines[i].strokeWidth = 0.8
        lp.lines[i].strokeDashArray = [3, 2]
    lp.xValueAxis.valueMin = 0
    lp.xValueAxis.valueMax = days
    lp.xValueAxis.valueSteps = list(range(0, days + 1, 5))
    lp.yValueAxis.valueMin = 0
    lp.yValueAxis.valueMax = 100
    lp.yValueAxis.valueSteps = [0, 25, 50, 75, 100]
    for ax in (lp.xValueAxis, lp.yValueAxis):
        ax.labels.fontName = "Helvetica"
        ax.labels.fontSize = 7
    d.add(lp)
    d.add(String(40, 190, "Cumulative nutrient release (%) against days after application",
                 fontName="Helvetica", fontSize=8, fillColor=MUTED))
    d.add(String(width - 20, 12, "days", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    return d


def _input_table(payload, width):
    s = _styles()
    items = []
    for block in ("formulation", "soil", "environment"):
        for k, val in payload[block].items():
            items.append((friendly_feature_name(k), _fmt_val(val)))
    rows = []
    for i in range(0, len(items), 2):
        left = items[i]
        right = items[i + 1] if i + 1 < len(items) else ("", "")
        rows.append([_p(left[0], s["small"]), _p(left[1], s["bodybold"]),
                     _p(right[0], s["small"]), _p(right[1], s["bodybold"])])
    t = Table(rows, colWidths=[width * 0.22, width * 0.28, width * 0.22, width * 0.28])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _reliability_table(coverage, width):
    s = _styles()
    rows = [[_p("Input", s["small"]), _p("Your value", s["small"]),
             _p("Range seen in training data", s["small"]), _p("Check", s["small"])]]
    for name, info in coverage.get("features", {}).items():
        rng = info.get("training_range")
        seen = info.get("training_categories")
        trained = f"{rng[0]:.3g} to {rng[1]:.3g}" if rng else (", ".join(seen) if seen else "")
        label, hexcolor = STATUS.get(info.get("status"), ("Not checked", "#6E6E73"))
        rows.append([
            _p(friendly_feature_name(name), s["body"]),
            _p(_fmt_val(info.get("value")), s["body"]),
            _p(trained, s["small"]),
            Paragraph(f'<font color="{hexcolor}"><b>{escape(label)}</b></font>', s["body"]),
        ])
    t = Table(rows, colWidths=[width * 0.25, width * 0.2, width * 0.35, width * 0.2])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _reference_block(index, item, style):
    authors = item.get("authors") or []
    author_txt = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
    parts = [item.get("title") or "Untitled"]
    if author_txt:
        parts.append(author_txt)
    venue_year = ", ".join(x for x in [item.get("venue"), str(item.get("year") or "")]
                           if x and x not in ("None", ""))
    if venue_year:
        parts.append(venue_year)
    if item.get("doi"):
        parts.append(f"doi:{item['doi']}")
    return Paragraph(escape(_c(f"[{index}] " + ". ".join(parts) + ".")), style)


def build_pdf(payload: dict, result: dict, is_real_data: bool = False, related: list | None = None) -> bytes:
    related = related or []
    s = _styles()
    width = A4[0] - 40 * mm
    buf = io.BytesIO()

    coverage = result.get("domain_coverage", {})
    risk = coverage.get("overall_risk", "UNKNOWN")
    flagged = [f"{friendly_feature_name(n)}: {i['value']}"
               for n, i in coverage.get("features", {}).items()
               if i.get("status") in ("borderline", "out_of_range", "unseen")]
    valid = result.get("estimate_valid", True)
    v = verdict_content(result["release_constant_k"], result["predicted_r2_confidence"],
                        risk, flagged, is_real_data, valid)
    f = payload["formulation"]
    nutrient = NUTRIENT_NAMES.get(f["nutrient_type"], f["nutrient_type"])
    note = ("Computational estimate, not a substitute for experimental validation. "
            + ("" if is_real_data else "Prototype: trained on synthetic data."))

    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=24 * mm, bottomMargin=20 * mm,
        title="NEXUS prototype prediction report", author="NEXUS",
    )
    story = [
        _p("PROTOTYPE PREDICTION REPORT", s["kicker"]),
        _p(f"{f['coating_material'].capitalize()}-coated {nutrient} nano-fertilizer, "
           f"{f['particle_size_nm']:g} nm", s["title"]),
        _p(f"Generated {datetime.now():%d %B %Y, %H:%M}   |   Model: "
           f"{result['model_used'].replace('_', ' ')}", s["small"]),
        Spacer(1, 12),
        _verdict_box(v, width),
        Spacer(1, 12),
    ]

    if valid:
        story.append(_kpi_row([
            (_fmt_days(v["d50"]), "days until half the nutrient is released", "#2F7D4A"),
            (_fmt_days(v["d90"]), "days until 90% is released", "#2F7D4A"),
            (v["confidence"], "confidence in this estimate", TONES[v["tone"]][2]),
        ], width))
        story.append(Paragraph("Release over time", s["h2"]))
        story.append(_release_chart(result["release_curve"], width))
        story.append(_p("Solid line: expected cumulative release. Dashed lines: uncertainty range "
                        "from held-out validation error.", s["italic"]))
    else:
        story.append(_p("No release curve is shown because the model did not produce a physically "
                        "possible release rate for these inputs.", s["body"]))

    story.append(Paragraph("Inputs used", s["h2"]))
    story.append(_input_table(payload, width))

    story.append(Paragraph("Reliability check", s["h2"]))
    story.append(_p(f"Overall training-domain risk: {risk}, compared with "
                    f"{coverage.get('n_training_rows', 'an unknown number of')} training rows.", s["body"]))
    story.append(Spacer(1, 6))
    story.append(_reliability_table(coverage, width))
    story.append(Spacer(1, 4))
    story.append(_p(coverage.get("note", ""), s["italic"]))

    if related:
        story.append(Paragraph("Related published literature", s["h2"]))
        story.append(_p("Live search results from OpenAlex and Crossref, ranked by relevance to this "
                        "formulation. Listing a paper does not mean it supports these results. Open each "
                        "DOI and verify before citing.", s["small"]))
        story.append(Spacer(1, 6))
        for i, item in enumerate(related, start=1):
            story.append(_reference_block(i, item, s["ref"]))

    story.append(Paragraph("Source studies in the NEXUS dataset template", s["h2"]))
    story.append(_p("Studies whose DOIs have been checked for the planned literature dataset. Their values "
                    "are not yet extracted into the training data.", s["small"]))
    story.append(Spacer(1, 6))
    for i, item in enumerate(VERIFIED_SOURCES, start=1):
        story.append(_reference_block(i, item, s["ref"]))

    story.append(Paragraph("Limitations", s["h2"]))
    limits = [
        "Computational predictions are not a substitute for experimental validation.",
        "The model describes patterns in its training data. It does not prove cause and effect.",
        "The reliability check compares one input at a time. Unusual combinations can still fall outside "
        "the region the model learned.",
    ]
    if not is_real_data:
        limits.insert(0, "This prototype was trained on synthetic data, not published experiments. "
                         "Treat every number as a demonstration of the workflow.")
    for item in limits:
        story.append(_p("-  " + item, s["body"]))

    doc.build(
        story,
        onFirstPage=lambda c, d: _decorate(c, d, True, note),
        onLaterPages=lambda c, d: _decorate(c, d, False, note),
    )
    return buf.getvalue()