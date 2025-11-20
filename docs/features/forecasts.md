# 📊 Forecast Comparison

Multi-model weather forecast comparison with Open-Meteo.

## Overview

Compare SENAMHI forecasts with global weather models:
- **SENAMHI**: Official Peru weather service
- **GFS**: NOAA Global Forecast System
- **ECMWF**: European Centre forecasts

## Quick Start

### 1. Add Coordinates

Edit `config/coordinates.yaml`:
```yaml
LIMA:
  LIMA ESTE: [-12.0464, -77.0428]
  CANTA: [-11.4744, -76.6256]
```

### 2. Populate Database
```bash
poetry run python scripts/populate_coordinates.py --skip-existing
```

### 3. View Charts
```bash
poetry run senamhi web
# Click "📊 View Chart" on any location
```

## Configuration

### Add Models

Edit `config/openmeteo.yaml`:
```yaml
models:
  - id: gfs_seamless
    name: GFS
    colors:
      temp: rgb(255, 99, 132)
      precip: rgba(255, 99, 132, 0.7)

  - id: ecmwf_ifs
    name: ECMWF
    colors:
      temp: rgb(54, 162, 235)
      precip: rgba(54, 162, 235, 0.7)
```

### Customize Variables
```yaml
variables:
  - api_name: temperature_2m
    display_name: Temperature
    unit: °C

  - api_name: precipitation
    display_name: Precipitation
    unit: mm
```

## Chart Features

- **Interactive tooltips**: Hover for details
- **Toggle models**: Click legend to show/hide
- **Responsive**: Works on mobile
- **Real-time data**: Fresh from Open-Meteo API

## Troubleshooting

**Charts not loading:**
```bash
# Check coordinates
poetry run senamhi list

# Test API
curl "https://api.open-meteo.com/v1/forecast?latitude=-12.0464&longitude=-77.0428"
```

**Missing locations:**
```bash
# Add to coordinates.yaml, then:
poetry run python scripts/populate_coordinates.py
```

See [Configuration Guide](../configuration.md) for more options.
