"""Exact inference preprocessing using statistics saved during training."""
from pathlib import Path
import numpy as np
from app.core.constants import INPUT_SHAPE


class PreprocessingError(ValueError):
    pass


class Preprocessor:
    """Fills NaNs and normalizes channels without recalculating any statistics."""
    REQUIRED_KEYS = ("sst_mean", "sst_std", "ssh_mean", "ssh_std")

    def __init__(self, stats_path: Path) -> None:
        self.stats_path = stats_path
        self._stats: dict[str, float] | None = None

    def load(self) -> None:
        if not self.stats_path.is_file():
            raise PreprocessingError("Preprocessing statistics artifact is unavailable.")
        try:
            with np.load(self.stats_path) as artifact:
                missing = set(self.REQUIRED_KEYS) - set(artifact.files)
                if missing:
                    raise PreprocessingError("Preprocessing statistics artifact is incomplete.")
                stats = {key: float(artifact[key]) for key in self.REQUIRED_KEYS}
            if stats["sst_std"] <= 0 or stats["ssh_std"] <= 0:
                raise PreprocessingError("Preprocessing standard deviations must be positive.")
            self._stats = stats
        except (OSError, ValueError) as exc:
            if isinstance(exc, PreprocessingError):
                raise
            raise PreprocessingError("Could not load preprocessing statistics artifact.") from exc

    def build_tensor(self, sst_grids: list[np.ndarray], ssh_grids: list[np.ndarray]) -> np.ndarray:
        if self._stats is None:
            raise PreprocessingError("Preprocessor has not been initialized.")
        if len(sst_grids) != INPUT_SHAPE[0] or len(ssh_grids) != INPUT_SHAPE[0]:
            raise PreprocessingError("Temporal input count does not match the configured model.")
        sequence: list[np.ndarray] = []
        for sst, ssh in zip(sst_grids, ssh_grids, strict=True):
            if sst.shape != (180, 360) or ssh.shape != (180, 360):
                raise PreprocessingError("Input grids must each have shape 180x360.")
            sst_clean = np.where(np.isnan(sst), self._stats["sst_mean"], sst)
            ssh_clean = np.where(np.isnan(ssh), self._stats["ssh_mean"], ssh)
            normalized_sst = (sst_clean - self._stats["sst_mean"]) / self._stats["sst_std"]
            normalized_ssh = (ssh_clean - self._stats["ssh_mean"]) / self._stats["ssh_std"]
            sequence.append(np.stack((normalized_sst, normalized_ssh), axis=-1))
        tensor = np.asarray(sequence, dtype=np.float32)[np.newaxis, ...]
        if tensor.shape != (1, *INPUT_SHAPE):
            raise PreprocessingError("Constructed tensor has an unexpected shape.")
        if not np.isfinite(tensor).all():
            raise PreprocessingError("Preprocessed model input contains non-finite values.")
        return tensor
