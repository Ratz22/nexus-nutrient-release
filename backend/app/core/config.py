"""
Central config. Everything env-driven so the same code runs locally,
in Docker, and on any cloud host without edits.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ML-NanoFertRelease"
    API_V1_PREFIX: str = "/api/v1"

    # CORS — "global access" means any frontend origin can call this API.
    # Lock this down to your real frontend domain(s) before going public.
    CORS_ORIGINS: list[str] = ["*"]

    # Model artifacts
    MODEL_DIR: str = "models"
    ACTIVE_MODEL_NAME: str = "release_predictor_v1.joblib"

    # External APIs (all free-tier / no-key-required by default)
    SOILGRIDS_BASE_URL: str = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    NASA_POWER_BASE_URL: str = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    SEMANTIC_SCHOLAR_BASE_URL: str = "https://api.semanticscholar.org/graph/v1/paper/search"

    # Optional: only needed if you add higher-rate-limit literature search
    SEMANTIC_SCHOLAR_API_KEY: str | None = None

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
