"""Alarm polling engine.

Status transitions:
  active  → firing  : condition first met   → notify
  firing  → firing  : condition still met   → notify every cycle
  firing  → active  : condition cleared     → no notification
  active  → error   : poll threw            → no notification
  error   → active  : next successful poll  → resume checking

The /trigger endpoint lets the frontend (mock mode) report a crossing
so the backend fires Telegram without needing real model data.
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.repositories.alarm_repository import AlarmRepository
from app.repositories.recipient_repository import RecipientRepository
from app.schemas.alarm import AlarmCondition, AlarmCreate, AlarmResponse, AlarmStatus
from app.schemas.prediction import PredictionRequest
from app.services.prediction_service import PredictionService
from app.services.telegram_service import TelegramService, NullTelegramService

logger = logging.getLogger(__name__)

_CONDITION_MET = {
    AlarmCondition.above: lambda val, thr: val > thr,
    AlarmCondition.below: lambda val, thr: val < thr,
}

# Statuses that should keep being polled
_POLLABLE = {AlarmStatus.active, AlarmStatus.firing, AlarmStatus.error}


def _fmt(alarm: AlarmResponse, value: float) -> str:
    label = f" ({alarm.label})" if alarm.label else ""
    direction = "above" if alarm.condition == AlarmCondition.above else "below"
    return (
        f"🚨 <b>Ocean Alarm{label}</b>\n"
        f"📍 {alarm.latitude:.2f}°, {alarm.longitude:.2f}°  ·  {alarm.target_month}\n"
        f"🌊 Depth index {alarm.depth_index} — "
        f"<b>{value:.2f}°C</b> is {direction} {alarm.threshold_celsius:.2f}°C"
    )


class AlarmService:
    def __init__(
        self,
        alarm_repo: AlarmRepository,
        recipient_repo: RecipientRepository,
        prediction_service: PredictionService,
        telegram: TelegramService | NullTelegramService,
        poll_interval: float = 2.0,
    ) -> None:
        self._alarms = alarm_repo
        self._recipients = recipient_repo
        self._prediction = prediction_service
        self._telegram = telegram
        self._interval = poll_interval
        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------ CRUD
    def create(self, payload: AlarmCreate) -> AlarmResponse:
        return self._alarms.create(payload)

    def list_all(self) -> list[AlarmResponse]:
        return self._alarms.list_all()

    def get(self, alarm_id: str) -> AlarmResponse | None:
        return self._alarms.get(alarm_id)

    def delete(self, alarm_id: str) -> bool:
        return self._alarms.delete(alarm_id)

    # ------------------------------------------------------------------ frontend trigger (mock mode)
    async def report_triggered(self, alarm_id: str, value: float) -> AlarmResponse | None:
        """Frontend detected a crossing; fire Telegram and update state."""
        alarm = self._alarms.get(alarm_id)
        if alarm is None:
            return None
        alarm.last_value_celsius = value
        alarm.triggered_at = datetime.now(timezone.utc)
        alarm.status = AlarmStatus.firing
        alarm.error_detail = None
        self._alarms.update(alarm)
        await self._telegram.send(self._recipients.all(), _fmt(alarm, value))
        logger.info("Alarm %s client-reported firing: %.2f°C", alarm_id, value)
        return alarm

    # ------------------------------------------------------------------ lifecycle
    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._poll_loop(), name="alarm-poll")
            logger.info("Alarm poll loop started (interval=%.1fs)", self._interval)

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Alarm poll loop stopped")

    # ------------------------------------------------------------------ poll loop
    async def _poll_loop(self) -> None:
        while True:
            await asyncio.sleep(self._interval)
            pollable = [a for a in self._alarms.list_all() if a.status in _POLLABLE]
            if pollable:
                await asyncio.gather(*[self._check(a) for a in pollable])

    async def _check(self, alarm: AlarmResponse) -> None:
        try:
            req = PredictionRequest(
                latitude=alarm.latitude,
                longitude=alarm.longitude,
                target_month=alarm.target_month,
            )
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self._prediction.predict, req)
            value = result.temperature_celsius[alarm.depth_index]
            alarm.last_value_celsius = value
            alarm.error_detail = None

            if _CONDITION_MET[alarm.condition](value, alarm.threshold_celsius):
                # Condition met — fire every cycle regardless of previous status
                alarm.status = AlarmStatus.firing
                alarm.triggered_at = datetime.now(timezone.utc)
                self._alarms.update(alarm)
                await self._telegram.send(self._recipients.all(), _fmt(alarm, value))
                logger.info("Alarm %s firing: %.2f°C", alarm.id, value)
            else:
                # Condition cleared — reset to active so it can fire again
                alarm.status = AlarmStatus.active
                self._alarms.update(alarm)

        except Exception as exc:
            alarm.status = AlarmStatus.error
            alarm.error_detail = str(exc)
            self._alarms.update(alarm)
            logger.warning("Alarm %s poll failed: %s", alarm.id, exc)
