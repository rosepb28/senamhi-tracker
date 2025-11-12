import re
from datetime import datetime

from app.models.forecast import WeatherIcon


def parse_temperature(text: str) -> int:
    """Extract temperature value from text like '22ºC'."""
    match = re.search(r"(\d+)ºC", text)
    if match:
        return int(match.group(1))
    raise ValueError(f"Cannot parse temperature from: {text}")


def parse_date(date_text: str, year: int | None = None) -> datetime:
    """Parse Spanish date format to datetime object."""
    months_es = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    
    pattern = r"(\w+),\s+(\d+)\s+de\s+(\w+)"
    match = re.search(pattern, date_text.lower())
    
    if not match:
        raise ValueError(f"Cannot parse date from: {date_text}")
    
    day_name = match.group(1)
    day = int(match.group(2))
    month_name = match.group(3)
    
    month = months_es.get(month_name)
    if not month:
        raise ValueError(f"Unknown month: {month_name}")
    
    if year is None:
        year = datetime.now().year
    
    return datetime(year, month, day)


def extract_icon_type(icon_url: str) -> WeatherIcon:
    """Map SENAMHI icon filename to WeatherIcon enum."""
    icon_map = {
        "icon001": WeatherIcon.CLEAR,
        "icon002": WeatherIcon.PARTLY_CLOUDY,
        "icon003": WeatherIcon.PARTLY_CLOUDY,
        "icon004": WeatherIcon.CLOUDY,
        "icon005": WeatherIcon.CLOUDY,
        "icon006": WeatherIcon.RAIN,
        "icon007": WeatherIcon.RAIN,
        "icon008": WeatherIcon.STORM,
    }
    
    for key, value in icon_map.items():
        if key in icon_url:
            return value
    
    return WeatherIcon.UNKNOWN
