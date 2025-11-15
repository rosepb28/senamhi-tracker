"""Scraper for SENAMHI weather warnings."""
from datetime import datetime

import requests
from rich.console import Console

from app.config import settings
from app.models.warning import Warning, WarningSeverity, WarningStatus

console = Console()


class WarningScraper:
    """Scraper for SENAMHI weather warnings."""
    
    API_URL = "https://www.senamhi.gob.pe/app_senamhi/sisper/api/avisoMeteoroCabEmergencia/15"
    
    def __init__(self):
        """Initialize scraper."""
        self.timeout = settings.request_timeout
        self.user_agent = settings.user_agent
    
    def _parse_senamhi_datetime(self, date_str: str) -> datetime:
        """Parse SENAMHI datetime format: DD/MM/YYYY HH:MM:SS."""
        return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
    
    def _map_severity(self, nivel: str, color: str) -> WarningSeverity:
        """Map severity level to enum."""
        # Use color as primary indicator
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
            # Fallback to nivel
            nivel_map = {
                "1": WarningSeverity.GREEN,
                "2": WarningSeverity.YELLOW,
                "3": WarningSeverity.ORANGE,
                "4": WarningSeverity.RED,
            }
            return nivel_map.get(str(nivel), WarningSeverity.YELLOW)
    

    def _parse_warning(self, aviso_data: dict) -> Warning | None:
        """Parse warning from API response."""
        try:
            # Parse dates
            issued_at = self._parse_senamhi_datetime(aviso_data["fechaEmision"])
            valid_from = self._parse_senamhi_datetime(aviso_data["fechaInicio"])
            valid_until = self._parse_senamhi_datetime(aviso_data["fechaFin"])
            
            # Check if active or upcoming
            if not self._is_active_or_upcoming(valid_from, valid_until):
                return None
            
            # Map severity
            severity = self._map_severity(
                aviso_data["nivel"],
                aviso_data["colorNivel"]
            )
            
            return Warning(
                warning_number=aviso_data["numero"],
                severity=severity,
                title=aviso_data["titulo"],
                description=aviso_data["descripcion"],
                valid_from=valid_from,
                valid_until=valid_until,
                issued_at=issued_at,
            )
            
        except Exception as e:
            console.print(f"[yellow]Failed to parse warning: {e}[/yellow]")
            return None
    
    def scrape_warnings(self) -> list[Warning]:
        """Scrape warnings (active + recent past) with limit."""
        try:
            headers = {
                "User-Agent": self.user_agent,
            }
            
            response = requests.get(
                self.API_URL,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "Avisos" not in data:
                console.print("[yellow]No warnings found in API response[/yellow]")
                return []
            
            # Parse ALL warnings from API (active and past)
            warnings = []
            for aviso in data["Avisos"]:
                warning = self._parse_warning_without_filter(aviso)
                if warning:
                    warnings.append(warning)
            
            # Sort by issued_at (most recent first)
            warnings.sort(key=lambda w: w.issued_at, reverse=True)
            
            # Apply limit
            limited_warnings = warnings[:settings.max_warnings]
            
            if len(warnings) > settings.max_warnings:
                console.print(
                    f"[dim]Limited to {settings.max_warnings} most recent warnings "
                    f"(out of {len(warnings)} total)[/dim]"
                )
            
            return limited_warnings
            
        except Exception as e:
            console.print(f"[red]Error scraping warnings: {e}[/red]")
            return []


    def _parse_warning_without_filter(self, aviso_data: dict) -> Warning | None:
        """Parse warning from API response without date filtering."""
        try:
            # Skip forest fire warnings
            titulo = aviso_data["titulo"]
            if "incendios forestales" in titulo.lower():
                return None
            
            issued_at = self._parse_senamhi_datetime(aviso_data["fechaEmision"])
            valid_from = self._parse_senamhi_datetime(aviso_data["fechaInicio"])
            valid_until = self._parse_senamhi_datetime(aviso_data["fechaFin"])
            
            severity = self._map_severity(
                aviso_data["nivel"],
                aviso_data["colorNivel"]
            )
            
            # Determine status based on dates
            now = datetime.now()
            if valid_from <= now <= valid_until:
                status = WarningStatus.VIGENTE
            elif valid_from > now:
                status = WarningStatus.EMITIDO
            else:
                status = WarningStatus.VENCIDO
            
            return Warning(
                warning_number=aviso_data["numero"],
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