"""Integration tests for scheduler jobs."""

from unittest.mock import Mock, patch

from app.scheduler.jobs import run_forecast_scrape_job, run_warnings_scrape_job


class TestSchedulerJobs:
    """Test scheduler job execution."""

    @patch("app.services.coordinates_service.populate_coordinates")
    @patch("app.scheduler.jobs.time.sleep")
    @patch("app.scheduler.jobs.SessionLocal")
    @patch("app.scheduler.jobs.get_service")
    def test_forecast_job_success(
        self, mock_get_service, mock_session_local, mock_sleep, mock_populate
    ):
        """Test successful forecast scraping job."""
        # Mock database session
        mock_db = Mock()
        mock_db.close = Mock()
        mock_session_local.return_value = mock_db

        # Mock service
        mock_service = Mock()
        mock_service.db = mock_db
        mock_service.update_forecasts.return_value = {
            "success": True,
            "issued_at": Mock(strftime=lambda x: "2025-11-18"),
            "locations": 10,
            "saved": 30,
        }
        mock_get_service.return_value = mock_service

        # Mock CRUD operations
        with patch("app.scheduler.jobs.crud") as mock_crud:
            mock_run = Mock(id=1)
            mock_crud.create_scrape_run.return_value = mock_run

            # Execute job
            run_forecast_scrape_job()

            # Verify service was called once
            mock_service.update_forecasts.assert_called_once_with(
                departments=None, force=False
            )

            # Verify populate_coordinates was called
            mock_populate.assert_called_once_with(skip_existing=True)

            # Verify run was updated
            mock_crud.update_scrape_run.assert_called_once()

            # Verify no retries
            mock_sleep.assert_not_called()

    @patch("app.scheduler.jobs.get_service")
    def test_warnings_job_success(self, mock_get_service):
        """Test successful warnings scraping job."""
        # Mock service
        mock_service = Mock()
        mock_service.db = Mock()
        mock_service.update_warnings.return_value = {
            "success": True,
            "found": 5,
            "saved": 3,
            "updated": 2,
        }
        mock_get_service.return_value = mock_service

        # Execute job
        run_warnings_scrape_job()

        # Verify service was called
        mock_service.update_warnings.assert_called_once_with(force=False)

    @patch("app.scheduler.jobs.time.sleep")
    @patch("app.scheduler.jobs.SessionLocal")
    @patch("app.scheduler.jobs.get_service")
    def test_forecast_job_skipped(
        self, mock_get_service, mock_session_local, mock_sleep
    ):
        """Test forecast job when data already exists."""
        # Mock database session
        mock_db = Mock()
        mock_db.close = Mock()
        mock_session_local.return_value = mock_db

        # Mock service
        mock_service = Mock()
        mock_service.db = mock_db
        mock_service.update_forecasts.return_value = {
            "success": False,
            "skipped": True,
            "issued_at": Mock(strftime=lambda x: "2025-11-18"),
            "locations": 10,
            "saved": 0,
            "message": "Data already exists",
        }
        mock_get_service.return_value = mock_service

        # Mock CRUD
        with patch("app.scheduler.jobs.crud") as mock_crud:
            mock_run = Mock(id=1)
            mock_crud.create_scrape_run.return_value = mock_run

            # Execute job
            run_forecast_scrape_job()

            # Verify run was marked as skipped
            call_args = mock_crud.update_scrape_run.call_args
            assert call_args[1]["status"] == "skipped"

            # Verify no retries
            mock_sleep.assert_not_called()
