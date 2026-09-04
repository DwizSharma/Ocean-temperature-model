"""A small boundary around Keras, so routes never depend on TensorFlow."""
from pathlib import Path
import logging
import numpy as np
from app.core.constants import INPUT_SHAPE, OUTPUT_SHAPE

logger = logging.getLogger(__name__)


class ModelUnavailableError(RuntimeError):
    pass


class ModelService:
    def __init__(self, model_path: Path, version: str) -> None:
        self.model_path = model_path
        self.version = version
        self.model: object | None = None
        self.load_error: str | None = None

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        if not self.model_path.is_file():
            self.load_error = "Configured model file is unavailable."
            logger.error("Model file is not available")
            return
        try:
            # Delayed import keeps pure schema/location tests lightweight.
            from tensorflow import keras
            self.model = keras.models.load_model(self.model_path, compile=False)
            self.load_error = None
            logger.info("Loaded model version %s", self.version)
        except Exception:  # TensorFlow errors vary greatly by installed version.
            self.model = None
            self.load_error = "Model could not be loaded."
            logger.exception("Could not load configured model")

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise ModelUnavailableError("Model is currently unavailable.")
        try:
            result = np.asarray(self.model.predict(tensor, verbose=0), dtype=np.float32)
            expected = (1, *OUTPUT_SHAPE)
            if result.shape != expected:
                raise ModelUnavailableError("Configured model returned an incompatible output shape.")
            return result
        except ModelUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Model inference failed")
            raise ModelUnavailableError("Model inference failed.") from exc

    def metadata(self) -> dict[str, object]:
        return {"model_version": self.version, "input_shape": list(INPUT_SHAPE), "output_shape": list(OUTPUT_SHAPE)}
