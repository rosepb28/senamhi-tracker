"""CLI commands for SENAMHI tracker."""
from datetime import datetime
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import func

from app.config import settings
from app.database import SessionLocal
from app.scrapers.forecast_scraper import ForecastScraper
from app.storage import crud

app = typer.Typer()
console = Console()


@app.command()
def scrape(
    departments: Annotated[
        str | None,
        typer.Option(help="Comma-separated departments (default: from config)"),
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Force scrape even if data exists")
    ] = False,
):
    """Scrape weather forecasts from SENAMHI."""
    db = SessionLocal()
    
    try:
        dept_list = (
            [d.strip().upper() for d in departments.split(",")]
            if departments
            else settings.get_departments_list()
        )
        
        console.print(f"\n[bold cyan]Scraping forecasts for:[/bold cyan] {', '.join(dept_list)}\n")
        
        scraper = ForecastScraper()
        
        console.print("[yellow]Fetching data from SENAMHI...[/yellow]")
        forecasts = scraper.scrape_forecasts(departments=dept_list)
        
        if not forecasts:
            console.print("[red]No forecasts found![/red]")
            return
        
        issued_at = forecasts[0].issued_at
        console.print(f"[dim]Issue date: {issued_at.strftime('%Y-%m-%d')}[/dim]\n")
        
        # Check if data already exists
        data_exists = False
        for dept in dept_list:
            if crud.forecast_exists_for_issue_date(db, issued_at, dept):
                data_exists = True
                break
        
        if data_exists:
            if not force:
                console.print(
                    f"[yellow]⚠️  Forecasts with issue date "
                    f"{issued_at.strftime('%Y-%m-%d')} already exist in database.[/yellow]"
                )
                console.print(
                    "[dim]Use --force to replace existing data.[/dim]\n"
                )
                return
            else:
                # Delete existing data for this issue date
                console.print("[yellow]Replacing existing data...[/yellow]")
                for dept in dept_list:
                    deleted = crud.delete_forecasts_by_issue_date(db, issued_at, dept)
                    if deleted > 0:
                        console.print(f"  [dim]Deleted {deleted} old entries for {dept}[/dim]")
        
        console.print(f"[green]Found {len(forecasts)} locations[/green]")
        
        saved_count = 0
        for location_forecast in forecasts:
            saved = crud.save_forecast(db, location_forecast)
            saved_count += len(saved)
            console.print(
                f"  [dim]✓[/dim] {location_forecast.location}: {len(saved)} forecasts"
            )
        
        console.print(
            f"\n[bold green]✓ Successfully saved {saved_count} forecast entries![/bold green]\n"
        )
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def list(
    department: Annotated[
        str | None, typer.Option(help="Filter by department")
    ] = None,
    active_only: Annotated[
        bool, typer.Option(help="Show only active locations")
    ] = True,
):
    """List all locations in database."""
    db = SessionLocal()
    
    try:
        locations = crud.get_locations(db, active_only=active_only)
        
        if department:
            locations = [
                loc for loc in locations if loc.department.upper() == department.upper()
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
                f"{forecast.temp_max}°C",
                f"{forecast.temp_min}°C",
                forecast.description[:60] + "..." if len(forecast.description) > 60 else forecast.description,
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
    from datetime import date
    
    db = SessionLocal()
    
    try:
        db_location = crud.get_location_by_name(db, location.upper())
        
        if not db_location:
            console.print(f"[red]Location '{location}' not found.[/red]")
            raise typer.Exit(1)
        
        # Parse as date, not datetime
        forecast_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        forecasts = crud.get_forecast_history(db, db_location.id, forecast_date)
        
        if not forecasts:
            console.print(f"[yellow]No forecast history found for {location} on {date_str}.[/yellow]")
            return
        
        console.print(f"\n[bold cyan]Forecast History: {db_location.full_name}[/bold cyan]")
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
            console.print(f"[bold]Latest issue date:[/bold] {latest_issued.strftime('%Y-%m-%d')}")
        
        if latest_scraped:
            console.print(f"[bold]Last scraped:[/bold] {latest_scraped.strftime('%Y-%m-%d %H:%M')}")
        
        console.print("\n[bold]Locations by department:[/bold]")
        
        departments = {}
        for loc in locations:
            departments[loc.department] = departments.get(loc.department, 0) + 1
        
        for dept, count in sorted(departments.items()):
            console.print(f"  {dept}: {count}")
        
        console.print()
        
    finally:
        db.close()