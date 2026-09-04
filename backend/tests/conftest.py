import numpy as np
import pytest
from types import SimpleNamespace
from app.main import create_app
from app.schemas.prediction import PredictionRequest, PredictionResponse


class FakePredictionService:
    """Keeps route tests independent of TensorFlow, NetCDF files, and a model."""
    def predict(self, request: PredictionRequest) -> PredictionResponse:
        longitude = request.longitude % 360
        return PredictionResponse(
            latitude=request.latitude, longitude=longitude,
            grid_latitude=20.5, grid_longitude=75.5,
            target_month=request.target_month,
            temperature_celsius=[float(value) for value in np.arange(23)],
            model_version="test-model",
        )


class FakeModelService:
    version = "test-model"
    is_loaded = True

    @staticmethod
    def metadata() -> dict[str, object]:
        return {
            "model_version": "test-model",
            "input_shape": [3, 180, 360, 2],
            "output_shape": [180, 360, 23],
        }


@pytest.fixture
def app_request():  # type: ignore[no-untyped-def]
    app = create_app()
    # Route tests intentionally bypass startup's real model/data initialization.
    app.state.model_service = FakeModelService()
    app.state.prediction_service = FakePredictionService()
    return SimpleNamespace(app=app)
