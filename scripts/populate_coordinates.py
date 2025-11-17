"""Populate location coordinates for Open Meteo integration."""

import sys
from pathlib import Path

import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.storage import crud

# Load coordinates from config
CONFIG_PATH = Path(__file__).parent.parent / "config" / "coordinates.yaml"

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        COORDINATES_CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Error: Config file not found at {CONFIG_PATH}")
    sys.exit(1)

# Flatten coordinates dict
COORDINATES = {}
for department, locations in COORDINATES_CONFIG.items():
    for location, coords in locations.items():
        COORDINATES[location.upper()] = tuple(coords)


def populate_coordinates(skip_existing: bool = False):
    """
    Populate coordinates for all locations in database.

    Args:
        skip_existing: If True, skip locations that already have coordinates
    """
    db = SessionLocal()

    try:
        locations = crud.get_locations(db, active_only=False)

        updated_count = 0
        skipped_count = 0
        missing_count = 0

        print(f"Found {len(locations)} locations in database\n")

        for location in locations:
            # Skip if already has coordinates
            if (
                skip_existing
                and location.latitude is not None
                and location.longitude is not None
            ):
                print(
                    f"⊙ {location.location} ({location.department}): Already has coordinates"
                )
                skipped_count += 1
                continue

            location_upper = location.location.upper()

            if location_upper in COORDINATES:
                lat, lon = COORDINATES[location_upper]

                # Update location
                location.latitude = lat
                location.longitude = lon

                db.commit()

                print(f"✓ {location.location} ({location.department}): {lat}, {lon}")
                updated_count += 1
            else:
                print(f"✗ {location.location} ({location.department}): No coordinates")
                missing_count += 1

        print(f"\n{'=' * 60}")
        print(f"Updated: {updated_count}")
        print(f"Skipped (already populated): {skipped_count}")
        print(f"Missing: {missing_count}")
        print(f"{'=' * 60}\n")

        if missing_count > 0:
            print("💡 Tip: Add missing coordinates to config/coordinates.yaml")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Populate location coordinates from config"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip locations that already have coordinates",
    )
    args = parser.parse_args()

    populate_coordinates(skip_existing=args.skip_existing)
