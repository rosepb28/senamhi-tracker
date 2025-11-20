"""Service for GeoJSON conversion and operations."""

import json

from sqlalchemy.orm import Session

from app.storage.models import WarningAlert
from config.settings import settings

if settings.supports_postgis:
    from geoalchemy2.functions import ST_AsGeoJSON
    from app.storage.geo_models import WarningGeometry


class GeoJSONService:
    """Service for GeoJSON operations."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    def warning_geometry_to_geojson(
        self,
        warning_id: int | None = None,
        warning_number: str | None = None,
        day_number: int | None = None,
    ) -> dict | None:
        """
        Convert warning geometry to GeoJSON Feature.

        Args:
            warning_id: Warning ID (deprecated, use warning_number instead)
            warning_number: Warning number (e.g., "418") - preferred for multi-dept warnings
            day_number: Optional specific day (1-based). If None, returns all days.

        Returns:
            GeoJSON Feature or FeatureCollection, or None if not available
        """
        if not settings.supports_postgis:
            return None

        # Get warning info for metadata
        if warning_number:
            warning = (
                self.db.query(WarningAlert)
                .filter(WarningAlert.warning_number == warning_number)
                .first()
            )
            if not warning:
                return None
        elif warning_id:
            warning = (
                self.db.query(WarningAlert)
                .filter(WarningAlert.id == warning_id)
                .first()
            )
            if not warning:
                return None
            warning_number = warning.warning_number
        else:
            return None

        # Query by warning_number instead of warning_id
        from app.storage.geo_crud import (
            get_warning_geometries_by_number,
            get_warning_geometry_by_number_and_day,
        )

        # Single day requested
        if day_number is not None:
            geometries = get_warning_geometry_by_number_and_day(
                self.db, warning_number, day_number
            )
            if not geometries:
                return None

            features = [
                self._create_geojson_feature(geom, warning)
                for geom in geometries
                if geom.geometry
            ]

            return {
                "type": "FeatureCollection",
                "features": features,
            }

        # All days
        geometries = get_warning_geometries_by_number(self.db, warning_number)
        if not geometries:
            return None

        features = [
            self._create_geojson_feature(geom, warning)
            for geom in geometries
            if geom.geometry
        ]

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    def _create_geojson_feature(
        self, geometry_record: "WarningGeometry", warning: WarningAlert
    ) -> dict:
        """Create GeoJSON Feature from geometry record."""
        # Get GeoJSON from PostGIS
        geojson_str = self.db.query(ST_AsGeoJSON(geometry_record.geometry)).scalar()

        geometry_dict = json.loads(geojson_str) if geojson_str else None

        return {
            "type": "Feature",
            "geometry": geometry_dict,
            "properties": {
                "warning_id": warning.id,
                "warning_number": warning.warning_number,
                "day_number": geometry_record.day_number,
                "nivel": geometry_record.nivel,
                "title": warning.title,
                "severity": warning.severity,
                "status": warning.status,
                "department": warning.department,
                "valid_from": warning.valid_from.isoformat(),
                "valid_until": warning.valid_until.isoformat(),
                "issued_at": warning.issued_at.isoformat(),
            },
        }

    def get_active_warnings_geojson(self) -> dict:
        """
        Get all active warnings with geometries as GeoJSON FeatureCollection.

        Returns:
            GeoJSON FeatureCollection
        """
        if not settings.supports_postgis:
            return {"type": "FeatureCollection", "features": []}

        # Get active warnings
        from app.storage.crud import get_active_warnings

        active_warnings = get_active_warnings(self.db)
        features = []

        for warning in active_warnings:
            geojson = self.warning_geometry_to_geojson(warning.id)
            if geojson and geojson.get("type") == "FeatureCollection":
                features.extend(geojson["features"])
            elif geojson and geojson.get("type") == "Feature":
                features.append(geojson)

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    def get_backend_capabilities(self) -> dict:
        """Get GeoJSON backend capabilities."""
        return {
            "geojson_available": settings.supports_postgis,
            "database_type": "PostgreSQL" if settings.is_postgresql else "SQLite",
            "features": {
                "warning_geometries": settings.supports_postgis,
                "department_boundaries": False,  # TODO: Implement in next commit
                "spatial_queries": settings.supports_postgis,
            },
        }
