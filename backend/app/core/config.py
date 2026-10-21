from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# Project root = the folder that contains backend/, models/, data/
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    PROJECT_NAME: str = "ML-NanoFertRelease"
    API_V1_PREFIX: str = "/api/v1"

    # Local development: the Streamlit frontend runs on another port, so CORS must allow it.
    # Before any public deployment, replace this with your real frontend domain.
    CORS_ORIGINS: list[str] = ["*"]

    # Absolute paths, so the server finds files no matter which folder you start it from.
    MODEL_DIR: str = str(PROJECT_ROOT / "models")
    ACTIVE_MODEL_NAME: str = "release_predictor_v1.joblib"

    DATASET_PATH: str = str(PROJECT_ROOT / "data" / "processed" / "dataset.csv")

    SOILGRIDS_BASE_URL: str = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    NASA_POWER_BASE_URL: str = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    OPENALEX_BASE_URL: str = "https://api.openalex.org/works"
    CROSSREF_BASE_URL: str = "https://api.crossref.org/works"

    # Optional. OpenAlex and Crossref give identified clients a more reliable service.
    # Add to a .env file as:  CONTACT_EMAIL=you@university.edu
    CONTACT_EMAIL: str | None = None

    HTTP_TIMEOUT_S: float = 30.0
    HTTP_RETRIES: int = 1

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()