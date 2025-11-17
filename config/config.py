from pydantic_settings import BaseSettings, SettingsConfigDict


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

    def get_departments_list(self) -> list[str]:
        """Parse departments from comma-separated string."""
        if self.scrape_all_departments:
            return []  # Return empty list to signal "all departments"
        return [d.strip().upper() for d in self.departments.split(",")]


settings = Settings()
