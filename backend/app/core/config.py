"""Settings are kept here so paths and model details are never scattered."""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_path: Path = Path("model/ConvLSTM_JanFebMar_Prototype.keras")
    model_version: str = "prototype-v1"
    sst_data_dir: Path = Path("data/SST")
    ssh_data_dir: Path = Path("data/SSH")
    preprocessing_stats_path: Path = Path("preprocessing_artifacts/preprocessing_stats.npz")
    allow_origins: str = "*"
    temporal_window_months: int = 3
    # Empty means a future broadly trained model can use every month whose inputs exist.
    supported_target_months: str = "2020-03"
    require_ocean_input: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.allow_origins.split(",") if item.strip()]

    @property
    def supported_month_set(self) -> set[str]:
        return {item.strip() for item in self.supported_target_months.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
