# 🌐 Web Dashboard Guide

Complete guide to using the SENAMHI Tracker web interface.

## Overview

The web dashboard provides an interactive interface for viewing weather forecasts, warnings, and geospatial data.

## Starting the Web Server

### Local Development
```bash
poetry run senamhi web
```

Visit: http://localhost:5001

### Docker

**SQLite:**
```bash
docker compose up -d
```

**PostgreSQL:**
```bash
docker compose -f docker-compose.postgres.yml up -d
```

The web interface is not exposed by default in Docker. To access it, modify `docker-compose.yml`:
```yaml
services:
  senamhi-tracker:
    ports:
      - "5001:5001"  # Add this line
```

Then restart:
```bash
docker compose restart
```

### Configuration
```bash
# .env
WEB_HOST=127.0.0.1    # Localhost only (secure)
WEB_PORT=5001         # Port number
WEB_DEBUG=True        # Enable debug mode
```

**Production Settings:**
```bash
WEB_HOST=0.0.0.0      # Allow external connections
WEB_PORT=80           # Standard HTTP port
WEB_DEBUG=False       # Disable debug
```

## Pages

### Homepage

**URL:** `http://localhost:5001/`

**Features:**
- Department list with quick access
- Total statistics (locations, forecasts, warnings)
- Database status indicator
- Quick navigation to all departments

**Actions:**
- Click department name to view detailed forecasts

### Department View

**URL:** `http://localhost:5001/department/{DEPARTMENT}`

Example: `http://localhost:5001/department/LIMA`

**Features:**
- All locations within department
- Active weather warnings for department
- Current forecast for each location
- Quick access to detailed views

**Sections:**

#### Active Warnings
- Warning number and title
- Severity badge (Amarillo/Naranja/Rojo)
- Status badge (EMITIDO/VIGENTE)
- Validity period with days remaining
- View details button
- View map button (PostGIS only)

#### Location Forecasts
- Location name
- 3-day forecast preview
- Temperature range (min/max)
- Weather condition
- Precipitation amount
- View chart button (opens modal)

### Warning Details

**URL:** `http://localhost:5001/warning/{WARNING_NUMBER}`

Example: `http://localhost:5001/warning/418`

**Features:**
- Complete warning information
- All affected departments
- Full description
- Validity timeline
- Back to department button

## Interactive Features

### Forecast Charts

**Access:** Click "📊 View Chart" on any location card

**Features:**
- Temperature comparison (SENAMHI vs GFS vs ECMWF)
- Precipitation comparison
- Interactive tooltips
- Legend with model colors
- Configurable forecast period (3/5/7 days)
- Real-time data from Open-Meteo API

**Chart Controls:**
- Hover over data points for details
- Click legend to show/hide models
- Responsive design (works on mobile)

**Models Compared:**
- **SENAMHI**: Official Peru weather service
- **GFS**: NOAA Global Forecast System
- **ECMWF**: European Centre for Medium-Range Weather Forecasts

### Warning Maps (PostGIS only)

![Interactive Map](../images/dashboard-map.png)

**Access:** Click "🗺️ View Map" on warning cards

**Features:**
- Interactive Leaflet.js map
- Color-coded warning levels:
  - **Nivel 1** (Gray): Sin fenómeno - very faint
  - **Nivel 2** (Yellow): Amarillo - moderate risk
  - **Nivel 3** (Orange): Naranja - high risk
  - **Nivel 4** (Red): Rojo - very high risk
- Day-by-day timeline navigation
- Department boundaries overlay
- Auto-zoom to affected department
- Click polygons for details

**Map Controls:**
- **Timeline buttons**: Navigate through warning days (shows actual dates: DD MMM)
- **Active day**: Highlighted button shows current day
- **Zoom controls**: Standard Leaflet zoom (+/-)
- **Base layers**: Streets, Satellite, Terrain

**Timeline Features:**
- Shows actual dates (e.g., "19 Nov", "20 Nov")
- Active warnings: Timeline starts at current day
- Expired warnings: Timeline starts at day 1
- Smooth transitions between days

**Example:**
```
Warning #418 - Lluvias intensas

Timeline: [19 Nov] [20 Nov] [21 Nov]
              ↑ Active day
```

## API Endpoints

The web dashboard uses these REST API endpoints:

### Forecasts
```bash
GET /api/forecast/{location_id}
```

Returns forecast data for charts.

### Warnings
```bash
# Get warning info
GET /api/warnings/{warning_number}/info

# Get warning geometry (PostGIS only)
GET /api/warnings/{warning_number}/geometry

# Get specific day geometry
GET /api/warnings/{warning_number}/geometry?day={day_number}
```

### Departments
```bash
# Get department bounds (PostGIS only)
GET /api/departments/{department_name}/bounds

# Get department geometry (PostGIS only)
GET /api/departments/{department_name}/geometry

# Get all departments geometry (PostGIS only)
GET /api/departments/all/geometry
```

**Example API Calls:**
```bash
# Get Lima boundaries
curl http://localhost:5001/api/departments/LIMA/bounds

# Get warning 418 geometries
curl http://localhost:5001/api/warnings/418/geometry

# Get warning info
curl http://localhost:5001/api/warnings/418/info
```

## Customization

### Map Styling

Edit `app/web/static/css/style.css`:
```css
/* Warning level colors */
:root {
    --nivel-1-color: #cccccc;  /* Light gray */
    --nivel-2-color: #ffc107;  /* Yellow */
    --nivel-3-color: #fd7e14;  /* Orange */
    --nivel-4-color: #dc3545;  /* Red */
    --department-border-color: #000000;  /* Black */
}

/* Adjust transparency */
.warning-nivel-2 {
    fill-opacity: 0.6;  /* More visible */
}

/* Adjust border thickness */
.department-boundary {
    stroke-width: 2px;  /* Thicker borders */
}
```

### Chart Colors

Edit `config/openmeteo.yaml`:
```yaml
models:
  - id: gfs_seamless
    name: GFS
    colors:
      temp: rgb(255, 99, 132)      # Red for temperature
      precip: rgba(255, 99, 132, 0.7)  # Red transparent for precip

  - id: ecmwf_ifs04
    name: ECMWF
    colors:
      temp: rgb(54, 162, 235)      # Blue
      precip: rgba(54, 162, 235, 0.7)
```

### Forecast Period

Currently hardcoded to 3 days. To change, edit `app/web/routes/main.py`:
```python
# Change this line
forecast_days = 3  # Change to 5 or 7
```

## Mobile Support

The web dashboard is responsive and works on mobile devices:

- ✅ Touch-friendly buttons
- ✅ Responsive layout
- ✅ Mobile-optimized charts
- ✅ Pinch-to-zoom on maps
- ✅ Collapsible sections

**Tested on:**
- iOS Safari
- Android Chrome
- Desktop browsers (Chrome, Firefox, Safari, Edge)

## Performance

### Optimization Tips

**For large databases:**
1. Enable pagination (not implemented yet)
2. Filter by date range
3. Use database indexes (already configured)

**For slow maps:**
1. Reduce polygon complexity (simplified shapefiles)
2. Limit displayed days
3. Use CDN for Leaflet.js (already configured)

**For slow charts:**
1. Reduce forecast period (3 days vs 7 days)
2. Cache Open-Meteo responses
3. Limit number of models compared

### Caching

Currently no caching implemented. For production:
- Add Flask-Caching
- Cache API responses (5-15 minutes)
- Cache Open-Meteo responses (1 hour)

## Troubleshooting

### Port 5001 already in use
```bash
# Check what's using the port
lsof -i :5001

# Change port in .env
WEB_PORT=5002

# Restart server
poetry run senamhi web
```

### Maps not showing (PostGIS)

**Check:**
1. PostGIS is enabled: `SELECT PostGIS_version();`
2. Shapefiles are downloaded: `poetry run senamhi geo list`
3. Geometries are synced: Check `warning_geometries` table
4. Browser console for errors: F12 → Console tab

**Fix:**
```bash
# Re-download and sync
poetry run senamhi geo download 418
poetry run senamhi geo sync 418

# Restart web server
poetry run senamhi web
```

### Charts not loading

**Check:**
1. Open-Meteo API is accessible
2. Location has coordinates in database
3. Browser console for errors

**Fix:**
```bash
# Verify coordinates
poetry run senamhi list

# Populate missing coordinates
poetry run python scripts/populate_coordinates.py

# Test API directly
curl "https://api.open-meteo.com/v1/forecast?latitude=-12.0464&longitude=-77.0428&temperature_2m"
```

### 404 Not Found

**Common causes:**
1. Department name case-sensitive: Use uppercase (LIMA not Lima)
2. Location name has special characters: Use exact name from database
3. Warning number doesn't exist: Check `poetry run senamhi warnings list`

### Slow page load

**Optimization:**
```bash
# Check database size
poetry run senamhi status

# Remove old data
poetry run python scripts/cleanup_old_warnings.py

# Optimize database (PostgreSQL)
VACUUM ANALYZE;
```

## Security Considerations

### Production Deployment

**⚠️ Important for public deployment:**

1. **Disable debug mode:**
```bash
   WEB_DEBUG=False
   DEBUG=False
```

2. **Use reverse proxy:**
```nginx
   # nginx config
   location / {
       proxy_pass http://127.0.0.1:5001;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
```

3. **Enable HTTPS:**
   - Use Let's Encrypt certificates
   - Configure nginx/Apache with SSL

4. **Rate limiting:**
   - Add Flask-Limiter
   - Limit API endpoints to prevent abuse

5. **Authentication (optional):**
   - Add Flask-Login for user management
   - Protect sensitive endpoints

### CORS Configuration

Currently CORS is enabled for all origins (development). For production:
```python
# app/web/__init__.py
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"]
    }
})
```

## Advanced Usage

### Embedding Maps

You can embed warning maps in external applications:
```html
<iframe
  src="http://localhost:5001/warning/418"
  width="100%"
  height="600px"
  frameborder="0">
</iframe>
```

### Custom Styling

Add custom CSS by creating `app/web/static/css/custom.css`:
```css
/* Dark theme example */
body {
    background-color: #1a1a1a;
    color: #ffffff;
}

.card {
    background-color: #2d2d2d;
    border-color: #404040;
}
```

Then include in templates:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
```

## Examples

### Daily Weather Check

1. Visit homepage: http://localhost:5001
2. Click your department (e.g., LIMA)
3. Check active warnings at top
4. Review forecasts for your locations
5. Click "View Chart" for detailed comparison

### Warning Investigation

1. Navigate to department with active warning
2. Click "View Map" on warning card
3. Use timeline to see progression
4. Check different days
5. Note affected areas
6. Read full description

### Multi-Model Comparison

1. Click "View Chart" on location
2. Compare SENAMHI vs GFS vs ECMWF
3. Note discrepancies
4. Check precipitation differences
5. Use for planning decisions

## Next Steps

- [CLI Usage](cli.md) - Command-line tools
- [Scheduler Configuration](scheduler.md) - Automatic updates
- [Geospatial Features](../features/geospatial.md) - PostGIS setup
- [API Documentation](../API.md) - REST API reference
