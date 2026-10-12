"""
ISRIC SoilGrids v2.0 (global soil maps, free, no key). Top-soil values at a point.
Conversions:
  phh2o  stored as pH x 10       -> pH
  soc    stored as dg/kg          -> % organic carbon (divide by 100)
  clay, sand  stored as g/kg      -> used only for the texture class
"""
from app.core.config import get_settings
from app.services.http_utils import UpstreamError, get_json

settings = get_settings()
PROPERTIES = ["phh2o", "soc", "clay", "sand"]


def _texture(sand, clay):
    if sand is None and clay is None:
        return None
    if clay is not None and clay > 400:
        return "clay"
    if sand is not None and sand > 500:
        return "sandy"
    return "loamy"


def fetch_soil_properties(lat: float, lon: float) -> dict:
    params = {"lon": lon, "lat": lat, "property": PROPERTIES, "depth": "0-5cm", "value": "mean"}
    data = get_json(settings.SOILGRIDS_BASE_URL, params=params, service="the ISRIC SoilGrids soil database")

    layers = {}
    for layer in data.get("properties", {}).get("layers", []):
        try:
            value = layer["depths"][0]["values"]["mean"]
        except (KeyError, IndexError, TypeError):
            continue
        if value is not None:
            layers[layer["name"]] = value

    if "phh2o" not in layers and "soc" not in layers:
        raise UpstreamError(
            "SoilGrids has no soil values for this location (it may be open water or outside coverage). "
            "Enter the values by hand."
        )

    result = {
        "ph": round(layers["phh2o"] / 10, 2) if "phh2o" in layers else None,
        "organic_carbon_pct": round(layers["soc"] / 100, 2) if "soc" in layers else None,
        "texture": _texture(layers.get("sand"), layers.get("clay")),
        "source": "ISRIC SoilGrids v2.0",
    }
    return {k: v for k, v in result.items() if v is not None}