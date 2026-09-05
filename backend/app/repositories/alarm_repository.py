"""In-memory alarm store with a dict-based interface.

Swap this class for a DB-backed one by implementing the same four methods.
"""
from datetime import datetime, timezone
from app.schemas.alarm import AlarmCreate, AlarmResponse, AlarmStatus
import uuid


class AlarmRepository:
    def __init__(self) -> None:
        self._store: dict[str, AlarmResponse] = {}

    # ------------------------------------------------------------------
    def create(self, payload: AlarmCreate) -> AlarmResponse:
        alarm = AlarmResponse(
            id=str(uuid.uuid4()),
            **payload.model_dump(),
            status=AlarmStatus.active,
            created_at=datetime.now(timezone.utc),
        )
        self._store[alarm.id] = alarm
        return alarm

    def get(self, alarm_id: str) -> AlarmResponse | None:
        return self._store.get(alarm_id)

    def list_all(self) -> list[AlarmResponse]:
        return list(self._store.values())

    def delete(self, alarm_id: str) -> bool:
        return self._store.pop(alarm_id, None) is not None

    # ------------------------------------------------------------------
    def update(self, alarm: AlarmResponse) -> None:
        """Persist an already-mutated AlarmResponse back into the store."""
        self._store[alarm.id] = alarm

    def active_alarms(self) -> list[AlarmResponse]:
        return [a for a in self._store.values() if a.status == AlarmStatus.active]
