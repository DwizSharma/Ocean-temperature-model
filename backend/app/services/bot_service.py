"""Telegram bot command listener.

Runs as a background asyncio task using long-polling (getUpdates).
Supported commands:
  /subscribe   — adds the sender's chat_id to the recipient list
  /unsubscribe — removes the sender's chat_id
  /list        — shows all current recipients (chat_ids)

The service only processes updates once (tracks the offset), so
messages are never handled twice even across rapid restarts within
the same process lifetime.
"""
import asyncio
import logging

from app.repositories.recipient_repository import RecipientRepository
from app.services.telegram_service import TelegramService, NullTelegramService

logger = logging.getLogger(__name__)

_HELP = (
    "🌊 <b>OceanEmbed Alarm Bot</b>\n\n"
    "/subscribe — add your chat to alarm notifications\n"
    "/unsubscribe — remove your chat from notifications\n"
    "/list — show all subscribed chat IDs\n"
)


class BotService:
    def __init__(
        self,
        telegram: TelegramService | NullTelegramService,
        recipients: RecipientRepository,
    ) -> None:
        self._telegram = telegram
        self._recipients = recipients
        self._offset = 0
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if isinstance(self._telegram, NullTelegramService):
            logger.info("Bot listener disabled (no token configured)")
            return
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._listen(), name="bot-listener")
            logger.info("Telegram bot listener started")

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Telegram bot listener stopped")

    async def _listen(self) -> None:
        while True:
            try:
                updates = await self._telegram.get_updates(offset=self._offset)
                for update in updates:
                    self._offset = update["update_id"] + 1
                    await self._handle(update)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Bot listener error — retrying in 5s")
                await asyncio.sleep(5)

    async def _handle(self, update: dict) -> None:
        msg = update.get("message", {})
        text = (msg.get("text") or "").strip()
        chat_id = str(msg.get("chat", {}).get("id", ""))
        if not chat_id or not text.startswith("/"):
            return

        cmd = text.split()[0].split("@")[0].lower()  # strip @botname suffix

        if cmd == "/subscribe":
            if self._recipients.add(chat_id):
                reply = f"✅ Subscribed! Your chat_id <code>{chat_id}</code> will receive ocean alarm notifications."
            else:
                reply = f"ℹ️ Already subscribed (chat_id <code>{chat_id}</code>)."

        elif cmd == "/unsubscribe":
            if self._recipients.remove(chat_id):
                reply = f"🔕 Unsubscribed. You will no longer receive notifications."
            else:
                reply = f"ℹ️ You weren't subscribed (chat_id <code>{chat_id}</code>)."

        elif cmd == "/list":
            ids = self._recipients.all()
            if ids:
                listed = "\n".join(f"• <code>{cid}</code>" for cid in ids)
                reply = f"📋 <b>Subscribed recipients ({len(ids)}):</b>\n{listed}"
            else:
                reply = "📋 No recipients subscribed yet."

        elif cmd in ("/start", "/help"):
            reply = _HELP

        else:
            reply = f"Unknown command <code>{cmd}</code>. Send /help for options."

        await self._telegram.send([chat_id], reply)
