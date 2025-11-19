"""CLI commands for SENAMHI tracker."""

from typing import Annotated
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

from config.settings import settings
from app.database import SessionLocal
from app.services.weather_service import WeatherService
from scripts.populate_coordinates import populate_coordinates
from app.storage.models import WarningAlert

app = typer.Typer()
scrape_app = typer.Typer(help="Scrape weather data from SENAMHI")
warnings_app = typer.Typer(help="Manage weather warnings")
geo_app = typer.Typer(help="Geospatial operations (shapefiles, geometries)")
daemon = typer.Typer(help="Scheduler daemon commands")

app.add_typer(scrape_app, name="scrape")
app.add_typer(daemon, name="daemon")
app.add_typer(warnings_app, name="warnings")
app.add_typer(geo_app, name="geo")

console = Console()


def get_service() -> WeatherService:
    """Factory function to create WeatherService with database session."""
    db = SessionLocal()
    return WeatherService(db)


@scrape_app.command(name="forecasts")
def scrape_forecasts(
    departments: Annotated[
        str | None,
        typer.Option(help="Comma-separated departments (overrides config)"),
    ] = None,
    all_departments: Annotated[
        bool,
        typer.Option("--all", help="Scrape all available departments"),
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Force scrape even if data exists")
    ] = False,
):
    """Scrape weather forecasts only."""
    service = get_service()
    try:
        dept_list = None
        if departments:
            dept_list = [d.strip().upper() for d in departments.split(",")]
        elif not all_departments and not settings.scrape_all_departments:
            dept_list = settings.get_departments_list()

        console.print("[yellow]Fetching data from SENAMHI...[/yellow]")
        result = service.update_forecasts(departments=dept_list, force=force)

        if not result["success"]:
            if result.get("skipped"):
                console.print(
                    f"\n[yellow]Warning: Forecasts with issue date "
                    f"{result['issued_at'].strftime('%Y-%m-%d')} already exist.[/yellow]"
                )
                console.print("[dim]Use --force to replace existing data.[/dim]\n")
            else:
                console.print(
                    f"[red]Error: {result.get('error', 'Unknown error')}[/red]"
                )
            return

        console.print(
            f"[dim]Issue date: {result['issued_at'].strftime('%Y-%m-%d')}[/dim]\n"
        )
        console.print(f"[green]Found {result['locations']} locations[/green]\n")

        console.print(
            f"[bold green]Successfully saved {result['saved']} forecast entries![/bold green]\n"
        )

        populate_coordinates(skip_existing=True)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        service.db.close()


@scrape_app.command(name="warnings")
def scrape_warnings_cmd(
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Force scrape even if data exists")
    ] = False,
):
    """Scrape weather warnings only."""
    service = get_service()
    try:
        console.print("[yellow]Fetching warnings from SENAMHI...[/yellow]")
        console.print("[dim]Scraping only EMITIDO and VIGENTE warnings[/dim]\n")

        result = service.update_warnings(force=force)

        if result["found"] == 0:
            console.print("[yellow]No active warnings found.[/yellow]")
            return

        console.print(f"[green]Found {result['found']} active warnings[/green]\n")
        console.print(
            f"[bold green]Saved {result['saved']} new, updated {result['updated']} warnings![/bold green]\n"
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        service.db.close()


@scrape_app.callback(invoke_without_command=True)
def scrape_callback(
    ctx: typer.Context,
    departments: Annotated[
        str | None,
        typer.Option(help="Comma-separated departments (overrides config)"),
    ] = None,
    all_departments: Annotated[
        bool,
        typer.Option("--all", help="Scrape all available departments"),
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Force scrape even if data exists")
    ] = False,
):
    """Scrape both forecasts and warnings (default behavior)."""
    if ctx.invoked_subcommand is None:
        console.print("\n[bold cyan]Scraping forecasts and warnings[/bold cyan]\n")

        console.print("[bold]Step 1/2: Scraping forecasts...[/bold]")
        ctx.invoke(
            scrape_forecasts,
            departments=departments,
            all_departments=all_departments,
            force=force,
        )

        console.print("\n[bold]Step 2/2: Scraping warnings...[/bold]")
        ctx.invoke(scrape_warnings_cmd, force=force)


@app.command(name="list")
def list_locations(
    department: Annotated[str | None, typer.Option(help="Filter by department")] = None,
    active_only: Annotated[
        bool, typer.Option(help="Show only active locations")
    ] = True,
):
    """List all locations in database."""
    service = get_service()
    try:
        locations = service.get_all_locations(active_only=active_only)

        if department:
            dept_filter = department.upper()
            locations = [
                loc for loc in locations if loc.department.upper() == dept_filter
            ]

        if not locations:
            console.print("[yellow]No locations found in database.[/yellow]")
            console.print("[dim]Run 'senamhi scrape' first.[/dim]")
            return

        table = Table(title="Locations", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Location", style="white")
        table.add_column("Department", style="green")
        table.add_column("Status", style="yellow", justify="center")

        for loc in locations:
            status = "✓" if loc.active else "✗"
            table.add_row(str(loc.id), loc.location, loc.department, status)

        console.print()
        console.print(table)
        console.print()

    finally:
        service.db.close()


@app.command()
def show(
    location: Annotated[str, typer.Argument(help="Location name")],
):
    """Show latest forecast for a location."""
    service = get_service()
    try:
        result = service.get_location_forecasts(location.upper())

        if not result:
            console.print(f"[red]Location '{location}' not found in database.[/red]")
            console.print("[dim]Use 'senamhi list' to see available locations.[/dim]")
            raise typer.Exit(1)

        db_location = result["location"]
        forecasts = result["forecasts"]

        if not forecasts:
            console.print(f"[yellow]No forecasts found for {location}.[/yellow]")
            return

        console.print(f"\n[bold cyan]{db_location.full_name}[/bold cyan]\n")

        issued_at = forecasts[0].issued_at
        scraped_at = forecasts[0].scraped_at

        console.print(f"[dim]Issued: {issued_at.strftime('%Y-%m-%d')}[/dim]")
        console.print(f"[dim]Scraped: {scraped_at.strftime('%Y-%m-%d %H:%M')}[/dim]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Date", style="cyan")
        table.add_column("Day", style="white")
        table.add_column("Max", style="red", justify="right")
        table.add_column("Min", style="blue", justify="right")
        table.add_column("Description", style="white")

        for forecast in forecasts:
            desc = forecast.description
            if len(desc) > 60:
                desc = desc[:60] + "..."

            table.add_row(
                forecast.forecast_date.strftime("%Y-%m-%d"),
                forecast.day_name,
                f"{forecast.temp_max}°C",
                f"{forecast.temp_min}°C",
                desc,
            )

        console.print(table)
        console.print()

    finally:
        service.db.close()


@app.command()
def history(
    location: Annotated[str, typer.Argument(help="Location name")],
    date_str: Annotated[str, typer.Argument(help="Forecast date (YYYY-MM-DD)")],
):
    """Show forecast history for a specific date."""
    service = get_service()
    try:
        forecast_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        forecasts = service.get_forecast_history(location.upper(), forecast_date)

        if forecasts is None:
            console.print(f"[red]Location '{location}' not found.[/red]")
            raise typer.Exit(1)

        if not forecasts:
            console.print(
                f"[yellow]No forecast history found for {location} on {date_str}.[/yellow]"
            )
            return

        console.print(f"\n[bold cyan]Forecast History: {location}[/bold cyan]")
        console.print(f"[bold]Date:[/bold] {date_str}\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Issued", style="cyan")
        table.add_column("Scraped", style="dim")
        table.add_column("Max", style="red", justify="right")
        table.add_column("Min", style="blue", justify="right")
        table.add_column("Change", style="yellow", justify="right")

        prev_max = None
        prev_min = None

        for forecast in forecasts:
            change = ""
            if prev_max is not None:
                max_diff = forecast.temp_max - prev_max
                min_diff = forecast.temp_min - prev_min
                if max_diff != 0 or min_diff != 0:
                    change = f"({max_diff:+d}/{min_diff:+d})"

            table.add_row(
                forecast.issued_at.strftime("%Y-%m-%d"),
                forecast.scraped_at.strftime("%m-%d %H:%M"),
                f"{forecast.temp_max}°C",
                f"{forecast.temp_min}°C",
                change,
            )

            prev_max = forecast.temp_max
            prev_min = forecast.temp_min

        console.print(table)
        console.print()

    finally:
        service.db.close()


@app.command()
def status():
    """Show database status and latest information."""
    service = get_service()
    try:
        stats = service.get_database_status()

        if stats["locations"] == 0:
            console.print("[yellow]Database is empty.[/yellow]")
            console.print("[dim]Run 'senamhi scrape' to fetch data.[/dim]")
            return

        console.print("\n[bold cyan]Database Status[/bold cyan]\n")
        console.print(f"[bold]Locations:[/bold] {stats['locations']}")
        console.print(f"[bold]Total forecasts:[/bold] {stats['total_forecasts']}")

        if stats["latest_issued"]:
            console.print(
                f"[bold]Latest issue date:[/bold] {stats['latest_issued'].strftime('%Y-%m-%d')}"
            )

        console.print("\n[bold]Locations by department:[/bold]")
        for dept, count in sorted(stats["departments"].items()):
            console.print(f"  {dept}: {count}")

        console.print()

    finally:
        service.db.close()


# ==================== Warnings Commands ====================


@warnings_app.command(name="list")
def warnings_list(
    limit: Annotated[int, typer.Option(help="Number of warnings to show")] = 10,
    severity: Annotated[
        str | None,
        typer.Option(help="Filter by severity (verde/amarillo/naranja/rojo)"),
    ] = None,
    active_only: Annotated[
        bool,
        typer.Option(help="Show only active warnings"),
    ] = False,
    department: Annotated[
        str | None,
        typer.Option(help="Filter by department"),
    ] = None,
):
    """List recent weather warnings (deduplicated by warning number)."""
    service = get_service()
    try:
        warnings_list_data = service.get_warnings(
            severity=severity,
            active_only=active_only,
            limit=limit * 10,  # Get more to allow for deduplication
        )

        if not warnings_list_data:
            console.print("[yellow]No warnings found.[/yellow]")
            return

        # Filter by department if specified
        if department:
            warnings_list_data = [
                w
                for w in warnings_list_data
                if w.department.upper() == department.upper()
            ]

        # Deduplicate by warning_number (keep first occurrence)
        seen = set()
        unique_warnings = []
        for warning in warnings_list_data:
            if warning.warning_number not in seen:
                seen.add(warning.warning_number)
                unique_warnings.append(warning)

            if len(unique_warnings) >= limit:
                break

        if not unique_warnings:
            console.print("[yellow]No warnings found matching filters.[/yellow]")
            return

        title = f"Weather Warnings (Last {len(unique_warnings)})"
        table = Table(title=title, show_header=True, header_style="bold magenta")

        table.add_column("Number", style="cyan", justify="right")
        table.add_column("Title", style="white")
        table.add_column("Severity")
        table.add_column("Status")
        table.add_column("Departments", style="dim")  # Show affected departments
        table.add_column("Valid From")
        table.add_column("Valid Until")

        severity_colors = {
            "verde": "green",
            "amarillo": "#FFD700",
            "naranja": "#FF8C00",
            "rojo": "red",
        }
        status_colors = {
            "emitido": "blue",
            "vigente": "red",
            "vencido": "white",
        }

        for warning in unique_warnings:
            severity_color = severity_colors.get(warning.severity, "white")
            severity_text = (
                f"[{severity_color}]{warning.severity.upper()}[/{severity_color}]"
            )

            status_color = status_colors.get(warning.status, "white")
            status_text = f"[{status_color}]{warning.status.upper()}[/{status_color}]"

            title_text = warning.title
            if len(title_text) > 50:
                title_text = title_text[:50] + "..."

            # Count departments affected by this warning number
            dept_count = sum(
                1
                for w in warnings_list_data
                if w.warning_number == warning.warning_number
            )
            dept_text = (
                f"{dept_count} dept(s)" if dept_count > 1 else warning.department
            )

            table.add_row(
                warning.warning_number,
                title_text,
                severity_text,
                status_text,
                dept_text,
                warning.valid_from.strftime("%Y-%m-%d"),
                warning.valid_until.strftime("%Y-%m-%d"),
            )

        console.print()
        console.print(table)
        console.print()

    finally:
        service.db.close()


@warnings_app.command(name="show")
def warnings_show(
    number: Annotated[str, typer.Argument(help="Warning number")],
):
    """Show detailed information for a specific warning."""
    service = get_service()
    try:
        warning = service.get_warning_details(number)

        if not warning:
            console.print(f"[red]Warning #{number} not found.[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold cyan]Warning #{warning.warning_number}[/bold cyan]")

        status_colors = {"emitido": "blue", "vigente": "red", "vencido": "white"}
        status_color = status_colors.get(warning.status, "white")
        console.print(
            f"Status: [{status_color}]{warning.status.upper()}[/{status_color}]"
        )
        console.print()

        severity_colors = {
            "verde": "green",
            "amarillo": "#FFD700",
            "naranja": "#FF8C00",
            "rojo": "red",
        }
        severity_color = severity_colors.get(warning.severity, "white")

        console.print(f"[bold]Title:[/bold] {warning.title}")
        console.print(
            f"[bold]Severity:[/bold] [{severity_color}]{warning.severity.upper()}[/{severity_color}]"
        )
        console.print()
        console.print(
            f"[bold]Issued:[/bold] {warning.issued_at.strftime('%Y-%m-%d %H:%M')}"
        )
        console.print(
            f"[bold]Valid from:[/bold] {warning.valid_from.strftime('%Y-%m-%d %H:%M')}"
        )
        console.print(
            f"[bold]Valid until:[/bold] {warning.valid_until.strftime('%Y-%m-%d %H:%M')}"
        )
        console.print()
        console.print("[bold]Description:[/bold]")
        console.print(warning.description)
        console.print()

    finally:
        service.db.close()


@warnings_app.command(name="active")
def warnings_active(
    limit: Annotated[int, typer.Option(help="Number of warnings to show")] = 20,
):
    """List only active warnings (EMITIDO + VIGENTE)."""
    warnings_list(limit=limit, severity=None, active_only=True)


@app.command()
def departments():
    """List all available departments from SENAMHI."""
    service = get_service()
    try:
        console.print(
            "\n[yellow]Fetching available departments from SENAMHI...[/yellow]\n"
        )

        depts = service.get_available_departments()

        console.print(f"[bold cyan]Available Departments ({len(depts)}):[/bold cyan]\n")

        for dept in depts:
            console.print(f"  - {dept}")

        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        service.db.close()


# ==================== Daemon commands ====================
@daemon.command(name="start")
def daemon_start():
    """Start the scheduler daemon in foreground."""
    from app.scheduler.scheduler import ForecastScheduler

    if not settings.enable_scheduler:
        console.print("[red]Scheduler is disabled in configuration.[/red]")
        console.print("[dim]Set ENABLE_SCHEDULER=True in .env to enable.[/dim]")
        raise typer.Exit(1)

    scheduler = ForecastScheduler()
    scheduler.start()


@daemon.command(name="status")
def daemon_status():
    """Show scheduler status and configuration."""
    console.print("\n[bold cyan]Scheduler Configuration[/bold cyan]\n")

    console.print(
        f"[bold]Enabled:[/bold] {'Yes' if settings.enable_scheduler else 'No'}"
    )
    console.print(
        f"[bold]Forecast Interval:[/bold] {settings.forecast_scrape_interval} hours"
    )
    console.print(
        f"[bold]Warning Interval:[/bold] {settings.warning_scrape_interval} hours"
    )
    console.print(
        f"[bold]Start Immediately:[/bold] {'Yes' if settings.scheduler_start_immediately else 'No'}"
    )
    console.print()

    import subprocess

    try:
        result = subprocess.run(
            ["pgrep", "-f", "ForecastScheduler"], capture_output=True, text=True
        )
        if result.returncode == 0:
            console.print("[green]Status: RUNNING[/green]")
            console.print(f"[dim]PID: {result.stdout.strip()}[/dim]")
        else:
            console.print("[yellow]Status: NOT RUNNING[/yellow]")
    except Exception:
        console.print("[dim]Cannot determine status[/dim]")

    console.print()


@app.command()
def runs(
    limit: Annotated[int, typer.Option(help="Number of runs to show")] = 20,
    status: Annotated[
        str | None, typer.Option(help="Filter by status (success/failed/skipped)")
    ] = None,
):
    """Show scrape run history."""
    service = get_service()
    try:
        runs = service.get_scrape_runs(limit=limit, status=status)

        if not runs:
            console.print("[yellow]No scrape runs found in database.[/yellow]")
            return

        table = Table(
            title=f"Scrape Run History (Last {limit})",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Started", style="white")
        table.add_column("Duration", style="dim", justify="right")
        table.add_column("Status", style="yellow")
        table.add_column("Locations", style="green", justify="right")
        table.add_column("Forecasts", style="green", justify="right")
        table.add_column("Departments", style="dim")

        for run in runs:
            if run.finished_at:
                duration = run.finished_at - run.started_at
                duration_str = f"{duration.total_seconds():.0f}s"
            else:
                duration_str = "running"

            if run.status == "success":
                status_text = "[green]success[/green]"
            elif run.status == "failed":
                status_text = "[red]failed[/red]"
            elif run.status == "skipped":
                status_text = "[yellow]skipped[/yellow]"
            else:
                status_text = run.status

            dept_text = run.departments
            if len(dept_text) > 30:
                dept_text = dept_text[:30] + "..."

            table.add_row(
                str(run.id),
                run.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                duration_str,
                status_text,
                str(run.locations_scraped),
                str(run.forecasts_saved),
                dept_text,
            )

        console.print()
        console.print(table)
        console.print()

        failed_runs = [r for r in runs if r.status == "failed" and r.error_message]
        if failed_runs:
            console.print("[bold red]Recent Errors:[/bold red]\n")
            for run in failed_runs[:3]:
                error_msg = run.error_message[:100] if run.error_message else "Unknown"
                console.print(f"[red]Run #{run.id}:[/red] {error_msg}")
            console.print()

    finally:
        service.db.close()


@app.command()
def web(
    host: Annotated[str | None, typer.Option(help="Host to bind")] = None,
    port: Annotated[int | None, typer.Option(help="Port to bind")] = None,
    debug: Annotated[bool | None, typer.Option(help="Debug mode")] = None,
):
    """Start the web dashboard."""
    from app.web.app import create_app

    final_host = host or settings.web_host
    final_port = port or settings.web_port
    final_debug = debug if debug is not None else settings.web_debug

    console.print("\n[bold cyan]Starting SENAMHI Tracker Dashboard[/bold cyan]\n")
    console.print(f"[dim]Running on http://{final_host}:{final_port}[/dim]\n")

    app_instance = create_app()
    app_instance.run(host=final_host, port=final_port, debug=final_debug)


# ==================== Geospatial Commands ====================


@geo_app.command(name="download")
def geo_download(
    warning_number: Annotated[str, typer.Argument(help="Warning number to download")],
):
    """Download shapefiles for a specific warning."""
    from app.scrapers.shapefile_downloader import ShapefileDownloader

    db = SessionLocal()
    try:
        # Find warning
        warning = (
            db.query(WarningAlert)
            .filter(WarningAlert.warning_number == warning_number)
            .first()
        )

        if not warning:
            console.print(
                f"[red]Warning #{warning_number} not found in database.[/red]"
            )
            console.print("[dim]Run 'senamhi scrape warnings' first.[/dim]")
            raise typer.Exit(1)

        if not warning.senamhi_id:
            console.print(
                f"[yellow]Warning #{warning_number} has no SENAMHI ID.[/yellow]"
            )
            console.print("[dim]Re-scrape warnings to get SENAMHI ID.[/dim]")
            raise typer.Exit(1)

        # Download shapefiles
        downloader = ShapefileDownloader()
        files = downloader.download_warning_shapefiles(warning)

        if files:
            console.print(f"\n[green]✓ Downloaded {len(files)} shapefile(s)[/green]")
        else:
            console.print("[yellow]No shapefiles downloaded.[/yellow]")

    finally:
        db.close()


@geo_app.command(name="sync")
def geo_sync(
    warning_number: Annotated[str, typer.Argument(help="Warning number to sync")],
):
    """Parse shapefiles and save geometries to database (PostgreSQL only)."""
    if not settings.supports_postgis:
        console.print("[red]PostGIS is not available (using SQLite).[/red]")
        console.print("[dim]Use PostgreSQL to enable geometry storage.[/dim]")
        raise typer.Exit(1)

    from app.scrapers.shapefile_downloader import ShapefileDownloader
    from app.scrapers.shapefile_parser import ShapefileParser
    from app.storage.geo_crud import save_warning_geometry

    db = SessionLocal()
    try:
        # Find warning
        warning = (
            db.query(WarningAlert)
            .filter(WarningAlert.warning_number == warning_number)
            .first()
        )

        if not warning:
            console.print(f"[red]Warning #{warning_number} not found.[/red]")
            raise typer.Exit(1)

        # Find downloaded shapefiles
        downloader = ShapefileDownloader()
        parser = ShapefileParser()

        year = warning.valid_from.year
        num_days = downloader.calculate_warning_days(warning)

        console.print(
            f"\n[bold]Syncing geometries for Warning #{warning_number}[/bold]"
        )
        console.print(f"[dim]Days: {num_days}[/dim]\n")

        synced = 0
        for day in range(1, num_days + 1):
            zip_path = (
                downloader.download_dir
                / f"warning_{warning_number}_day_{day}_{year}.zip"
            )

            if not zip_path.exists():
                console.print(f"  [yellow]Day {day}: Shapefile not found[/yellow]")
                continue

            # Parse geometry
            geometry = parser.parse_shapefile_zip(zip_path)

            if geometry:
                # Save to database
                url = downloader.build_shapefile_url(warning_number, day, year)
                save_warning_geometry(
                    db,
                    warning_id=warning.id,
                    day_number=day,
                    geometry=geometry,
                    shapefile_url=url,
                    shapefile_path=zip_path,
                )
                synced += 1
                console.print(f"  [green]✓ Day {day}: Synced geometry[/green]")
            else:
                console.print(f"  [red]✗ Day {day}: Failed to parse[/red]")

        console.print(
            f"\n[green]Synced {synced}/{num_days} geometries to database[/green]\n"
        )

    finally:
        db.close()


@geo_app.command(name="list")
def geo_list():
    """List downloaded shapefiles."""
    from app.scrapers.shapefile_downloader import ShapefileDownloader
    from app.scrapers.shapefile_parser import ShapefileParser

    downloader = ShapefileDownloader()
    parser = ShapefileParser()

    files = downloader.list_downloaded_shapefiles()

    if not files:
        console.print("[yellow]No shapefiles downloaded.[/yellow]")
        console.print(
            "[dim]Use 'senamhi geo download <warning_number>' to download.[/dim]"
        )
        return

    console.print(f"\n[bold]Downloaded Shapefiles ({len(files)})[/bold]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File", style="cyan")
    table.add_column("Size", style="white", justify="right")
    table.add_column("Valid", style="green", justify="center")

    for filepath in files:
        size_kb = filepath.stat().st_size / 1024
        is_valid = parser.validate_shapefile_zip(filepath)

        table.add_row(
            filepath.name,
            f"{size_kb:.1f} KB",
            "✓" if is_valid else "✗",
        )

    console.print(table)
    console.print()


@geo_app.command(name="status")
def geo_status():
    """Show geospatial backend information."""
    from app.services.geo_service import GeoService

    db = SessionLocal()
    try:
        geo_service = GeoService(db)
        info = geo_service.get_backend_info()

        console.print("\n[bold cyan]Geospatial Backend Status[/bold cyan]\n")
        console.print(f"[bold]Database:[/bold] {info['database_type']}")
        console.print(
            f"[bold]PostGIS Available:[/bold] {'Yes' if info['postgis_available'] else 'No'}"
        )
        console.print(f"[bold]Spatial Queries:[/bold] {info['spatial_queries']}")
        console.print()

        if not info["postgis_available"]:
            console.print(
                "[yellow]💡 Tip: Use PostgreSQL to enable PostGIS features[/yellow]"
            )
            console.print(
                "[dim]   docker compose -f docker-compose.postgres.yml up -d[/dim]"
            )
            console.print()

    finally:
        db.close()


@geo_app.command(name="info")
def geo_info(
    warning_number: Annotated[str, typer.Argument(help="Warning number")],
):
    """Show geometry information for a warning."""
    if not settings.supports_postgis:
        console.print("[red]PostGIS not available (using SQLite).[/red]")
        raise typer.Exit(1)

    from app.storage.geo_crud import get_warning_geometries

    db = SessionLocal()
    try:
        # Find warning
        warning = (
            db.query(WarningAlert)
            .filter(WarningAlert.warning_number == warning_number)
            .first()
        )

        if not warning:
            console.print(f"[red]Warning #{warning_number} not found.[/red]")
            raise typer.Exit(1)

        # Get geometries
        geometries = get_warning_geometries(db, warning.id)

        if not geometries:
            console.print(
                f"[yellow]No geometries found for Warning #{warning_number}.[/yellow]"
            )
            console.print(
                "[dim]Use 'senamhi geo sync {warning_number}' to parse shapefiles.[/dim]"
            )
            return

        console.print(f"\n[bold]Warning #{warning_number} Geometries[/bold]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Day", style="cyan", justify="center")
        table.add_column("Downloaded", style="white")
        table.add_column("Has Geometry", style="green", justify="center")

        for geom in geometries:
            table.add_row(
                str(geom.day_number),
                geom.downloaded_at.strftime("%Y-%m-%d %H:%M")
                if geom.downloaded_at
                else "N/A",
                "✓" if geom.geometry else "✗",
            )

        console.print(table)
        console.print()

    finally:
        db.close()
