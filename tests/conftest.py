"""Shared test fixtures and configuration."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.weather_service import WeatherService
from datetime import datetime, date
from app.models.forecast import LocationForecast, DailyForecast

from app.models.warning import Warning, WarningSeverity, WarningStatus


@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create database session for testing."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def weather_service(db_session):
    """Create WeatherService instance with test database."""
    return WeatherService(db_session)


@pytest.fixture
def sample_forecast_data():
    """Sample forecast data for testing."""

    return LocationForecast(
        location="LIMA ESTE",
        department="LIMA",
        full_name="Lima Este - Lima",
        issued_at=datetime(2025, 11, 18, 0, 0),
        scraped_at=datetime.now(),
        forecasts=[
            DailyForecast(
                date=date(2025, 11, 19),
                day_name="Martes",
                temp_max=24,
                temp_min=18,
                icon_number=2,
                description="Parcialmente nublado",
            ),
            DailyForecast(
                date=date(2025, 11, 20),
                day_name="Miércoles",
                temp_max=25,
                temp_min=19,
                icon_number=1,
                description="Soleado",
            ),
        ],
    )


@pytest.fixture
def sample_warning_data():
    """Sample warning data for testing."""

    return Warning(
        warning_number="001-2025",
        department="LIMA",
        severity=WarningSeverity.YELLOW,
        status=WarningStatus.VIGENTE,
        title="Aviso de lluvia moderada",
        description="Se esperan lluvias moderadas en la zona",
        valid_from=datetime(2025, 11, 18, 12, 0),
        valid_until=datetime(2025, 11, 19, 12, 0),
        issued_at=datetime(2025, 11, 18, 8, 0),
        scraped_at=datetime.now(),
    )
