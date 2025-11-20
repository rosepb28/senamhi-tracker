"""API routes for GeoJSON and geospatial data."""

from flask import Blueprint, jsonify

from app.database import SessionLocal
from app.services.geojson_service import GeoJSONService
from app.storage.models import WarningAlert
from config.settings import settings

api_bp = Blueprint("api", __name__, url_prefix="/api")


def get_geojson_service():
    """Factory function for GeoJSONService."""
    db = SessionLocal()
    return GeoJSONService(db), db


@api_bp.route("/warnings/<string:warning_number>/geometry")
def get_warning_geometry(warning_number: str):
    """Get all geometries for a warning (all days)."""
    if not settings.supports_postgis:
        return jsonify(
            {
                "error": "PostGIS not available",
                "message": "Geometry features require PostgreSQL + PostGIS",
            }
        ), 503

    service, db = get_geojson_service()

    try:
        # Find warning by number
        warning = (
            db.query(WarningAlert)
            .filter(WarningAlert.warning_number == warning_number)
            .first()
        )

        if not warning:
            return jsonify(
                {"error": "Warning not found", "warning_number": warning_number}
            ), 404

        # Get GeoJSON
        geojson = service.warning_geometry_to_geojson(warning_number=warning_number)

        if not geojson:
            return jsonify(
                {
                    "error": "No geometries found",
                    "message": "Warning has no associated geometries.",
                }
            ), 404

        # Add logging
        feature_count = len(geojson.get("features", []))
        print(f"API: Warning {warning_number} - Returning {feature_count} features")

        return jsonify(geojson)

    finally:
        db.close()


@api_bp.route("/warnings/<string:warning_number>/geometry/<int:day>")
def get_warning_geometry_day(warning_number: str, day: int):
    """
    Get geometry for a specific warning day.

    Args:
        warning_number: Warning number (e.g., "418")
        day: Day number (1-based)

    Example:
        GET /api/warnings/418/geometry/1
    """
    if not settings.supports_postgis:
        return jsonify(
            {
                "error": "PostGIS not available",
                "message": "Geometry features require PostgreSQL + PostGIS",
            }
        ), 503

    service, db = get_geojson_service()

    try:
        # Find warning
        warning = (
            db.query(WarningAlert)
            .filter(WarningAlert.warning_number == warning_number)
            .first()
        )

        if not warning:
            return jsonify(
                {"error": "Warning not found", "warning_number": warning_number}
            ), 404

        # Get GeoJSON for specific day
        geojson = service.warning_geometry_to_geojson(warning.id, day_number=day)

        if not geojson:
            return jsonify(
                {
                    "error": "Geometry not found",
                    "message": f"No geometry found for day {day}",
                }
            ), 404

        return jsonify(geojson)

    finally:
        db.close()


@api_bp.route("/warnings/active/geometries")
def get_active_warnings_geometries():
    """
    Get all active warnings with geometries.

    Returns GeoJSON FeatureCollection with all active warnings.

    Example:
        GET /api/warnings/active/geometries
    """
    if not settings.supports_postgis:
        return jsonify(
            {
                "error": "PostGIS not available",
                "message": "Geometry features require PostgreSQL + PostGIS",
            }
        ), 503

    service, db = get_geojson_service()

    try:
        geojson = service.get_active_warnings_geojson()
        return jsonify(geojson)

    finally:
        db.close()


@api_bp.route("/capabilities")
def get_capabilities():
    """
    Get API capabilities and feature availability.

    Example:
        GET /api/capabilities
    """
    service, db = get_geojson_service()

    try:
        caps = service.get_backend_capabilities()
        return jsonify(caps)

    finally:
        db.close()


@api_bp.route("/departments/<string:department_name>/bounds")
def get_department_bounds(department_name: str):
    """
    Get bounding box for a department.

    Example:
        GET /api/departments/LIMA/bounds
        Returns: {"south": -12.5, "west": -77.5, "north": -11.5, "east": -76.5}
    """
    from app.services.boundaries_service import BoundariesService

    service = BoundariesService()
    bounds = service.get_department_bounds(department_name)

    if not bounds:
        return jsonify(
            {"error": "Department not found", "department": department_name}
        ), 404

    return jsonify(bounds)


@api_bp.route("/departments/<string:department_name>/geometry")
def get_department_geometry(department_name: str):
    """
    Get GeoJSON geometry for a department.

    Example:
        GET /api/departments/LIMA/geometry
        Returns: GeoJSON Feature with department polygon
    """
    from app.services.boundaries_service import BoundariesService

    service = BoundariesService()
    geojson = service.get_department_geojson(department_name)

    if not geojson:
        return jsonify(
            {"error": "Department not found", "department": department_name}
        ), 404

    return jsonify(geojson)


@api_bp.route("/departments/all/geometry")
def get_all_departments_geometry():
    """
    Get GeoJSON for all departments.

    Returns:
        GeoJSON FeatureCollection with all department polygons
    """
    from app.services.boundaries_service import BoundariesService

    service = BoundariesService()
    geojson = service.get_all_departments_geojson()

    if not geojson:
        return jsonify({"error": "Departments data not available"}), 404

    return jsonify(geojson)


@api_bp.route("/warnings/<string:warning_number>/info")
def get_warning_info(warning_number: str):
    """
    Get warning metadata without geometry.

    Example:
        GET /api/warnings/418/info
    """
    db = SessionLocal()

    try:
        warning = (
            db.query(WarningAlert)
            .filter(WarningAlert.warning_number == warning_number)
            .first()
        )

        if not warning:
            return jsonify(
                {"error": "Warning not found", "warning_number": warning_number}
            ), 404

        return jsonify(
            {
                "warning_number": warning.warning_number,
                "senamhi_id": warning.senamhi_id,
                "title": warning.title,
                "description": warning.description,
                "severity": warning.severity,
                "status": warning.status,
                "department": warning.department,
                "valid_from": warning.valid_from.isoformat(),
                "valid_until": warning.valid_until.isoformat(),
                "issued_at": warning.issued_at.isoformat(),
            }
        )

    finally:
        db.close()


@api_bp.route("/health")
def health_check():
    """
    API health check endpoint.

    Returns API status and available features.

    Example:
        GET /api/health
    """
    return jsonify(
        {
            "status": "ok",
            "api_version": "1.0",
            "endpoints": {
                "capabilities": "/api/capabilities",
                "warning_info": "/api/warnings/<number>/info",
                "warning_geometry": "/api/warnings/<number>/geometry",
                "warning_geometry_day": "/api/warnings/<number>/geometry/<day>",
                "active_warnings": "/api/warnings/active/geometries",
            },
        }
    )


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response."""
    return jsonify(
        {"error": "Not found", "message": "The requested endpoint does not exist"}
    ), 404


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with JSON response."""
    return jsonify(
        {"error": "Internal server error", "message": "An unexpected error occurred"}
    ), 500
