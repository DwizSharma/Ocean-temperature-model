"""Coordinate normalization and safe extraction from global model fields."""
import numpy as np
from app.core.constants import GRID_LATITUDES, GRID_LONGITUDES


class InvalidOceanLocationError(ValueError):
    """The requested cell has no usable ocean observations."""


class LocationService:
    @staticmethod
    def normalize_longitude(longitude: float) -> float:
        # 360 is equivalent to 0; grid centres themselves are .5 values.
        return longitude % 360.0

    def nearest_grid_point(self, latitude: float, longitude: float) -> tuple[int, int, float, float]:
        normalized_longitude = self.normalize_longitude(longitude)
        lat_index = int(np.argmin(np.abs(np.asarray(GRID_LATITUDES) - latitude)))
        lon_index = int(np.argmin(np.abs(np.asarray(GRID_LONGITUDES) - normalized_longitude)))
        return lat_index, lon_index, GRID_LATITUDES[lat_index], GRID_LONGITUDES[lon_index]

    @staticmethod
    def extract_profile(prediction: np.ndarray, lat_index: int, lon_index: int) -> list[float]:
        field = prediction[0] if prediction.ndim == 4 else prediction
        if field.shape != (180, 360, 23):
            raise ValueError("Model output is incompatible with the expected 180x360x23 grid.")
        profile = field[lat_index, lon_index, :]
        if not np.isfinite(profile).all():
            raise ValueError("Model returned invalid values for the requested location.")
        return [float(value) for value in profile]
