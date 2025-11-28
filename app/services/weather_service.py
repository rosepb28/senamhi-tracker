"""Weather service facade - orchestrates forecast and warning services."""

from typing import Protocol
from sqlalchemy.orm import Session

from app.services.forecast_service import ForecastService
from app.services.warning_service import WarningService
from app.services.weather_query_service import WeatherQueryService


class DatabaseSession(Protocol):
    """Protocol for database session."""

    def close(self) -> None: ...


class WeatherService:
    """Facade service that orchestrates forecast and warning operations."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.forecast_service = ForecastService(db)
        self.warning_service = WarningService(db)
        self.query_service = WeatherQueryService(db)

    def update_forecasts(
        self, departments: list[str] | None = None, force: bool = False
    ) -> dict:
        """Delegate to ForecastService."""
        return self.forecast_service.update_forecasts(
            departments=departments, force=force
        )

    def update_warnings(self, force: bool = False) -> dict:
        """Delegate to WarningService."""
        return self.warning_service.update_warnings(force=force)

    def update_all(
        self, departments: list[str] | None = None, force: bool = False
    ) -> dict:
        """Update both forecasts and warnings."""
        forecast_result = self.forecast_service.update_forecasts(
            departments=departments, force=force
        )
        warning_result = self.warning_service.update_warnings(force=force)

        return {
            "forecasts": forecast_result,
            "warnings": warning_result,
        }

    def get_location_forecasts(self, location_name: str) -> dict | None:
        """Delegate to ForecastService."""
        return self.forecast_service.get_location_forecasts(location_name)

    def get_forecast_history(self, location_name: str, forecast_date):
        """Delegate to ForecastService."""
        return self.forecast_service.get_forecast_history(location_name, forecast_date)

    def get_available_departments(self) -> list[str]:
        """Delegate to ForecastService."""
        return self.forecast_service.get_available_departments()

    def get_all_locations(self, active_only: bool = True):
        """Delegate to ForecastService."""
        return self.forecast_service.get_all_locations(active_only=active_only)

    def get_warnings(
        self, severity: str | None = None, active_only: bool = True, limit: int = 50
    ):
        """Delegate to WarningService."""
        return self.warning_service.get_warnings(
            severity=severity, active_only=active_only, limit=limit
        )

    def get_warning_details(self, warning_number: str, department: str | None = None):
        """Delegate to WarningService."""
        return self.warning_service.get_warning_details(warning_number, department)

    def save_warning_details(
        self, warning_number: str, senamhi_id: int, departments: list[str]
    ) -> dict:
        """Delegate to WarningService."""
        return self.warning_service.save_warning_details(
            warning_number, senamhi_id, departments
        )

    def get_department_data(self, department: str) -> dict:
        """Delegate to QueryService."""
        return self.query_service.get_department_data(department)

    def get_database_status(self) -> dict:
        """Delegate to QueryService."""
        return self.query_service.get_database_status()

    def get_scrape_runs(self, limit: int = 20, status: str | None = None):
        """Delegate to QueryService."""
        return self.query_service.get_scrape_runs(limit=limit, status=status)
