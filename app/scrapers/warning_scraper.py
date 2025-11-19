"""Scraper for SENAMHI weather warnings."""

from datetime import datetime

import requests
from rich.console import Console

from config.settings import settings
from app.models.warning import Warning, WarningSeverity, WarningStatus

console = Console()


class WarningScraper:
    """Scraper for SENAMHI weather warnings."""

    # Department ID mapping
    DEPARTMENT_IDS = {
        "AMAZONAS": "01",
        "ANCASH": "02",
        "APURIMAC": "03",
        "AREQUIPA": "04",
        "AYACUCHO": "05",
        "CAJAMARCA": "06",
        "CALLAO": "07",
        "CUSCO": "08",
        "HUANCAVELICA": "09",
        "HUANUCO": "10",
        "ICA": "11",
        "JUNIN": "12",
        "LA LIBERTAD": "13",
        "LAMBAYEQUE": "14",
        "LIMA": "15",
        "LORETO": "16",
        "MADRE DE DIOS": "17",
        "MOQUEGUA": "18",
        "PASCO": "19",
        "PIURA": "20",
        "PUNO": "21",
        "SAN MARTIN": "22",
        "TACNA": "23",
        "TUMBES": "24",
        "UCAYALI": "25",
    }

    def __init__(self):
        """Initialize scraper."""
        self.timeout = settings.request_timeout
        self.user_agent = settings.user_agent
        self.api_base = settings.senamhi_warnings_api

    def _parse_senamhi_datetime(self, date_str: str) -> datetime:
        """Parse SENAMHI datetime format: DD/MM/YYYY HH:MM:SS."""
        return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")

    def _map_severity(self, nivel: str, color: str) -> WarningSeverity:
        """Map severity level to enum."""
        color_upper = color.upper()

        if color_upper == "VERDE":
            return WarningSeverity.GREEN
        elif color_upper == "AMARILLO":
            return WarningSeverity.YELLOW
        elif color_upper == "NARANJA":
            return WarningSeverity.ORANGE
        elif color_upper == "ROJO":
            return WarningSeverity.RED
        else:
            nivel_map = {
                "1": WarningSeverity.GREEN,
                "2": WarningSeverity.YELLOW,
                "3": WarningSeverity.ORANGE,
                "4": WarningSeverity.RED,
            }
            return nivel_map.get(str(nivel), WarningSeverity.YELLOW)

    def _parse_warning(self, aviso_data: dict, department: str) -> Warning | None:
        """Parse warning from API response."""
        try:
            # Skip forest fire warnings
            titulo = aviso_data["titulo"]
            if "incendios forestales" in titulo.lower():
                return None

            issued_at = self._parse_senamhi_datetime(aviso_data["fechaEmision"])
            valid_from = self._parse_senamhi_datetime(aviso_data["fechaInicio"])
            valid_until = self._parse_senamhi_datetime(aviso_data["fechaFin"])

            severity = self._map_severity(aviso_data["nivel"], aviso_data["colorNivel"])

            # Determine status based on dates
            now = datetime.now()
            if valid_from <= now <= valid_until:
                status = WarningStatus.VIGENTE
            elif valid_from > now:
                status = WarningStatus.EMITIDO
            else:
                status = WarningStatus.VENCIDO

            # Only scrape EMITIDO and VIGENTE
            if status == WarningStatus.VENCIDO:
                return None

            return Warning(
                senamhi_id=aviso_data["id"],
                warning_number=aviso_data["numero"],
                department=department,
                severity=severity,
                status=status,
                title=aviso_data["titulo"],
                description=aviso_data["descripcion"],
                valid_from=valid_from,
                valid_until=valid_until,
                issued_at=issued_at,
            )

        except Exception as e:
            console.print(f"[yellow]Failed to parse warning: {e}[/yellow]")
            return None

    def scrape_warnings_for_department(self, department: str) -> list[Warning]:
        """Scrape warnings for a specific department."""
        dept_upper = department.upper()

        if dept_upper not in self.DEPARTMENT_IDS:
            console.print(f"[yellow]Unknown department: {department}[/yellow]")
            return []

        dept_id = self.DEPARTMENT_IDS[dept_upper]
        url = f"{self.api_base}/{dept_id}"

        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if "Avisos" not in data:
                return []

            warnings = []
            for aviso in data["Avisos"]:
                warning = self._parse_warning(aviso, dept_upper)
                if warning:
                    warnings.append(warning)

            return warnings

        except Exception as e:
            console.print(f"[red]Error scraping {department}: {e}[/red]")
            return []

    def scrape_warnings(self, departments: list[str] | None = None) -> list[Warning]:
        """Scrape warnings for multiple departments."""
        if departments is None:
            departments = settings.get_departments_list()
            if not departments or settings.scrape_all_departments:
                departments = list(self.DEPARTMENT_IDS.keys())

        all_warnings = []
        seen_combinations = set()

        for department in departments:
            console.print(f"[dim]Scraping warnings for {department}...[/dim]")

            dept_warnings = self.scrape_warnings_for_department(department)

            # Deduplicate by (warning_number, department) combination
            for warning in dept_warnings:
                combination = (warning.warning_number, warning.department)
                if combination not in seen_combinations:
                    all_warnings.append(warning)
                    seen_combinations.add(combination)

        # Sort by issued_at (most recent first)
        all_warnings.sort(key=lambda w: w.issued_at, reverse=True)

        # NO limit - return all active warnings
        return all_warnings
