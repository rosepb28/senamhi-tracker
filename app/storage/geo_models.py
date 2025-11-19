"""Geospatial database models (PostGIS only)."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.storage.models import utc_now
from config.settings import settings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.storage.models import WarningAlert

# Import GeoAlchemy2 only if PostGIS is available
if settings.supports_postgis:
    from geoalchemy2 import Geometry


class WarningGeometry(Base):
    """Warning geometry storage (PostGIS only)."""

    __tablename__ = "warning_geometries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign key to warning
    warning_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warnings.id"), nullable=False, index=True
    )

    # Day number (1-based, relative to warning start date)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Shapefile metadata
    shapefile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    shapefile_path: Mapped[str | None] = mapped_column(String, nullable=True)
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Geometry (PostGIS only)
    if settings.supports_postgis:
        geometry: Mapped[str | None] = mapped_column(
            Geometry("MULTIPOLYGON", srid=4326), nullable=True
        )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    # Relationship
    warning: Mapped["WarningAlert"] = relationship(
        "WarningAlert", back_populates="geometries"
    )

    def __repr__(self) -> str:
        return f"<WarningGeometry(id={self.id}, warning_id={self.warning_id}, day={self.day_number})>"

    # Spatial index (PostgreSQL only)
    if settings.supports_postgis:
        __table_args__ = (
            Index("idx_warning_geometry", "geometry", postgresql_using="gist"),
            Index("idx_warning_day", "warning_id", "day_number"),
        )
    else:
        __table_args__ = (Index("idx_warning_day", "warning_id", "day_number"),)
