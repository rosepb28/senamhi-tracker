"""Warning service layer - handles warning operations."""

from typing import Protocol
from datetime import datetime
from sqlalchemy.orm import Session

from app.scrapers.protocols import WarningScraperProtocol, WarningDetailsScraperProtocol
from app.scrapers.warning_scraper import WarningScraper
from app.scrapers.warning_details_scraper import WarningDetailsScraper
from app.storage import crud
from app.storage.models import WarningAlert, WarningDailyDetail
from app.models.enums import WarningStatus

from loguru import logger


class DatabaseSession(Protocol):
    """Protocol for database session."""

    def close(self) -> None: ...


class WarningService:
    """Service for warning operations."""

    def __init__(
        self,
        db: Session,
        scraper: WarningScraperProtocol | None = None,
        details_scraper: WarningDetailsScraperProtocol | None = None,
    ):
        """Initialize service with database session and scrapers."""
        self.db = db
        self.scraper = scraper or WarningScraper()
        self.details_scraper = details_scraper or WarningDetailsScraper()

    def update_warnings(self, force: bool = False) -> dict:
        """
        Scrape and update weather warnings.

        Args:
            force: Update existing warnings

        Returns:
            Dict with scrape results
        """
        self._update_expired_warnings()

        warnings = self.scraper.scrape_warnings()

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

        details_stats = {"saved": 0, "updated": 0}

        scraped_warning_numbers = set()
        for warning in warnings:
            if warning.senamhi_id:
                scraped_warning_numbers.add(warning.warning_number)

        if scraped_warning_numbers:
            logger.info(
                f"Scraping details for {len(scraped_warning_numbers)} warning(s)"
            )

            for warning_number in scraped_warning_numbers:
                warning_records = (
                    self.db.query(WarningAlert)
                    .filter(WarningAlert.warning_number == warning_number)
                    .all()
                )

                if not warning_records:
                    continue

                senamhi_id = warning_records[0].senamhi_id
                departments = list(set(w.department for w in warning_records))

                existing_details = (
                    self.db.query(WarningDailyDetail)
                    .filter(WarningDailyDetail.warning_number == warning_number)
                    .count()
                )

                if existing_details > 0:
                    logger.debug(
                        f"Warning #{warning_number} already has details, skipping"
                    )
                    continue

                try:
                    result = self.save_warning_details(
                        warning_number, senamhi_id, departments
                    )
                    details_stats["saved"] += result["saved"]
                    details_stats["updated"] += result["updated"]
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
            "details_saved": details_stats["saved"],
            "details_updated": details_stats["updated"],
        }

    def save_warning_details(
        self, warning_number: str, senamhi_id: int, departments: list[str]
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
        saved_count = 0
        updated_count = 0

        for department in departments:
            details_list = self.details_scraper.scrape_warning_details(
                senamhi_id, department
            )

            for detail_data in details_list:
                detail_data["warning_number"] = warning_number

                existing = (
                    self.db.query(WarningDailyDetail)
                    .filter_by(
                        warning_number=warning_number,
                        department=department,
                        day_number=detail_data["day_number"],
                    )
                    .first()
                )

                if existing:
                    for key, value in detail_data.items():
                        setattr(existing, key, value)
                    updated_count += 1
                else:
                    new_detail = WarningDailyDetail(**detail_data)
                    self.db.add(new_detail)
                    saved_count += 1

        self.db.commit()

        logger.info(
            f"Warning details for #{warning_number}: "
            f"{saved_count} saved, {updated_count} updated"
        )

        return {
            "warning_number": warning_number,
            "saved": saved_count,
            "updated": updated_count,
            "total": saved_count + updated_count,
        }

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

    def _update_expired_warnings(self):
        """Mark expired warnings as 'vencido'."""
        now = datetime.now()

        expired_count = (
            self.db.query(WarningAlert)
            .filter(
                WarningAlert.valid_until < now,
                WarningAlert.status != WarningStatus.VENCIDO.value,
            )
            .update({"status": WarningStatus.VENCIDO.value}, synchronize_session=False)
        )

        if expired_count > 0:
            self.db.commit()
        logger.info(f"Updated {expired_count} expired warning(s) to 'vencido'")
