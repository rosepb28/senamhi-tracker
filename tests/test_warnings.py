"""Tests for warning storage and scraping."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.warning import Warning, WarningSeverity, WarningStatus
from app.storage import crud

TEST_DATABASE_URL = "sqlite:///./test_warnings.db"

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


def test_save_warning(db_session):
    """Test saving warning to database."""
    now = datetime.now()

    warning = Warning(
        warning_number="001",
        severity=WarningSeverity.YELLOW,
        status=WarningStatus.VIGENTE,
        title="Lluvias moderadas",
        description="Se esperan lluvias moderadas",
        valid_from=now,
        valid_until=now + timedelta(days=2),
        issued_at=now,
    )

    db_warning = crud.save_warning(db_session, warning)

    assert db_warning.id is not None
    assert db_warning.warning_number == "001"
    assert db_warning.severity == "amarillo"
    assert db_warning.status == "vigente"


def test_get_active_warnings(db_session):
    """Test retrieving active warnings."""
    now = datetime.now()

    # Active warning
    warning1 = Warning(
        warning_number="001",
        severity=WarningSeverity.YELLOW,
        status=WarningStatus.VIGENTE,
        title="Active Warning",
        description="Test",
        valid_from=now - timedelta(hours=1),
        valid_until=now + timedelta(hours=1),
        issued_at=now,
    )

    # Expired warning
    warning2 = Warning(
        warning_number="002",
        severity=WarningSeverity.RED,
        status=WarningStatus.VENCIDO,
        title="Expired Warning",
        description="Test",
        valid_from=now - timedelta(days=2),
        valid_until=now - timedelta(hours=1),
        issued_at=now,
    )

    crud.save_warning(db_session, warning1)
    crud.save_warning(db_session, warning2)

    active = crud.get_active_warnings(db_session)

    assert len(active) == 1
    assert active[0].warning_number == "001"


def test_update_existing_warning(db_session):
    """Test updating existing warning."""
    now = datetime.now()

    warning = Warning(
        warning_number="001",
        severity=WarningSeverity.YELLOW,
        status=WarningStatus.EMITIDO,
        title="Original Title",
        description="Original",
        valid_from=now,
        valid_until=now + timedelta(days=1),
        issued_at=now,
    )

    crud.save_warning(db_session, warning)

    # Update
    warning.title = "Updated Title"
    warning.severity = WarningSeverity.ORANGE

    updated = crud.save_warning(db_session, warning)

    assert updated.title == "Updated Title"
    assert updated.severity == "naranja"

    # Should only be one record
    all_warnings = crud.get_warnings(db_session, active_only=False)
    assert len(all_warnings) == 1


def test_get_warning_by_number(db_session):
    """Test retrieving warning by number."""
    now = datetime.now()

    warning = Warning(
        warning_number="123",
        severity=WarningSeverity.YELLOW,
        status=WarningStatus.VIGENTE,
        title="Test",
        description="Test",
        valid_from=now,
        valid_until=now + timedelta(days=1),
        issued_at=now,
    )

    crud.save_warning(db_session, warning)

    found = crud.get_warning_by_number(db_session, "123")
    assert found is not None
    assert found.warning_number == "123"

    not_found = crud.get_warning_by_number(db_session, "999")
    assert not_found is None


def test_filter_emitido_warnings(db_session):
    """Test filtering EMITIDO warnings."""
    now = datetime.now()

    warning = Warning(
        warning_number="001",
        severity=WarningSeverity.ORANGE,
        status=WarningStatus.EMITIDO,
        title="Upcoming Warning",
        description="Test",
        valid_from=now + timedelta(days=1),
        valid_until=now + timedelta(days=3),
        issued_at=now,
    )

    crud.save_warning(db_session, warning)

    active = crud.get_active_warnings(db_session)

    assert len(active) == 1
    assert active[0].status == "emitido"
