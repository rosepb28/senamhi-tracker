"""Tests for scheduler functionality."""

from unittest.mock import Mock, patch

import pytest

from app.database import Base
from app.storage import crud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.scheduler.jobs import run_forecast_scrape_job

TEST_DATABASE_URL = "sqlite:///./test_scheduler.db"

test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create test database session."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


def test_create_scrape_run(db_session):
    """Test creating scrape run record."""
    run = crud.create_scrape_run(db_session, departments=["LIMA", "CUSCO"])

    assert run.id is not None
    assert run.status == "running"
    assert run.departments == "LIMA,CUSCO"
    assert run.started_at is not None


def test_update_scrape_run(db_session):
    """Test updating scrape run record."""
    run = crud.create_scrape_run(db_session, departments=["LIMA"])

    updated = crud.update_scrape_run(
        db_session,
        run.id,
        status="success",
        locations_scraped=13,
        forecasts_saved=39,
    )

    assert updated.status == "success"
    assert updated.locations_scraped == 13
    assert updated.forecasts_saved == 39
    assert updated.finished_at is not None


def test_get_scrape_runs(db_session):
    """Test retrieving scrape runs."""
    crud.create_scrape_run(db_session, departments=["LIMA"])
    crud.create_scrape_run(db_session, departments=["CUSCO"])

    runs = crud.get_scrape_runs(db_session, limit=10)

    assert len(runs) == 2


def test_get_scrape_runs_filtered(db_session):
    """Test filtering scrape runs by status."""
    run1 = crud.create_scrape_run(db_session, departments=["LIMA"])
    crud.update_scrape_run(db_session, run1.id, status="success")

    run2 = crud.create_scrape_run(db_session, departments=["CUSCO"])
    crud.update_scrape_run(
        db_session, run2.id, status="failed", error_message="Test error"
    )

    success_runs = crud.get_scrape_runs(db_session, status="success")
    failed_runs = crud.get_scrape_runs(db_session, status="failed")

    assert len(success_runs) == 1
    assert len(failed_runs) == 1
    assert failed_runs[0].error_message == "Test error"


@patch("app.scheduler.jobs.get_service")
@patch("app.scheduler.jobs.crud")
def test_run_forecast_scrape_job_success(mock_crud, mock_get_service):
    """Test successful scrape job execution with WeatherService."""
    # Mock service
    mock_service = Mock()
    mock_service.db = Mock()
    mock_service.update_forecasts.return_value = {
        "success": True,
        "issued_at": Mock(strftime=lambda x: "2025-11-18"),
        "locations": 10,
        "saved": 30,
    }
    mock_get_service.return_value = mock_service

    # Mock CRUD operations
    mock_run = Mock(id=1)
    mock_crud.create_scrape_run.return_value = mock_run

    # Execute job
    run_forecast_scrape_job()

    # Verify service was called
    mock_service.update_forecasts.assert_called_once()

    # Verify run was updated with success
    mock_crud.update_scrape_run.assert_called_once()
    call_args = mock_crud.update_scrape_run.call_args
    assert call_args[1]["status"] == "success"
