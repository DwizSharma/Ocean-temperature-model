import logging
from fastapi import APIRouter, HTTPException, Request, status
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.temporal_service import UnsupportedMonthError
from app.services.location_service import InvalidOceanLocationError
from app.services.model_service import ModelUnavailableError
from app.repositories.base import DataUnavailableError
from app.preprocessing.preprocessor import PreprocessingError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Prediction"])


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest, request: Request) -> PredictionResponse:
    try:
        return request.app.state.prediction_service.predict(payload)
    except UnsupportedMonthError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except (DataUnavailableError, InvalidOceanLocationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (PreprocessingError, ModelUnavailableError, ValueError) as exc:
        logger.exception("Prediction request could not be completed")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Prediction service is temporarily unavailable.") from exc
