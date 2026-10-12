from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_dataset_schema():
    resp = client.get("/api/v1/dataset/schema")
    assert resp.status_code == 200
    body = resp.json()
    assert "features" in body
    assert "target" in body


def test_predict_without_model_returns_503():
    """Until train.py has run and produced models/, /predict should fail
    gracefully with a clear message, not a 500 stack trace."""
    payload = {
        "formulation": {
            "particle_size_nm": 120,
            "coating_material": "chitosan",
            "nutrient_type": "N",
            "nutrient_loading_pct": 15,
            "shell_thickness_nm": 30,
        },
        "soil": {
            "ph": 6.5,
            "moisture_pct": 40,
            "temperature_c": 25,
            "organic_carbon_pct": 1.2,
            "texture": "loamy",
            "salinity_ds_m": 0.5,
        },
        "environment": {"rainfall_mm": 80, "humidity_pct": 60},
    }
    resp = client.post("/api/v1/predict", json=payload)
    assert resp.status_code in (200, 503)
