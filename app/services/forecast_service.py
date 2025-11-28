"""Forecast service layer - handles forecast operations."""

from typing import Protocol
from sqlalchemy.orm import Session

from app.scrapers.protocols import ForecastScraperProtocol
from app.scrapers.forecast_scraper import ForecastScraper
from app.storage import crud
from app.storage.models import Forecast, Location
from config.settings import settings


class DatabaseSession(Protocol):
    """Protocol for database session."""

    def close(self) -> None: ...


class ForecastService:
    """Service for forecast operations."""

    def __init__(self, db: Session, scraper: ForecastScraperProtocol | None = None):
        """Initialize service with database session and scraper."""
        self.db = db
        self.scraper = scraper or ForecastScraper()

    def update_forecasts(
        self,
        departments: list[str] | None = None,
        force: bool = False,
    ) -> dict:
        """
        Scrape and update weather forecasts.

        Args:
            departments: List of departments to scrape (None = use config)
            force: Replace existing data for same issue date

        Returns:
            Dict with scrape results
        """
        if departments is None:
            if settings.scrape_all_departments:
                forecasts = self.scraper.scrape_all_departments()
                dept_list = sorted(set(f.department for f in forecasts))
            else:
                dept_list = settings.get_departments_list()
                forecasts = self.scraper.scrape_forecasts(departments=dept_list)
        else:
            dept_list = departments
            forecasts = self.scraper.scrape_forecasts(departments=dept_list)

        if not forecasts:
            return {
                "success": False,
                "error": "No forecasts found",
                "locations": 0,
                "saved": 0,
            }

        issued_at = forecasts[0].issued_at

        data_exists = any(
            crud.forecast_exists_for_issue_date(self.db, issued_at, dept)
            for dept in dept_list
        )

        if data_exists and not force:
            return {
                "success": False,
                "skipped": True,
                "issued_at": issued_at,
                "locations": len(forecasts),
                "saved": 0,
                "message": "Data already exists for this issue date",
            }

        if data_exists and force:
            for dept in dept_list:
                crud.delete_forecasts_by_issue_date(self.db, issued_at, dept)

        saved_count = 0
        for location_forecast in forecasts:
            saved = crud.save_forecast(self.db, location_forecast)
            saved_count += len(saved)

        return {
            "success": True,
            "issued_at": issued_at,
            "departments": dept_list,
            "locations": len(forecasts),
            "saved": saved_count,
        }

    def get_location_forecasts(self, location_name: str) -> dict | None:
        """
        Get latest forecasts for a location.

        Args:
            location_name: Location name

        Returns:
            Dict with location and forecasts, or None if not found
        """
        location = crud.get_location_by_name(self.db, location_name.upper())

        if not location:
            return None

        forecasts = crud.get_latest_forecasts(self.db, location_id=location.id)

        return {
            "location": location,
            "forecasts": forecasts,
        }

    def get_forecast_history(
        self, location_name: str, forecast_date
    ) -> list[Forecast] | None:
        """Get forecast history for a specific date."""
        location = crud.get_location_by_name(self.db, location_name.upper())

        if not location:
            return None

        return crud.get_forecast_history(self.db, location.id, forecast_date)

    def get_available_departments(self) -> list[str]:
        """Get list of departments available from SENAMHI."""
        return self.scraper.get_all_departments()

    def get_all_locations(self, active_only: bool = True) -> list[Location]:
        """Get all locations."""
        return crud.get_locations(self.db, active_only=active_only)

    def get_department_locations(self, department: str) -> list[Location]:
        """Get all locations for a department."""
        all_locations = crud.get_locations(self.db, active_only=True)
        return [
            loc for loc in all_locations if loc.department.upper() == department.upper()
        ]
