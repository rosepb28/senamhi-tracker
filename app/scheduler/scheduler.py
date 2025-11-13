"""Scheduler for periodic scraping."""

import signal
import sys
import time

import schedule

from app.config import settings
from app.scheduler.jobs import run_scrape_job
from app.scheduler.logger import setup_logger

logger = setup_logger()


class ForecastScheduler:
    """Scheduler for SENAMHI forecast scraping."""

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
        logger.info(f"Interval: Every {settings.scrape_interval_hours} hours")
        logger.info(f"Start immediately: {settings.scheduler_start_immediately}")

        if settings.scrape_all_departments:
            logger.info("Mode: Scraping ALL departments")
        else:
            depts = settings.get_departments_list()
            logger.info(f"Mode: Scraping {', '.join(depts)}")

        logger.info(f"Logs: {settings.log_file}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)

        # Schedule the job
        schedule.every(settings.scrape_interval_hours).hours.do(run_scrape_job)

        # Run immediately if configured
        if settings.scheduler_start_immediately:
            logger.info("Running initial scrape...")
            run_scrape_job()

        # Calculate next run time
        next_run = schedule.next_run()
        if next_run:
            logger.info(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

        # Main loop
        self.running = True

        while self.running:
            schedule.run_pending()
            time.sleep(1)

        logger.info("Scheduler stopped gracefully")
        sys.exit(0)
