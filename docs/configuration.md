# ⚙️ Configuration Guide

Complete reference for configuring SENAMHI Tracker.

## Configuration Methods

SENAMHI Tracker uses environment variables for configuration, loaded from:
1. `.env` file (local development)
2. `.env.docker` file (Docker deployment)
3. System environment variables (override file values)

## Quick Setup
```bash
# Local development
cp .env.example .env
nano .env

# Docker deployment
cp .env.example .env.docker
nano .env.docker
```

## Environment Variables

### Database Configuration

#### SQLite (Default)
```bash
DATABASE_URL=sqlite:///./data/weather.db
```

#### PostgreSQL + PostGIS
```bash
DATABASE_URL=postgresql://senamhi_user:senamhi_pass@localhost:5433/senamhi
```

**Format:** `postgresql://USER:PASSWORD@HOST:PORT/DATABASE`

**Notes:**
- Use `localhost` for local PostgreSQL
- Use `postgres` for Docker internal network
- Default PostgreSQL port: 5432
- Docker external port: 5433 (mapped to avoid conflicts)

### Application Settings
```bash
# Application metadata
APP_NAME="SENAMHI Tracker"
APP_VERSION="0.1.0"

# Debug mode (disable in production)
DEBUG=True
DB_ECHO=False  # Echo SQL queries (useful for debugging)
```

### Scraping Configuration
```bash
# Which departments to scrape
SCRAPE_ALL_DEPARTMENTS=False
DEPARTMENTS=LIMA,CUSCO,AREQUIPA

# Scraping behavior
SCRAPE_DELAY=2.0          # Seconds between location requests
REQUEST_TIMEOUT=30        # HTTP request timeout (seconds)
USER_AGENT=SENAMHI-Tracker/0.1.0 (Educational Project)
```

**Department Options:**
- `SCRAPE_ALL_DEPARTMENTS=True`: Scrape all 24 departments
- `SCRAPE_ALL_DEPARTMENTS=False`: Use `DEPARTMENTS` list

**Available Departments:**
```
AMAZONAS, ANCASH, APURIMAC, AREQUIPA, AYACUCHO, CAJAMARCA,
CUSCO, HUANCAVELICA, HUANUCO, ICA, JUNIN, LA LIBERTAD,
LAMBAYEQUE, LIMA, LORETO, MADRE DE DIOS, MOQUEGUA, PASCO,
PIURA, PUNO, SAN MARTIN, TACNA, TUMBES, UCAYALI
```

### Scheduler Configuration
```bash
# Enable automatic scheduling
ENABLE_SCHEDULER=False

# Run immediately on startup
SCHEDULER_START_IMMEDIATELY=True

# Scraping intervals (hours)
FORECAST_SCRAPE_INTERVAL=24    # Forecasts every 24 hours
WARNING_SCRAPE_INTERVAL=6      # Warnings every 6 hours (also triggers shapefile downloads)

# Logging
LOG_FILE=logs/scheduler.log

# Retry configuration
MAX_RETRIES=3              # Number of retry attempts
RETRY_DELAY_SECONDS=60     # Seconds between retries
```

**Recommended Intervals:**
- **Forecasts:** 24 hours (SENAMHI updates daily)
- **Warnings:** 6 hours (warnings can be issued frequently)
- **Shapefiles:** Automatic with warnings scrape

### Web Server Configuration
```bash
WEB_HOST=127.0.0.1
WEB_PORT=5001
WEB_DEBUG=True  # Disable in production
```

**Notes:**
- Port 5001 used to avoid macOS AirPlay conflict (port 5000)
- Use `0.0.0.0` as host to allow external connections
- Disable debug mode in production

### SENAMHI URLs
```bash
SENAMHI_BASE_URL=https://www.senamhi.gob.pe
SENAMHI_FORECAST_URL=https://www.senamhi.gob.pe/?p=pronostico-meteorologico
SENAMHI_WARNINGS_API=https://www.senamhi.gob.pe/app_senamhi/sisper/api/avisoMeteoroCabEmergencia
```

**⚠️ Warning:** Only change if SENAMHI updates their URLs.

### Docker-Specific (`.env.docker` only)
```bash
# PostgreSQL container settings
POSTGRES_HOST=postgres       # Internal Docker network hostname
POSTGRES_USER=senamhi_user
POSTGRES_PASSWORD=senamhi_pass
POSTGRES_DB=senamhi
```

**Note:** These are used by Docker Compose to configure PostgreSQL container.

## Configuration Files

### `config/coordinates.yaml`

Location coordinates for Open-Meteo API integration:
```yaml
LIMA:
  LIMA ESTE: [-12.0464, -77.0428]
  CANTA: [-11.4744, -76.6256]
  # Add more locations...

CUSCO:
  CUSCO: [-13.5319, -71.9675]
  # Add more locations...
```

**Format:** `[latitude, longitude]` in decimal degrees

### `config/openmeteo.yaml`

Weather model configuration for forecast comparison:
```yaml
url: https://api.open-meteo.com/v1/forecast

models:
  - id: gfs_seamless
    name: GFS
    colors:
      temp: rgb(255, 99, 132)
      precip: rgba(255, 99, 132, 0.7)

  - id: ecmwf_ifs04
    name: ECMWF
    colors:
      temp: rgb(54, 162, 235)
      precip: rgba(54, 162, 235, 0.7)

variables:
  - api_name: temperature_2m
    display_name: Temperature
    unit: °C
    chart_color: rgb(255, 99, 132)

  - api_name: precipitation
    display_name: Precipitation
    unit: mm
    chart_color: rgb(54, 162, 235)
```

**Customization:**
- Add/remove models
- Change chart colors
- Modify displayed variables

## Example Configurations

### Development (Local, SQLite)
```bash
# .env
DATABASE_URL=sqlite:///./data/weather.db
ENABLE_SCHEDULER=False
SCRAPE_ALL_DEPARTMENTS=False
DEPARTMENTS=LIMA
DEBUG=True
WEB_PORT=5001
```

### Production (Docker, PostgreSQL)
```bash
# .env.docker
DATABASE_URL=postgresql://senamhi_user:senamhi_pass@postgres:5432/senamhi
ENABLE_SCHEDULER=True
SCHEDULER_START_IMMEDIATELY=True
SCRAPE_ALL_DEPARTMENTS=True
FORECAST_SCRAPE_INTERVAL=24
WARNING_SCRAPE_INTERVAL=6
DEBUG=False
WEB_DEBUG=False
LOG_FILE=logs/scheduler.log
```

### Testing Multiple Departments
```bash
# .env
DATABASE_URL=sqlite:///./data/weather.db
SCRAPE_ALL_DEPARTMENTS=False
DEPARTMENTS=LIMA,CUSCO,AREQUIPA,PIURA
ENABLE_SCHEDULER=True
FORECAST_SCRAPE_INTERVAL=12
WARNING_SCRAPE_INTERVAL=6
```

### Geospatial Features (PostGIS)
```bash
# .env
DATABASE_URL=postgresql://senamhi_user:senamhi_pass@localhost:5433/senamhi
ENABLE_SCHEDULER=True
WARNING_SCRAPE_INTERVAL=6  # Triggers automatic shapefile downloads
SCRAPE_ALL_DEPARTMENTS=True
```

## Validation

### Check Configuration
```bash
# View current settings
poetry run python -c "from config.settings import settings; print(settings.model_dump())"

# Test database connection
poetry run senamhi status

# Verify departments
poetry run senamhi departments
```

### Test Scraping
```bash
# Test forecast scraping
poetry run senamhi scrape forecasts --departments LIMA

# Test warning scraping
poetry run senamhi scrape warnings

# Test geospatial (PostGIS only)
poetry run senamhi geo list
```

## Security Considerations

### Production Deployment

**⚠️ Important:**

1. **Change default passwords:**
```bash
   POSTGRES_PASSWORD=your-strong-password-here
```

2. **Disable debug mode:**
```bash
   DEBUG=False
   WEB_DEBUG=False
   DB_ECHO=False
```

3. **Restrict web server:**
```bash
   WEB_HOST=127.0.0.1  # Localhost only
   # Or use reverse proxy (nginx, traefik)
```

4. **Use environment variables:**
   - Don't commit `.env` or `.env.docker`
   - Use system environment variables in production
   - Or use secrets management (Docker secrets, Kubernetes secrets)

5. **Limit database access:**
```bash
   # PostgreSQL: Restrict to localhost or specific IPs
   # Edit pg_hba.conf
```

### Rate Limiting

Be respectful of SENAMHI's infrastructure:
```bash
# Recommended minimums
FORECAST_SCRAPE_INTERVAL=24  # Don't scrape more than daily
WARNING_SCRAPE_INTERVAL=6    # Don't scrape more than every 6 hours
SCRAPE_DELAY=2.0             # Wait between requests
```

## Troubleshooting

### Configuration not loading
```bash
# Check .env file exists
ls -la .env

# Check for syntax errors
cat .env | grep -v '^#' | grep -v '^$'

# Verify environment variables
poetry run python -c "import os; print(os.getenv('DATABASE_URL'))"
```

### Database connection fails
```bash
# Test PostgreSQL connection
psql -U senamhi_user -h localhost -p 5433 -d senamhi

# Check Docker network
docker network inspect senamhi-tracker_senamhi-network
```

### Scheduler not running
```bash
# Check ENABLE_SCHEDULER
grep ENABLE_SCHEDULER .env

# View scheduler logs
tail -f logs/scheduler.log
```

## Next Steps

- [CLI Usage Guide](usage/cli.md)
- [Scheduler Configuration](usage/scheduler.md)
- [Geospatial Setup](features/geospatial.md)
- [Production Deployment](deployment/production.md)
