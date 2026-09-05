from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.constants import DEPTHS_M


class PredictionRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90, description="Latitude in degrees.")
    longitude: float = Field(ge=-180, le=360, description="Longitude in -180..180 or 0..360.")
    target_month: str = Field(pattern=r"^\d{4}-\d{2}$", description="Target month in YYYY-MM format.")

    @model_validator(mode="before")
    @classmethod
    def parse_frontend_format(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            if "coordinates" in data and isinstance(data["coordinates"], dict):
                coords = data["coordinates"]
                if "latitude" not in data and "lat" in coords:
                    data["latitude"] = coords["lat"]
                if "longitude" not in data and "lon" in coords:
                    data["longitude"] = coords["lon"]
            if "target_month" not in data and "timestamp" in data:
                ts = str(data["timestamp"])
                if len(ts) >= 7 and ts[:4].isdigit() and ts[4] == "-" and ts[5:7].isdigit():
                    data["target_month"] = ts[:7]
        return data

    @field_validator("target_month")
    @classmethod
    def valid_calendar_month(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m")
        except ValueError as exc:
            raise ValueError("target_month must be a real calendar month in YYYY-MM format") from exc
        return value



class PredictionResponse(BaseModel):
    latitude: float
    longitude: float
    grid_latitude: float
    grid_longitude: float
    target_month: str
    depths_m: list[int] = Field(default_factory=lambda: list(DEPTHS_M))
    temperature_celsius: list[float] = Field(min_length=23, max_length=23)
    model_version: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str


class ModelInfoResponse(BaseModel):
    model_version: str
    input_shape: list[int]
    output_shape: list[int]
    input_channels: list[str]
    depths_m: list[int]
