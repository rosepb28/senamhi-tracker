# 🐳 Docker Deployment

Container deployment guide.

## Quick Start

### SQLite (Simple)
```bash
# Start
docker compose up -d

# Logs
docker compose logs -f senamhi-tracker

# Stop
docker compose down
```

### PostgreSQL + PostGIS (Full Features)
```bash
# Start
docker compose -f docker-compose.postgres.yml up -d

# Logs
docker compose -f docker-compose.postgres.yml logs -f

# Stop
docker compose -f docker-compose.postgres.yml down
```

## Configuration
```bash
# Create Docker environment
cp .env.example .env.docker

# Edit settings
nano .env.docker
```

**Important variables:**
```bash
# SQLite
DATABASE_URL=sqlite:///./data/weather.db

# PostgreSQL (use 'postgres' as host in Docker)
DATABASE_URL=postgresql://senamhi_user:senamhi_pass@postgres:5432/senamhi

# Scheduler
ENABLE_SCHEDULER=True
FORECAST_SCRAPE_INTERVAL=24
WARNING_SCRAPE_INTERVAL=6
```

## Services

### SQLite Compose
```yaml
services:
  senamhi-tracker:    # Scheduler
  senamhi-scraper:    # Manual scrape (--profile manual)
```

### PostgreSQL Compose
```yaml
services:
  postgres:           # PostgreSQL + PostGIS
  senamhi-tracker:    # Scheduler
  senamhi-scraper:    # Manual scrape (--profile manual)
```

## Common Tasks

### Manual Scrape
```bash
# SQLite
docker compose --profile manual up senamhi-scraper

# PostgreSQL
docker compose -f docker-compose.postgres.yml --profile manual up senamhi-scraper
```

### Access Database

**PostgreSQL:**
```bash
docker exec -it senamhi-postgres psql -U senamhi_user -d senamhi
```

**SQLite:**
```bash
docker exec -it senamhi-tracker sqlite3 /app/data/weather.db
```

### View Logs
```bash
# All logs
docker compose logs

# Follow logs
docker compose logs -f senamhi-tracker

# Last 100 lines
docker compose logs --tail 100 senamhi-tracker
```

### Rebuild
```bash
# Rebuild and restart
docker compose down
docker compose up -d --build

# Clear cache
docker compose build --no-cache
```

## Persistent Data

### SQLite

Data stored in `./data/` (mounted as volume)

### PostgreSQL

Data stored in `postgres_data` volume
```bash
# Backup
docker exec senamhi-postgres pg_dump -U senamhi_user senamhi > backup.sql

# Restore
cat backup.sql | docker exec -i senamhi-postgres psql -U senamhi_user -d senamhi

# Remove volume (⚠️ deletes data)
docker compose -f docker-compose.postgres.yml down -v
```

## Resource Limits

Configured in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
```

Adjust based on your needs.

## Networking

Services communicate on `senamhi-network`:
```bash
# Inspect network
docker network inspect senamhi-tracker_senamhi-network
```

## Troubleshooting

**Port conflicts:**
```yaml
# Change external port in docker-compose.postgres.yml
ports:
  - "5434:5432"  # Use 5434 instead of 5433
```

**Container won't start:**
```bash
# Check logs
docker logs senamhi-tracker-postgres

# Rebuild
docker compose down
docker compose up -d --build
```

**Database connection fails:**
```bash
# Check postgres is healthy
docker ps

# Check network
docker network ls
```
