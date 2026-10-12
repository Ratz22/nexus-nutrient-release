"""
Reads a lab soil spreadsheet (CSV) and turns it into the values the
Release Predictor form needs.

  - Column names are matched loosely ("pH", "Soil pH", "ph_h2o" all work).
  - Comma, semicolon and tab separators are detected. Semicolon files may
    use decimal commas, as many European labs export them.
  - Several samples are averaged, and the spread is reported.
  - Problems produce plain-language notes, never a traceback.

It does not read photos of soil. That needs a trained vision model.
"""
import io
import re

import pandas as pd

ALIASES = {
    "ph": "ph", "soilph": "ph", "phh2o": "ph", "phwater": "ph", "phcacl2": "ph",
    "moisture": "moisture_pct", "moisturepct": "moisture_pct", "soilmoisture": "moisture_pct",
    "watercontent": "moisture_pct", "vwc": "moisture_pct", "moisturecontent": "moisture_pct",
    "temperature": "temperature_c", "temp": "temperature_c", "tempc": "temperature_c",
    "temperaturec": "temperature_c", "soiltemperature": "temperature_c",
    "organiccarbon": "organic_carbon_pct", "oc": "organic_carbon_pct", "soc": "organic_carbon_pct",
    "organiccarbonpct": "organic_carbon_pct", "orgc": "organic_carbon_pct", "organicc": "organic_carbon_pct",
    "salinity": "salinity_ds_m", "ec": "salinity_ds_m", "salinitydsm": "salinity_ds_m",
    "electricalconductivity": "salinity_ds_m", "ecdsm": "salinity_ds_m",
    "texture": "texture", "soiltexture": "texture", "texturalclass": "texture", "textureclass": "texture",
}

LABELS = {
    "ph": "Soil pH",
    "moisture_pct": "Moisture (%)",
    "temperature_c": "Temperature (°C)",
    "organic_carbon_pct": "Organic carbon (%)",
    "salinity_ds_m": "Salinity (dS/m)",
    "texture": "Texture",
}

RANGES = {
    "ph": (0, 14),
    "moisture_pct": (0, 100),
    "organic_carbon_pct": (0, 100),
    "salinity_ds_m": (0, 100),
    "temperature_c": (-30, 70),
}

TEMPLATE_CSV = (
    "sample_id,pH,moisture_pct,temperature_c,organic_carbon_pct,salinity_ds_m,texture\n"
    "A1,6.4,38,24,1.3,0.4,loamy\n"
    "A2,6.7,42,24,1.1,0.5,loamy\n"
)


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _texture_from_text(value: str):
    v = str(value).lower()
    if "clay" in v:
        return "clay"
    if "sand" in v:
        return "sandy"
    if "loam" in v or "silt" in v:
        return "loamy"
    return None


def _read_table(file_bytes: bytes) -> pd.DataFrame:
    text = file_bytes.decode("utf-8-sig", errors="replace")
    first = text.splitlines()[0] if text.strip() else ""
    if first.count(";") > first.count(","):
        return pd.read_csv(io.StringIO(text), sep=";", decimal=",")
    if first.count("\t") > first.count(","):
        return pd.read_csv(io.StringIO(text), sep="\t")
    return pd.read_csv(io.StringIO(text))


def parse_soil_csv(file_bytes: bytes) -> dict:
    result = {"values": {}, "notes": [], "found": [], "missing": [], "n_samples": 0, "error": None}
    try:
        df = _read_table(file_bytes)
    except Exception:
        result["error"] = (
            "That file could not be read as a CSV spreadsheet. In Excel, choose "
            "'Save as' and then 'CSV (comma delimited)', and try again."
        )
        return result

    if df.empty:
        result["error"] = "The file has no data rows. Check that your samples sit below the header row."
        return result

    result["n_samples"] = len(df)

    column_map = {}
    for col in df.columns:
        field = ALIASES.get(_norm(col))
        if field and field not in column_map.values():
            column_map[col] = field

    unmatched = [c for c in df.columns
                 if c not in column_map and _norm(c) not in ("sampleid", "id", "sample", "name", "site")]
    if unmatched:
        result["notes"].append("Columns not used by the predictor: " + ", ".join(str(c) for c in unmatched) + ".")

    for col, field in column_map.items():
        if field == "texture":
            labels = [x for x in (_texture_from_text(v) for v in df[col].dropna()) if x]
            if not labels:
                result["notes"].append(f"No soil texture could be recognised in '{col}'. Use words like sandy, loamy or clay.")
                continue
            value = pd.Series(labels).mode().iloc[0]
            result["values"]["texture"] = value
            result["found"].append(field)
            if len(set(labels)) > 1:
                result["notes"].append(f"Samples mix several textures. Using the most common one ({value}).")
            continue

        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            result["notes"].append(f"'{col}' contains no readable numbers, so it was skipped.")
            continue
        lo, hi = RANGES[field]
        if ((series < lo) | (series > hi)).any():
            result["notes"].append(f"'{col}' has values outside the usual range {lo} to {hi}. Check the units.")
            series = series[(series >= lo) & (series <= hi)]
            if series.empty:
                continue
        mean = float(series.mean())
        result["values"][field] = round(mean, 3)
        result["found"].append(field)
        if len(series) > 1 and mean != 0 and float(series.std(ddof=0)) / abs(mean) > 0.25:
            result["notes"].append(
                f"{LABELS[field]} varies a lot between your samples (average {mean:.2f}). The prediction uses the average."
            )

    if result["values"].get("organic_carbon_pct", 0) > 15:
        result["notes"].append(
            "Organic carbon above 15% is unusual for mineral soils. If your lab reports g/kg, divide by 10."
        )

    result["missing"] = [f for f in LABELS if f not in result["values"]]
    if not result["values"]:
        result["error"] = (
            "None of the columns were recognised. Use headers such as pH, moisture, temperature, "
            "organic_carbon, salinity and texture, or download the template."
        )
    return result