"""CRUD endpoints for temperature alarms."""
import logging
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from app.schemas.alarm import AlarmCreate, AlarmResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/alarms", tags=["Alarms"])


def _svc(request: Request):
    return request.app.state.alarm_service


class TriggerPayload(BaseModel):
    value_celsius: float


@router.post("", response_model=AlarmResponse, status_code=status.HTTP_201_CREATED)
def create_alarm(payload: AlarmCreate, request: Request) -> AlarmResponse:
    """Register a new alarm for a lat/lon coordinate."""
    return _svc(request).create(payload)


@router.get("", response_model=list[AlarmResponse], status_code=status.HTTP_200_OK)
def list_alarms(request: Request) -> list[AlarmResponse]:
    """Return all alarms (active, triggered, and errored)."""
    return _svc(request).list_all()


@router.get("/{alarm_id}", response_model=AlarmResponse, status_code=status.HTTP_200_OK)
def get_alarm(alarm_id: str, request: Request) -> AlarmResponse:
    """Fetch a single alarm by ID."""
    alarm = _svc(request).get(alarm_id)
    if alarm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alarm '{alarm_id}' not found.")
    return alarm


@router.post("/{alarm_id}/trigger", response_model=AlarmResponse, status_code=status.HTTP_200_OK)
async def report_trigger(alarm_id: str, payload: TriggerPayload, request: Request) -> AlarmResponse:
    """Called by the frontend when mock-mode detects a threshold crossing.
    Fires the Telegram notification server-side and marks the alarm triggered."""
    alarm = await _svc(request).report_triggered(alarm_id, payload.value_celsius)
    if alarm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alarm '{alarm_id}' not found.")
    return alarm


@router.delete("/{alarm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alarm(alarm_id: str, request: Request) -> None:
    """Remove an alarm. Returns 404 if it never existed."""
    if not _svc(request).delete(alarm_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alarm '{alarm_id}' not found.")
