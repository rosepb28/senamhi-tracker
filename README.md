# 🌤️ SENAMHI Tracker

Web scraper and monitor for Peru's national weather service (SENAMHI) with historical tracking and automatic scheduling.

## Features

- 🌍 **Multi-department scraping** - Scrape forecasts from all 24 Peruvian departments
- 🚨 **Weather warnings** - Track active meteorological alerts by department (EMITIDO/VIGENTE)
- 🌐 **Web Dashboard** - Flask-based UI to visualize forecasts and warnings
- 📊 **Multi-model comparison** - Compare SENAMHI with Open Meteo models (GFS & ECMWF)
- 📈 **Interactive charts** - Visualize temperature and precipitation with Chart.js
- 💾 **SQLite database** - Store and query forecast and warning history
- ⏰ **Automatic scheduling** - Run periodic scraping with configurable intervals
- 🖥️ **CLI interface** - Rich terminal interface with tables and colors
- 🐳 **Docker support** - Easy deployment with Docker Compose
- 📝 **Comprehensive logging** - Track all scraping operations

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry for dependency management
- SQLite (included with Python)
- Docker & Docker Compose (for containerized deployment)

### Installation (Local)
```bash
# Clone repository
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker

# Install dependencies
poetry install

# Setup database
poetry run alembic upgrade head

# Configure (optional)
cp .env.example .env
# Edit .env with your preferences
```

### Installation (Docker)
```bash
# Clone repository
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker

# Start services
docker compose up -d

# View logs
docker compose logs -f
```

## Usage

### CLI Commands

#### Scraping
```bash
# Scrape both forecasts and warnings (default)
poetry run senamhi scrape

# Scrape only forecasts
poetry run senamhi scrape forecasts

# Scrape only warnings
poetry run senamhi scrape warnings

# Scrape specific departments
poetry run senamhi scrape forecasts --departments "LIMA,CUSCO"

# Scrape all departments
poetry run senamhi scrape forecasts --all

# Force rescrape (replace existing data)
poetry run senamhi scrape forecasts --force
```

#### Viewing Warnings
```bash
# List last 10 warnings (all)
poetry run senamhi warnings list

# List last 20 warnings
poetry run senamhi warnings list --limit 20

# List only active warnings (EMITIDO + VIGENTE)
poetry run senamhi warnings active

# Show specific warning details
poetry run senamhi warnings show 409
```

#### Viewing Data
```bash
# List all locations
poetry run senamhi list

# Filter by department
poetry run senamhi list --department LIMA

# Show forecast for location
poetry run senamhi show CANTA

# View forecast history
poetry run senamhi history CANTA 2025-11-13

# Database status
poetry run senamhi status
```

#### Scheduler
```bash
# Start scheduler daemon (foreground)
poetry run senamhi daemon start

# Check scheduler status
poetry run senamhi daemon status

# View scrape run history
poetry run senamhi runs

# View only successful runs
poetry run senamhi runs --status success

# View last 10 runs
poetry run senamhi runs --limit 10
```

#### Web Dashboard

Start the web server:
```bash
poetry run senamhi web
```

Then visit:
- **Homepage**: http://localhost:5000
- **Department view**: http://localhost:5000/department/LIMA
- **Interactive charts**: Click "📊 View Chart" on any location

The dashboard provides:
- Real-time SENAMHI forecasts by location
- Active weather warnings by department
- Interactive model comparison (SENAMHI vs GFS vs ECMWF)
- Configurable forecast periods (3, 5, or 7 days)

#### Utilities
```bash
# List available departments
poetry run senamhi departments
```

### Docker Usage
```bash
# Start scheduler (background)
docker compose up -d

# View logs
docker compose logs -f senamhi-tracker

# Stop scheduler
docker compose stop

# Manual scrape (one-time)
docker compose run --rm senamhi-scraper

# Scrape all departments (one-time)
docker compose --profile manual up senamhi-scraper
```

## Configuration

Configuration is done via environment variables in `.env` file:
```bash
# Scraping Configuration
SCRAPE_ALL_DEPARTMENTS=False    # True to scrape all departments
DEPARTMENTS=LIMA                 # Comma-separated list if not scraping all

# Scheduler Configuration
ENABLE_SCHEDULER=False           # Enable automatic scheduling
FORECAST_SCRAPE_INTERVAL=24      # Hours between forecast scrapes
WARNING_SCRAPE_INTERVAL=6        # Hours between warning scrapes
SCHEDULER_START_IMMEDIATELY=True # Run immediately on start


# Advanced
MAX_RETRIES=3                    # Retry attempts on failure
RETRY_DELAY_SECONDS=60           # Delay between retries
SCRAPE_DELAY=2.0                 # Seconds between locations
```

See `.env.example` for all available options.

### Location Coordinates

Edit `config/coordinates.yaml` to add or update location coordinates for Open Meteo integration:
```yaml
LIMA:
  LIMA ESTE: [-12.0464, -77.0428]
  CANTA: [-11.4744, -76.6256]
```

Then populate the database:
```bash
poetry run python scripts/populate_coordinates.py --skip-existing
```

### Open Meteo Models

Edit `config/openmeteo.yaml` to configure weather models and variables:
```yaml
models:
  - id: gfs_seamless
    name: GFS
    colors:
      temp: rgb(255, 99, 132)
      precip: rgba(255, 99, 132, 0.7)
```

## Project Structure
```
senamhi-tracker/
├── app/
│   ├── cli/              # CLI commands (Typer)
│   ├── logging.py        # Centralized logging configuration
│   ├── scrapers/         # SENAMHI scraping logic
│   ├── services/         # Business logic layer (WeatherService, OpenMeteo)
│   ├── storage/          # Database models and CRUD operations
│   ├── scheduler/        # Background jobs and scheduling
│   └── web/              # Flask web application
├── config/
│   ├── settings.py       # Centralized configuration (Pydantic)
│   ├── coordinates.yaml  # Location coordinates for Open Meteo
│   └── openmeteo.yaml    # Weather model configuration
├── scripts/              # Production scripts
│   ├── populate_coordinates.py  # Update location coordinates
│   └── cleanup_old_warnings.py  # Remove expired warnings
├── dev_tools/            # Development utilities
│   ├── new_migration.sh  # Create database migrations
│   └── reset_db.sh       # Reset database (destructive)
├── tests/                # Test suite with fixtures
├── logs/                 # Application logs
└── data/                 # SQLite database
```

## Development

### Running Tests
```bash
poetry run pytest -v
```

### Code Quality
```bash
# Fix + format
poetry run ruff check . --fix && poetry run ruff format .

# Run pre-commit hooks
poetry run pre-commit run --all-files
```

### Database Migrations
```bash
# Create new migration
./dev_tools/new_migration.sh "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Reset database (⚠️ deletes all data - development only)
./dev_tools/reset_db.sh
```

### Maintenance Scripts
```bash
# Populate location coordinates (after adding new locations)
poetry run python scripts/populate_coordinates.py --skip-existing

# Remove expired warnings (production maintenance)
poetry run python scripts/cleanup_old_warnings.py

# Preview what would be deleted (dry run)
poetry run python scripts/cleanup_old_warnings.py --dry-run
```

## Examples

### Monitor Lima weather and warnings automatically
```bash
# Configure
cat > .env << 'EOF'
ENABLE_SCHEDULER=True
FORECAST_SCRAPE_INTERVAL=24
WARNING_SCRAPE_INTERVAL=6
DEPARTMENTS=LIMA
EOF

# Start
poetry run senamhi daemon start
```

### Track active weather warnings
```bash
# Scrape current warnings
poetry run senamhi scrape warnings

# View active warnings
poetry run senamhi warnings active

# View specific warning
poetry run senamhi warnings show 409

# List all warnings (including expired)
poetry run senamhi warnings list --limit 20
```

### Track forecast changes
```bash
# Day 1: Scrape
poetry run senamhi scrape

# Day 2: Scrape again
poetry run senamhi scrape --force

# View changes
poetry run senamhi history CANTA 2025-11-13
```

### Build national database
```bash
# Scrape all departments
poetry run senamhi scrape --all

# View statistics
poetry run senamhi status

# Query by department
poetry run senamhi list --department CUSCO
```

## Troubleshooting

### Database locked error
If running multiple instances, ensure only one process accesses the database at a time.

### Missing data
Check logs: `tail -f logs/scheduler.log`

### Docker issues
```bash
# Rebuild containers
docker compose build --no-cache

# Reset volumes
docker compose down -v
```

## API Rate Limits

⚠️ **Important**: Be mindful of rate limits when scraping:

- **SENAMHI**: No official limit, but avoid excessive requests
- **Open Meteo**: Free tier allows reasonable usage
- Use the scheduler's configurable intervals to avoid abuse
- Manual scraping should be done sparingly

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Data provided by [SENAMHI](https://www.senamhi.gob.pe/)
- Weather models from [Open Meteo](https://open-meteo.com/)
- Built with Python, Flask, SQLAlchemy, and Chart.js

## Disclaimer

This project is for educational purposes. Please respect SENAMHI's terms of service and rate limits when scraping.
