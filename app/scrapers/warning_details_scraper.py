# app/scrapers/warning_details_scraper.py

"""Scraper for warning daily details from SENAMHI API."""

import requests
from loguru import logger
from config.settings import settings

from app.scrapers.warning_scraper import WarningScraper


class WarningDetailsScraper:
    """Scrapes daily details for weather warnings by department."""

    def __init__(self):
        """Initialize scraper."""
        self.timeout = settings.request_timeout
        self.user_agent = settings.user_agent
        self.api_base = settings.senamhi_warning_details_api

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def scrape_warning_details(self, senamhi_id: int, department: str) -> list[dict]:
        """
        Scrape daily details for a warning in a specific department.

        Args:
            senamhi_id: SENAMHI internal ID for the warning
            department: Department name (e.g., 'ANCASH')

        Returns:
            List of daily detail dictionaries
        """
        dept_id = WarningScraper.DEPARTMENT_IDS.get(department.upper())

        if not dept_id:
            logger.warning(f"No SENAMHI ID found for department: {department}")
            return []

        url = f"{self.api_base}/{senamhi_id}/{dept_id}"

        try:
            logger.debug(f"Fetching details: {url}")
            response = self.session.get(url, timeout=self.timeout)

            if not response.ok:
                logger.warning(
                    f"Failed to fetch details for warning {senamhi_id}, "
                    f"dept {department}: HTTP {response.status_code}"
                )
                return []

            data = response.json()

            # Extract aviso data
            aviso = data.get("Aviso", {})
            if not aviso:
                logger.warning(
                    f"No 'Aviso' key in response for {senamhi_id}/{department}"
                )
                return []

            mapas = aviso.get("mapas", [])
            if not mapas:
                logger.debug(f"No daily maps found for {senamhi_id}/{department}")
                return []

            # Parse each day's details
            details = []
            for mapa in mapas:
                detail = self._parse_daily_map(mapa, senamhi_id, department)
                if detail:
                    details.append(detail)

            logger.info(
                f"Scraped {len(details)} daily detail(s) for "
                f"warning {senamhi_id} in {department}"
            )

            return details

        except requests.RequestException as e:
            logger.error(f"Network error fetching warning details: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing warning details: {e}")
            return []

    def _parse_daily_map(
        self, mapa: dict, senamhi_id: int, department: str
    ) -> dict | None:
        """
        Parse a single day's map data.

        Args:
            mapa: Map dictionary from API response
            senamhi_id: SENAMHI warning ID
            department: Department name

        Returns:
            Dictionary with parsed data or None if invalid
        """
        try:
            day_number = mapa.get("numMapa")
            if day_number is None:
                logger.warning("Missing 'numMapa' in map data")
                return None

            # Extract affected provinces
            lugares = mapa.get("lugaresAfectados", [])
            affected_provinces = [
                lugar.get("descripcion")
                for lugar in lugares
                if lugar.get("descripcion")
            ]

            return {
                "senamhi_id": senamhi_id,
                "department": department.upper(),
                "day_number": int(day_number),
                "nivel": int(mapa.get("nivel", 0)),
                "description": mapa.get("descripcion", "").strip(),
                "affected_provinces": affected_provinces,
            }

        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing map data: {e}")
            return None

    def scrape_all_departments(
        self, senamhi_id: int, departments: list[str]
    ) -> dict[str, list[dict]]:
        """
        Scrape details for multiple departments.

        Args:
            senamhi_id: SENAMHI warning ID
            departments: List of department names

        Returns:
            Dictionary mapping department -> list of daily details
        """
        results = {}

        for department in departments:
            details = self.scrape_warning_details(senamhi_id, department)
            if details:
                results[department] = details

        return results
