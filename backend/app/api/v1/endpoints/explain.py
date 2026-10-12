from fastapi import APIRouter, HTTPException

from app.ml.shap_explain import explain_prediction
from app.schemas.formulation import ExplanationResponse, PredictionRequest

router = APIRouter()


@router.post("/explain", response_model=ExplanationResponse)
def explain(payload: PredictionRequest):
    try:
        return explain_prediction(
            payload.formulation.model_dump(),
            payload.soil.model_dump(),
            payload.environment.model_dump(),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
