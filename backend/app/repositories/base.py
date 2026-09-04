"""Shared NetCDF grid reader used by SST and SSH repositories."""
from pathlib import Path
import numpy as np
import xarray as xr
from app.core.constants import GRID_LATITUDES, GRID_LONGITUDES


class DataUnavailableError(FileNotFoundError):
    pass


class GridRepository:
    def __init__(self, data_dir: Path, filename_prefix: str, variable_candidates: tuple[str, ...]) -> None:
        self.data_dir = data_dir
        self.filename_prefix = filename_prefix
        self.variable_candidates = variable_candidates

    def _path_for(self, month: str) -> Path:
        compact = month.replace("-", "")
        matches = sorted(self.data_dir.glob(f"{self.filename_prefix}_{compact}*.nc"))
        if not matches:
            raise DataUnavailableError(f"Required {self.filename_prefix} data for {month} is unavailable.")
        return matches[0]

    def load_month(self, month: str) -> np.ndarray:
        path = self._path_for(month)
        try:
            with xr.open_dataset(path) as dataset:
                variable = next((name for name in self.variable_candidates if name in dataset.data_vars), None)
                if variable is None:
                    raise ValueError(f"No expected data variable found in {path.name}.")
                data = dataset[variable].squeeze(drop=True)
                # Conventional coordinate aliases are deliberately handled at this boundary.
                lat_name = next((name for name in ("lat", "latitude") if name in data.coords), None)
                lon_name = next((name for name in ("lon", "longitude") if name in data.coords), None)
                if not lat_name or not lon_name:
                    raise ValueError("Dataset is missing latitude or longitude coordinates.")
                # Convert -180..180 datasets to OceanEmbed's 0..360 convention,
                # then place values on the exact 1-degree model grid.
                data = data.assign_coords({lon_name: data[lon_name] % 360}).sortby(lat_name).sortby(lon_name)
                data = data.reindex(
                    {lat_name: list(GRID_LATITUDES), lon_name: list(GRID_LONGITUDES)},
                    method="nearest",
                    tolerance=0.51,
                )
                result = np.asarray(data.transpose(lat_name, lon_name).values, dtype=np.float32)
                if result.shape != (180, 360):
                    raise ValueError("Dataset cannot be aligned to the required 180x360 grid.")
                return result
        except OSError as exc:
            raise DataUnavailableError(f"Could not read required {self.filename_prefix} data for {month}.") from exc
