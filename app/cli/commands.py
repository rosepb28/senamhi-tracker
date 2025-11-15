"""CLI commands for SENAMHI tracker."""

from typing import Annotated

import typer
from datetime import datetime
from rich.console import Console
from rich.table import Table
from sqlalchemy import func

from app.config import settings
from app.database import SessionLocal
from app.scrapers.forecast_scraper import ForecastScraper
from app.storage import crud
from app.scrapers.warning_scraper import WarningScraper

app = typer.Typer()
scrape_app = typer.Typer(help="Scrape weather data from SENAMHI")
warnings_app = typer.Typer(help="Manage weather warnings")
daemon = typer.Typer(help="Scheduler daemon commands")

app.add_typer(scrape_app, name="scrape")
app.add_typer(daemon, name="daemon")
app.add_typer(warnings_app, name="warnings")
console = Console()


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
    _run_forecast_scrape(departments, all_departments, force)


@scrape_app.command(name="warnings")
def scrape_warnings(
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Force scrape even if data exists")
    ] = False,
):
    """Scrape weather warnings only."""
    _run_warnings_scrape(force)


def _run_warnings_scrape(force: bool):
    """Internal function to run warnings scraping."""
    
    db = SessionLocal()
    
    try:
        console.print("[yellow]Fetching warnings from SENAMHI...[/yellow]")
        console.print(f"[dim]Max warnings: {settings.max_warnings}[/dim]\n")
        
        scraper = WarningScraper()
        warnings = scraper.scrape_warnings()
        
        if not warnings:
            console.print("[yellow]No active warnings found.[/yellow]")
            return
        
        console.print(f"[green]Found {len(warnings)} warnings[/green]\n")
        
        saved_count = 0
        updated_count = 0
        
        for warning in warnings:
            existing = crud.get_warning_by_number(db, warning.warning_number)
            
            if existing and not force:
                console.print(
                    f"  [dim]Skip[/dim] Warning #{warning.warning_number} "
                    f"(already exists, use --force to update)"
                )
                continue
            
            saved = crud.save_warning(db, warning)
            
            if existing:
                updated_count += 1
                status = "Updated"
            else:
                saved_count += 1
                status = "Saved"
            
            console.print(
                f"  [dim]{status}[/dim] Warning #{warning.warning_number}: "
                f"{warning.title[:50]}... "
                f"[{warning.severity.value.upper()}]"
            )
        
        console.print(
            f"\n[bold green]Saved {saved_count} new, updated {updated_count} warnings![/bold green]\n"
        )
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)
    finally:
        db.close()



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
        _run_forecast_scrape(departments, all_departments, force)
        
        console.print("\n[bold]Step 2/2: Scraping warnings...[/bold]")
        _run_warnings_scrape(force)


def _run_forecast_scrape(
    departments: str | None,
    all_departments: bool,
    force: bool,
):
    """Internal function to run forecast scraping."""
    db = SessionLocal()

    try:
        scraper = ForecastScraper()

        if all_departments:
            console.print("[yellow]Fetching data from SENAMHI...[/yellow]")
            forecasts = scraper.scrape_all_departments()
            dept_list = sorted(list(set(f.department for f in forecasts)))
        elif departments:
            dept_list = [d.strip().upper() for d in departments.split(",")]
            console.print("[yellow]Fetching data from SENAMHI...[/yellow]")
            forecasts = scraper.scrape_forecasts(departments=dept_list)
        else:
            dept_list = settings.get_departments_list()
            console.print("[yellow]Fetching data from SENAMHI...[/yellow]")
            forecasts = scraper.scrape_forecasts(departments=dept_list)

        if not forecasts:
            console.print("[red]No forecasts found![/red]")
            return

        issued_at = forecasts[0].issued_at
        console.print(f"[dim]Issue date: {issued_at.strftime('%Y-%m-%d')}[/dim]\n")

        data_exists = False
        for dept in dept_list:
            if crud.forecast_exists_for_issue_date(db, issued_at, dept):
                data_exists = True
                break

        if data_exists:
            if not force:
                console.print(
                    f"[yellow]Warning: Forecasts with issue date "
                    f"{issued_at.strftime('%Y-%m-%d')} already exist in database.[/yellow]"
                )
                console.print("[dim]Use --force to replace existing data.[/dim]\n")
                return
            else:
                console.print("[yellow]Replacing existing data...[/yellow]")
                for dept in dept_list:
                    deleted = crud.delete_forecasts_by_issue_date(db, issued_at, dept)
                    if deleted > 0:
                        console.print(
                            f"  [dim]Deleted {deleted} old entries for {dept}[/dim]"
                        )
                console.print()

        console.print(f"[green]Found {len(forecasts)} locations[/green]\n")

        saved_count = 0
        for location_forecast in forecasts:
            saved = crud.save_forecast(db, location_forecast)
            saved_count += len(saved)
            console.print(
                f"  [dim]OK[/dim] {location_forecast.location} ({location_forecast.department}): {len(saved)} forecasts"
            )

        console.print(
            f"\n[bold green]Successfully saved {saved_count} forecast entries for {len(dept_list)} departments![/bold green]\n"
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command(name="list")
def list_locations(
    department: Annotated[str | None, typer.Option(help="Filter by department")] = None,
    active_only: Annotated[
        bool, typer.Option(help="Show only active locations")
    ] = True,
):
    """List all locations in database."""
    db = SessionLocal()

    try:
        locations = crud.get_locations(db, active_only=active_only)

        if department:
            if isinstance(department, set):
                dept_filters = {d.upper() for d in department}
                locations = [
                    loc for loc in locations if loc.department.upper() in dept_filters
                ]
            else:
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
            status = "OK" if loc.active else "X"
            table.add_row(str(loc.id), loc.location, loc.department, status)

        console.print()
        console.print(table)
        console.print()

    finally:
        db.close()


@app.command()
def show(
    location: Annotated[str, typer.Argument(help="Location name")],
):
    """Show latest forecast for a location."""
    db = SessionLocal()

    try:
        db_location = crud.get_location_by_name(db, location.upper())

        if not db_location:
            console.print(f"[red]Location '{location}' not found in database.[/red]")
            console.print("[dim]Use 'senamhi list' to see available locations.[/dim]")
            raise typer.Exit(1)

        forecasts = crud.get_latest_forecasts(db, location_id=db_location.id)

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
            table.add_row(
                forecast.forecast_date.strftime("%Y-%m-%d"),
                forecast.day_name,
                f"{forecast.temp_max}C",
                f"{forecast.temp_min}C",
                forecast.description[:60] + "..."
                if len(forecast.description) > 60
                else forecast.description,
            )

        console.print(table)
        console.print()

    finally:
        db.close()


@app.command()
def history(
    location: Annotated[str, typer.Argument(help="Location name")],
    date_str: Annotated[str, typer.Argument(help="Forecast date (YYYY-MM-DD)")],
):
    """Show forecast history for a specific date."""

    db = SessionLocal()

    try:
        db_location = crud.get_location_by_name(db, location.upper())

        if not db_location:
            console.print(f"[red]Location '{location}' not found.[/red]")
            raise typer.Exit(1)

        forecast_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        forecasts = crud.get_forecast_history(db, db_location.id, forecast_date)

        if not forecasts:
            console.print(
                f"[yellow]No forecast history found for {location} on {date_str}.[/yellow]"
            )
            return

        console.print(
            f"\n[bold cyan]Forecast History: {db_location.full_name}[/bold cyan]"
        )
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
                f"{forecast.temp_max}C",
                f"{forecast.temp_min}C",
                change,
            )

            prev_max = forecast.temp_max
            prev_min = forecast.temp_min

        console.print(table)
        console.print()

    finally:
        db.close()


@app.command()
def status():
    """Show database status and latest information."""
    db = SessionLocal()

    try:
        locations = crud.get_locations(db)

        if not locations:
            console.print("[yellow]Database is empty.[/yellow]")
            console.print("[dim]Run 'senamhi scrape' to fetch data.[/dim]")
            return

        console.print("\n[bold cyan]Database Status[/bold cyan]\n")

        total_forecasts = db.query(crud.Forecast).count()

        latest_issued = crud.get_latest_issued_date(db)
        latest_scraped = db.query(func.max(crud.Forecast.scraped_at)).scalar()

        console.print(f"[bold]Locations:[/bold] {len(locations)}")
        console.print(f"[bold]Total forecasts:[/bold] {total_forecasts}")

        if latest_issued:
            console.print(
                f"[bold]Latest issue date:[/bold] {latest_issued.strftime('%Y-%m-%d')}"
            )

        if latest_scraped:
            console.print(
                f"[bold]Last scraped:[/bold] {latest_scraped.strftime('%Y-%m-%d %H:%M')}"
            )

        console.print("\n[bold]Locations by department:[/bold]")

        departments = {}
        for loc in locations:
            departments[loc.department] = departments.get(loc.department, 0) + 1

        for dept, count in sorted(departments.items()):
            console.print(f"  {dept}: {count}")

        console.print()

    finally:
        db.close()

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
):
    """List recent weather warnings."""
    db = SessionLocal()
    
    try:
        warnings_list_data = crud.get_warnings(
            db,
            severity=severity,
            active_only=active_only,
            limit=limit,
        )
        
        if not warnings_list_data:
            console.print("[yellow]No warnings found.[/yellow]")
            return
        
        title = f"Weather Warnings (Last {limit})"
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        table.add_column("Number", style="cyan", justify="right")
        table.add_column("Title", style="white")
        table.add_column("Severity")
        table.add_column("Status")
        table.add_column("Valid From")
        table.add_column("Valid Until")
        
        for warning in warnings_list_data:
            # Severity with color
            severity_colors = {
                "verde": "green",
                "amarillo": "#FFD700",
                "naranja": "#FF8C00",
                "rojo": "red",
            }
            severity_color = severity_colors.get(warning.severity, "white")
            severity_text = f"[{severity_color}]{warning.severity.upper()}[/{severity_color}]"
            
            # Status with color
            status_colors = {
                "emitido": "blue",
                "vigente": "red",
                "vencido": "white",
            }
            status_color = status_colors.get(warning.status, "white")
            status_text = f"[{status_color}]{warning.status.upper()}[/{status_color}]"
            
            table.add_row(
                warning.warning_number,
                warning.title[:50] + "..." if len(warning.title) > 50 else warning.title,
                severity_text,
                status_text,
                warning.valid_from.strftime("%Y-%m-%d"),
                warning.valid_until.strftime("%Y-%m-%d"),
            )
        
        console.print()
        console.print(table)
        console.print()
        
    finally:
        db.close()


@warnings_app.command(name="show")
def warnings_show(
    number: Annotated[str, typer.Argument(help="Warning number")],
):
    """Show detailed information for a specific warning."""
    db = SessionLocal()
    
    try:
        warning_obj = crud.get_warning_by_number(db, number)
        
        if not warning_obj:
            console.print(f"[red]Warning #{number} not found.[/red]")
            raise typer.Exit(1)
        
        console.print(f"\n[bold cyan]Warning #{warning_obj.warning_number}[/bold cyan]")
        
        # Status with color
        status_colors = {
            "emitido": "blue",
            "vigente": "red",
            "vencido": "white",
        }
        status_color = status_colors.get(warning_obj.status, "white")
        console.print(f"Status: [{status_color}]{warning_obj.status.upper()}[/{status_color}]")
        
        console.print()
        
        # Severity with color
        severity_colors = {
            "verde": "green",
            "amarillo": "#FFD700",
            "naranja": "#FF8C00",
            "rojo": "red",
        }
        severity_color = severity_colors.get(warning_obj.severity, "white")
        
        console.print(f"[bold]Title:[/bold] {warning_obj.title}")
        console.print(f"[bold]Severity:[/bold] [{severity_color}]{warning_obj.severity.upper()}[/{severity_color}]")
        console.print()
        console.print(f"[bold]Issued:[/bold] {warning_obj.issued_at.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"[bold]Valid from:[/bold] {warning_obj.valid_from.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"[bold]Valid until:[/bold] {warning_obj.valid_until.strftime('%Y-%m-%d %H:%M')}")
        console.print()
        console.print(f"[bold]Description:[/bold]")
        console.print(warning_obj.description)
        console.print()
        
    finally:
        db.close()

@warnings_app.command(name="active")
def warnings_active(
    limit: Annotated[int, typer.Option(help="Number of warnings to show")] = 20,
):
    """List only active warnings (EMITIDO + VIGENTE)."""
    warnings_list(limit=limit, severity=None, active_only=True)


@app.command()
def departments():
    """List all available departments from SENAMHI."""
    try:
        console.print(
            "\n[yellow]Fetching available departments from SENAMHI...[/yellow]\n"
        )

        scraper = ForecastScraper()
        depts = scraper.get_all_departments()

        console.print(f"[bold cyan]Available Departments ({len(depts)}):[/bold cyan]\n")

        for dept in depts:
            console.print(f"  - {dept}")

        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


# Create subgroup for daemon commands
daemon = typer.Typer(help="Scheduler daemon commands")
app.add_typer(daemon, name="daemon")


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
    
    console.print(f"[bold]Enabled:[/bold] {'Yes' if settings.enable_scheduler else 'No'}")
    console.print(f"[bold]Forecast Interval:[/bold] {settings.forecast_scrape_interval} hours")
    console.print(f"[bold]Warning Interval:[/bold] {settings.warning_scrape_interval} hours")
    console.print(f"[bold]Start Immediately:[/bold] {'Yes' if settings.scheduler_start_immediately else 'No'}")
    console.print(f"[bold]Max Warnings per Scrape:[/bold] {settings.max_warnings}")
    console.print()
    
    # Check if scheduler is running
    import subprocess
    try:
        result = subprocess.run(
            ["pgrep", "-f", "ForecastScheduler"],
            capture_output=True,
            text=True
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
    db = SessionLocal()

    try:
        runs = crud.get_scrape_runs(db, limit=limit, status=status)

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
            # Calculate duration
            if run.finished_at:
                duration = run.finished_at - run.started_at
                duration_str = f"{duration.total_seconds():.0f}s"
            else:
                duration_str = "running"

            # Status color
            if run.status == "success":
                status_text = "[green]success[/green]"
            elif run.status == "failed":
                status_text = "[red]failed[/red]"
            elif run.status == "skipped":
                status_text = "[yellow]skipped[/yellow]"
            else:
                status_text = run.status

            table.add_row(
                str(run.id),
                run.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                duration_str,
                status_text,
                str(run.locations_scraped),
                str(run.forecasts_saved),
                run.departments[:30] + "..."
                if len(run.departments) > 30
                else run.departments,
            )

        console.print()
        console.print(table)
        console.print()

        # Show error details for failed runs
        failed_runs = [r for r in runs if r.status == "failed" and r.error_message]
        if failed_runs:
            console.print("[bold red]Recent Errors:[/bold red]\n")
            for run in failed_runs[:3]:
                console.print(f"[red]Run #{run.id}:[/red] {run.error_message[:100]}")
            console.print()

    finally:
        db.close()
