"""In-memory store of Telegram chat_ids that receive alarm notifications.

Seeded from the TELEGRAM_CHAT_IDS env var on startup.
Add/remove at runtime via the /api/v1/telegram-recipients endpoints
or via the bot's /subscribe and /unsubscribe commands.
"""


class RecipientRepository:
    def __init__(self, initial_ids: list[str]) -> None:
        # preserve insertion order, deduplicate
        self._ids: dict[str, None] = {cid: None for cid in initial_ids if cid}

    def all(self) -> list[str]:
        return list(self._ids)

    def add(self, chat_id: str) -> bool:
        """Returns True if the id was new, False if already present."""
        if chat_id in self._ids:
            return False
        self._ids[chat_id] = None
        return True

    def remove(self, chat_id: str) -> bool:
        """Returns True if removed, False if not found."""
        if chat_id not in self._ids:
            return False
        del self._ids[chat_id]
        return True

    def contains(self, chat_id: str) -> bool:
        return chat_id in self._ids
