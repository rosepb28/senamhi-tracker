"""Service for populating location coordinates."""

from pathlib import Path
import yaml
from rich.console import Console

from app.database import SessionLocal
from app.storage.models import Location

console = Console()


def populate_coordinates(skip_existing: bool = True) -> dict:
    """
    Populate location coordinates from config/coordinates.yaml.

    Args:
        skip_existing: Skip locations that already have coordinates

    Returns:
        Dict with stats: {'updated': int, 'skipped': int, 'not_found': int}
    """
    coords_file = Path("config/coordinates.yaml")

    if not coords_file.exists():
        console.print(f"[yellow]Coordinates file not found: {coords_file}[/yellow]")
        return {"updated": 0, "skipped": 0, "not_found": 0}

    # Load coordinates
    with open(coords_file) as f:
        coords_data = yaml.safe_load(f)

    db = SessionLocal()
    stats = {"updated": 0, "skipped": 0, "not_found": 0}

    try:
        locations = db.query(Location).all()

        for location in locations:
            # Skip if has coordinates and skip_existing=True
            if skip_existing and location.latitude is not None:
                stats["skipped"] += 1
                continue

            # Look up coordinates
            dept_coords = coords_data.get(location.department, {})
            coords = dept_coords.get(location.location)

            if coords and len(coords) == 2:
                location.latitude = coords[0]
                location.longitude = coords[1]
                stats["updated"] += 1
            else:
                stats["not_found"] += 1

        db.commit()

        if stats["updated"] > 0:
            console.print(
                f"[green]✓ Updated {stats['updated']} location(s) with coordinates[/green]"
            )
        if stats["not_found"] > 0:
            console.print(
                f"[yellow]⚠ {stats['not_found']} location(s) not found in coordinates.yaml[/yellow]"
            )

        return stats

    finally:
        db.close()
