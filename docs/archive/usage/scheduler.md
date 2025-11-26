# ⏰ Scheduler Configuration Guide

Complete guide to configuring and using the automatic scheduler.

## Overview

The scheduler runs periodic scraping jobs for forecasts, warnings, and shapefile downloads. It uses the `schedule` library and runs as a foreground process.

## Quick Start
```bash
# Configure
cat > .env << 'EOF'
ENABLE_SCHEDULER=True
SCHEDULER_START_IMMEDIATELY=True
FORECAST_SCRAPE_INTERVAL=24
WARNING_SCRAPE_INTERVAL=6
SCRAPE_ALL_DEPARTMENTS=True
EOF

# Start
poetry run senamhi daemon start
```

## Configuration

### Environment Variables
```bash
# Enable/disable scheduler
ENABLE_SCHEDULER=True

# Run jobs immediately on startup
SCHEDULER_START_IMMEDIATELY=True

# Job intervals (hours)
FORECAST_SCRAPE_INTERVAL=24    # Forecasts every 24 hours
WARNING_SCRAPE_INTERVAL=6      # Warnings every 6 hours (also triggers shapefile downloads)

# Departments to scrape
SCRAPE_ALL_DEPARTMENTS=True
# DEPARTMENTS=LIMA,CUSCO  # Or specific departments

# Retry configuration
MAX_RETRIES=3
RETRY_DELAY_SECONDS=60

# Logging
LOG_FILE=logs/scheduler.log
```

### Recommended Intervals

**Forecasts:**
- **Daily (24 hours)**: Standard - SENAMHI updates once daily
- **Twice daily (12 hours)**: For critical monitoring
- **Minimum**: 6 hours (avoid excessive scraping)

**Warnings:**
- **Every 6 hours**: Recommended - captures new warnings quickly
- **Every 3 hours**: For critical situations
- **Every 12 hours**: Minimum for active monitoring

**Shapefiles:**
- Automatic with warning scrapes
- Downloads only for new active warnings
- Skips warnings that already have geometries

## Scheduled Jobs

The scheduler runs three types of jobs:

### 1. Forecast Scrape Job

**Frequency:** `FORECAST_SCRAPE_INTERVAL` hours

**What it does:**
1. Discovers all departments (or uses configured list)
2. Scrapes forecast data for each department
3. Saves to database
4. Updates scrape run records
5. Handles errors with retries

**Behavior:**
- **Skips** if data already exists for today (unless `force=True`)
- **Retries** up to `MAX_RETRIES` times on failure
- **Logs** all operations to `LOG_FILE`

**Example log:**
```
2025-11-19 06:00:00 | INFO | Starting scheduled forecast scrape job
2025-11-19 06:00:00 | INFO | Scraping ALL departments
2025-11-19 06:00:02 | INFO | Scrape attempt 1/3
2025-11-19 06:04:30 | INFO | Successfully scraped 145 locations, saved 1015 forecasts
2025-11-19 06:04:30 | INFO | Forecast scrape job completed successfully
```

### 2. Warning Scrape Job

**Frequency:** `WARNING_SCRAPE_INTERVAL` hours

**What it does:**
1. Updates expired warnings to 'vencido' status
2. Scrapes current warnings from all departments
3. Saves new warnings or updates existing ones
4. Records statistics

**Behavior:**
- **Always scrapes all departments** (no filtering)
- **Updates status** of expired warnings automatically
- **Tracks duplicates** across departments

**Example log:**
```
2025-11-19 06:00:00 | INFO | Starting scheduled warnings scrape job
2025-11-19 06:00:00 | INFO | Updated 5 expired warning(s) to 'vencido'
2025-11-19 06:00:05 | INFO | Warnings scrape completed: 38 found, 3 saved, 2 updated
```

### 3. Shapefile Download Job (PostGIS only)

**Frequency:** `WARNING_SCRAPE_INTERVAL` hours (same as warnings)

**What it does:**
1. Finds all active warnings (vigente/emitido)
2. Groups by warning_number (avoid duplicates)
3. Checks if geometries already exist
4. Downloads missing shapefiles from GeoServer
5. Parses and syncs geometries to database

**Behavior:**
- **Only runs** with PostGIS enabled
- **Skips** warnings that already have geometries
- **Downloads** one ZIP per warning day
- **Parses** polygons and saves to `warning_geometries` table

**Example log:**
```
2025-11-19 06:00:10 | INFO | Starting scheduled shapefile download job
2025-11-19 06:00:10 | INFO | Found 3 unique active warning(s)
2025-11-19 06:00:10 | DEBUG | Warning #418 already has geometries, skipping
2025-11-19 06:00:10 | INFO | Processing warning #417
2025-11-19 06:00:12 | DEBUG |   Day 1: Downloaded
2025-11-19 06:00:14 | DEBUG |   Day 2: Downloaded
2025-11-19 06:00:16 | INFO |   Synced 6 geometry record(s)
2025-11-19 06:00:16 | INFO | Shapefile download job completed: 2 downloaded, 1 synced, 1 skipped
```

## Running the Scheduler

### Foreground Mode (Development)
```bash
poetry run senamhi daemon start
```

**Output:**
```
============================================================
SENAMHI Tracker Scheduler Started
============================================================
Forecast interval: Every 24 hours
Warnings interval: Every 6 hours
Start immediately: True
Forecast mode: Scraping ALL departments
Logs: logs/scheduler.log
Press Ctrl+C to stop
============================================================
Running initial scrapes...
[... job outputs ...]

Scheduled jobs:
  - run_forecast_scrape_job: next run at 2025-11-20 06:00:00
  - run_warnings_scrape_job: next run at 2025-11-19 12:00:00
  - run_shapefile_download_job: next run at 2025-11-19 12:00:00
```

**Features:**
- **Ctrl+C** for graceful shutdown
- **Real-time logs** to console
- **Immediate execution** if configured
- **Next run times** displayed

## Monitoring

### View Logs
```bash
# Follow logs in real-time
tail -f logs/scheduler.log

# View last 100 lines
tail -n 100 logs/scheduler.log

# Search for errors
grep ERROR logs/scheduler.log

# Search for specific date
grep "2025-11-19" logs/scheduler.log
```

### Check Scrape History
```bash
# View last 10 runs
poetry run senamhi runs

# View last 20 runs
poetry run senamhi runs --limit 20

# View only failures
poetry run senamhi runs --status failed

# View successes
poetry run senamhi runs --status success
```

### Database Status
```bash
# Check database stats
poetry run senamhi status

# Check active warnings
poetry run senamhi warnings active

# Check recent forecasts
poetry run senamhi list
```

## Error Handling

### Retry Mechanism

The scheduler automatically retries failed scrapes:

1. **First attempt** - immediate execution
2. **Wait** `RETRY_DELAY_SECONDS` (default: 60s)
3. **Second attempt**
4. **Wait** again
5. **Third attempt** (if `MAX_RETRIES=3`)
6. **Give up** and log error

**Example:**
```
2025-11-19 06:00:00 | INFO | Scrape attempt 1/3
2025-11-19 06:00:05 | ERROR | Scrape attempt 1 failed: Connection timeout
2025-11-19 06:00:05 | INFO | Retrying in 60 seconds...
2025-11-19 06:01:05 | INFO | Scrape attempt 2/3
2025-11-19 06:01:45 | INFO | Successfully scraped 145 locations
```

### Common Errors

#### Network timeout
```
ERROR | Scrape attempt 1 failed: Connection timeout
```

**Fix:**
- Increase `REQUEST_TIMEOUT` in `.env`
- Check internet connection
- Verify SENAMHI website is accessible

#### Database locked
```
ERROR | Database is locked
```

**Fix:**
- Stop other processes accessing database
- Use PostgreSQL instead of SQLite for concurrent access

#### Data already exists
```
INFO | Data already exists for issue date 2025-11-18, skipping
```

**Not an error** - scheduler intelligently skips duplicate data

#### GeoServer unavailable
```
WARNING | Day 1: Download failed
```

**Fix:**
- Check SENAMHI GeoServer status
- Retry manually: `poetry run senamhi geo download 418`

## Performance Tuning

### Optimize Intervals
```bash
# Conservative (respects SENAMHI resources)
FORECAST_SCRAPE_INTERVAL=24
WARNING_SCRAPE_INTERVAL=12

# Balanced (good for monitoring)
FORECAST_SCRAPE_INTERVAL=24
WARNING_SCRAPE_INTERVAL=6

# Aggressive (only for critical situations)
FORECAST_SCRAPE_INTERVAL=12
WARNING_SCRAPE_INTERVAL=3
```

### Reduce Load
```bash
# Scrape specific departments only
SCRAPE_ALL_DEPARTMENTS=False
DEPARTMENTS=LIMA,AREQUIPA

# Increase delays
SCRAPE_DELAY=3.0  # Wait 3 seconds between locations

# Reduce retries
MAX_RETRIES=2
```

## Troubleshooting

### Scheduler not starting

**Check configuration:**
```bash
grep ENABLE_SCHEDULER .env
```

**Should be:**
```bash
ENABLE_SCHEDULER=True
```

### Jobs not running

**Check intervals:**
```bash
grep INTERVAL .env
```

**View next run times:**
```bash
poetry run senamhi daemon start
# Look for "Scheduled jobs:" section
```

### Shapefiles not downloading

**Check PostGIS:**
```bash
poetry run python -c "from config.settings import settings; print(f'PostGIS: {settings.supports_postgis}')"
```

**Check active warnings:**
```bash
poetry run senamhi warnings active
```

**Manual download:**
```bash
poetry run senamhi geo download 418
```

### High memory usage

**Check database size:**
```bash
du -h data/weather.db
```

**Clean old data:**
```bash
poetry run python scripts/cleanup_old_warnings.py
```

**Reduce concurrent jobs:**
- Don't run manual scrapes while scheduler is active
- Use PostgreSQL instead of SQLite

## Best Practices

### Development
- Use short intervals for testing (e.g., 1 hour)
- Enable `SCHEDULER_START_IMMEDIATELY=True`
- Monitor logs actively: `tail -f logs/scheduler.log`
- Use SQLite for simplicity

### Production
- Use recommended intervals (24h forecasts, 6h warnings)
- Disable debug mode: `DEBUG=False`
- Use PostgreSQL for reliability
- Set up monitoring alerts
- Use systemd or supervisor for process management
- Rotate logs regularly

### Monitoring
- Check logs daily
- Review scrape history weekly
- Monitor database size monthly
- Set up alerts for failed runs

## Next Steps

- [CLI Usage](cli.md) - Manual commands
- [Web Dashboard](web.md) - View data
- [Geospatial Features](../features/geospatial.md) - PostGIS setup
- [Production Deployment](../deployment/production.md) - Production best practices
