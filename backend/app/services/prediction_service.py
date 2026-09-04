"""Orchestrates the full SST/SSH -> global field -> point profile workflow."""
import numpy as np
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.temporal_service import TemporalService
from app.services.location_service import LocationService, InvalidOceanLocationError
from app.services.model_service import ModelService
from app.preprocessing.preprocessor import Preprocessor
from app.repositories.sst_repository import SSTRepository
from app.repositories.ssh_repository import SSHRepository


class PredictionService:
    def __init__(self, temporal: TemporalService, sst_repository: SSTRepository,
                 ssh_repository: SSHRepository, preprocessor: Preprocessor,
                 model: ModelService, location: LocationService) -> None:
        self.temporal = temporal
        self.sst_repository = sst_repository
        self.ssh_repository = ssh_repository
        self.preprocessor = preprocessor
        self.model = model
        self.location = location

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        months = self.temporal.required_months(request.target_month)
        sst_grids = [self.sst_repository.load_month(month) for month in months]
        ssh_grids = [self.ssh_repository.load_month(month) for month in months]
        lat_index, lon_index, grid_lat, grid_lon = self.location.nearest_grid_point(
            request.latitude, request.longitude
        )
        # A cell that is absent from both satellite sources for every input month is land/no-data.
        if all(np.isnan(sst[lat_index, lon_index]) and np.isnan(ssh[lat_index, lon_index])
               for sst, ssh in zip(sst_grids, ssh_grids, strict=True)):
            raise InvalidOceanLocationError("Requested location is not a valid ocean cell or has no input data.")
        tensor = self.preprocessor.build_tensor(sst_grids, ssh_grids)
        prediction = self.model.predict(tensor)
        profile = self.location.extract_profile(prediction, lat_index, lon_index)
        return PredictionResponse(
            latitude=request.latitude,
            longitude=self.location.normalize_longitude(request.longitude),
            grid_latitude=grid_lat,
            grid_longitude=grid_lon,
            target_month=request.target_month,
            temperature_celsius=profile,
            model_version=self.model.version,
        )
