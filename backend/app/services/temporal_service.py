"""Model temporal-window rules, isolated from HTTP and data loading."""
from datetime import date


class UnsupportedMonthError(ValueError):
    """Raised when configured model coverage does not include a requested month."""


class TemporalService:
    def __init__(self, window_months: int, supported_months: set[str]) -> None:
        if window_months < 1:
            raise ValueError("temporal_window_months must be at least 1")
        self.window_months = window_months
        self.supported_months = supported_months

    def required_months(self, target_month: str) -> list[str]:
        """Return oldest-to-newest YYYY-MM months ending at target_month."""
        if self.supported_months and target_month not in self.supported_months:
            raise UnsupportedMonthError(
                "Requested month is not supported by the currently configured prototype model."
            )
        try:
            year, month = map(int, target_month.split("-"))
            cursor = date(year, month, 1)
        except (TypeError, ValueError) as exc:
            raise ValueError("target_month must use YYYY-MM format") from exc

        months: list[str] = []
        for offset in range(self.window_months - 1, -1, -1):
            total = cursor.year * 12 + cursor.month - 1 - offset
            months.append(f"{total // 12:04d}-{total % 12 + 1:02d}")
        return months
