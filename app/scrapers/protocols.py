"""Protocols for scraper interfaces."""

from typing import Protocol

from app.models.forecast import LocationForecast
from app.models.warning import Warning


class ForecastScraperProtocol(Protocol):
    """Protocol for forecast scraper implementations."""

    def scrape_forecasts(self, departments: list[str]) -> list[LocationForecast]:
        """Scrape forecasts for specified departments."""
        ...

    def scrape_all_departments(self) -> list[LocationForecast]:
        """Scrape forecasts for all available departments."""
        ...

    def get_all_departments(self) -> list[str]:
        """Get list of all available departments."""
        ...


class WarningScraperProtocol(Protocol):
    """Protocol for warning scraper implementations."""

    def scrape_warnings(self) -> list[Warning]:
        """Scrape active warnings."""
        ...


class WarningDetailsScraperProtocol(Protocol):
    """Protocol for warning details scraper implementations."""

    def scrape_warning_details(self, senamhi_id: int, department: str) -> list[dict]:
        """Scrape daily details for a warning."""
        ...
