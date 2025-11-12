from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WeatherIcon(str, Enum):
    """Weather icon types from SENAMHI."""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    UNKNOWN = "unknown"


class DailyForecast(BaseModel):
    """Single day weather forecast."""
    date: datetime
    day_name: str
    temp_max: int = Field(ge=-20, le=50)
    temp_min: int = Field(ge=-20, le=50)
    weather_icon: WeatherIcon = WeatherIcon.UNKNOWN
    description: str


class LocationForecast(BaseModel):
    """Weather forecast for a specific location with multiple days."""
    
    location: str
    department: str
    full_name: str
    forecasts: list[DailyForecast] = Field(min_length=1, max_length=3)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
