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
from app.services.telegram_service import TelegramService, NullTelegramService
from app.services.alarm_service import AlarmService
from app.services.bot_service import BotService
from app.repositories.sst_repository import SSTRepository
from app.repositories.ssh_repository import SSHRepository
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.recipient_repository import RecipientRepository
from app.preprocessing.preprocessor import Preprocessor, PreprocessingError
from app.api.routes import health, model_info, prediction, alarms, recipients

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # ── prediction stack ──────────────────────────────────────────────────
    model = ModelService(settings.model_path, settings.model_version)
    preprocessor = Preprocessor(settings.preprocessing_stats_path)
    try:
        preprocessor.load()
    except PreprocessingError:
        logger.exception("Preprocessing init failed; predictions unavailable")
    model.load()

    prediction_service = PredictionService(
        TemporalService(settings.temporal_window_months, settings.supported_month_set),
        SSTRepository(settings.sst_data_dir), SSHRepository(settings.ssh_data_dir),
        preprocessor, model, LocationService(),
    )
    app.state.model_service = model
    app.state.prediction_service = prediction_service

    # ── telegram stack ────────────────────────────────────────────────────
    telegram = (
        TelegramService(settings.telegram_bot_token)
        if settings.telegram_enabled
        else NullTelegramService()
    )
    recipient_repo = RecipientRepository(settings.initial_chat_ids)
    app.state.recipient_repo = recipient_repo

    # ── alarm service ─────────────────────────────────────────────────────
    alarm_service = AlarmService(
        AlarmRepository(), recipient_repo, prediction_service, telegram,
        poll_interval=settings.alarm_poll_interval_seconds,
    )
    app.state.alarm_service = alarm_service
    alarm_service.start()

    # ── bot command listener ──────────────────────────────────────────────
    bot = BotService(telegram, recipient_repo)
    bot.start()

    yield

    bot.stop()
    alarm_service.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="OceanEmbed API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
    app.include_router(health.router)
    app.include_router(model_info.router)
    app.include_router(prediction.router)
    app.include_router(alarms.router)
    app.include_router(recipients.router)
    return app


app = create_app()
