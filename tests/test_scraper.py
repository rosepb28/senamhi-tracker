from datetime import datetime

from app.scrapers.utils import extract_icon_type, parse_date, parse_temperature
from app.models.forecast import WeatherIcon


def test_parse_temperature():
    """Test temperature extraction from text."""
    assert parse_temperature("22ºC") == 22
    assert parse_temperature("9ºC") == 9
    assert parse_temperature("  15ºC  ") == 15


def test_parse_date():
    """Test Spanish date parsing."""
    date = parse_date("miércoles, 12 de noviembre", year=2024)
    assert date.day == 12
    assert date.month == 11
    assert date.year == 2024


def test_extract_icon_type():
    """Test weather icon type mapping."""
    assert extract_icon_type("icon001.png") == WeatherIcon.CLEAR
    assert extract_icon_type("icon002.png") == WeatherIcon.PARTLY_CLOUDY
    assert extract_icon_type("icon006.png") == WeatherIcon.RAIN
    assert extract_icon_type("icon999.png") == WeatherIcon.UNKNOWN


def test_scraper_integration():
    """Integration test for forecast scraper."""
    from app.scrapers.forecast_scraper import ForecastScraper
    
    scraper = ForecastScraper()
    
    # Test with Lima only
    forecasts = scraper.scrape_forecasts(departments=["LIMA"])
    
    assert len(forecasts) > 0
    assert len(forecasts) <= 15
    
    for location in forecasts:
        assert location.location
        assert location.department == "LIMA"
        assert "LIMA" in location.full_name
        assert len(location.forecasts) >= 1
        assert len(location.forecasts) <= 3
        
        for daily in location.forecasts:
            assert daily.temp_max > daily.temp_min
            assert -20 <= daily.temp_min <= 50
            assert -20 <= daily.temp_max <= 50
            assert daily.description
            assert daily.day_name

def test_scraper_multiple_departments():
    """Test scraping multiple departments."""
    from app.scrapers.forecast_scraper import ForecastScraper
    
    scraper = ForecastScraper()
    
    # Test with multiple departments (if they exist)
    forecasts = scraper.scrape_forecasts(departments=["LIMA", "CUSCO"])
    
    departments_found = set(f.department for f in forecasts)
    
    assert len(departments_found) >= 1
    assert "LIMA" in departments_found or "CUSCO" in departments_found