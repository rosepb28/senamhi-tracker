"""CLI entry point."""

import typer

from app.cli.commands import app as cli_app

app = typer.Typer(
    name="senamhi",
    help="SENAMHI Tracker - Weather forecast scraper and monitor",
)

app.add_typer(cli_app)

if __name__ == "__main__":
    app()
