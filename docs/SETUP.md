# 🔧 Setup Guide

Quick setup guide with Makefile commands.

## Prerequisites

- **Python 3.12+**
- **Poetry**
- **PostgreSQL 16+ with PostGIS 3.4+** (for maps)
- **Docker & Docker Compose** (optional)

## Installation

### Local Development (SQLite)
```bash
# Clone and install
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker
poetry install

# Setup database
poetry run alembic upgrade head

# Configure
cp .env.example .env

# Test
poetry run senamhi status
poetry run senamhi scrape --departments LIMA
poetry run senamhi web  # http://localhost:5001
```

### Docker (PostgreSQL + PostGIS)
```bash
# Setup
cp .env.example .env.docker
nano .env.docker  # Edit if needed

# Start services
make up

# View logs
make logs

# Test
make scrape-warnings
```

### Local with PostgreSQL
```bash
# Install PostgreSQL + PostGIS
# macOS:
brew install postgresql@16 postgis
brew services start postgresql@16

# Ubuntu/Debian:
sudo apt-get install postgresql-16 postgresql-16-postgis-3

# Create database
psql -U postgres << EOF
CREATE DATABASE senamhi;
CREATE USER senamhi_user WITH PASSWORD 'senamhi_pass';
GRANT ALL PRIVILEGES ON DATABASE senamhi TO senamhi_user;
\c senamhi
CREATE EXTENSION postgis;
EOF

# Configure
echo "DATABASE_URL=postgresql://senamhi_user:senamhi_pass@localhost:5432/senamhi" >> .env

# Migrate
poetry run alembic upgrade head
```

## Makefile Commands

### Service Management
```bash
make up              # Start Docker services
make down            # Stop services
make restart         # Restart services
make ps              # Show service status
make logs            # View app logs
make logs-all        # View all logs
```

### Scraping
```bash
make scrape              # Scrape forecasts and warnings
make scrape-warnings     # Scrape warnings only
make scrape-forecasts    # Scrape forecasts only
make scrape-force        # Force scrape (replace existing)
```

### Database
```bash
make migrate             # Run migrations
make migrate-status      # Show migration status
make db-shell            # Enter PostgreSQL shell
make db-status           # Show database stats
```

### Geospatial
```bash
make geo-download warning=421    # Download shapefile
make geo-sync warning=421        # Sync to database
make geo-list                    # List downloaded files
```

### Development
```bash
make shell               # Enter app container
make build               # Build without cache
make rebuild             # Rebuild and restart
make clean               # Remove volumes (deletes data!)
make check               # Run linting and formatting
```

### CLI Commands
```bash
make list-locations      # List all locations
make list-warnings       # List warnings
make runs                # Show scrape history
```

### Help
```bash
make help                # Show all commands
```

## Configuration

### Environment Variables

**Local (`.env`):**
```bash
# Database
DATABASE_URL=sqlite:///./data/weather.db
# Or PostgreSQL:
# DATABASE_URL=postgresql://senamhi_user:senamhi_pass@localhost:5432/senamhi

# Scraping
SCRAPE_ALL_DEPARTMENTS=True
FORECAST_SCRAPE_INTERVAL=24
WARNING_SCRAPE_INTERVAL=6

# Scheduler
ENABLE_SCHEDULER=False

# Web
WEB_PORT=5001
WEB_DEBUG=True
```

**Docker (`.env.docker`):**
```bash
DATABASE_URL=postgresql://senamhi_user:senamhi_pass@postgres:5432/senamhi
ENABLE_SCHEDULER=True
SCRAPE_ALL_DEPARTMENTS=True
```

See [Configuration Guide](archive/configuration.md) for all options.

## Common Workflows

### Daily Monitoring
```bash
# Docker
make scrape-warnings
make logs

# Local
poetry run senamhi scrape warnings
poetry run senamhi warnings active
poetry run senamhi web
```

### Geospatial Setup
```bash
# Get active warnings
poetry run senamhi warnings active

# Download and sync
make geo-download warning=421
make geo-sync warning=421

# Or local:
poetry run senamhi geo download 421
poetry run senamhi geo sync 421

# View in browser
poetry run senamhi web  # Click "View Map"
```

### Development Workflow
```bash
# Format and lint
make check

# Run tests
poetry run pytest -v

# Start web server
poetry run senamhi web

# View logs
tail -f logs/scheduler.log
```

## Verification

### Check Installation
```bash
# Local
poetry run senamhi status
poetry run senamhi list

# Docker
make db-status
make ps
```

### Test Scraping
```bash
# Local
poetry run senamhi scrape --departments LIMA

# Docker
make scrape-warnings
```

### Access Services

- **Web Dashboard:** http://localhost:5001
- **PostgreSQL:** `localhost:5433` (Docker) or `localhost:5432` (local)
- **API:** http://localhost:5001/api/health

## Troubleshooting

**Port conflicts:**
```bash
# Change web port
WEB_PORT=5002

# Change PostgreSQL port (docker-compose.postgres.yml)
ports:
  - "5434:5432"
```

**Docker won't start:**
```bash
make logs
make rebuild
```

**Database connection fails:**
```bash
# Local
psql -U senamhi_user -d senamhi

# Docker
make db-shell
```

See [Troubleshooting Guide](archive/troubleshooting.md) for more.

## Next Steps

- [API Reference](API.md)
- [Development Guide](DEVELOPMENT.md)
- [CLI Commands](archive/usage/cli.md)
- [Web Dashboard](archive/usage/web.md)
