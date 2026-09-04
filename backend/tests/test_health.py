from app.api.routes.health import health
from app.api.routes.model_info import model_info


def test_health_reports_model_state(app_request) -> None:  # type: ignore[no-untyped-def]
    body = health(app_request)
    assert body.status == "ok"
    assert body.model_loaded is True


def test_model_info_has_stable_contract(app_request) -> None:  # type: ignore[no-untyped-def]
    body = model_info(app_request)
    assert body.input_shape == [3, 180, 360, 2]
    assert body.output_shape == [180, 360, 23]
    assert len(body.depths_m) == 23
