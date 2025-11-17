from flask import Blueprint, render_template

from app.database import SessionLocal
from app.services.openmeteo import OpenMeteoClient
from app.storage import crud

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Homepage - list all departments and active warnings."""
    db = SessionLocal()

    try:
        # Get all unique departments from locations
        locations = crud.get_locations(db, active_only=True)
        departments = sorted(list(set(loc.department for loc in locations)))

        # Get last update times
        from sqlalchemy import func

        last_forecast_update = db.query(func.max(crud.Forecast.scraped_at)).scalar()
        last_warning_update = db.query(func.max(crud.WarningAlert.scraped_at)).scalar()

        return render_template(
            "index.html",
            departments=departments,
            last_forecast_update=last_forecast_update,
            last_warning_update=last_warning_update,
        )

    finally:
        db.close()


@bp.route("/department/<name>")
def department(name):
    """Department view - show forecasts and warnings for department."""
    db = SessionLocal()

    try:
        dept_name = name.upper()

        # Get locations for this department
        locations = crud.get_locations(db, active_only=True)
        dept_locations = [loc for loc in locations if loc.department == dept_name]

        if not dept_locations:
            return render_template(
                "error.html", message=f"Department {dept_name} not found"
            ), 404

        # Get active warnings for THIS department only
        active_warnings = crud.get_active_warnings(db, department=dept_name)

        # Initialize Open Meteo client
        openmeteo_client = OpenMeteoClient()
        openmeteo_config = openmeteo_client.get_config()  # ← Obtener config

        # Get latest forecasts for each location + Open Meteo data
        location_forecasts = []
        for location in dept_locations:
            forecasts = crud.get_latest_forecasts(db, location_id=location.id)

            # Get Open Meteo data if coordinates available
            openmeteo_data = None
            if location.latitude is not None and location.longitude is not None:
                try:
                    openmeteo_data = openmeteo_client.get_hourly_forecast(
                        latitude=location.latitude, longitude=location.longitude
                    )
                except Exception as e:
                    print(
                        f"Error fetching Open Meteo data for {location.location}: {e}"
                    )

            if forecasts:
                location_forecasts.append(
                    {
                        "location": location,
                        "forecasts": forecasts[:3],
                        "openmeteo": openmeteo_data,
                    }
                )

        return render_template(
            "department.html",
            department=dept_name,
            locations=location_forecasts,
            warnings=active_warnings,
            openmeteo_config=openmeteo_config,
        )

    finally:
        db.close()
