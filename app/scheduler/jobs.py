"""Scheduled jobs for SENAMHI scraper."""

import time
import traceback

from config.settings import settings
from app.database import SessionLocal
from app.scheduler.logger import setup_logger
from app.services.weather_service import WeatherService
from app.storage import crud

logger = setup_logger()


def get_service() -> WeatherService:
    """Factory function to create WeatherService with database session."""
    db = SessionLocal()
    return WeatherService(db)


def run_forecast_scrape_job() -> None:
    """Execute forecast scraping job with error handling and logging."""
    service = get_service()

    try:
        logger.info("Starting scheduled forecast scrape job")

        # Determine departments to scrape
        if settings.scrape_all_departments:
            dept_list = None
            logger.info("Scraping ALL departments")
        else:
            dept_list = settings.get_departments_list()
            logger.info(f"Scraping departments: {', '.join(dept_list)}")

        # Create run record
        run = crud.create_scrape_run(
            service.db,
            departments=dept_list if dept_list else ["ALL"],
        )
        logger.debug(f"Created scrape run #{run.id}")

        # Execute scraping with retries
        result = None
        last_error = None

        for attempt in range(1, settings.max_retries + 1):
            try:
                logger.info(f"Scrape attempt {attempt}/{settings.max_retries}")

                result = service.update_forecasts(departments=dept_list, force=False)

                if result["success"]:
                    logger.info(
                        f"Successfully scraped {result['locations']} locations, "
                        f"saved {result['saved']} forecasts"
                    )
                    break
                elif result.get("skipped"):
                    logger.info(
                        f"Data already exists for issue date "
                        f"{result['issued_at'].strftime('%Y-%m-%d')}, skipping"
                    )
                    crud.update_scrape_run(
                        service.db,
                        run.id,
                        status="skipped",
                        locations_scraped=result["locations"],
                        forecasts_saved=0,
                        error_message=result.get("message"),
                    )
                    return
                else:
                    last_error = result.get("error", "Unknown error")
                    logger.error(f"Scrape attempt {attempt} failed: {last_error}")

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

        if not result or not result["success"]:
            # All retries failed
            crud.update_scrape_run(
                service.db,
                run.id,
                status="failed",
                error_message=last_error,
            )
            logger.error(f"Forecast scrape job failed: {last_error}")
            return

        # Update run record with success
        crud.update_scrape_run(
            service.db,
            run.id,
            status="success",
            locations_scraped=result["locations"],
            forecasts_saved=result["saved"],
        )

        logger.info(
            f"Forecast scrape job completed successfully: "
            f"{result['locations']} locations, {result['saved']} forecasts saved"
        )

    except Exception as e:
        logger.error(f"Unexpected error in forecast scrape job: {e}")
        logger.debug(traceback.format_exc())

        try:
            if "run" in locals():
                crud.update_scrape_run(
                    service.db,
                    run.id,
                    status="failed",
                    error_message=str(e),
                )
        except Exception as update_error:
            logger.error(f"Failed to update run record: {update_error}")

    finally:
        service.db.close()


def run_warnings_scrape_job() -> None:
    """Execute warnings scraping job with error handling and logging."""
    service = get_service()

    try:
        logger.info("Starting scheduled warnings scrape job")

        result = service.update_warnings(force=False)

        if result["success"]:
            logger.info(
                f"Warnings scrape completed: {result['found']} found, "
                f"{result['saved']} saved, {result['updated']} updated"
            )
        else:
            logger.error("Warnings scrape failed")

    except Exception as e:
        logger.error(f"Warnings scrape job failed: {e}")
        logger.debug(traceback.format_exc())

    finally:
        service.db.close()
