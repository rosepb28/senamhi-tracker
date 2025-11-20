"""Tests for GeoService with both SQLite and PostGIS."""

import pytest
from app.services.geo_service import GeoService
from config.settings import settings


class TestGeoServiceSQLite:
    """Test GeoService with SQLite (Haversine fallback)."""

    @pytest.mark.skipif(
        settings.supports_postgis, reason="PostGIS available, skip SQLite tests"
    )
    def test_find_nearby_locations_haversine(self, db_session, sample_forecast_data):
        """Test finding nearby locations using Haversine formula."""
        from app.storage import crud
        from app.storage.models import Location

        # Save a location at known coordinates
        crud.save_forecast(db_session, sample_forecast_data)

        # Update the location with coordinates
        location = (
            db_session.query(Location).filter(Location.location == "LIMA ESTE").first()
        )
        location.latitude = -12.0464
        location.longitude = -77.0428
        db_session.commit()

        # Create service
        geo_service = GeoService(db_session)

        # Search near Lima (-12.0464, -77.0428)
        nearby = geo_service.find_nearby_locations(
            latitude=-12.0464,
            longitude=-77.0428,
            radius_km=50,
        )

        # Should find Lima Este
        assert len(nearby) >= 1
        assert any(loc.location == "LIMA ESTE" for loc in nearby)

    @pytest.mark.skipif(
        settings.supports_postgis, reason="PostGIS available, skip SQLite tests"
    )
    def test_find_nearby_locations_no_results(self, db_session):
        """Test search with no results."""
        geo_service = GeoService(db_session)

        # Search in middle of ocean
        nearby = geo_service.find_nearby_locations(
            latitude=0.0,
            longitude=0.0,
            radius_km=10,
        )

        assert len(nearby) == 0

    @pytest.mark.skipif(
        settings.supports_postgis, reason="PostGIS available, skip SQLite tests"
    )
    def test_backend_info_sqlite(self, db_session):
        """Test backend info returns SQLite information."""
        geo_service = GeoService(db_session)
        info = geo_service.get_backend_info()

        assert info["postgis_available"] is False
        assert info["database_type"] == "SQLite"
        assert "Python fallback" in info["spatial_queries"]

    @pytest.mark.skipif(
        settings.supports_postgis, reason="PostGIS available, skip SQLite tests"
    )
    def test_sync_points_not_available_sqlite(self, db_session):
        """Test that sync operations return False/0 on SQLite."""
        geo_service = GeoService(db_session)

        # Should return 0 (not available)
        assert geo_service.sync_all_points() == 0
        assert geo_service.sync_point_from_coordinates(1) is False
