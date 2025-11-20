"""Integration tests for WeatherService."""

import pytest
from app.storage import crud
from config.settings import settings


@pytest.mark.skipif(
    settings.supports_postgis, reason="PostGIS available, skip SQLite tests"
)
class TestWeatherServiceForecasts:
    """Test forecast operations in WeatherService."""

    def test_save_and_retrieve_forecasts(self, weather_service, sample_forecast_data):
        """Test saving and retrieving forecast data."""
        # Save forecast
        _ = weather_service.update_forecasts(departments=["LIMA"], force=True)

        # Mock the scraper response - in real test, you'd mock the scraper
        # For now, we test the service layer assuming scrapers work
        saved = crud.save_forecast(weather_service.db, sample_forecast_data)

        assert len(saved) == 2
        assert saved[0].temp_max == 24
        assert saved[1].temp_max == 25

    def test_get_location_forecasts(self, weather_service, sample_forecast_data):
        """Test retrieving forecasts for a location."""
        # Save sample data
        crud.save_forecast(weather_service.db, sample_forecast_data)

        # Retrieve
        result = weather_service.get_location_forecasts("LIMA ESTE")

        assert result is not None
        assert result["location"].location == "LIMA ESTE"
        assert len(result["forecasts"]) == 2

    def test_get_location_forecasts_not_found(self, weather_service):
        """Test retrieving forecasts for non-existent location."""
        result = weather_service.get_location_forecasts("NONEXISTENT")

        assert result is None

    def test_get_all_locations(self, weather_service, sample_forecast_data):
        """Test retrieving all locations."""
        # Save sample data
        crud.save_forecast(weather_service.db, sample_forecast_data)

        # Retrieve
        locations = weather_service.get_all_locations()

        assert len(locations) == 1
        assert locations[0].location == "LIMA ESTE"
        assert locations[0].department == "LIMA"

    def test_duplicate_forecast_handling(self, weather_service, sample_forecast_data):
        """Test that duplicate forecasts are handled correctly."""
        # Save once
        saved1 = crud.save_forecast(weather_service.db, sample_forecast_data)

        # Save again with same data
        saved2 = crud.save_forecast(weather_service.db, sample_forecast_data)

        # Should create new entries (as per current CRUD logic)
        assert len(saved1) == 2
        assert len(saved2) == 2

        # But location should be reused
        locations = weather_service.get_all_locations()
        assert len(locations) == 1


@pytest.mark.skipif(
    settings.supports_postgis, reason="PostGIS available, skip SQLite tests"
)
class TestWeatherServiceWarnings:
    """Test warning operations in WeatherService."""

    def test_save_and_retrieve_warnings(self, weather_service, sample_warning_data):
        """Test saving and retrieving warning data."""
        # Save warning
        saved = crud.save_warning(weather_service.db, sample_warning_data)

        assert saved.warning_number == "001-2025"
        assert saved.department == "LIMA"
        assert saved.severity == "amarillo"

    def test_get_warnings_filtered(self, weather_service, sample_warning_data):
        """Test retrieving warnings with filters."""
        # Save warning
        crud.save_warning(weather_service.db, sample_warning_data)

        # Retrieve with severity filter
        warnings = weather_service.get_warnings(severity="amarillo")

        assert len(warnings) == 1
        assert warnings[0].severity == "amarillo"

    def test_get_warning_details(self, weather_service, sample_warning_data):
        """Test retrieving specific warning details."""
        # Save warning
        crud.save_warning(weather_service.db, sample_warning_data)

        # Retrieve by number
        warning = weather_service.get_warning_details("001-2025", "LIMA")

        assert warning is not None
        assert warning.title == "Aviso de lluvia moderada"

    def test_update_existing_warning(self, weather_service, sample_warning_data):
        """Test updating an existing warning."""
        # Save initial warning
        crud.save_warning(weather_service.db, sample_warning_data)

        # Modify and save again
        sample_warning_data.title = "Aviso actualizado"
        updated = crud.save_warning(weather_service.db, sample_warning_data)

        assert updated.title == "Aviso actualizado"

        # Verify only one warning exists
        warnings = weather_service.get_warnings()
        assert len(warnings) == 1


@pytest.mark.skipif(
    settings.supports_postgis, reason="PostGIS available, skip SQLite tests"
)
class TestWeatherServiceIntegration:
    """Integration tests for combined operations."""

    def test_get_department_data(
        self, weather_service, sample_forecast_data, sample_warning_data
    ):
        """Test retrieving all data for a department."""
        # Save sample data
        crud.save_forecast(weather_service.db, sample_forecast_data)
        crud.save_warning(weather_service.db, sample_warning_data)

        # Retrieve department data
        result = weather_service.get_department_data("LIMA")

        assert result["department"] == "LIMA"
        assert len(result["locations"]) == 1
        assert len(result["warnings"]) == 1

    def test_database_status(self, weather_service, sample_forecast_data):
        """Test database statistics retrieval."""
        # Save sample data
        crud.save_forecast(weather_service.db, sample_forecast_data)

        # Get status
        status = weather_service.get_database_status()

        assert status["locations"] == 1
        assert status["total_forecasts"] == 2
        assert status["latest_issued"] is not None
        assert "LIMA" in status["departments"]
        assert status["departments"]["LIMA"] == 1

    def test_forecast_history(self, weather_service, sample_forecast_data):
        """Test forecast history retrieval."""
        from datetime import date

        # Save sample data
        crud.save_forecast(weather_service.db, sample_forecast_data)

        # Get history
        history = weather_service.get_forecast_history("LIMA ESTE", date(2025, 11, 19))

        assert history is not None
        assert len(history) == 1
        assert history[0].temp_max == 24
