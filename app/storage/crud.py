"""CRUD operations for database."""

from datetime import UTC, date, datetime

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.forecast import LocationForecast as PydanticLocationForecast
from app.storage.models import Forecast, Location
from app.storage.models import ScrapeRun
from app.storage.models import WarningAlert
from app.models.warning import Warning


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
            forecast_date=daily.date.date()
            if isinstance(daily.date, datetime)
            else daily.date,
            day_name=daily.day_name,
            temp_max=daily.temp_max,
            temp_min=daily.temp_min,
            icon_number=daily.icon_number,
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
    if department:
        # Get location IDs for this department first
        location_ids = (
            db.query(Location.id)
            .filter(Location.department == department.upper())
            .all()
        )
        location_ids = [loc_id[0] for loc_id in location_ids]

        if not location_ids:
            return 0

        # Delete forecasts for these locations
        count = (
            db.query(Forecast)
            .filter(
                Forecast.issued_at == issued_at, Forecast.location_id.in_(location_ids)
            )
            .delete(synchronize_session=False)
        )
    else:
        # Delete all forecasts for this issue date
        count = (
            db.query(Forecast)
            .filter(Forecast.issued_at == issued_at)
            .delete(synchronize_session=False)
        )

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


# ==================== Warning Operations ====================


def save_warning(db: Session, warning: Warning) -> WarningAlert:
    """Save warning to database."""
    # Check if warning already exists for this department
    existing = (
        db.query(WarningAlert)
        .filter(
            WarningAlert.warning_number == warning.warning_number,
            WarningAlert.department == warning.department,
        )
        .first()
    )

    if existing:
        existing.senamhi_id = warning.senamhi_id
        existing.severity = warning.severity.value
        existing.status = warning.status.value
        existing.title = warning.title
        existing.description = warning.description
        existing.valid_from = warning.valid_from
        existing.valid_until = warning.valid_until
        existing.issued_at = warning.issued_at
        existing.scraped_at = warning.scraped_at

        db.commit()
        db.refresh(existing)
        return existing

    db_warning = WarningAlert(
        senamhi_id=warning.senamhi_id,
        warning_number=warning.warning_number,
        department=warning.department,
        severity=warning.severity.value,
        status=warning.status.value,
        title=warning.title,
        description=warning.description,
        valid_from=warning.valid_from,
        valid_until=warning.valid_until,
        issued_at=warning.issued_at,
        scraped_at=warning.scraped_at,
    )

    db.add(db_warning)
    db.commit()
    db.refresh(db_warning)

    return db_warning


def get_active_warnings(
    db: Session, department: str | None = None
) -> list["WarningAlert"]:
    """Get all currently active or upcoming warnings (EMITIDO + VIGENTE, not expired)."""

    now = datetime.now()

    query = db.query(WarningAlert).filter(
        WarningAlert.status.in_(["emitido", "vigente"]),
        WarningAlert.valid_until >= now,  # ← Solo avisos vigentes
    )

    if department:
        query = query.filter(WarningAlert.department == department.upper())

    warnings = query.all()

    def sort_key(w):
        # VIGENTE = 0, EMITIDO = 1 (VIGENTE first)
        status_priority = 0 if w.status == "vigente" else 1
        # Time difference from now (absolute value, closest = smallest)
        time_diff = abs((w.valid_from - now).total_seconds())
        return (status_priority, time_diff)

    return sorted(warnings, key=sort_key)


def get_warnings(
    db: Session,
    severity: str | None = None,
    active_only: bool = True,
    limit: int = 50,
) -> list["WarningAlert"]:
    """Get warnings with filters."""

    query = db.query(WarningAlert)

    if active_only:
        # Filter by status field (not dates)
        query = query.filter(WarningAlert.status.in_(["emitido", "vigente"]))

    if severity:
        query = query.filter(WarningAlert.severity == severity)

    return query.order_by(WarningAlert.issued_at.desc()).limit(limit).all()


def get_warning_by_number(
    db: Session, warning_number: str, department: str | None = None
) -> "WarningAlert | None":
    """Get warning by its official number and optionally department."""

    query = db.query(WarningAlert).filter(WarningAlert.warning_number == warning_number)

    if department:
        query = query.filter(WarningAlert.department == department.upper())

    return query.first()
