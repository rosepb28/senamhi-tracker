from datetime import datetime, date

from app.scrapers.utils import parse_date, parse_temperature
from typer.testing import CliRunner
from app.main import app

runner = CliRunner()


def test_parse_temperature():
    """Test temperature extraction from text."""
    assert parse_temperature("22ºC") == 22
    assert parse_temperature("9ºC") == 9
    assert parse_temperature("  15ºC  ") == 15


def test_parse_date():
    """Test Spanish date parsing."""
    parsed = parse_date("miércoles, 12 de noviembre", year=2024)
    assert parsed.day == 12
    assert parsed.month == 11
    assert parsed.year == 2024
    assert isinstance(parsed, date)


def test_parse_issued_date():
    """Test issued date parsing."""
    from app.scrapers.utils import parse_issued_date

    issued = parse_issued_date("Emisión: martes, 11 de noviembre del 2025")
    assert issued.day == 11
    assert issued.month == 11
    assert issued.year == 2025
    assert isinstance(issued, datetime)


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
        assert len(location.forecasts) <= 7


def test_scraper_multiple_departments():
    """Test scraping multiple departments."""
    from app.scrapers.forecast_scraper import ForecastScraper

    scraper = ForecastScraper()

    # Test with multiple departments (if they exist)
    forecasts = scraper.scrape_forecasts(departments=["LIMA", "CUSCO"])

    departments_found = set(f.department for f in forecasts)

    assert len(departments_found) >= 1
    assert "LIMA" in departments_found or "CUSCO" in departments_found


def test_scrape_help():
    """Test scrape command help."""
    result = runner.invoke(app, ["scrape", "--help"])
    assert result.exit_code == 0
    assert "forecasts" in result.stdout
    assert "warnings" in result.stdout


def test_scrape_forecasts_help():
    """Test scrape forecasts command help."""
    result = runner.invoke(app, ["scrape", "forecasts", "--help"])
    assert result.exit_code == 0
    assert "Scrape weather forecasts" in result.stdout


def test_scrape_warnings_help():
    """Test scrape warnings command help."""
    result = runner.invoke(app, ["scrape", "warnings", "--help"])
    assert result.exit_code == 0
    assert "Scrape weather warnings" in result.stdout


def test_get_all_departments():
    """Test discovering all departments."""
    from app.scrapers.forecast_scraper import ForecastScraper

    scraper = ForecastScraper()
    departments = scraper.get_all_departments()

    assert len(departments) > 0
    assert "LIMA" in departments
    assert all(dept.isupper() for dept in departments)
