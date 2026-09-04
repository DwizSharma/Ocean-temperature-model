from fastapi import APIRouter, Request
from app.schemas.prediction import HealthResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    model = request.app.state.model_service
    return HealthResponse(
        status="ok" if model.is_loaded else "unhealthy",
        model_loaded=model.is_loaded,
        model_version=model.version,
    )
