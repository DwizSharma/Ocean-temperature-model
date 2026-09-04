import numpy as np
from app.services.location_service import LocationService


def test_normalizes_negative_longitude_and_finds_nearest_cell() -> None:
    service = LocationService()
    lat_index, lon_index, grid_lat, grid_lon = service.nearest_grid_point(20.4, -284.4)
    assert (lat_index, lon_index) == (110, 75)
    assert (grid_lat, grid_lon) == (20.5, 75.5)


def test_extracts_23_value_profile() -> None:
    field = np.zeros((1, 180, 360, 23), dtype=np.float32)
    field[0, 110, 75] = np.arange(23)
    assert LocationService.extract_profile(field, 110, 75) == [float(value) for value in range(23)]
