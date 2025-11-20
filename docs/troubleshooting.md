# 🔧 Troubleshooting

Common issues and solutions.

## Installation Issues

**Poetry not found:**
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Dependencies fail to install:**
```bash
poetry cache clear pypi --all
poetry install
```

## Database Issues

**SQLite locked:**
```bash
# Stop all running processes
ps aux | grep senamhi
pkill -f senamhi

# Or use PostgreSQL
```

**PostgreSQL connection failed:**
```bash
# Check it's running
pg_isalive

# Test connection
psql -U senamhi_user -d senamhi

# Check port
lsof -i :5433
```

**Migrations fail:**
```bash
# Check current version
poetry run alembic current

# Reset (⚠️ destructive)
./dev_tools/reset_db.sh
poetry run alembic upgrade head
```

## Scraping Issues

**Network timeout:**
```bash
# Increase timeout in .env
REQUEST_TIMEOUT=60
SCRAPE_DELAY=3.0
```

**No data scraped:**
```bash
# Check SENAMHI website is accessible
curl https://www.senamhi.gob.pe

# Check logs
tail -f logs/scheduler.log
```

## Web Interface Issues

**Port 5001 in use:**
```bash
# Change port in .env
WEB_PORT=5002

# Or kill process
lsof -ti:5001 | xargs kill -9
```

**Maps not showing:**
```bash
# Check PostGIS
psql -d senamhi -c "SELECT PostGIS_version();"

# Re-sync geometries
poetry run senamhi geo sync 418

# Check browser console (F12)
```

**Charts not loading:**
```bash
# Verify coordinates
poetry run senamhi list

# Populate coordinates
poetry run python scripts/populate_coordinates.py
```

## Docker Issues

**Container won't start:**
```bash
# Check logs
docker logs senamhi-tracker-postgres

# Rebuild
docker compose down
docker compose up -d --build --force-recreate
```

**Database volume issues:**
```bash
# Remove volumes (⚠️ deletes data)
docker compose down -v
docker compose up -d
```

## Performance Issues

**Slow scraping:**
```bash
# Reduce concurrent operations
SCRAPE_DELAY=3.0

# Scrape fewer departments
SCRAPE_ALL_DEPARTMENTS=False
DEPARTMENTS=LIMA
```

**High memory usage:**
```bash
# Check database size
du -h data/weather.db

# Clean old data
poetry run python scripts/cleanup_old_warnings.py
```

## Common Error Messages

**"PostGIS not available":**
- Using SQLite but trying geospatial features
- Switch to PostgreSQL or disable geo features

**"Warning not found":**
- Warning number doesn't exist
- Check: `poetry run senamhi warnings list`

**"No such function: RecoverGeometryColumn":**
- Tests trying to use PostGIS with SQLite
- Tests are automatically skipped, this is expected

**"Database is locked":**
- Multiple processes accessing SQLite
- Use PostgreSQL or ensure only one process runs

## Getting Help

1. Check [documentation](README.md)
2. Search [issues](https://github.com/rosepb28/senamhi-tracker/issues)
3. Enable debug logging: `DEBUG=True`
4. Check logs: `tail -f logs/scheduler.log`
5. Open new issue with logs and error message
