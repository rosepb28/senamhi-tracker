"""Downloader for SENAMHI warning shapefiles."""

from datetime import datetime, timedelta
from pathlib import Path
import zipfile

import requests

from app.storage.models import WarningAlert
from config.settings import settings

from loguru import logger


class ShapefileDownloader:
    """Download shapefiles for SENAMHI weather warnings."""

    def __init__(self, download_dir: Path | None = None):
        """
        Initialize downloader.

        Args:
            download_dir: Directory to save shapefiles (default: data/shapefiles)
        """
        self.geoserver_base = settings.senamhi_geoserver_url
        self.download_dir = download_dir or Path("data/shapefiles")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = settings.request_timeout

    def build_shapefile_url(self, warning_number: str, day: int, year: int) -> str:
        """
        Build shapefile download URL for a specific warning day.

        Args:
            warning_number: Warning number (e.g., "418")
            day: Day number (1-based, relative to warning start)
            year: Year of the warning

        Returns:
            Full download URL

        Example:
            >>> downloader.build_shapefile_url("418", 1, 2025)
            'https://idesep.senamhi.gob.pe/geoserver/g_aviso/ows?...'
        """
        filename = f"shp_aviso_{warning_number}_{day}_{year}.zip"
        viewparams = f"{warning_number}_{day}_{year}"

        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": "g_aviso:view_aviso",
            "format_options": f"filename:{filename}",
            "maxFeatures": "50",
            "viewparams": f"qry:{viewparams}",
            "outputFormat": "SHAPE-ZIP",
        }

        # Build query string
        query_parts = [f"{k}={v}" for k, v in params.items()]
        return f"{self.geoserver_base}?{'&'.join(query_parts)}"

    def calculate_warning_days(self, warning: WarningAlert) -> int:
        """
        Calculate number of days a warning spans.

        Args:
            warning: Warning alert object

        Returns:
            Number of days (minimum 1)
        """
        delta = warning.valid_until - warning.valid_from
        days = delta.days + 1  # Include both start and end day
        return max(1, days)

    def download_shapefile(
        self, warning_number: str, day: int, year: int
    ) -> Path | None:
        """
        Download a single shapefile for a warning day.

        Args:
            warning_number: Warning number
            day: Day number (1-based)
            year: Year

        Returns:
            Path to downloaded ZIP file, or None if failed
        """
        url = self.build_shapefile_url(warning_number, day, year)
        filename = f"warning_{warning_number}_day_{day}_{year}.zip"
        filepath = self.download_dir / filename

        # Skip if already downloaded
        if filepath.exists():
            logger.debug(f"  Already exists: {filename}")
            return filepath

        try:
            logger.debug(f"  Downloading day {day}...")

            response = requests.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            # Check if response is actually a ZIP file
            content_type = response.headers.get("Content-Type", "")
            if "zip" not in content_type.lower():
                logger.warning(f"  Unexpected content type: {content_type}")

            # Save file
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify it's a valid ZIP
            if not zipfile.is_zipfile(filepath):
                logger.warning("  Downloaded file is not a valid ZIP")
                filepath.unlink()
                return None

            logger.info(f"  ✓ Downloaded: {filename}")
            return filepath

        except requests.exceptions.RequestException as e:
            logger.error(f"  Download failed: {e}")
            if filepath.exists():
                filepath.unlink()
            return None

    def download_warning_shapefiles(self, warning: WarningAlert) -> list[Path]:
        """
        Download all shapefiles for a warning (all days).

        Args:
            warning: Warning alert object

        Returns:
            List of paths to downloaded ZIP files
        """
        if not warning.senamhi_id:
            logger.warning(
                f"Warning #{warning.warning_number} has no senamhi_id, cannot download shapefiles"
            )
            return []

        year = warning.valid_from.year
        num_days = self.calculate_warning_days(warning)

        logger.debug(f"Downloading shapefiles for Warning #{warning.warning_number}")
        logger.debug(
            f"Duration: {num_days} days ({warning.valid_from.date()} to {warning.valid_until.date()})"
        )

        downloaded = []
        for day in range(1, num_days + 1):
            filepath = self.download_shapefile(warning.warning_number, day, year)
            if filepath:
                downloaded.append(filepath)

        logger.info(f"Downloaded {len(downloaded)}/{num_days} shapefiles")
        return downloaded

    def list_downloaded_shapefiles(self) -> list[Path]:
        """List all downloaded shapefile ZIPs."""
        return sorted(self.download_dir.glob("warning_*.zip"))

    def cleanup_old_shapefiles(self, days_old: int = 30) -> int:
        """
        Remove shapefiles older than specified days.

        Args:
            days_old: Remove files older than this many days

        Returns:
            Number of files removed
        """
        cutoff = datetime.now() - timedelta(days=days_old)
        removed = 0

        for filepath in self.list_downloaded_shapefiles():
            if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff:
                filepath.unlink()
                removed += 1

        if removed > 0:
            logger.info(f"Removed {removed} old shapefile(s)")

        return removed
