"""Weather query service - handles read-only queries."""

from typing import Protocol
from sqlalchemy.orm import Session

from app.storage import crud
from app.storage.models import Forecast, Location, ScrapeRun


class DatabaseSession(Protocol):
    """Protocol for database session."""

    def close(self) -> None: ...


class WeatherQueryService:
    """Service for weather data queries."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    def get_department_data(self, department: str) -> dict:
        """
        Get all data for a department.

        Args:
            department: Department name

        Returns:
            Dict with locations, forecasts, and warnings
        """
        locations = self._get_department_locations(department)
        warnings = crud.get_active_warnings(self.db, department=department)

        return {
            "department": department,
            "locations": locations,
            "warnings": warnings,
        }

    def get_database_status(self) -> dict:
        """Get overall database statistics."""
        locations = crud.get_locations(self.db)
        total_forecasts = self.db.query(Forecast).count()
        latest_issued = crud.get_latest_issued_date(self.db)

        departments = {}
        for loc in locations:
            departments[loc.department] = departments.get(loc.department, 0) + 1

        return {
            "locations": len(locations),
            "total_forecasts": total_forecasts,
            "latest_issued": latest_issued,
            "departments": departments,
        }

    def get_scrape_runs(
        self, limit: int = 20, status: str | None = None
    ) -> list[ScrapeRun]:
        """Get recent scrape runs."""
        return crud.get_scrape_runs(self.db, limit=limit, status=status)

    def _get_department_locations(self, department: str) -> list[Location]:
        """Get all locations for a department."""
        all_locations = crud.get_locations(self.db, active_only=True)
        return [
            loc for loc in all_locations if loc.department.upper() == department.upper()
        ]
