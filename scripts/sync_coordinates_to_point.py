#!/usr/bin/env python
"""Sync latitude/longitude to PostGIS point geometry (PostgreSQL only)."""

from app.database import SessionLocal
from app.storage.models import Location
from config.settings import settings

if settings.supports_postgis:
    from geoalchemy2.elements import WKTElement


def sync_coordinates():
    """Sync existing lat/lon to point geometry."""
    if not settings.supports_postgis:
        print("⚠️  PostGIS not available (using SQLite). Skipping sync.")
        return

    db = SessionLocal()

    try:
        locations = (
            db.query(Location)
            .filter(Location.latitude.isnot(None), Location.longitude.isnot(None))
            .all()
        )

        print(f"Found {len(locations)} locations with coordinates")

        updated = 0
        for location in locations:
            # Create point from lat/lon
            location.point = WKTElement(
                f"POINT({location.longitude} {location.latitude})", srid=4326
            )
            updated += 1

        db.commit()
        print(f"✓ Synced {updated} locations to PostGIS point geometry")

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    sync_coordinates()
