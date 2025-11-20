# 🗺️ Geospatial Features

Interactive warning maps with PostGIS and Leaflet.js.

## Quick Setup

### 1. PostgreSQL + PostGIS
```bash
# Local
brew install postgresql@16 postgis
psql -U postgres -c "CREATE DATABASE senamhi;"
psql -U postgres -d senamhi -c "CREATE EXTENSION postgis;"

# Docker
docker compose -f docker-compose.postgres.yml up -d
```

### 2. Configure
```bash
# .env
DATABASE_URL=postgresql://senamhi_user:senamhi_pass@localhost:5433/senamhi
```

### 3. Migrate
```bash
poetry run alembic upgrade head
```

### 4. Use
```bash
# Download shapefiles
poetry run senamhi geo download 418

# Sync to database
poetry run senamhi geo sync 418

# View map
poetry run senamhi web
# Click "🗺️ View Map" on warning
```

## Features

### Interactive Maps
- **Color-coded levels**: Nivel 1-4 (gray, yellow, orange, red)
- **Day timeline**: Navigate through warning progression
- **Auto-zoom**: Focus on affected department
- **Boundaries**: Peru department borders overlay

### Automatic Downloads
Scheduler downloads shapefiles for new active warnings every 6 hours.

### Data Sources
- **Warning shapefiles**: SENAMHI GeoServer
- **Department boundaries**: INEI (included in `data/boundaries/`)
- **District boundaries**: INEI (included in `data/boundaries/`)

## CLI Commands
```bash
# Download
poetry run senamhi geo download 418

# Sync to DB
poetry run senamhi geo sync 418

# List files
poetry run senamhi geo list
```

## Customization

### Map Colors

Edit `app/web/static/css/style.css`:
```css
:root {
    --nivel-2-color: #ffc107;  /* Yellow */
    --nivel-3-color: #fd7e14;  /* Orange */
    --nivel-4-color: #dc3545;  /* Red */
}
```

## Migration from SQLite
```bash
# 1. Start PostgreSQL
docker compose -f docker-compose.postgres.yml up -d postgres

# 2. Update .env
DATABASE_URL=postgresql://...

# 3. Run migrations
poetry run alembic upgrade head

# 4. Re-scrape data
poetry run senamhi scrape --all
poetry run senamhi scrape warnings

# 5. Download shapefiles
poetry run senamhi warnings active  # Get numbers
poetry run senamhi geo download 418
poetry run senamhi geo sync 418
```

## Troubleshooting

**Maps not showing:**
```bash
# Check PostGIS
psql -d senamhi -c "SELECT PostGIS_version();"

# Re-sync geometries
poetry run senamhi geo sync 418
```

**Download fails:**
- Check SENAMHI GeoServer: https://idesep.senamhi.gob.pe/geoserver
- Verify warning exists on SENAMHI website

See [Configuration Guide](../configuration.md) for more details.
