# 🐳 Docker Deployment

PostgreSQL + PostGIS container deployment guide.

## Quick Start
```bash
# Using Makefile (recommended)
make up

# Or using Docker Compose directly
make up

# View logs
make logs

# Stop services
make down
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
# PostgreSQL (use 'postgres' as host in Docker)
DATABASE_URL=postgresql://senamhi_user:senamhi_pass@postgres:5432/senamhi

# Scheduler
ENABLE_SCHEDULER=True
FORECAST_SCRAPE_INTERVAL=24
WARNING_SCRAPE_INTERVAL=6
```

## Services
```yaml
services:
  postgres:           # PostgreSQL + PostGIS
  senamhi-tracker:    # Scheduler
```

## Common Tasks

### Using Makefile (Recommended)
```bash
# Service management
make up                  # Start services
make down                # Stop services
make restart             # Restart services
make ps                  # Show status
make logs                # View logs

# Scraping
make scrape              # Scrape forecasts and warnings
make scrape-warnings     # Scrape warnings only
make scrape-force        # Force scrape

# Database
make migrate             # Run migrations
make db-shell            # Enter PostgreSQL shell

# Development
make shell               # Enter app container
make rebuild             # Rebuild containers
```

### Using Docker Compose Directly
```bash
# Start
docker compose -f docker-compose.postgres.yml up -d

# Stop
docker compose -f docker-compose.postgres.yml down

# Logs
docker compose -f docker-compose.postgres.yml logs -f senamhi-tracker

# Execute command
docker compose -f docker-compose.postgres.yml exec senamhi-tracker python -m app.main status
```

## Persistent Data

### PostgreSQL

Data stored in `postgres_data` volume
```bash
# Backup database
docker exec senamhi-postgres pg_dump -U senamhi_user senamhi > backup.sql

# Restore database
cat backup.sql | docker exec -i senamhi-postgres psql -U senamhi_user -d senamhi

# Remove volume (⚠️ deletes all data)
make clean
# Or: docker compose -f docker-compose.postgres.yml down -v
```

## Resource Limits

Configured in `docker-compose.postgres.yml`:
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
make logs
# Or: docker logs senamhi-tracker-postgres

# Rebuild
make rebuild
```

**Database connection fails:**
```bash
# Check postgres is healthy
make ps

# Check network
docker network ls

# Test connection
make db-shell
```
