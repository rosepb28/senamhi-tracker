# app/storage/models.py
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from config.settings import settings

# Import GeoAlchemy2 only if PostGIS is available
if settings.supports_postgis:
    from geoalchemy2 import Geometry


def utc_now():
    """Get current UTC datetime."""
    return datetime.now(UTC)


class Location(Base):
    """Location table for weather forecast locations."""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location: Mapped[str] = mapped_column(String, unique=True, index=True)
    department: Mapped[str] = mapped_column(String, index=True)
    full_name: Mapped[str] = mapped_column(String)
    active: Mapped[bool] = mapped_column(default=True)

    # Coordinates for Open Meteo integration (always available)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Geospatial point (PostgreSQL + PostGIS only)
    if settings.supports_postgis:
        point: Mapped[str | None] = mapped_column(
            Geometry("POINT", srid=4326), nullable=True
        )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    forecasts: Mapped[list["Forecast"]] = relationship(
        "Forecast", back_populates="location"
    )

    def __repr__(self) -> str:
        return f"<Location(id={self.id}, location='{self.location}', department='{self.department}')>"

    # Spatial index (PostgreSQL only)
    if settings.supports_postgis:
        __table_args__ = (
            Index("idx_location_point", "point", postgresql_using="gist"),
        )


class Forecast(Base):
    """Forecast table for daily weather forecasts."""

    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    location_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("locations.id"), index=True
    )

    forecast_date: Mapped[date] = mapped_column(Date, index=True)
    day_name: Mapped[str] = mapped_column(String)

    temp_max: Mapped[int] = mapped_column(Integer)
    temp_min: Mapped[int] = mapped_column(Integer)

    icon_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)

    issued_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)

    location: Mapped["Location"] = relationship("Location", back_populates="forecasts")

    def __repr__(self) -> str:
        return f"<Forecast(id={self.id}, location_id={self.location_id}, date={self.forecast_date})>"


class ScrapeRun(Base):
    """Scrape run history table."""

    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    locations_scraped: Mapped[int] = mapped_column(Integer, default=0)
    forecasts_saved: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String)  # success, failed, partial
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    departments: Mapped[str] = mapped_column(String)  # Comma-separated

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    def __repr__(self) -> str:
        return f"<ScrapeRun(id={self.id}, status='{self.status}', started_at={self.started_at})>"


class WarningAlert(Base):
    """Weather warnings and alerts table."""

    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # SENAMHI internal ID (from API response)
    senamhi_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    warning_number: Mapped[str] = mapped_column(String, index=True)
    department: Mapped[str] = mapped_column(String, index=True)
    severity: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)

    valid_from: Mapped[datetime] = mapped_column(DateTime, index=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    def __repr__(self) -> str:
        return f"<WarningAlert(id={self.id}, senamhi_id={self.senamhi_id}, number='{self.warning_number}')>"


# Add relationship only if PostGIS is available
if settings.supports_postgis:
    # Import here to avoid circular dependency
    from sqlalchemy.orm import relationship as _relationship

    WarningAlert.geometries = _relationship(
        "WarningGeometry",
        back_populates="warning",
        lazy="select",
        cascade="all, delete-orphan",
    )
