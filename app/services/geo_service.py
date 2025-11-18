# app/services/geo_service.py
"""Geospatial service with fallback support for SQLite."""

from math import asin, cos, radians, sin, sqrt

from sqlalchemy.orm import Session

from app.storage.models import Location
from config.settings import settings

# Import PostGIS functions only if available
if settings.supports_postgis:
    from geoalchemy2.functions import ST_DWithin
    from geoalchemy2.elements import WKTElement


class GeoService:
    """Service for geospatial operations with SQLite fallback."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    def find_nearby_locations(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
    ) -> list[Location]:
        """
        Find locations within radius of a point.

        Uses PostGIS ST_DWithin if available, otherwise falls back to
        Haversine formula calculation in Python.

        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            radius_km: Search radius in kilometers

        Returns:
            List of locations within radius
        """
        if settings.supports_postgis:
            return self._find_nearby_postgis(latitude, longitude, radius_km)
        else:
            return self._find_nearby_haversine(latitude, longitude, radius_km)

    def _find_nearby_postgis(
        self, latitude: float, longitude: float, radius_km: float
    ) -> list[Location]:
        """Find nearby locations using PostGIS (fast)."""
        # Create point from coordinates
        point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)

        # Query with spatial index
        # ST_DWithin uses meters for geography type
        return (
            self.db.query(Location)
            .filter(
                Location.point.isnot(None),
                ST_DWithin(Location.point, point, radius_km * 1000),
            )
            .all()
        )

    def _find_nearby_haversine(
        self, latitude: float, longitude: float, radius_km: float
    ) -> list[Location]:
        """Find nearby locations using Haversine formula (Python fallback)."""

        def haversine_distance(
            lat1: float, lon1: float, lat2: float, lon2: float
        ) -> float:
            """Calculate great circle distance in kilometers."""
            R = 6371  # Earth radius in kilometers

            # Convert to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))

            return R * c

        # Get all locations with coordinates
        all_locations = (
            self.db.query(Location)
            .filter(
                Location.latitude.isnot(None),
                Location.longitude.isnot(None),
            )
            .all()
        )

        # Filter by distance in Python
        nearby = []
        for location in all_locations:
            distance = haversine_distance(
                latitude, longitude, location.latitude, location.longitude
            )
            if distance <= radius_km:
                nearby.append(location)

        return nearby

    def sync_point_from_coordinates(self, location_id: int) -> bool:
        """
        Sync point geometry from lat/lon for a single location.

        Args:
            location_id: Location ID to sync

        Returns:
            True if synced, False if PostGIS not available or no coordinates
        """
        if not settings.supports_postgis:
            return False

        location = self.db.query(Location).filter(Location.id == location_id).first()

        if not location or not location.latitude or not location.longitude:
            return False

        # Update point geometry
        location.point = WKTElement(
            f"POINT({location.longitude} {location.latitude})", srid=4326
        )

        self.db.commit()
        return True

    def sync_all_points(self) -> int:
        """
        Sync point geometries for all locations with coordinates.

        Returns:
            Number of locations synced
        """
        if not settings.supports_postgis:
            return 0

        locations = (
            self.db.query(Location)
            .filter(
                Location.latitude.isnot(None),
                Location.longitude.isnot(None),
            )
            .all()
        )

        count = 0
        for location in locations:
            location.point = WKTElement(
                f"POINT({location.longitude} {location.latitude})", srid=4326
            )
            count += 1

        self.db.commit()
        return count

    def get_backend_info(self) -> dict:
        """Get information about the geospatial backend in use."""
        return {
            "postgis_available": settings.supports_postgis,
            "database_type": "PostgreSQL" if settings.is_postgresql else "SQLite",
            "spatial_queries": "Native (PostGIS)"
            if settings.supports_postgis
            else "Python fallback (Haversine)",
        }
