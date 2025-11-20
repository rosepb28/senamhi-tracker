# 🔧 Installation Guide

Complete installation instructions for SENAMHI Tracker.

## Prerequisites

### Required
- **Python 3.12+**
- **Poetry** (dependency management)
- **SQLite** (included with Python) OR **PostgreSQL 16+** with **PostGIS 3.4+**

### Optional
- **Docker & Docker Compose** (for containerized deployment)
- **Git** (for cloning repository)

## Local Installation

### 1. Clone Repository
```bash
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker
```

### 2. Install Dependencies
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 3. Setup Database

#### Option A: SQLite (Default)
```bash
# Create database tables
poetry run alembic upgrade head
```

Database will be created at `data/weather.db`.

#### Option B: PostgreSQL + PostGIS

**Install PostgreSQL and PostGIS:**

**macOS (Homebrew):**
```bash
brew install postgresql@16 postgis
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-16 postgresql-16-postgis-3
sudo systemctl start postgresql
```

**Create database and enable PostGIS:**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE senamhi;
CREATE USER senamhi_user WITH PASSWORD 'senamhi_pass';
GRANT ALL PRIVILEGES ON DATABASE senamhi TO senamhi_user;

# Connect to database
\c senamhi

# Enable PostGIS
CREATE EXTENSION postgis;

# Verify
SELECT PostGIS_version();
\q
```

**Configure connection:**
```bash
# Edit .env
DATABASE_URL=postgresql://senamhi_user:senamhi_pass@localhost:5432/senamhi
```

**Run migrations:**
```bash
poetry run alembic upgrade head
```

### 4. Configure Environment
```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env  # or your preferred editor
```

See [Configuration Guide](configuration.md) for all options.

### 5. Verify Installation
```bash
# Check database status
poetry run senamhi status

# Test scraper
poetry run senamhi scrape forecasts --departments LIMA

# Start web server
poetry run senamhi web
```

Visit http://localhost:5001

## Docker Installation

### 1. Prepare Environment
```bash
# Clone repository
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker

# Create Docker environment file
cp .env.example .env.docker

# Edit configuration
nano .env.docker
```

### 2A. SQLite Deployment (Simplest)

**Start scheduler:**
```bash
docker compose up -d
```

**View logs:**
```bash
docker compose logs -f senamhi-tracker
```

**Manual scrape:**
```bash
docker compose --profile manual up senamhi-scraper
```

**Stop:**
```bash
docker compose down
```

### 2B. PostgreSQL + PostGIS Deployment (Full Features)

**Start services:**
```bash
docker compose -f docker-compose.postgres.yml up -d
```

This starts:
- PostgreSQL 16 with PostGIS 3.4
- SENAMHI Tracker scheduler

**View logs:**
```bash
# Scheduler logs
docker compose -f docker-compose.postgres.yml logs -f senamhi-tracker

# PostgreSQL logs
docker compose -f docker-compose.postgres.yml logs -f postgres
```

**Access PostgreSQL:**
```bash
docker exec -it senamhi-postgres psql -U senamhi_user -d senamhi
```

**Manual scrape:**
```bash
docker compose -f docker-compose.postgres.yml --profile manual up senamhi-scraper
```

**Stop (keep data):**
```bash
docker compose -f docker-compose.postgres.yml down
```

**Stop and remove data (⚠️ destructive):**
```bash
docker compose -f docker-compose.postgres.yml down -v
```

## Post-Installation

### Populate Location Coordinates

For Open-Meteo integration:
```bash
poetry run python scripts/populate_coordinates.py --skip-existing
```

### Initial Data Scrape
```bash
# Scrape all departments
poetry run senamhi scrape --all

# Scrape only Lima
poetry run senamhi scrape --departments LIMA
```

### Download Shapefiles (PostGIS only)
```bash
# Get active warnings
poetry run senamhi warnings active

# Download shapefiles for each warning
poetry run senamhi geo download 418
poetry run senamhi geo sync 418
```

## Upgrading

### Local Upgrade
```bash
# Pull latest changes
git pull origin main

# Update dependencies
poetry install

# Run new migrations
poetry run alembic upgrade head

# Restart services
poetry run senamhi daemon stop
poetry run senamhi daemon start
```

### Docker Upgrade
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build

# For PostgreSQL
docker compose -f docker-compose.postgres.yml down
docker compose -f docker-compose.postgres.yml up -d --build
```

## Uninstallation

### Local
```bash
# Stop scheduler if running
poetry run senamhi daemon stop

# Remove virtual environment
poetry env remove python3.12

# Remove data (optional)
rm -rf data/
rm -rf logs/
```

### Docker
```bash
# Stop and remove containers
docker compose down -v

# For PostgreSQL
docker compose -f docker-compose.postgres.yml down -v

# Remove images
docker rmi senamhi-tracker:latest
docker rmi postgis/postgis:16-3.4
```

## Troubleshooting

### Poetry not found
```bash
# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall
curl -sSL https://install.python-poetry.org | python3 -
```

### Database connection failed

**SQLite:**
- Check `data/` directory exists and is writable
- Verify `DATABASE_URL` in `.env`

**PostgreSQL:**
- Verify PostgreSQL is running: `pg_isalive`
- Check connection string in `.env`
- Test connection: `psql -U senamhi_user -d senamhi`

### Port conflicts

**Port 5001 already in use:**
```bash
# Change web port in .env
WEB_PORT=5002
```

**PostgreSQL port 5433 in use:**
```bash
# Change in docker-compose.postgres.yml
ports:
  - "5434:5432"  # Use different external port
```

### Docker build fails
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker compose build --no-cache
```

## Next Steps

- [Configure the application](configuration.md)
- [Learn CLI commands](usage/cli.md)
- [Set up the scheduler](usage/scheduler.md)
- [Enable geospatial features](features/geospatial.md)
