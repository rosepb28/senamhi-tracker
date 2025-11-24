"""Weather service layer - centralizes business logic."""

from typing import Protocol
from datetime import datetime
from rich.console import Console
from sqlalchemy.orm import Session

from app.scrapers.forecast_scraper import ForecastScraper
from app.scrapers.warning_scraper import WarningScraper
from app.storage import crud
from app.storage.models import Forecast, Location, ScrapeRun, WarningAlert
from config.settings import settings

from app.scrapers.warning_details_scraper import WarningDetailsScraper
from app.storage.models import WarningDailyDetail

from loguru import logger

console = Console()


class DatabaseSession(Protocol):
    """Protocol for database session."""

    def close(self) -> None: ...


class WeatherService:
    """Service for weather data operations."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.forecast_scraper = ForecastScraper()
        self.warning_scraper = WarningScraper()

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
        # Determine departments to scrape
        if departments is None:
            if settings.scrape_all_departments:
                forecasts = self.forecast_scraper.scrape_all_departments()
                dept_list = sorted(set(f.department for f in forecasts))
            else:
                dept_list = settings.get_departments_list()
                forecasts = self.forecast_scraper.scrape_forecasts(
                    departments=dept_list
                )
        else:
            dept_list = departments
            forecasts = self.forecast_scraper.scrape_forecasts(departments=dept_list)

        if not forecasts:
            return {
                "success": False,
                "error": "No forecasts found",
                "locations": 0,
                "saved": 0,
            }

        issued_at = forecasts[0].issued_at

        # Check if data exists
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

        # Delete existing data if force
        if data_exists and force:
            for dept in dept_list:
                crud.delete_forecasts_by_issue_date(self.db, issued_at, dept)

        # Save forecasts
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

    def update_warnings(self, force: bool = False) -> dict:
        """
        Scrape and update weather warnings.

        Args:
            force: Update existing warnings

        Returns:
            Dict with scrape results
        """
        # First, update expired warnings
        self._update_expired_warnings()

        warnings = self.warning_scraper.scrape_warnings()

        if not warnings:
            return {
                "success": True,
                "found": 0,
                "saved": 0,
                "updated": 0,
            }

        saved_count = 0
        updated_count = 0

        for warning in warnings:
            existing = crud.get_warning_by_number(
                self.db, warning.warning_number, warning.department
            )

            if existing and not force:
                continue

            crud.save_warning(self.db, warning)

            if existing:
                updated_count += 1
            else:
                saved_count += 1

        # Scrape details for ALL warnings (not just new ones)
        details_stats = {'saved': 0, 'updated': 0}
        
        # Get unique warning numbers from scraped warnings (with senamhi_id)
        scraped_warning_numbers = set()
        for warning in warnings:
            if warning.senamhi_id:
                scraped_warning_numbers.add(warning.warning_number)
        
        if scraped_warning_numbers:
            logger.info(f"Scraping details for {len(scraped_warning_numbers)} warning(s)")
            
            for warning_number in scraped_warning_numbers:
                # Get all departments for this warning
                warning_records = self.db.query(WarningAlert).filter(
                    WarningAlert.warning_number == warning_number
                ).all()
                
                if not warning_records:
                    continue
                
                senamhi_id = warning_records[0].senamhi_id
                departments = list(set(w.department for w in warning_records))
                
                try:
                    result = self.save_warning_details(
                        warning_number,
                        senamhi_id,
                        departments
                    )
                    details_stats['saved'] += result['saved']
                    details_stats['updated'] += result['updated']
                except Exception as e:
                    logger.error(
                        f"Error saving details for warning #{warning_number}: {e}"
                    )
        
        logger.info(
            f"Warning details: {details_stats['saved']} saved, "
            f"{details_stats['updated']} updated"
        )
        
        return {
            "success": True,
            "found": len(warnings),
            "saved": saved_count,
            "updated": updated_count,
            "details_saved": details_stats['saved'],
            "details_updated": details_stats['updated']
        }

    def save_warning_details(
        self,
        warning_number: str,
        senamhi_id: int,
        departments: list[str]
    ) -> dict:
        """
        Scrape and save daily details for a warning.
        
        Args:
            warning_number: Warning number (e.g., '420')
            senamhi_id: SENAMHI internal ID
            departments: List of affected departments
        
        Returns:
            Dict with statistics
        """
        scraper = WarningDetailsScraper()
        
        saved_count = 0
        updated_count = 0
        
        for department in departments:
            details_list = scraper.scrape_warning_details(senamhi_id, department)
            
            for detail_data in details_list:
                # Add warning_number
                detail_data['warning_number'] = warning_number
                
                # Check if exists
                existing = self.db.query(WarningDailyDetail).filter_by(
                    warning_number=warning_number,
                    department=department,
                    day_number=detail_data['day_number']
                ).first()
                
                if existing:
                    # Update
                    for key, value in detail_data.items():
                        setattr(existing, key, value)
                    updated_count += 1
                else:
                    # Insert
                    new_detail = WarningDailyDetail(**detail_data)
                    self.db.add(new_detail)
                    saved_count += 1
        
        self.db.commit()
        
        logger.info(
            f"Warning details for #{warning_number}: "
            f"{saved_count} saved, {updated_count} updated"
        )
        
        return {
            'warning_number': warning_number,
            'saved': saved_count,
            'updated': updated_count,
            'total': saved_count + updated_count
        }
        
    def update_all(
        self, departments: list[str] | None = None, force: bool = False
    ) -> dict:
        """
        Update both forecasts and warnings.

        Args:
            departments: List of departments for forecasts
            force: Force update existing data

        Returns:
            Combined results
        """
        forecast_result = self.update_forecasts(departments=departments, force=force)
        warning_result = self.update_warnings(force=force)

        return {
            "forecasts": forecast_result,
            "warnings": warning_result,
        }

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

    def get_available_departments(self) -> list[str]:
        """Get list of departments available from SENAMHI."""
        return self.forecast_scraper.get_all_departments()

    def _get_department_locations(self, department: str) -> list[Location]:
        """Get all locations for a department."""
        all_locations = crud.get_locations(self.db, active_only=True)
        return [
            loc for loc in all_locations if loc.department.upper() == department.upper()
        ]

    # Delegated CRUD operations for convenience
    def get_all_locations(self, active_only: bool = True) -> list[Location]:
        """Get all locations."""
        return crud.get_locations(self.db, active_only=active_only)

    def get_warnings(
        self,
        severity: str | None = None,
        active_only: bool = True,
        limit: int = 50,
    ) -> list[WarningAlert]:
        """Get warnings with filters."""
        return crud.get_warnings(
            self.db, severity=severity, active_only=active_only, limit=limit
        )

    def get_warning_details(
        self, warning_number: str, department: str | None = None
    ) -> WarningAlert | None:
        """Get detailed warning information."""
        return crud.get_warning_by_number(self.db, warning_number, department)

    def get_forecast_history(
        self, location_name: str, forecast_date
    ) -> list[Forecast] | None:
        """Get forecast history for a specific date."""
        location = crud.get_location_by_name(self.db, location_name.upper())

        if not location:
            return None

        return crud.get_forecast_history(self.db, location.id, forecast_date)

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

    def _update_expired_warnings(self):
        """Mark expired warnings as 'vencido'."""

        now = datetime.now()

        # Find warnings that are expired but not marked as vencido
        expired_count = (
            self.db.query(WarningAlert)
            .filter(WarningAlert.valid_until < now, WarningAlert.status != "vencido")
            .update({"status": "vencido"}, synchronize_session=False)
        )

        if expired_count > 0:
            self.db.commit()
        console.print(
            f"[dim]Updated {expired_count} expired warning(s) to 'vencido'[/dim]"
        )
