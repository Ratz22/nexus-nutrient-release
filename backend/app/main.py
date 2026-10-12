from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Interpretable ML API for predicting nano-fertilizer nutrient release.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health():
    # The OpenAPI schema lists every endpoint, including those inside included routers.
    # app.routes does not show them directly in this FastAPI version.
    paths = set(app.openapi().get("paths", {}).keys())
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "has_literature_search": any(p.endswith("/literature") for p in paths),
        "has_dataset_info": any(p.endswith("/dataset/info") for p in paths),
    }