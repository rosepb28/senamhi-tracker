"""CRUD operations for geospatial data (PostGIS only)."""

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from config.settings import settings

if settings.supports_postgis:
    from geoalchemy2.elements import WKTElement
    from shapely.geometry import MultiPolygon
    from app.storage.geo_models import WarningGeometry


def save_warning_geometry(
    db: Session,
    warning_id: int,
    warning_number: str,
    day_number: int,
    geometry: "MultiPolygon",
    nivel: int,
    shapefile_url: str | None = None,
    shapefile_path: Path | None = None,
) -> "WarningGeometry | None":
    """Save warning geometry to database (PostGIS only)."""
    if not settings.supports_postgis:
        return None

    # Convert Shapely geometry to WKT
    wkt_geom = WKTElement(geometry.wkt, srid=4326)

    # Check by warning_number + day_number + nivel
    existing = (
        db.query(WarningGeometry)
        .filter(
            WarningGeometry.warning_number == warning_number,
            WarningGeometry.day_number == day_number,
            WarningGeometry.nivel == nivel,
        )
        .first()
    )

    if existing:
        # Update existing
        existing.geometry = wkt_geom
        existing.shapefile_url = shapefile_url
        existing.shapefile_path = str(shapefile_path) if shapefile_path else None
        existing.downloaded_at = datetime.now()
        existing.updated_at = datetime.now()
        db.commit()
        db.refresh(existing)
        return existing

    # Create new
    geom_record = WarningGeometry(
        warning_id=warning_id,
        warning_number=warning_number,
        day_number=day_number,
        nivel=nivel,
        geometry=wkt_geom,
        shapefile_url=shapefile_url,
        shapefile_path=str(shapefile_path) if shapefile_path else None,
        downloaded_at=datetime.now(),
    )

    db.add(geom_record)
    db.commit()
    db.refresh(geom_record)

    return geom_record


def get_warning_geometries(
    db: Session, warning_id: int
) -> "list[WarningGeometry] | None":
    """
    Get all geometries for a warning (all days).

    Args:
        db: Database session
        warning_id: Warning ID

    Returns:
        List of WarningGeometry objects or None if PostGIS not available
    """
    if not settings.supports_postgis:
        return None

    return (
        db.query(WarningGeometry)
        .filter(WarningGeometry.warning_id == warning_id)
        .order_by(WarningGeometry.day_number)
        .all()
    )


def get_warning_geometry_by_day(
    db: Session, warning_id: int, day_number: int
) -> "WarningGeometry | None":
    """
    Get geometry for a specific warning day.

    Args:
        db: Database session
        warning_id: Warning ID
        day_number: Day number (1-based)

    Returns:
        WarningGeometry object or None if not found/PostGIS not available
    """
    if not settings.supports_postgis:
        return None

    return (
        db.query(WarningGeometry)
        .filter(
            WarningGeometry.warning_id == warning_id,
            WarningGeometry.day_number == day_number,
        )
        .first()
    )


def get_warning_geometries_by_number(
    db: Session, warning_number: str
) -> list["WarningGeometry"]:
    """Get all geometries for a warning by warning_number."""
    if not settings.supports_postgis:
        return []

    return (
        db.query(WarningGeometry)
        .filter(WarningGeometry.warning_number == warning_number)
        .order_by(WarningGeometry.day_number, WarningGeometry.nivel)
        .all()
    )


def get_warning_geometry_by_number_and_day(
    db: Session, warning_number: str, day_number: int
) -> list["WarningGeometry"]:
    """Get geometries for a specific warning day by warning_number."""
    if not settings.supports_postgis:
        return []

    return (
        db.query(WarningGeometry)
        .filter(
            WarningGeometry.warning_number == warning_number,
            WarningGeometry.day_number == day_number,
        )
        .all()
    )


def delete_warning_geometries(db: Session, warning_id: int) -> int:
    """
    Delete all geometries for a warning.

    Args:
        db: Database session
        warning_id: Warning ID

    Returns:
        Number of geometries deleted
    """
    if not settings.supports_postgis:
        return 0

    count = (
        db.query(WarningGeometry)
        .filter(WarningGeometry.warning_id == warning_id)
        .delete()
    )

    db.commit()
    return count
