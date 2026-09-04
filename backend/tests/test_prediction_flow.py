import numpy as np
from app.preprocessing.preprocessor import Preprocessor
from app.schemas.prediction import PredictionRequest
from app.services.location_service import LocationService
from app.services.prediction_service import PredictionService
from app.services.temporal_service import TemporalService


class FakeRepository:
    def load_month(self, month: str) -> np.ndarray:
        return np.ones((180, 360), dtype=np.float32)


class FakeModel:
    version = "integration-test"

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        assert tensor.shape == (1, 3, 180, 360, 2)
        result = np.zeros((1, 180, 360, 23), dtype=np.float32)
        result[0, 110, 75] = np.arange(23)
        return result


def test_complete_prediction_orchestration(tmp_path) -> None:
    stats_path = tmp_path / "stats.npz"
    np.savez(stats_path, sst_mean=1.0, sst_std=1.0, ssh_mean=1.0, ssh_std=1.0)
    preprocessor = Preprocessor(stats_path)
    preprocessor.load()
    service = PredictionService(
        TemporalService(3, {"2020-03"}), FakeRepository(), FakeRepository(),
        preprocessor, FakeModel(), LocationService(),  # type: ignore[arg-type]
    )
    result = service.predict(PredictionRequest(latitude=20.4, longitude=75.6, target_month="2020-03"))
    assert (result.grid_latitude, result.grid_longitude) == (20.5, 75.5)
    assert result.temperature_celsius == [float(value) for value in range(23)]
