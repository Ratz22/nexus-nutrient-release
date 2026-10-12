"""
This schema IS your dataset schema from the master reference doc,
turned into a validated API contract. Keep these two in sync —
whatever columns train.py trains on, this must accept.
"""
from pydantic import BaseModel, Field


class FormulationInput(BaseModel):
    particle_size_nm: float = Field(..., gt=0, description="Nanoparticle size, nm")
    coating_material: str = Field(..., description="e.g. chitosan, alginate, silica")
    nutrient_type: str = Field(..., description="e.g. N, P, K, Zn")
    nutrient_loading_pct: float = Field(..., ge=0, le=100)
    shell_thickness_nm: float = Field(..., gt=0)


class SoilInput(BaseModel):
    ph: float = Field(..., ge=0, le=14)
    moisture_pct: float = Field(..., ge=0, le=100)
    temperature_c: float
    organic_carbon_pct: float = Field(..., ge=0, le=100)
    texture: str = Field(..., description="e.g. sandy, loamy, clay")
    salinity_ds_m: float = Field(..., ge=0, description="Soil salinity, dS/m")


class EnvironmentInput(BaseModel):
    rainfall_mm: float = Field(..., ge=0)
    humidity_pct: float = Field(..., ge=0, le=100)


class PredictionRequest(BaseModel):
    formulation: FormulationInput
    soil: SoilInput
    environment: EnvironmentInput


class ReleasePoint(BaseModel):
    day: int
    release_pct: float
    release_pct_lower: float
    release_pct_upper: float


class PredictionResponse(BaseModel):
    model_used: str
    release_curve: list[ReleasePoint]
    release_constant_k: float
    raw_release_constant_k: float
    estimate_valid: bool
    release_constant_k_interval: tuple[float, float]
    predicted_r2_confidence: float
    domain_coverage: dict


class ExplanationResponse(BaseModel):
    model_used: str
    base_value: float
    feature_contributions: dict[str, float]
    top_drivers: list[str]