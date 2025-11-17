from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class DailyForecast(BaseModel):
    """Daily weather forecast."""

    date: datetime
    day_name: str
    temp_max: int
    temp_min: int
    description: str
    icon_number: int

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """Parse date from string."""
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d")
        return v


class LocationForecast(BaseModel):
    """Weather forecast for a specific location with multiple days."""

    location: str
    department: str
    full_name: str
    forecasts: list[DailyForecast] = Field(min_length=1, max_length=7)
    issued_at: datetime
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
