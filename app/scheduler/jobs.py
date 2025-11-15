"""Scheduled jobs for SENAMHI scraper."""

import time
import traceback

from app.cli.commands import _run_warnings_scrape
from app.config import settings
from app.database import SessionLocal
from app.scrapers.forecast_scraper import ForecastScraper
from app.scheduler.logger import setup_logger
from app.storage import crud

logger = setup_logger()


def run_forecast_scrape_job() -> None:
    """Execute forecast scraping job with error handling and logging."""
    db = SessionLocal()

    try:
        logger.info("Starting scheduled forecast scrape job")

        # Determine what to scrape
        if settings.scrape_all_departments:
            dept_list = None  # Will scrape all
            logger.info("Scraping ALL departments")
        else:
            dept_list = settings.get_departments_list()
            logger.info(f"Scraping departments: {', '.join(dept_list)}")

        # Create run record
        run = crud.create_scrape_run(
            db,
            departments=dept_list if dept_list else ["ALL"],
        )
        logger.debug(f"Created scrape run #{run.id}")

        # Execute scraping with retries
        forecasts = None
        last_error = None

        for attempt in range(1, settings.max_retries + 1):
            try:
                logger.info(f"Scrape attempt {attempt}/{settings.max_retries}")

                scraper = ForecastScraper()

                if settings.scrape_all_departments:
                    forecasts = scraper.scrape_all_departments()
                    actual_depts = sorted(list(set(f.department for f in forecasts)))
                else:
                    forecasts = scraper.scrape_forecasts(departments=dept_list)
                    actual_depts = dept_list

                logger.info(f"Successfully scraped {len(forecasts)} locations")
                break

            except Exception as e:
                last_error = str(e)
                logger.error(f"Scrape attempt {attempt} failed: {e}")

                if attempt < settings.max_retries:
                    logger.info(
                        f"Retrying in {settings.retry_delay_seconds} seconds..."
                    )
                    time.sleep(settings.retry_delay_seconds)
                else:
                    logger.error("All retry attempts exhausted")

        if not forecasts:
            # All retries failed
            crud.update_scrape_run(
                db,
                run.id,
                status="failed",
                error_message=last_error,
            )
            logger.error(f"Forecast scrape job failed: {last_error}")
            return

        # Check if data already exists (skip if same issue date)
        issued_at = forecasts[0].issued_at
        logger.info(f"Forecast issue date: {issued_at.strftime('%Y-%m-%d')}")

        data_exists = False
        for dept in actual_depts:
            if crud.forecast_exists_for_issue_date(db, issued_at, dept):
                data_exists = True
                break

        if data_exists:
            logger.info("Data already exists for this issue date, skipping save")
            crud.update_scrape_run(
                db,
                run.id,
                status="skipped",
                locations_scraped=len(forecasts),
                forecasts_saved=0,
                error_message="Data already exists for this issue date",
            )
            return

        # Save forecasts
        logger.info("Saving forecasts to database...")
        saved_count = 0

        for location_forecast in forecasts:
            try:
                saved = crud.save_forecast(db, location_forecast)
                saved_count += len(saved)
            except Exception as e:
                logger.warning(f"Failed to save {location_forecast.location}: {e}")

        # Update run record
        crud.update_scrape_run(
            db,
            run.id,
            status="success",
            locations_scraped=len(forecasts),
            forecasts_saved=saved_count,
        )

        logger.info(
            f"Forecast scrape job completed successfully: "
            f"{len(forecasts)} locations, {saved_count} forecasts saved"
        )

    except Exception as e:
        logger.error(f"Unexpected error in forecast scrape job: {e}")
        logger.debug(traceback.format_exc())

        try:
            if "run" in locals():
                crud.update_scrape_run(
                    db,
                    run.id,
                    status="failed",
                    error_message=str(e),
                )
        except Exception as update_error:
            logger.error(f"Failed to update run record: {update_error}")

    finally:
        db.close()


def run_warnings_scrape_job() -> None:
    """Execute warnings scraping job with error handling and logging."""
    logger.info("Starting scheduled warnings scrape job")

    try:
        _run_warnings_scrape(force=False)
        logger.info("Warnings scrape job completed successfully")

    except Exception as e:
        logger.error(f"Warnings scrape job failed: {e}")
        logger.debug(traceback.format_exc())
