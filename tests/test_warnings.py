"""Tests for warning alert storage and retrieval."""

import pytest
from datetime import datetime, timedelta

from app.models.warning import Warning, WarningSeverity, WarningStatus
from app.storage import crud
from config.settings import settings


@pytest.mark.skipif(
    settings.supports_postgis, reason="PostGIS available, skip SQLite tests"
)
class TestWarningAlerts:
    """Test warning alert CRUD operations (SQLite only)."""

    def test_save_warning(self, db_session):
        """Test saving a warning alert."""
        warning = Warning(
            senamhi_id=123,
            warning_number="001",
            department="LIMA",
            severity=WarningSeverity.YELLOW,
            status=WarningStatus.VIGENTE,
            title="Test Warning",
            description="Test description",
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=1),
            issued_at=datetime.now(),
        )

        db_warning = crud.save_warning(db_session, warning)

        assert db_warning.id is not None
        assert db_warning.senamhi_id == 123
        assert db_warning.department == "LIMA"
        assert db_warning.severity == "amarillo"
        assert db_warning.status == "vigente"

    def test_get_active_warnings(self, db_session):
        """Test retrieving active warnings."""
        now = datetime.now()
        future = now + timedelta(days=1)

        warning_active = Warning(
            senamhi_id=1001,
            warning_number="001",
            department="LIMA",
            severity=WarningSeverity.YELLOW,
            status=WarningStatus.VIGENTE,
            title="Active Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            issued_at=now,
        )

        warning_expired = Warning(
            senamhi_id=1002,
            warning_number="002",
            department="LIMA",
            severity=WarningSeverity.RED,
            status=WarningStatus.VENCIDO,
            title="Expired Warning",
            description="Test",
            valid_from=now - timedelta(days=2),
            valid_until=now - timedelta(hours=1),
            issued_at=now,
        )

        crud.save_warning(db_session, warning_active)
        crud.save_warning(db_session, warning_expired)

        active_warnings = crud.get_active_warnings(db_session)

        assert len(active_warnings) == 1
        assert active_warnings[0].status == "vigente"

    def test_get_active_warnings_by_department(self, db_session):
        """Test retrieving active warnings by department."""
        now = datetime.now()
        future = now + timedelta(days=1)

        warning_lima = Warning(
            senamhi_id=1003,
            warning_number="001",
            department="LIMA",
            severity=WarningSeverity.YELLOW,
            status=WarningStatus.VIGENTE,
            title="Lima Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            issued_at=now,
        )

        warning_cusco = Warning(
            senamhi_id=1004,
            warning_number="002",
            department="CUSCO",
            severity=WarningSeverity.ORANGE,
            status=WarningStatus.VIGENTE,
            title="Cusco Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            issued_at=now,
        )

        crud.save_warning(db_session, warning_lima)
        crud.save_warning(db_session, warning_cusco)

        lima_warnings = crud.get_active_warnings(db_session, department="LIMA")

        assert len(lima_warnings) == 1
        assert lima_warnings[0].department == "LIMA"

    def test_same_warning_different_departments(self, db_session):
        """Test that same warning number can exist for different departments."""
        now = datetime.now()
        future = now + timedelta(days=1)

        warning1 = Warning(
            senamhi_id=1005,
            warning_number="100",
            department="LIMA",
            severity=WarningSeverity.YELLOW,
            status=WarningStatus.VIGENTE,
            title="Multi-dept Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            issued_at=now,
        )

        warning2 = Warning(
            senamhi_id=1006,
            warning_number="100",
            department="CUSCO",
            severity=WarningSeverity.YELLOW,
            status=WarningStatus.VIGENTE,
            title="Multi-dept Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            issued_at=now,
        )

        db_warning1 = crud.save_warning(db_session, warning1)
        db_warning2 = crud.save_warning(db_session, warning2)

        assert db_warning1.warning_number == db_warning2.warning_number
        assert db_warning1.department != db_warning2.department

    def test_filter_emitido_warnings(self, db_session):
        """Test filtering warnings by emitido status."""
        now = datetime.now()
        future = now + timedelta(days=1)

        warning_emitido = Warning(
            senamhi_id=1007,
            warning_number="200",
            department="LIMA",
            severity=WarningSeverity.YELLOW,
            status=WarningStatus.EMITIDO,
            title="Emitido Warning",
            description="Test",
            valid_from=future,
            valid_until=future + timedelta(days=1),
            issued_at=now,
        )

        warning_vigente = Warning(
            senamhi_id=1008,
            warning_number="201",
            department="LIMA",
            severity=WarningSeverity.YELLOW,
            status=WarningStatus.VIGENTE,
            title="Vigente Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            issued_at=now,
        )

        crud.save_warning(db_session, warning_emitido)
        crud.save_warning(db_session, warning_vigente)

        active_warnings = crud.get_active_warnings(db_session)

        assert len(active_warnings) == 2
        statuses = [w.status for w in active_warnings]
        assert "emitido" in statuses
        assert "vigente" in statuses
