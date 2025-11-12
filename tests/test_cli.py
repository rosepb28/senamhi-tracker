"""Tests for CLI commands."""
from typer.testing import CliRunner

from app.main import app

runner = CliRunner()


def test_cli_help():
    """Test CLI help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "SENAMHI Tracker" in result.stdout


def test_scrape_help():
    """Test scrape command help."""
    result = runner.invoke(app, ["scrape", "--help"])
    assert result.exit_code == 0
    assert "Scrape weather forecasts" in result.stdout


def test_list_help():
    """Test list command help."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    assert "List all locations" in result.stdout


def test_show_help():
    """Test show command help."""
    result = runner.invoke(app, ["show", "--help"])
    assert result.exit_code == 0
    assert "Show latest forecast" in result.stdout


def test_history_help():
    """Test history command help."""
    result = runner.invoke(app, ["history", "--help"])
    assert result.exit_code == 0
    assert "Show forecast history" in result.stdout


def test_status_help():
    """Test status command help."""
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0
    assert "Show database status" in result.stdout
