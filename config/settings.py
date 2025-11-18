from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenMeteoModel(dict):
    """Open Meteo model configuration."""

    pass


class OpenMeteoVariable(dict):
    """Open Meteo variable configuration."""

    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    app_name: str = "SENAMHI Tracker"
    app_version: str = "0.1.0"

    # SENAMHI URLs
    senamhi_base_url: str = "https://www.senamhi.gob.pe"
    senamhi_forecast_url: str = "https://www.senamhi.gob.pe/?p=pronostico-meteorologico"
    senamhi_warnings_api: str = (
        "https://www.senamhi.gob.pe/app_senamhi/sisper/api/avisoMeteoroCabEmergencia"
    )

    database_url: str = "sqlite:///./data/weather.db"

    # Scraping configuration
    scrape_delay: float = 2.0
    request_timeout: int = 30
    user_agent: str = "SENAMHI-Tracker/0.1.0 (Educational Project)"

    scrape_all_departments: bool = True
    departments: str = "LIMA"

    # Scheduler configuration
    enable_scheduler: bool = False
    scheduler_start_immediately: bool = True
    log_file: str = "logs/scheduler.log"
    max_retries: int = 3
    retry_delay_seconds: int = 60

    debug: bool = True
    db_echo: bool = False

    # Scheduler intervals (in hours)
    forecast_scrape_interval: int = 24
    warning_scrape_interval: int = 6

    # Web server
    web_host: str = "127.0.0.1"
    web_port: int = 5000
    web_debug: bool = True

    # Paths for YAML configs
    coordinates_file: Path = Field(default=Path("config/coordinates.yaml"))
    openmeteo_file: Path = Field(default=Path("config/openmeteo.yaml"))

    # Cached configs
    _coordinates: dict[str, dict[str, list[float]]] | None = None
    _openmeteo_config: dict[str, Any] | None = None

    def get_departments_list(self) -> list[str]:
        """Parse departments from comma-separated string."""
        if self.scrape_all_departments:
            return []  # Return empty list to signal "all departments"
        return [d.strip().upper() for d in self.departments.split(",")]

    @property
    def coordinates(self) -> dict[str, dict[str, list[float]]]:
        """Load and cache coordinates from YAML."""
        if self._coordinates is None:
            with open(self.coordinates_file) as f:
                self._coordinates = yaml.safe_load(f)
        return self._coordinates

    @property
    def openmeteo_config(self) -> dict[str, Any]:
        """Load and cache Open-Meteo configuration from YAML."""
        if self._openmeteo_config is None:
            with open(self.openmeteo_file) as f:
                self._openmeteo_config = yaml.safe_load(f)
        return self._openmeteo_config

    def get_location_coordinates(
        self, department: str, location: str
    ) -> tuple[float, float] | None:
        """Get coordinates for a specific location."""
        dept_coords = self.coordinates.get(department.upper(), {})
        coords = dept_coords.get(location.upper())
        return tuple(coords) if coords else None

    def get_openmeteo_url(self) -> str:
        """Get Open-Meteo API URL."""
        return self.openmeteo_config.get("url", "")

    def get_openmeteo_models(self) -> list[dict]:
        """Get configured Open-Meteo models."""
        return self.openmeteo_config.get("models", [])

    def get_openmeteo_variables(self) -> list[dict]:
        """Get configured Open-Meteo variables."""
        return self.openmeteo_config.get("variables", [])


settings = Settings()
