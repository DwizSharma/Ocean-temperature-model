"""Telegram Bot API wrapper.

TelegramService broadcasts to every chat_id supplied by RecipientRepository.
NullTelegramService is a silent drop-in when the bot token is not configured.
"""
import logging
import httpx

logger = logging.getLogger(__name__)

_SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"
_UPDATES_URL = "https://api.telegram.org/bot{token}/getUpdates"


class TelegramService:
    def __init__(self, bot_token: str) -> None:
        self._token = bot_token
        self._send_url = _SEND_URL.format(token=bot_token)
        self._updates_url = _UPDATES_URL.format(token=bot_token)

    async def send(self, recipients: list[str], text: str) -> None:
        """Broadcast text to all recipients. Logs errors but never raises."""
        if not recipients:
            logger.debug("No Telegram recipients — skipping notification")
            return
        async with httpx.AsyncClient(timeout=10) as client:
            for chat_id in recipients:
                try:
                    resp = await client.post(
                        self._send_url,
                        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                    )
                    resp.raise_for_status()
                except Exception:
                    logger.exception("Telegram send failed for chat_id=%s", chat_id)

    async def get_updates(self, offset: int = 0) -> list[dict]:
        """Long-poll for bot updates (used by the bot listener loop)."""
        try:
            async with httpx.AsyncClient(timeout=35) as client:
                resp = await client.get(
                    self._updates_url,
                    params={"timeout": 30, "offset": offset, "allowed_updates": ["message"]},
                )
                resp.raise_for_status()
                return resp.json().get("result", [])
        except Exception:
            logger.exception("Telegram getUpdates failed")
            return []


class NullTelegramService:
    """Drop-in replacement when bot token is not configured."""

    async def send(self, recipients: list[str], text: str) -> None:
        logger.debug("Telegram disabled — skipping notification to %d recipients", len(recipients))

    async def get_updates(self, offset: int = 0) -> list[dict]:
        return []
