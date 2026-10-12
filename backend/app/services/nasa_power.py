"""
NASA POWER long-term climate averages (free, no key).
PRECTOTCORR is mean daily precipitation (mm/day). The monthly figure is
approximated as 30.4 x the daily mean, and the UI labels it that way.
NASA POWER uses -999 for missing values.
"""
from app.core.config import get_settings
from app.services.http_utils import UpstreamError, get_json

settings = get_settings()
PARAMETERS = "PRECTOTCORR,RH2M,T2M"


def _value(block: dict, key: str):
    v = block.get(key, {}).get("ANN")
    if v is None or v <= -900:
        return None
    return float(v)


def fetch_environment(lat: float, lon: float) -> dict:
    params = {"parameters": PARAMETERS, "community": "AG", "longitude": lon, "latitude": lat, "format": "JSON"}
    data = get_json(settings.NASA_POWER_BASE_URL, params=params, service="the NASA POWER climate database")
    block = data.get("properties", {}).get("parameter", {})

    rain_day = _value(block, "PRECTOTCORR")
    humidity = _value(block, "RH2M")
    temperature = _value(block, "T2M")
    if rain_day is None and humidity is None and temperature is None:
        raise UpstreamError("NASA POWER returned no climate values for this location.")

    result = {
        "rainfall_mm": round(rain_day * 30.4, 1) if rain_day is not None else None,
        "humidity_pct": round(humidity, 1) if humidity is not None else None,
        "temperature_c": round(temperature, 1) if temperature is not None else None,
        "source": "NASA POWER climatology",
    }
    return {k: v for k, v in result.items() if v is not None}