"""Scheduler for periodic scraping."""

import signal
import sys
import time

import schedule

from config.config import settings
from app.scheduler.jobs import run_forecast_scrape_job, run_warnings_scrape_job
from app.scheduler.logger import setup_logger

logger = setup_logger()


class ForecastScheduler:
    """Scheduler for SENAMHI forecast and warnings scraping."""

    def __init__(self):
        """Initialize scheduler."""
        self.running = False
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signal."""
        logger.info("Shutdown signal received, stopping scheduler...")
        self.running = False

    def start(self):
        """Start the scheduler."""
        logger.info("=" * 60)
        logger.info("SENAMHI Tracker Scheduler Started")
        logger.info("=" * 60)
        logger.info(
            f"Forecast interval: Every {settings.forecast_scrape_interval} hours"
        )
        logger.info(
            f"Warnings interval: Every {settings.warning_scrape_interval} hours"
        )
        logger.info(f"Start immediately: {settings.scheduler_start_immediately}")

        if settings.scrape_all_departments:
            logger.info("Forecast mode: Scraping ALL departments")
        else:
            depts = settings.get_departments_list()
            logger.info(f"Forecast mode: Scraping {', '.join(depts)}")

        logger.info(f"Logs: {settings.log_file}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)

        # Schedule forecast job
        schedule.every(settings.forecast_scrape_interval).hours.do(
            run_forecast_scrape_job
        )

        # Schedule warnings job
        schedule.every(settings.warning_scrape_interval).hours.do(
            run_warnings_scrape_job
        )

        # Run immediately if configured
        if settings.scheduler_start_immediately:
            logger.info("Running initial scrapes...")
            run_forecast_scrape_job()
            run_warnings_scrape_job()

        # Calculate next run times
        jobs = schedule.get_jobs()
        if jobs:
            logger.info("\nScheduled jobs:")
            for job in jobs:
                logger.info(
                    f"  - {job.job_func.__name__}: next run at {job.next_run.strftime('%Y-%m-%d %H:%M:%S')}"
                )

        # Main loop
        self.running = True

        while self.running:
            schedule.run_pending()
            time.sleep(1)

        logger.info("Scheduler stopped gracefully")
        sys.exit(0)
