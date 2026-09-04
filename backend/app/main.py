"""FastAPI application factory and startup initialization."""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.services.model_service import ModelService
from app.services.temporal_service import TemporalService
from app.services.location_service import LocationService
from app.services.prediction_service import PredictionService
from app.repositories.sst_repository import SSTRepository
from app.repositories.ssh_repository import SSHRepository
from app.preprocessing.preprocessor import Preprocessor, PreprocessingError
from app.api.routes import health, model_info, prediction

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    model = ModelService(settings.model_path, settings.model_version)
    preprocessor = Preprocessor(settings.preprocessing_stats_path)
    try:
        preprocessor.load()
    except PreprocessingError:
        logger.exception("Preprocessing initialization failed; predictions will be unavailable")
    model.load()
    app.state.model_service = model
    app.state.prediction_service = PredictionService(
        TemporalService(settings.temporal_window_months, settings.supported_month_set),
        SSTRepository(settings.sst_data_dir), SSHRepository(settings.ssh_data_dir),
        preprocessor, model, LocationService(),
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="OceanEmbed API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
    app.include_router(health.router)
    app.include_router(model_info.router)
    app.include_router(prediction.router)
    return app


app = create_app()
