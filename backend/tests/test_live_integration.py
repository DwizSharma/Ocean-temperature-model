"""End-to-end integration test running the live FastAPI app with real model and NetCDF data."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def live_client():
    with TestClient(app) as client:
        yield client


def test_live_health_endpoint(live_client):
    res = live_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert data["model_version"] == "prototype-v1"


def test_live_model_info_endpoint(live_client):
    res = live_client.get("/api/v1/model-info")
    assert res.status_code == 200
    data = res.json()
    assert data["model_version"] == "prototype-v1"
    assert data["input_shape"] == [3, 180, 360, 2]
    assert data["output_shape"] == [180, 360, 23]
    assert data["input_channels"] == ["SST", "SSH/SLA"]
    assert len(data["depths_m"]) == 23


def test_live_prediction_standard_request(live_client):
    payload = {
        "latitude": 12.5,
        "longitude": 145.3,
        "target_month": "2020-03",
    }
    res = live_client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["target_month"] == "2020-03"
    assert (data["grid_latitude"], data["grid_longitude"]) == (12.5, 145.5)
    assert len(data["depths_m"]) == 23
    assert len(data["temperature_celsius"]) == 23
    # Check that all temperatures are finite floating numbers
    assert all(isinstance(v, float) for v in data["temperature_celsius"])
    # Realistic temperature ranges (surface ocean warmer than deep ocean)
    assert 5.0 <= data["temperature_celsius"][0] <= 35.0
    assert 0.0 <= data["temperature_celsius"][-1] <= 10.0
    assert data["temperature_celsius"][0] > data["temperature_celsius"][-1]


def test_live_prediction_frontend_request(live_client):
    payload = {
        "request_type": "point_profile",
        "coordinates": {
            "lat": 12.5,
            "lon": 145.3,
        },
        "timestamp": "2020-03-01",
    }
    res = live_client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["target_month"] == "2020-03"
    assert len(data["temperature_celsius"]) == 23


def test_live_prediction_unsupported_month(live_client):
    payload = {
        "latitude": 12.5,
        "longitude": 145.3,
        "target_month": "2020-04",
    }
    res = live_client.post("/api/v1/predict", json=payload)
    assert res.status_code == 422


def test_live_prediction_land_location_returns_404(live_client):
    payload = {
        "latitude": 20.5,
        "longitude": 75.5,
        "target_month": "2020-03",
    }
    res = live_client.post("/api/v1/predict", json=payload)
    assert res.status_code == 404

