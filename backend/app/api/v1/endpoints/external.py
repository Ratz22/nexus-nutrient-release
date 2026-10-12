from fastapi import APIRouter, HTTPException, Query

from app.services import nasa_power, soilgrids
from app.services.http_utils import UpstreamError
from app.services.literature import search_literature

router = APIRouter()


@router.get("/soil")
def get_soil(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180)):
    """Soil pH, organic carbon and texture for a location (ISRIC SoilGrids)."""
    try:
        return soilgrids.fetch_soil_properties(lat, lon)
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/weather")
def get_weather(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180)):
    """Rainfall, humidity and temperature averages for a location (NASA POWER)."""
    try:
        return nasa_power.fetch_environment(lat, lon)
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/literature")
def get_literature(
    q: str = Query(..., min_length=3, max_length=200),
    limit: int = Query(10, ge=1, le=25),
):
    """Published papers matching a query, with DOIs (OpenAlex, falling back to Crossref)."""
    try:
        return search_literature(q.strip(), limit)
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc