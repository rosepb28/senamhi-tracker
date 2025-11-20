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
                    # Populate coordinates after successful scrape
                    from app.services.coordinates_service import populate_coordinates

                    populate_coordinates(skip_existing=True)

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


def run_shapefile_download_job() -> None:
    """
    Execute automatic shapefile download and sync for active warnings.

    Only downloads and syncs warnings that:
    - Are in 'vigente' or 'emitido' status
    - Don't already have geometries in database
    - Have PostGIS available
    """
    from config.settings import settings

    if not settings.supports_postgis:
        logger.info("PostGIS not available, skipping shapefile download job")
        return

    db = SessionLocal()

    try:
        logger.info("Starting scheduled shapefile download job")

        from app.storage.models import WarningAlert
        from app.storage.geo_models import WarningGeometry
        from app.scrapers.shapefile_downloader import ShapefileDownloader
        from app.scrapers.shapefile_parser import ShapefileParser
        from app.storage.geo_crud import save_warning_geometry
        from shapely.geometry import MultiPolygon

        # Get active warnings (vigente or emitido)
        active_warnings = (
            db.query(WarningAlert)
            .filter(WarningAlert.status.in_(["vigente", "emitido"]))
            .all()
        )

        if not active_warnings:
            logger.info("No active warnings found")
            return

        # Group by warning_number to avoid duplicates
        warnings_by_number = {}
        for warning in active_warnings:
            if warning.warning_number not in warnings_by_number:
                warnings_by_number[warning.warning_number] = warning

        logger.info(f"Found {len(warnings_by_number)} unique active warning(s)")

        downloader = ShapefileDownloader()
        parser = ShapefileParser()

        downloaded = 0
        synced = 0
        skipped = 0

        for warning_number, warning in warnings_by_number.items():
            # Check if already has geometries by warning_number
            existing_geom = (
                db.query(WarningGeometry)
                .filter(WarningGeometry.warning_number == warning_number)
                .first()
            )

            if existing_geom:
                logger.debug(
                    f"Warning #{warning_number} already has geometries, skipping"
                )
                skipped += 1
                continue

            logger.info(f"Processing warning #{warning_number}")

            try:
                # Calculate number of days
                num_days = downloader.calculate_warning_days(warning)
                year = warning.valid_from.year

                # Download shapefiles
                download_success = True
                for day in range(1, num_days + 1):
                    filepath = downloader.download_shapefile(warning_number, day, year)

                    if filepath:
                        logger.debug(f"  Day {day}: Downloaded")
                        downloaded += 1
                    else:
                        logger.warning(f"  Day {day}: Download failed")
                        download_success = False
                        break

                if not download_success:
                    continue

                # Parse and sync geometries
                total_polygons = 0
                for day in range(1, num_days + 1):
                    zip_path = (
                        downloader.download_dir
                        / f"warning_{warning_number}_day_{day}_{year}.zip"
                    )

                    if not zip_path.exists():
                        continue

                    # Parse polygons
                    polygons = parser.parse_shapefile_zip(zip_path)

                    if not polygons:
                        logger.warning(f"  Day {day}: Failed to parse")
                        continue

                    # Group by nivel
                    polygons_by_nivel = {}
                    for poly_data in polygons:
                        nivel = poly_data["nivel"]
                        if nivel not in polygons_by_nivel:
                            polygons_by_nivel[nivel] = []
                        polygons_by_nivel[nivel].append(poly_data["geometry"])

                    # Save each nivel
                    url = downloader.build_shapefile_url(warning_number, day, year)
                    for nivel, geom_list in polygons_by_nivel.items():
                        all_polys = []
                        for mp in geom_list:
                            if isinstance(mp, MultiPolygon):
                                all_polys.extend(mp.geoms)
                            else:
                                all_polys.append(mp)

                        combined_mp = MultiPolygon(all_polys)

                        save_warning_geometry(
                            db,
                            warning_id=warning.id,
                            warning_number=warning_number,
                            day_number=day,
                            geometry=combined_mp,
                            nivel=nivel,
                            shapefile_url=url,
                            shapefile_path=zip_path,
                        )
                        total_polygons += 1

                if total_polygons > 0:
                    logger.info(f"  Synced {total_polygons} geometry record(s)")
                    synced += 1

            except Exception as e:
                logger.error(f"  Error processing warning #{warning_number}: {e}")
                continue

        logger.info(
            f"Shapefile download job completed: "
            f"{downloaded} downloaded, {synced} synced, {skipped} skipped"
        )

    except Exception as e:
        logger.error(f"Shapefile download job failed: {e}")
        logger.debug(traceback.format_exc())

    finally:
        db.close()
