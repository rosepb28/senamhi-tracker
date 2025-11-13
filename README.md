# 🌤️ SENAMHI Tracker

Web scraper and monitor for Peru's national weather service (SENAMHI) with historical tracking and automatic scheduling.

## Features

- 🌍 **Multi-department scraping** - Scrape forecasts from all 24 Peruvian departments
- 📊 **Historical tracking** - Track how forecasts change over time
- ⏰ **Automatic scheduling** - Run periodic scraping with configurable intervals
- 💾 **SQLite database** - Store and query forecast history
- 🖥️ **CLI interface** - Rich terminal interface with tables and colors
- 🐳 **Docker support** - Easy deployment with Docker Compose
- 📝 **Comprehensive logging** - Track all scraping operations

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry (for local development)
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
docker-compose up -d

# View logs
docker-compose logs -f
```

## Usage

### CLI Commands

#### Scraping
```bash
# Scrape Lima (default)
poetry run senamhi scrape

# Scrape specific departments
poetry run senamhi scrape --departments "LIMA,CUSCO,AREQUIPA"

# Scrape all departments
poetry run senamhi scrape --all

# Force rescrape (replace existing data)
poetry run senamhi scrape --force
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

# View scrape run history
poetry run senamhi runs

# View only successful runs
poetry run senamhi runs --status success

# View last 10 runs
poetry run senamhi runs --limit 10
```

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
SCRAPE_INTERVAL_HOURS=12.0       # Hours between scrapes
SCHEDULER_START_IMMEDIATELY=True # Run immediately on start

# Advanced
MAX_RETRIES=3                    # Retry attempts on failure
RETRY_DELAY_SECONDS=60           # Delay between retries
SCRAPE_DELAY=2.0                 # Seconds between locations
```

See `.env.example` for all available options.

## Project Structure
```
senamhi-tracker/
├── app/
│   ├── cli/              # CLI commands
│   ├── models/           # Pydantic models
│   ├── scrapers/         # Web scraping logic
│   ├── scheduler/        # Scheduling system
│   └── storage/          # Database models & CRUD
├── alembic/              # Database migrations
├── data/                 # SQLite database
├── logs/                 # Application logs
├── tests/                # Test suite
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Development

### Running Tests
```bash
poetry run pytest -v
```

### Code Quality
```bash
# Format code
poetry run ruff format .

# Lint code
poetry run ruff check .

# Run pre-commit hooks
poetry run pre-commit run --all-files
```

### Database Migrations
```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1
```

## Examples

## Examples

### Monitor Lima weather automatically
```bash
# Configure
cat > .env << 'EOF'
ENABLE_SCHEDULER=True
SCRAPE_INTERVAL_HOURS=12.0
DEPARTMENTS=LIMA
EOF

# Start
poetry run senamhi daemon start
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

- Data source: [SENAMHI Peru](https://www.senamhi.gob.pe)
- Built with Python, SQLAlchemy, Typer, and Rich

## Disclaimer

This project is for educational purposes. Please respect SENAMHI's terms of service and rate limits when scraping.
