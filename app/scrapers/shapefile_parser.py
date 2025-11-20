"""Parser for SENAMHI warning shapefiles."""

import zipfile
from pathlib import Path

import geopandas as gpd
from rich.console import Console
from shapely.geometry import MultiPolygon, Polygon

from config.settings import settings

console = Console()


class ShapefileParser:
    """Parse shapefiles and extract geometries."""

    def __init__(self):
        """Initialize parser."""
        pass

    def parse_shapefile_zip(self, zip_path: Path) -> list[dict] | None:
        """
        Parse a shapefile ZIP and extract individual polygons with their nivel.

        Args:
            zip_path: Path to shapefile ZIP file

        Returns:
            List of dicts with 'geometry' and 'nivel', or None if parsing failed
        """
        if not settings.supports_postgis:
            console.print(
                "[yellow]PostGIS not available, cannot parse geometries[/yellow]"
            )
            return None

        try:
            # Read shapefile directly from ZIP
            gdf = gpd.read_file(f"zip://{zip_path}")

            if gdf.empty:
                console.print(f"[yellow]Empty shapefile: {zip_path.name}[/yellow]")
                return None

            # Convert to EPSG:4326 if needed (do it once for entire dataframe)
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            # Extract individual polygons with their nivel
            polygons = []
            for idx, row in gdf.iterrows():
                geom = row.geometry
                if geom is None:
                    continue

                # Extract nivel (parse "Nivel 1" -> 1)
                nivel_str = row.get("nivel", "Nivel 1")
                try:
                    nivel = (
                        int(nivel_str.split()[-1])
                        if isinstance(nivel_str, str)
                        else int(nivel_str)
                    )
                except (ValueError, IndexError):
                    nivel = 1

                # Convert Polygon to MultiPolygon if needed
                if isinstance(geom, Polygon):
                    geom = MultiPolygon([geom])
                elif isinstance(geom, MultiPolygon):
                    pass  # Already MultiPolygon
                else:
                    continue  # Skip invalid geometries

                polygons.append({"geometry": geom, "nivel": nivel})

            if not polygons:
                console.print(
                    f"[yellow]No valid geometries found in {zip_path.name}[/yellow]"
                )
                return None

            console.print(
                f"[green]✓ Parsed {len(polygons)} polygon(s) from {zip_path.name}[/green]"
            )

            return polygons

        except Exception as e:
            console.print(f"[red]Error parsing {zip_path.name}: {e}[/red]")
            return None

    def extract_shapefile_info(self, zip_path: Path) -> dict:
        """
        Extract metadata from shapefile without full parsing.

        Args:
            zip_path: Path to shapefile ZIP

        Returns:
            Dict with shapefile information
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                files = z.namelist()
                shp_files = [f for f in files if f.endswith(".shp")]

                return {
                    "zip_name": zip_path.name,
                    "size_kb": zip_path.stat().st_size / 1024,
                    "files": len(files),
                    "shp_files": len(shp_files),
                    "has_shp": len(shp_files) > 0,
                }

        except Exception as e:
            console.print(f"[red]Error reading {zip_path.name}: {e}[/red]")
            return {"error": str(e)}

    def validate_shapefile_zip(self, zip_path: Path) -> bool:
        """
        Validate that a ZIP contains required shapefile components.

        A valid shapefile needs at least: .shp, .shx, .dbf

        Args:
            zip_path: Path to shapefile ZIP

        Returns:
            True if valid shapefile ZIP
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                files = set(z.namelist())

                # Check for required extensions
                has_shp = any(f.endswith(".shp") for f in files)
                has_shx = any(f.endswith(".shx") for f in files)
                has_dbf = any(f.endswith(".dbf") for f in files)

                is_valid = has_shp and has_shx and has_dbf

                if not is_valid:
                    missing = []
                    if not has_shp:
                        missing.append(".shp")
                    if not has_shx:
                        missing.append(".shx")
                    if not has_dbf:
                        missing.append(".dbf")

                    console.print(
                        f"[yellow]Invalid shapefile (missing: {', '.join(missing)})[/yellow]"
                    )

                return is_valid

        except Exception as e:
            console.print(f"[red]Error validating {zip_path.name}: {e}[/red]")
            return False
