"""Service for reading Peru boundaries (departments, districts)."""

from pathlib import Path
import geopandas as gpd


class BoundariesService:
    """Service for Peru administrative boundaries."""

    DEPARTMENTS_PATH = Path("data/boundaries/departments/DEPARTAMENTOS.shp")

    def __init__(self):
        """Initialize service and load shapefiles."""
        self._departments_gdf = None

    @property
    def departments_gdf(self) -> gpd.GeoDataFrame:
        """Lazy load departments geodataframe."""
        if self._departments_gdf is None and self.DEPARTMENTS_PATH.exists():
            self._departments_gdf = gpd.read_file(self.DEPARTMENTS_PATH)
            # Ensure WGS84
            if (
                self._departments_gdf.crs
                and self._departments_gdf.crs.to_epsg() != 4326
            ):
                self._departments_gdf = self._departments_gdf.to_crs(epsg=4326)
        return self._departments_gdf

    def get_department_bounds(self, department_name: str) -> dict | None:
        """
        Get bounding box for a department.

        Args:
            department_name: Department name (e.g., "LIMA")

        Returns:
            Dict with bounds: {"south": float, "west": float, "north": float, "east": float}
            or None if not found
        """
        if self.departments_gdf is None:
            return None

        # Find department (case insensitive)
        dept = self.departments_gdf[
            self.departments_gdf["DEPARTAMEN"].str.upper() == department_name.upper()
        ]

        if dept.empty:
            return None

        # Get bounds
        bounds = dept.total_bounds  # [minx, miny, maxx, maxy]

        return {
            "west": float(bounds[0]),
            "south": float(bounds[1]),
            "east": float(bounds[2]),
            "north": float(bounds[3]),
        }

    def get_department_geojson(self, department_name: str) -> dict | None:
        """
        Get GeoJSON for a department.

        Args:
            department_name: Department name (e.g., "LIMA")

        Returns:
            GeoJSON Feature dict or None if not found
        """
        if self.departments_gdf is None:
            return None

        # Find department (case insensitive)
        dept = self.departments_gdf[
            self.departments_gdf["DEPARTAMEN"].str.upper() == department_name.upper()
        ]

        if dept.empty:
            return None

        # Get geometry from the GeoDataFrame row
        geom = dept.iloc[0].geometry
        name = dept.iloc[0]["DEPARTAMEN"]

        return {
            "type": "Feature",
            "properties": {"name": name},
            "geometry": geom.__geo_interface__,
        }

    def get_all_departments_geojson(self) -> dict | None:
        """
        Get GeoJSON for all departments.

        Returns:
            GeoJSON FeatureCollection dict or None if not available
        """
        if self.departments_gdf is None:
            return None

        features = []
        for idx, row in self.departments_gdf.iterrows():
            features.append(
                {
                    "type": "Feature",
                    "properties": {"name": row["DEPARTAMEN"]},
                    "geometry": row.geometry.__geo_interface__,
                }
            )

        return {"type": "FeatureCollection", "features": features}
