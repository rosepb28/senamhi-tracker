"""Tests for storage operations."""
from datetime import datetime, date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.forecast import DailyForecast, LocationForecast, WeatherIcon
from app.storage import crud

TEST_DATABASE_URL = "sqlite:///./test_storage.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_get_or_create_location(db_session):
    """Test location creation."""
    location = crud.get_or_create_location(
        db_session, "CANTA", "LIMA", "CANTA - LIMA"
    )
    
    assert location.id is not None
    assert location.location == "CANTA"
    assert location.department == "LIMA"
    
    location2 = crud.get_or_create_location(
        db_session, "CANTA", "LIMA", "CANTA - LIMA"
    )
    
    assert location.id == location2.id


def test_save_forecast(db_session):
    """Test saving forecast."""
    pydantic_forecast = LocationForecast(
        location="CANTA",
        department="LIMA",
        full_name="CANTA - LIMA",
        issued_at=datetime(2024, 11, 11),
        forecasts=[
            DailyForecast(
                date=date(2024, 11, 12),
                day_name="miércoles",
                temp_max=22,
                temp_min=9,
                weather_icon=WeatherIcon.PARTLY_CLOUDY,
                description="Test description",
            )
        ],
    )
    
    forecasts = crud.save_forecast(db_session, pydantic_forecast)
    
    assert len(forecasts) == 1
    assert forecasts[0].temp_max == 22
    assert forecasts[0].temp_min == 9


def test_get_locations(db_session):
    """Test getting all locations."""
    crud.get_or_create_location(db_session, "CANTA", "LIMA", "CANTA - LIMA")
    crud.get_or_create_location(db_session, "CHOSICA", "LIMA", "CHOSICA - LIMA")
    
    locations = crud.get_locations(db_session)
    
    assert len(locations) == 2


def test_get_latest_forecasts(db_session):
    """Test getting latest forecasts."""
    pydantic_forecast = LocationForecast(
        location="CANTA",
        department="LIMA",
        full_name="CANTA - LIMA",
        issued_at=datetime(2024, 11, 11),
        forecasts=[
            DailyForecast(
                date=date(2024, 11, 12),
                day_name="miércoles",
                temp_max=22,
                temp_min=9,
                weather_icon=WeatherIcon.CLEAR,
                description="Test",
            )
        ],
    )
    
    crud.save_forecast(db_session, pydantic_forecast)
    
    latest = crud.get_latest_forecasts(db_session)
    
    assert len(latest) >= 1
