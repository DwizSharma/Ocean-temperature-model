import pytest
from pydantic import ValidationError
from app.api.routes.prediction import predict
from app.schemas.prediction import PredictionRequest


def test_prediction_response_and_depth_count(app_request) -> None:  # type: ignore[no-untyped-def]
    body = predict(PredictionRequest(latitude=20.5, longitude=75.5, target_month="2020-03"), app_request)
    assert len(body.depths_m) == 23
    assert len(body.temperature_celsius) == 23
    assert body.longitude == 75.5


def test_valid_negative_longitude_is_normalized(app_request) -> None:  # type: ignore[no-untyped-def]
    body = predict(PredictionRequest(latitude=20.5, longitude=-75.5, target_month="2020-03"), app_request)
    assert body.longitude == 284.5


def test_invalid_latitude_longitude_and_month_are_rejected() -> None:
    cases = [
        {"latitude": 91, "longitude": 75.5, "target_month": "2020-03"},
        {"latitude": 20.5, "longitude": 361, "target_month": "2020-03"},
        {"latitude": 20.5, "longitude": 75.5, "target_month": "2020-13"},
    ]
    for payload in cases:
        with pytest.raises(ValidationError):
            PredictionRequest(**payload)


def test_frontend_nested_format_is_accepted(app_request) -> None:  # type: ignore[no-untyped-def]
    payload = {
        "request_type": "point_profile",
        "coordinates": {"lat": 12.5, "lon": 145.3},
        "timestamp": "2020-03-01",
    }
    req = PredictionRequest.model_validate(payload)
    assert req.latitude == 12.5
    assert req.longitude == 145.3
    assert req.target_month == "2020-03"
    body = predict(req, app_request)
    assert len(body.depths_m) == 23

