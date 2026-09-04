from fastapi import APIRouter, Request
from app.core.constants import DEPTHS_M, INPUT_CHANNELS
from app.schemas.prediction import ModelInfoResponse

router = APIRouter(prefix="/api/v1", tags=["Model"])


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info(request: Request) -> ModelInfoResponse:
    metadata = request.app.state.model_service.metadata()
    return ModelInfoResponse(**metadata, input_channels=INPUT_CHANNELS, depths_m=DEPTHS_M)
