"""
NanoFert data pack: download the primary datasets that have real downloadable files,
profile them (sheets/columns/rows) so we can map them to one schema, and write a
manual-entry template for papers whose data lives only in tables/figures.

Run:  pip install requests pandas openpyxl
      python scripts/fetch_datasets.py   (run from the repo root)
Outputs: data/raw/ (files), profile_report.md, manual_entry_template.csv
"""
import re
import sys
from pathlib import Path

import pandas as pd
import requests

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "NanoFert-research-pipeline/0.1 (academic project)"}

SOURCES = {
    "plos_pcu_2020": {
        "doi": "10.1371/journal.pone.0234544",
        "landing": "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0234544",
        "file": "https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0234544.s001",
        "license": "CC BY 4.0",
        "dest": RAW / "plos_pcu_2020_S1_Data.xlsx",
    },
    "bath_zn_beads_2023": {
        "doi": "10.15125/BATH-01224",
        "landing": "https://researchdata.bath.ac.uk/1224/",
        "file": None,  # scraped from landing page
        "license": "CC BY 4.0 (stated for the STL file; confirm on the xlsx entry)",
        "dest": RAW / "bath_zn_beads_2023.xlsx",
    },
}
ZENODO_RECORD = "23161934"  # cellulose-ether slow-release fertilizer; content UNVERIFIED


def download(url, dest):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    dest.write_bytes(r.content)
    print(f"  saved {dest} ({len(r.content)/1024:.0f} KB)")
    return dest


def fetch_plos(src):
    return download(src["file"], src["dest"])


def fetch_bath(src):
    html = requests.get(src["landing"], headers=HEADERS, timeout=60).text
    links = re.findall(r'href="([^"]+\.xlsx[^"]*)"', html, flags=re.I)
    if not links:
        raise RuntimeError("No .xlsx link found on landing page")
    url = links[0]
    if url.startswith("/"):
        url = "https://researchdata.bath.ac.uk" + url
    return download(url, src["dest"])


def fetch_zenodo(record_id):
    meta = requests.get(f"https://zenodo.org/api/records/{record_id}", headers=HEADERS, timeout=60)
    meta.raise_for_status()
    m = meta.json()
    print("  Zenodo title:", m.get("metadata", {}).get("title"))
    print("  Zenodo license:", m.get("metadata", {}).get("license"))
    out = []
    for f in m.get("files", []):
        name = f.get("key") or f.get("filename")
        url = f.get("links", {}).get("self")
        if name and url:
            out.append(download(url, RAW / f"zenodo_{record_id}_{name}"))
    return out


def profile_excel(path, report):
    xl = pd.ExcelFile(path)
    report.append(f"\n## {path.name}\n")
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        report.append(f"### Sheet `{sheet}` - {df.shape[0]} rows x {df.shape[1]} cols\n")
        report.append("Columns: " + ", ".join(map(str, df.columns)) + "\n")
        report.append("```\n" + df.head(8).to_string() + "\n```\n")


TEMPLATE_COLS = [
    "source_id", "doi", "figure_or_table", "extraction_method",  # table / WebPlotDigitizer / author-supplied
    "fertilizer_material", "carrier_or_coating", "nanoscale", "particle_size_nm",
    "nutrient", "medium", "soil_type", "soil_pH", "temperature_C",
    "time_days", "cumulative_release_pct", "replicate_or_sd", "license", "notes",
]


def main():
    report = ["# Dataset profile report\n"]
    for key, fn in [("plos_pcu_2020", fetch_plos), ("bath_zn_beads_2023", fetch_bath)]:
        src = SOURCES[key]
        print(f"[{key}] {src['doi']}")
        try:
            path = fn(src)
            profile_excel(path, report)
        except Exception as e:
            print(f"  FAILED: {e}\n  -> download manually from {src['landing']} into {src['dest']}")
    print(f"[zenodo {ZENODO_RECORD}] (unverified candidate)")
    try:
        for p in fetch_zenodo(ZENODO_RECORD):
            if p.suffix.lower() in (".xlsx", ".xls"):
                profile_excel(p, report)
    except Exception as e:
        print(f"  FAILED: {e}")

    Path("profile_report.md").write_text("\n".join(report), encoding="utf-8")
    pd.DataFrame(columns=TEMPLATE_COLS).to_csv("manual_entry_template.csv", index=False)
    print("\nWrote profile_report.md and manual_entry_template.csv")


if __name__ == "__main__":
    sys.exit(main())