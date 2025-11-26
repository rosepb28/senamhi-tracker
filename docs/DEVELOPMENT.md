# 🛠️ Development Guide

Guide for contributors and developers.

## Quick Setup
```bash
# Clone and install
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker
poetry install

# Setup database
poetry run alembic upgrade head

# Configure
cp .env.example .env

# Run tests
poetry run pytest -v
```

## Development Workflow

### Code Changes
```bash
# Create feature branch
git checkout -b feat/amazing-feature

# Make changes
# ... edit code ...

# Format and lint
make check

# Run tests
poetry run pytest -v

# Commit
git add .
git commit -m "feat: add amazing feature"

# Push
git push origin feat/amazing-feature
```

### Testing
```bash
# Run all tests
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_warnings.py -v

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Note:** Tests use SQLite and skip PostGIS-dependent tests automatically.

### Code Quality
```bash
# Lint and format (combined)
make check

# Or separately:
poetry run ruff check . --fix    # Lint with auto-fix
poetry run ruff format .          # Format code

# Pre-commit hooks (runs automatically on commit)
poetry run pre-commit install
poetry run pre-commit run --all-files
```

### Database Migrations
```bash
# Create new migration
poetry run alembic revision --autogenerate -m "add new field"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# View current version
poetry run alembic current

# View migration history
poetry run alembic history
```

**Helper scripts:**
```bash
# Create migration (interactive)
./dev_tools/new_migration.sh "add_new_field"

# Reset database (⚠️ destructive)
./dev_tools/reset_db.sh
```

## Project Structure
```
app/
├── cli/              # Typer CLI commands
│   ├── main.py
│   ├── scrape.py
│   ├── warnings.py
│   └── geo.py
├── scrapers/         # Web scrapers
│   ├── forecast_scraper.py
│   ├── warning_scraper.py
│   ├── warning_details_scraper.py
│   └── shapefile_downloader.py
├── services/         # Business logic
│   ├── forecast_service.py
│   ├── warning_service.py
│   ├── openmeteo_service.py
│   └── geospatial_service.py
├── storage/          # Database layer
│   ├── models.py
│   └── crud.py
├── scheduler/        # Background jobs
│   └── scheduler.py
└── web/              # Flask web app
    ├── app.py
    ├── routes/
    │   ├── main.py
    │   └── api.py
    ├── templates/
    └── static/
        ├── css/
        └── js/

config/               # Configuration files
├── coordinates.yaml  # Location coordinates
├── openmeteo.yaml   # Weather model config
└── settings.py      # Pydantic settings

data/                 # Data storage
├── weather.db       # SQLite database
├── boundaries/      # GeoJSON boundaries
└── shapefiles/      # Downloaded shapefiles

tests/               # Test suite
├── test_forecasts.py
├── test_warnings.py
├── test_scrapers.py
└── conftest.py

alembic/             # Database migrations
└── versions/
```

## Adding New Features

### New CLI Command
```python
# app/cli/mycommand.py
import typer

app = typer.Typer()

@app.command()
def my_command(option: str = typer.Option(..., help="Description")):
    """Command description."""
    typer.echo(f"Running with {option}")

# Register in app/cli/main.py:
from app.cli import mycommand
app.add_typer(mycommand.app, name="mycommand")
```

### New Scraper
```python
# app/scrapers/my_scraper.py
from bs4 import BeautifulSoup
import requests

class MyScraper:
    def __init__(self):
        self.base_url = "https://example.com"

    def scrape(self) -> list[dict]:
        """Scrape data from source."""
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # ... scraping logic ...
        return data
```

### New API Endpoint
```python
# app/web/routes/api.py
@api_bp.route('/api/myendpoint/<param>', methods=['GET'])
def get_my_data(param: str):
    """API endpoint description."""
    try:
        data = my_service.get_data(param)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### New Database Model
```python
# app/storage/models.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class MyModel(Base):
    __tablename__ = 'my_table'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name
        }
```

Then create migration:
```bash
poetry run alembic revision --autogenerate -m "add my_table"
poetry run alembic upgrade head
```

## Testing Guidelines

### Writing Tests
```python
# tests/test_my_feature.py
import pytest
from app.services.my_service import MyService

def test_my_feature():
    """Test description."""
    service = MyService()
    result = service.process_data("test")
    assert result == expected_value

@pytest.fixture
def sample_data():
    """Fixture for test data."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture."""
    assert sample_data["key"] == "value"
```

### Mocking External APIs
```python
from unittest.mock import patch, MagicMock

@patch('requests.get')
def test_scraper(mock_get):
    """Test with mocked HTTP request."""
    mock_response = MagicMock()
    mock_response.text = "<html>Test</html>"
    mock_get.return_value = mock_response

    scraper = MyScraper()
    result = scraper.scrape()

    assert len(result) > 0
```

## Debugging

### Local Development
```bash
# Enable debug mode
echo "DEBUG=True" >> .env
echo "DB_ECHO=True" >> .env  # Log SQL queries

# Run with debugger
poetry run python -m pdb -m app.main scrape

# Or use breakpoint()
# Add to code: breakpoint()
poetry run senamhi scrape
```

### Docker Debugging
```bash
# View logs
make logs

# Enter container
make shell

# Check database
make db-shell

# Run command in container
docker compose -f docker-compose.postgres.yml exec senamhi-tracker \
  python -m app.main status
```

## Contributing

### Commit Convention
```
feat: Add new feature
fix: Bug fix
docs: Documentation changes
test: Add tests
refactor: Code refactoring
chore: Maintenance tasks
perf: Performance improvements
```

### Pull Request Process

1. Fork repository
2. Create feature branch: `git checkout -b feat/feature-name`
3. Make changes
4. Run tests: `poetry run pytest -v`
5. Format code: `make check`
6. Commit changes
7. Push to fork
8. Open Pull Request

### Code Review Checklist

- [ ] Tests pass (`poetry run pytest -v`)
- [ ] Code formatted (`make check`)
- [ ] No new warnings from Ruff
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No breaking changes (or documented)

## Useful Commands
```bash
# Database
poetry run senamhi status              # Show stats
poetry run senamhi list                # List locations
poetry run senamhi runs                # Scrape history

# Development
poetry run senamhi web                 # Start web server
poetry run senamhi daemon start        # Start scheduler
tail -f logs/scheduler.log             # View logs

# Docker
make shell                             # Enter container
make db-shell                          # PostgreSQL shell
make rebuild                           # Rebuild containers
```

## Resources

- [Project README](../README.md)
- [Setup Guide](SETUP.md)
- [API Reference](API.md)
- [Troubleshooting](archive/troubleshooting.md)
