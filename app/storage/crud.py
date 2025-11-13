"""CRUD operations for database."""

from datetime import UTC, date, datetime

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.forecast import LocationForecast as PydanticLocationForecast
from app.storage.models import Forecast, Location
from app.storage.models import ScrapeRun


def get_or_create_location(
    db: Session, location: str, department: str, full_name: str
) -> Location:
    """Get existing location or create new one."""
    db_location = db.query(Location).filter(Location.location == location).first()

    if not db_location:
        db_location = Location(
            location=location,
            department=department,
            full_name=full_name,
        )
        db.add(db_location)
        db.commit()
        db.refresh(db_location)

    return db_location


def save_forecast(
    db: Session, location_forecast: PydanticLocationForecast
) -> list[Forecast]:
    """Save location forecast to database."""
    db_location = get_or_create_location(
        db,
        location_forecast.location,
        location_forecast.department,
        location_forecast.full_name,
    )

    saved_forecasts = []

    for daily in location_forecast.forecasts:
        db_forecast = Forecast(
            location_id=db_location.id,
            forecast_date=daily.date,
            day_name=daily.day_name,
            temp_max=daily.temp_max,
            temp_min=daily.temp_min,
            weather_icon=daily.weather_icon.value,
            description=daily.description,
            issued_at=location_forecast.issued_at,
            scraped_at=location_forecast.scraped_at,
        )
        db.add(db_forecast)
        saved_forecasts.append(db_forecast)

    db.commit()

    for forecast in saved_forecasts:
        db.refresh(forecast)

    return saved_forecasts


def get_locations(db: Session, active_only: bool = True) -> list[Location]:
    """Get all locations."""
    query = db.query(Location)

    if active_only:
        query = query.filter(Location.active)

    return query.all()


def get_location_by_name(db: Session, location: str) -> Location | None:
    """Get location by name."""
    return db.query(Location).filter(Location.location == location).first()


def get_latest_forecasts(db: Session, location_id: int | None = None) -> list[Forecast]:
    """Get latest forecasts for a location or all locations."""
    subquery = (
        db.query(
            Forecast.location_id,
            Forecast.forecast_date,
            func.max(Forecast.scraped_at).label("max_scraped"),
        )
        .group_by(Forecast.location_id, Forecast.forecast_date)
        .subquery()
    )

    query = db.query(Forecast).join(
        subquery,
        and_(
            Forecast.location_id == subquery.c.location_id,
            Forecast.forecast_date == subquery.c.forecast_date,
            Forecast.scraped_at == subquery.c.max_scraped,
        ),
    )

    if location_id:
        query = query.filter(Forecast.location_id == location_id)

    return query.order_by(Forecast.location_id, Forecast.forecast_date).all()


def get_forecast_history(
    db: Session, location_id: int, forecast_date: date
) -> list[Forecast]:
    """Get all historical forecasts for a specific date."""
    return (
        db.query(Forecast)
        .filter(
            and_(
                Forecast.location_id == location_id,
                Forecast.forecast_date == forecast_date,
            )
        )
        .order_by(Forecast.scraped_at)
        .all()
    )


def get_latest_issued_date(
    db: Session, department: str | None = None
) -> datetime | None:
    """Get the most recent issued_at date in database."""
    query = db.query(func.max(Forecast.issued_at))

    if department:
        query = query.join(Location).filter(Location.department == department)

    result = query.scalar()
    return result


def forecast_exists_for_issue_date(
    db: Session, issued_at: datetime, department: str | None = None
) -> bool:
    """Check if forecasts already exist for a specific issue date."""
    query = db.query(Forecast).filter(Forecast.issued_at == issued_at)

    if department:
        query = query.join(Location).filter(Location.department == department)

    return query.first() is not None


def delete_forecasts_by_issue_date(
    db: Session, issued_at: datetime, department: str | None = None
) -> int:
    """Delete all forecasts for a specific issue date."""
    query = db.query(Forecast).filter(Forecast.issued_at == issued_at)

    if department:
        query = query.join(Location).filter(Location.department == department)

    count = query.count()
    query.delete(synchronize_session=False)
    db.commit()

    return count


def create_scrape_run(db: Session, departments: list[str]) -> ScrapeRun:
    """Create a new scrape run record."""

    run = ScrapeRun(
        started_at=datetime.now(UTC),
        status="running",
        departments=",".join(departments),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_scrape_run(
    db: Session,
    run_id: int,
    status: str,
    locations_scraped: int = 0,
    forecasts_saved: int = 0,
    error_message: str | None = None,
) -> ScrapeRun:
    """Update scrape run with results."""

    run = db.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
    if not run:
        raise ValueError(f"ScrapeRun {run_id} not found")

    run.finished_at = datetime.now(UTC)
    run.status = status
    run.locations_scraped = locations_scraped
    run.forecasts_saved = forecasts_saved
    run.error_message = error_message

    db.commit()
    db.refresh(run)
    return run


def get_scrape_runs(
    db: Session, limit: int = 20, status: str | None = None
) -> list[ScrapeRun]:
    """Get recent scrape runs."""

    query = db.query(ScrapeRun).order_by(ScrapeRun.started_at.desc())

    if status:
        query = query.filter(ScrapeRun.status == status)

    return query.limit(limit).all()
