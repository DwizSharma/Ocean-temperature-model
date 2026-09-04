import pytest
from app.services.temporal_service import TemporalService, UnsupportedMonthError


def test_three_month_window_crosses_year_boundary() -> None:
    service = TemporalService(3, set())
    assert service.required_months("2020-03") == ["2020-01", "2020-02", "2020-03"]
    assert service.required_months("2020-01") == ["2019-11", "2019-12", "2020-01"]


def test_prototype_rejects_other_target_months() -> None:
    with pytest.raises(UnsupportedMonthError):
        TemporalService(3, {"2020-03"}).required_months("2020-04")
