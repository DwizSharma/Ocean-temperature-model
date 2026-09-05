"""Alarm request/response schemas."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AlarmCondition(str, Enum):
    above = "above"
    below = "below"


class AlarmStatus(str, Enum):
    active = "active"       # polling, condition not yet met
    firing = "firing"       # condition currently met — keeps polling, notifies every cycle
    error = "error"         # last poll failed


class AlarmCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=360)
    target_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    depth_index: int = Field(ge=0, le=22, description="Index into the 23-depth array (0 = 30 m, 22 = 2000 m).")
    condition: AlarmCondition
    threshold_celsius: float
    label: str = Field(default="", max_length=120)


class AlarmResponse(BaseModel):
    id: str
    latitude: float
    longitude: float
    target_month: str
    depth_index: int
    condition: AlarmCondition
    threshold_celsius: float
    label: str
    status: AlarmStatus
    last_value_celsius: float | None = None
    triggered_at: datetime | None = None
    created_at: datetime
    error_detail: str | None = None
