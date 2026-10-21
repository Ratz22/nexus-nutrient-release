from fastapi import APIRouter

from app.api.v1.endpoints import dataset, explain, external, predict, fit

api_router = APIRouter()
api_router.include_router(predict.router, tags=["prediction"])
api_router.include_router(explain.router, tags=["explainability"])
api_router.include_router(external.router, tags=["external-data"])
api_router.include_router(dataset.router, prefix="/dataset", tags=["dataset"])
api_router.include_router(fit.router, tags=["fit"])