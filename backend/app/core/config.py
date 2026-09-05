"""Settings are kept here so paths and model details are never scattered."""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BACKEND_DIR / "Assets"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", ".env"),
        extra="ignore",
    )

    model_path: Path = ASSETS_DIR / "model" / "best_model.keras"
    model_version: str = "prototype-v1"
    sst_data_dir: Path = ASSETS_DIR / "data" / "SST"
    ssh_data_dir: Path = ASSETS_DIR / "data" / "SSH"
    preprocessing_stats_path: Path = ASSETS_DIR / "preprocessing" / "preprocessing_stats.npz"
    allow_origins: str = "*"
    temporal_window_months: int = 3
    # Empty means a future broadly trained model can use every month whose inputs exist.
    supported_target_months: str = "2020-03"
    require_ocean_input: bool = True

    def model_post_init(self, __context: object) -> None:
        # Resolve any relative paths relative to BACKEND_DIR
        for field in ("model_path", "sst_data_dir", "ssh_data_dir", "preprocessing_stats_path"):
            val: Path = getattr(self, field)
            if not val.is_absolute():
                resolved = (BACKEND_DIR / val).resolve()
                setattr(self, field, resolved)
    # Alarm polling
    alarm_poll_interval_seconds: float = 2.0

    # Telegram — leave blank to disable notifications
    telegram_bot_token: str = ""
    # Comma-separated list of chat_ids to notify (seed values; more can be added at runtime)
    telegram_chat_ids: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.allow_origins.split(",") if item.strip()]

    @property
    def supported_month_set(self) -> set[str]:
        return {item.strip() for item in self.supported_target_months.split(",") if item.strip()}

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token)

    @property
    def initial_chat_ids(self) -> list[str]:
        return [cid.strip() for cid in self.telegram_chat_ids.split(",") if cid.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

