# API Documentation

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### Health Check
```http
GET /api/health
```

Returns API status and available endpoints.

**Response:**
```json
{
  "status": "ok",
  "api_version": "1.0",
  "endpoints": { ... }
}
```

---

### Get Capabilities
```http
GET /api/capabilities
```

Check PostGIS availability and supported features.

**Response:**
```json
{
  "geojson_available": false,
  "database_type": "SQLite",
  "features": {
    "warning_geometries": false,
    "spatial_queries": false
  }
}
```

---

### Get Warning Info
```http
GET /api/warnings/{warning_number}/info
```

Get warning metadata without geometry.

**Parameters:**
- `warning_number` (string): Warning number (e.g., "418")

**Response:**
```json
{
  "warning_number": "418",
  "title": "Incremento de temperatura...",
  "severity": "naranja",
  "status": "vigente",
  ...
}
```

---

### Get Warning Geometry (All Days)
```http
GET /api/warnings/{warning_number}/geometry
```

Get all geometries for a warning (all days) in GeoJSON format.

**Requires:** PostgreSQL + PostGIS

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { ... },
      "properties": {
        "warning_number": "418",
        "day_number": 1,
        "severity": "naranja",
        ...
      }
    }
  ]
}
```

---

### Get Warning Geometry (Specific Day)
```http
GET /api/warnings/{warning_number}/geometry/{day}
```

Get geometry for a specific day.

**Parameters:**
- `warning_number` (string): Warning number
- `day` (integer): Day number (1-based)

**Requires:** PostgreSQL + PostGIS

**Response:**
```json
{
  "type": "Feature",
  "geometry": { ... },
  "properties": { ... }
}
```

---

### Get Active Warnings Geometries
```http
GET /api/warnings/active/geometries
```

Get all active warnings with geometries.

**Requires:** PostgreSQL + PostGIS

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [ ... ]
}
```

---

## Error Responses

### 404 Not Found
```json
{
  "error": "Warning not found",
  "warning_number": "999"
}
```

### 503 Service Unavailable
```json
{
  "error": "PostGIS not available",
  "message": "Geometry features require PostgreSQL + PostGIS"
}
```
