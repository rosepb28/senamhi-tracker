"""Tests for warning alert storage and retrieval."""

import pytest
from datetime import datetime, timedelta

from app.storage import crud
from config.settings import settings


@pytest.mark.skipif(
    settings.supports_postgis, reason="PostGIS available, skip SQLite tests"
)
class TestWarningAlerts:
    """Test warning alert CRUD operations (SQLite only)."""

    def test_save_warning(self, test_db):
        """Test saving a warning alert."""
        warning_data = {
            "senamhi_id": "test123",
            "warning_number": "001",
            "department": "LIMA",
            "hazard_type": "lluvia",
            "severity": "amarillo",
            "title": "Test Warning",
            "description": "Test description",
            "valid_from": datetime.now(),
            "valid_until": datetime.now() + timedelta(days=1),
            "status": "vigente",
            "issued_at": datetime.now(),
        }

        warning = crud.save_warning_alert(test_db, **warning_data)

        assert warning.id is not None
        assert warning.senamhi_id == "test123"
        assert warning.department == "LIMA"
        assert warning.severity == "amarillo"
        assert warning.status == "vigente"

    def test_get_active_warnings(self, test_db):
        """Test retrieving active warnings."""
        now = datetime.now()
        future = now + timedelta(days=1)

        crud.save_warning_alert(
            test_db,
            senamhi_id="active1",
            warning_number="001",
            department="LIMA",
            hazard_type="lluvia",
            severity="amarillo",
            title="Active Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            status="vigente",
            issued_at=now,
        )

        crud.save_warning_alert(
            test_db,
            senamhi_id="expired1",
            warning_number="002",
            department="LIMA",
            hazard_type="lluvia",
            severity="rojo",
            title="Expired Warning",
            description="Test",
            valid_from=now - timedelta(days=2),
            valid_until=now - timedelta(hours=1),
            status="vencido",
            issued_at=now,
        )

        active_warnings = crud.get_active_warnings(test_db)

        assert len(active_warnings) == 1
        assert active_warnings[0].status == "vigente"

    def test_get_active_warnings_by_department(self, test_db):
        """Test retrieving active warnings by department."""
        now = datetime.now()
        future = now + timedelta(days=1)

        crud.save_warning_alert(
            test_db,
            senamhi_id="lima1",
            warning_number="001",
            department="LIMA",
            hazard_type="lluvia",
            severity="amarillo",
            title="Lima Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            status="vigente",
            issued_at=now,
        )

        crud.save_warning_alert(
            test_db,
            senamhi_id="cusco1",
            warning_number="002",
            department="CUSCO",
            hazard_type="helada",
            severity="naranja",
            title="Cusco Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            status="vigente",
            issued_at=now,
        )

        lima_warnings = crud.get_active_warnings_by_department(test_db, "LIMA")

        assert len(lima_warnings) == 1
        assert lima_warnings[0].department == "LIMA"

    def test_same_warning_different_departments(self, test_db):
        """Test that same warning number can exist for different departments."""
        now = datetime.now()
        future = now + timedelta(days=1)

        warning1 = crud.save_warning_alert(
            test_db,
            senamhi_id="multi1",
            warning_number="100",
            department="LIMA",
            hazard_type="lluvia",
            severity="amarillo",
            title="Multi-dept Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            status="vigente",
            issued_at=now,
        )

        warning2 = crud.save_warning_alert(
            test_db,
            senamhi_id="multi2",
            warning_number="100",
            department="CUSCO",
            hazard_type="lluvia",
            severity="amarillo",
            title="Multi-dept Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            status="vigente",
            issued_at=now,
        )

        assert warning1.warning_number == warning2.warning_number
        assert warning1.department != warning2.department

    def test_filter_emitido_warnings(self, test_db):
        """Test filtering warnings by emitido status."""
        now = datetime.now()
        future = now + timedelta(days=1)

        crud.save_warning_alert(
            test_db,
            senamhi_id="emitido1",
            warning_number="200",
            department="LIMA",
            hazard_type="lluvia",
            severity="amarillo",
            title="Emitido Warning",
            description="Test",
            valid_from=future,
            valid_until=future + timedelta(days=1),
            status="emitido",
            issued_at=now,
        )

        crud.save_warning_alert(
            test_db,
            senamhi_id="vigente1",
            warning_number="201",
            department="LIMA",
            hazard_type="lluvia",
            severity="amarillo",
            title="Vigente Warning",
            description="Test",
            valid_from=now,
            valid_until=future,
            status="vigente",
            issued_at=now,
        )

        active_warnings = crud.get_active_warnings(test_db)

        assert len(active_warnings) == 2
        statuses = [w.status for w in active_warnings]
        assert "emitido" in statuses
        assert "vigente" in statuses
