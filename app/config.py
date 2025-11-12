from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    app_name: str = "SENAMHI Tracker"
    app_version: str = "0.1.0"
    
    senamhi_base_url: str = "https://www.senamhi.gob.pe"
    senamhi_forecast_url: str = "https://www.senamhi.gob.pe/?p=pronostico-meteorologico"
    
    database_url: str = "sqlite:///./data/weather.db"
    
    scrape_delay: float = 2.0
    request_timeout: int = 30
    user_agent: str = "SENAMHI-Tracker/0.1.0 (Educational Project)"
    
    departments: str = "LIMA"
    
    debug: bool = True
    db_echo: bool = False
    
    def get_departments_list(self) -> list[str]:
        """Parse departments from comma-separated string."""
        return [d.strip().upper() for d in self.departments.split(",")]


settings = Settings()
