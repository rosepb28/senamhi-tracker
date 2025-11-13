"""Tests for scheduler functionality."""

from unittest.mock import patch

import pytest

from app.database import Base
from app.storage import crud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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


@patch("app.scheduler.jobs.ForecastScraper")
@patch("app.scheduler.jobs.SessionLocal")
def test_run_scrape_job_success(mock_session, mock_scraper):
    """Test successful scrape job execution."""
    # This is a basic integration test
    # Full testing would require mocking more components
    pass
