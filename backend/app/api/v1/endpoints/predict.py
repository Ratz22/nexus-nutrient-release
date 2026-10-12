from fastapi import APIRouter, HTTPException

from app.ml.predict import predict_release
from app.schemas.formulation import PredictionRequest, PredictionResponse

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest):
    try:
        result = predict_release(
            payload.formulation.model_dump(),
            payload.soil.model_dump(),
            payload.environment.model_dump(),
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
