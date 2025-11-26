# 🖥️ CLI Usage Guide

Complete command-line interface reference for SENAMHI Tracker.

## Overview

SENAMHI Tracker provides a rich CLI built with Typer. All commands are accessed through the `senamhi` command.

```bash
poetry run senamhi --help
```

## Command Structure

```bash
senamhi [COMMAND] [SUBCOMMAND] [OPTIONS]
```

## Scraping Commands

### `senamhi scrape`

Main scraping command with subcommands for forecasts and warnings.

#### Scrape Everything (Default)

```bash
# Scrape both forecasts and warnings
poetry run senamhi scrape

# Equivalent to:
poetry run senamhi scrape forecasts
poetry run senamhi scrape warnings
```

#### Scrape Forecasts

```bash
# Scrape configured departments (from .env)
poetry run senamhi scrape forecasts

# Scrape specific departments
poetry run senamhi scrape forecasts --departments "LIMA,CUSCO"

# Scrape all 24 departments
poetry run senamhi scrape forecasts --all

# Force rescrape (replace existing data for today)
poetry run senamhi scrape forecasts --force

# Combine options
poetry run senamhi scrape forecasts --all --force
```

**Options:**

- `--departments TEXT`: Comma-separated department list
- `--all`: Scrape all departments (overrides --departments)
- `--force`: Replace existing data for today

**Examples:**

```bash
# Scrape Lima only
poetry run senamhi scrape forecasts --departments LIMA

# Scrape multiple departments
poetry run senamhi scrape forecasts --departments "LIMA,AREQUIPA,CUSCO"

# Scrape everything, force update
poetry run senamhi scrape forecasts --all --force
```

#### Scrape Warnings

```bash
# Scrape warnings for all departments
poetry run senamhi scrape warnings

# Force update (replace existing warnings)
poetry run senamhi scrape warnings --force
```

**Options:**

- `--force`: Replace existing warnings for today

**Notes:**

- Warnings are always scraped for all departments
- Updates status of expired warnings automatically
- With PostGIS: triggers automatic shapefile downloads

## Viewing Data

### `senamhi list`

List all locations in the database.

```bash
# List all locations
poetry run senamhi list

# Filter by department
poetry run senamhi list --department LIMA

# List with forecast count
poetry run senamhi list
```

**Options:**

- `--department TEXT`: Filter by department name

**Output:**

```bash
┌────────────┬──────────────────┬───────────┐
│ Department │ Location         │ Forecasts │
├────────────┼──────────────────┼───────────┤
│ LIMA       │ LIMA ESTE        │ 45        │
│ LIMA       │ CANTA            │ 42        │
│ LIMA       │ CHILCA           │ 40        │
└────────────┴──────────────────┴───────────┘
```

### `senamhi show`

Show forecast details for a specific location.

```bash
# Show forecast for location
poetry run senamhi show "LIMA ESTE"

# Show forecast for location in specific department
poetry run senamhi show CANTA --department LIMA
```

**Options:**

- `--department TEXT`: Department name (helps with duplicate location names)

**Output:**

```bash
Forecast for LIMA ESTE (LIMA)
Issued: 2025-11-18 06:00:00

Day 1 (2025-11-19):
  Condition: Parcialmente nublado
  Temp: 18°C - 24°C
  Precipitation: 0.0 mm

Day 2 (2025-11-20):
  Condition: Nublado
  Temp: 17°C - 23°C
  Precipitation: 2.5 mm
...
```

### `senamhi history`

View forecast history for a location on specific date.

```bash
# View forecast history
poetry run senamhi history CANTA 2025-11-13

# With department
poetry run senamhi history CANTA 2025-11-13 --department LIMA
```

**Arguments:**

- `LOCATION`: Location name
- `DATE`: Date in YYYY-MM-DD format

**Options:**

- `--department TEXT`: Department name

**Output:**

```bash
Forecast History for CANTA on 2025-11-13

Issued: 2025-11-13 06:00:00
  Temp: 12°C - 22°C
  Condition: Soleado
  Precipitation: 0.0 mm

Issued: 2025-11-12 06:00:00
  Temp: 11°C - 21°C
  Condition: Despejado
  Precipitation: 0.0 mm
```

### `senamhi status`

Show database statistics.

```bash
poetry run senamhi status
```

**Output:**

```bash
Database Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Locations: 145
Forecasts: 5,234
Warnings: 38
Active Warnings: 12

Database: PostgreSQL (PostGIS enabled)
Location: postgresql://...@localhost:5433/senamhi
```

## Warning Commands

### `senamhi warnings list`

List all warnings.

```bash
# List last 10 warnings
poetry run senamhi warnings list

# List last 20 warnings
poetry run senamhi warnings list --limit 20

# List last 50 warnings
poetry run senamhi warnings list --limit 50
```

**Options:**

- `--limit INTEGER`: Number of warnings to show (default: 10)

**Output:**

```bash
┌────────┬────────────┬──────────┬──────────────┬────────────┬──────────┐
│ Number │ Department │ Hazard   │ Severity     │ Status     │ Valid    │
├────────┼────────────┼──────────┼──────────────┼────────────┼──────────┤
│ 418    │ ANCASH     │ lluvia   │ naranja      │ vigente    │ 3 days   │
│ 417    │ ANCASH     │ viento   │ amarillo     │ vigente    │ 2 days   │
│ 414    │ APURIMAC   │ helada   │ amarillo     │ emitido    │ 3 days   │
└────────┴────────────┴──────────┴──────────────┴────────────┴──────────┘
```

### `senamhi warnings active`

List only active warnings (VIGENTE + EMITIDO).

```bash
poetry run senamhi warnings active
```

**Output:**

```bash
Active Warnings (12)

┌────────┬────────────┬──────────┬──────────────┬────────────┐
│ Number │ Department │ Hazard   │ Severity     │ Days Left  │
├────────┼────────────┼──────────┼──────────────┼────────────┤
│ 418    │ ANCASH     │ lluvia   │ naranja      │ 3          │
│ 418    │ HUANUCO    │ lluvia   │ naranja      │ 3          │
│ 417    │ LIMA       │ viento   │ amarillo     │ 2          │
└────────┴────────────┴──────────┴──────────────┴────────────┘
```

### `senamhi warnings show`

Show detailed information for a specific warning.

```bash
# Show warning details
poetry run senamhi warnings show 418

# Show for specific department
poetry run senamhi warnings show 418 --department ANCASH
```

**Arguments:**

- `WARNING_NUMBER`: Warning number (e.g., 418)

**Options:**

- `--department TEXT`: Filter by department

**Output:**

```bash
Warning #418 - Lluvias de moderada a fuerte intensidad

Department: ANCASH
Hazard: lluvia
Severity: naranja (ORANGE)
Status: vigente (ACTIVE)

Valid Period:
  From: 2025-11-19 00:00:00
  Until: 2025-11-21 23:59:59
  Duration: 3 days

Issued: 2025-11-18 14:30:00

Description:
Se esperan lluvias de moderada a fuerte intensidad...

Affected Departments: 14
ANCASH, HUANUCO, PASCO, LIMA, JUNIN, ...
```

## Geospatial Commands (PostGIS only)

### `senamhi geo download`

Download shapefiles for a warning from SENAMHI GeoServer.

```bash
# Download shapefile for warning
poetry run senamhi geo download 418

# Download will create files like:
# data/shapefiles/warning_418_day_1_2025.zip
# data/shapefiles/warning_418_day_2_2025.zip
# data/shapefiles/warning_418_day_3_2025.zip
```

**Arguments:**

- `WARNING_NUMBER`: Warning number

**Notes:**

- Requires PostGIS (PostgreSQL)
- Downloads one ZIP per day of warning
- Skips already downloaded files
- Files stored in `data/shapefiles/`

### `senamhi geo sync`

Parse shapefiles and save geometries to database.

```bash
# Sync geometries for warning
poetry run senamhi geo sync 418

# This will:
# 1. Parse all downloaded shapefiles
# 2. Extract polygon geometries
# 3. Save to warning_geometries table
# 4. Delete existing geometries first
```

**Arguments:**

- `WARNING_NUMBER`: Warning number

**Prerequisites:**

- Shapefiles must be downloaded first
- Requires PostGIS enabled

### `senamhi geo list`

List all downloaded shapefile ZIPs.

```bash
poetry run senamhi geo list
```

**Output:**

```bash
Downloaded Shapefiles (9 files)

warning_418_day_1_2025.zip  (1.2 MB)
warning_418_day_2_2025.zip  (1.3 MB)
warning_418_day_3_2025.zip  (1.1 MB)
warning_417_day_1_2025.zip  (0.8 MB)
...
```

### Complete Geospatial Workflow

```bash
# 1. Check active warnings
poetry run senamhi warnings active

# 2. Download shapefiles
poetry run senamhi geo download 418

# 3. Sync to database
poetry run senamhi geo sync 418

# 4. View in web interface
poetry run senamhi web
# Visit http://localhost:5001/department/ANCASH
# Click "🗺️ View Map" on warning #418
```

## Scheduler Commands

### `senamhi daemon start`

Start the scheduler in foreground mode.

```bash
poetry run senamhi daemon start
```

**Notes:**

- Runs in foreground (not as background daemon)
- Press Ctrl+C to stop
- Respects `ENABLE_SCHEDULER` in `.env`
- Logs to console and `logs/scheduler.log`

**Output:**

```bash
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
```

### `senamhi daemon status`

Check scheduler status (not implemented yet).

```bash
poetry run senamhi daemon status
```

### `senamhi runs`

View scrape run history.

```bash
# List last 10 runs
poetry run senamhi runs

# List last 20 runs
poetry run senamhi runs --limit 20

# Filter by status
poetry run senamhi runs --status success
poetry run senamhi runs --status failed
poetry run senamhi runs --status running
```

**Options:**

- `--limit INTEGER`: Number of runs to show (default: 10)
- `--status TEXT`: Filter by status (success/failed/running/skipped)

**Output:**

```bash
┌────┬─────────────────────┬─────────┬───────────┬───────────┬─────────┐
│ ID │ Started             │ Status  │ Locations │ Forecasts │ Runtime │
├────┼─────────────────────┼─────────┼───────────┼───────────┼─────────┤
│ 15 │ 2025-11-19 06:00:00 │ success │ 145       │ 1,015     │ 4m 32s  │
│ 14 │ 2025-11-18 06:00:00 │ success │ 145       │ 1,015     │ 4m 28s  │
│ 13 │ 2025-11-17 06:00:00 │ failed  │ 0         │ 0         │ 0m 15s  │
└────┴─────────────────────┴─────────┴───────────┴───────────┴─────────┘
```

## Web Server Commands

### `senamhi web`

Start the Flask web server.

```bash
poetry run senamhi web
```

**Default settings:**

- Host: `127.0.0.1` (localhost only)
- Port: `5001`
- Debug: Enabled (from `.env`)

**Configuration:**

```bash
# .env
WEB_HOST=0.0.0.0  # Allow external connections
WEB_PORT=8080     # Custom port
WEB_DEBUG=False   # Disable debug mode
```

**Access:**

- Homepage: <http://localhost:5001>
- Department: <http://localhost:5001/department/LIMA>
- API: <http://localhost:5001/api/warnings/418/geometry>

## Utility Commands

### `senamhi departments`

List all available departments.

```bash
poetry run senamhi departments
```

**Output:**

```bash
Available Departments (24)

AMAZONAS, ANCASH, APURIMAC, AREQUIPA, AYACUCHO,
CAJAMARCA, CUSCO, HUANCAVELICA, HUANUCO, ICA,
JUNIN, LA LIBERTAD, LAMBAYEQUE, LIMA, LORETO,
MADRE DE DIOS, MOQUEGUA, PASCO, PIURA, PUNO,
SAN MARTIN, TACNA, TUMBES, UCAYALI
```

## Common Workflows

### Daily Monitoring

```bash
# Morning: Check for new warnings
poetry run senamhi scrape warnings
poetry run senamhi warnings active

# Afternoon: Update forecasts
poetry run senamhi scrape forecasts --all --force

# Evening: View web dashboard
poetry run senamhi web
```

### Weekly Review

```bash
# Check database stats
poetry run senamhi status

# Review scrape history
poetry run senamhi runs --limit 50

# Check failed runs
poetry run senamhi runs --status failed
```

### Geospatial Update

```bash
# Get active warnings
poetry run senamhi warnings active

# Download and sync shapefiles for each
poetry run senamhi geo download 418
poetry run senamhi geo sync 418

poetry run senamhi geo download 417
poetry run senamhi geo sync 417

# View on map
poetry run senamhi web
```

### Data Export

```bash
# Export forecast data (manual query)
poetry run python -c "
from app.database import SessionLocal
from app.storage.models import Forecast
import csv

db = SessionLocal()
forecasts = db.query(Forecast).limit(100).all()

with open('forecasts.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['Location', 'Date', 'Temp Min', 'Temp Max'])
    for fc in forecasts:
        writer.writerow([fc.location.name, fc.date, fc.temp_min, fc.temp_max])
"
```

## Tips & Tricks

### Using Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias senamhi='poetry run senamhi'
alias senamhi-web='poetry run senamhi web'
alias senamhi-scrape='poetry run senamhi scrape --all'
```

Then use:

```bash
senamhi warnings active
senamhi-scrape
```

### Piping Output

```bash
# Count active warnings
poetry run senamhi warnings active | grep -c vigente

# Export warnings list
poetry run senamhi warnings list --limit 100 > warnings.txt
```

### Scheduling with Cron

```bash
# Edit crontab
crontab -e

# Add daily scrape at 6 AM
0 6 * * * cd /path/to/senamhi-tracker && poetry run senamhi scrape --all

# Add warning check every 6 hours
0 */6 * * * cd /path/to/senamhi-tracker && poetry run senamhi scrape warnings
```

### Quick Status Check

```bash
# One-liner to check everything
poetry run senamhi status && \
poetry run senamhi warnings active && \
poetry run senamhi runs --limit 5
```

## Troubleshooting

### Command not found

```bash
# Ensure Poetry is installed
poetry --version

# Activate virtual environment
poetry shell
senamhi --help
```

### Permission denied

```bash
# Check file permissions
ls -la data/

# Fix permissions
chmod -R 755 data/
chmod -R 755 logs/
```

### Database locked

```bash
# Check for running processes
ps aux | grep senamhi

# Stop scheduler if running
pkill -f "senamhi daemon"
```

## Next Steps

- [Web Dashboard Guide](web.md)
- [Scheduler Configuration](scheduler.md)
- [Geospatial Features](../features/geospatial.md)
- [API Reference](../API.md)
