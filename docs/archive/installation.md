# 🔧 Installation Guide

Quick installation guide for SENAMHI Tracker.

## Prerequisites

- **Python 3.12+**
- **Poetry** (dependency management)
- **PostgreSQL 16+ with PostGIS 3.4+** (for geospatial features)
- **Docker & Docker Compose** (optional, for containerized deployment)

## Local Installation

### 1. Clone and Install
```bash
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker

# Install Poetry if needed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

### 2. Setup Database

#### SQLite (Quick Start)
```bash
# Create database
poetry run alembic upgrade head

# Database created at data/weather.db
```

#### PostgreSQL + PostGIS (Recommended)

**macOS:**
```bash
brew install postgresql@16 postgis
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-16 postgresql-16-postgis-3
sudo systemctl start postgresql
```

**Setup database:**
```bash
psql -U postgres << EOF
CREATE DATABASE senamhi;
CREATE USER senamhi_user WITH PASSWORD 'senamhi_pass';
GRANT ALL PRIVILEGES ON DATABASE senamhi TO senamhi_user;
\c senamhi
CREATE EXTENSION postgis;
EOF

# Configure
echo "DATABASE_URL=postgresql://senamhi_user:senamhi_pass@localhost:5432/senamhi" >> .env

# Run migrations
poetry run alembic upgrade head
```

### 3. Configure
```bash
cp .env.example .env
nano .env  # Edit as needed
```

### 4. Verify
```bash
# Test database
poetry run senamhi status

# Test scraper
poetry run senamhi scrape --departments LIMA

# Start web interface
poetry run senamhi web
# Visit http://localhost:5001
```

## Docker Installation (PostgreSQL)
```bash
# Setup
git clone https://github.com/rosepb28/senamhi-tracker.git
cd senamhi-tracker
cp .env.example .env.docker

# Start services
make up
# Or: docker compose -f docker-compose.postgres.yml up -d

# View logs
make logs

# Stop
make down
```

**Services:**
- PostgreSQL 16 with PostGIS 3.4
- SENAMHI Tracker scheduler
- Port 5433 (external) → 5432 (internal)

**Common commands:**
```bash
make scrape-warnings    # Scrape warnings
make db-shell           # PostgreSQL shell
make rebuild            # Rebuild containers
make clean              # Remove all data
```

## Post-Installation

### Initial Scrape
```bash
# Local
poetry run senamhi scrape --all

# Docker
make scrape
```

### Geospatial Setup (PostGIS only)
```bash
# Get active warnings
poetry run senamhi warnings active

# Download and sync geometries
poetry run senamhi geo download 418
poetry run senamhi geo sync 418
```

## Upgrading

**Local:**
```bash
git pull origin main
poetry install
poetry run alembic upgrade head
```

**Docker:**
```bash
git pull origin main
make rebuild
```

## Troubleshooting

**Poetry not found:**
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Port 5001 in use:**
```bash
# Change in .env
WEB_PORT=5002
```

**Docker build fails:**
```bash
make clean
make rebuild
```

**PostgreSQL connection fails:**
```bash
# Test connection
psql -U senamhi_user -d senamhi

# Check port
lsof -i :5433
```

## Next Steps

- [Makefile Commands](../README.md#makefile-commands)
- [CLI Usage](usage/cli.md)
- [Scheduler Setup](usage/scheduler.md)
- [Geospatial Features](features/geospatial.md)
