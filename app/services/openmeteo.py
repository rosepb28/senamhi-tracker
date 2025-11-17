"""Open Meteo API client for weather forecasts."""

import logging
from pathlib import Path

import openmeteo_requests
import pandas as pd
import yaml

try:
    import requests_cache
    from retry_requests import retry

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Load config
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "openmeteo.yaml"

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        OPENMETEO_CONFIG = yaml.safe_load(f)
    logger.info(f"Loaded Open Meteo config from {CONFIG_PATH}")
except FileNotFoundError:
    logger.error(f"Config file not found: {CONFIG_PATH}")
    OPENMETEO_CONFIG = {
        "models": [
            {"id": "gfs_seamless", "name": "GFS"},
            {"id": "ecmwf_ifs", "name": "ECMWF"},
        ],
        "variables": [
            {"id": "temperature_2m"},
            {"id": "precipitation"},
            {"id": "wind_speed_10m"},
        ],
        "forecast_days": 3,
        "timezone": "America/Lima",
    }
except Exception as e:
    logger.error(f"Error loading config: {e}")
    raise


class OpenMeteoClient:
    """Client for Open Meteo API."""

    def __init__(self):
        """Initialize Open Meteo client with cache and retry."""
        self.config = OPENMETEO_CONFIG

        # Extract model IDs from config
        self.models = [m["id"] for m in self.config["models"]]

        # Extract variable IDs from config
        self.variables = [v["id"] for v in self.config["variables"]]

        # Setup cache if available
        if CACHE_AVAILABLE:
            cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
            retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
            self.client = openmeteo_requests.Client(session=retry_session)
        else:
            logger.warning("requests-cache not available, using standard session")
            self.client = openmeteo_requests.Client()

        self.url = self.config.get("url", "https://api.open-meteo.com/v1/forecast")

    def get_config(self) -> dict:
        """Get Open Meteo configuration."""
        return self.config

    def get_hourly_forecast(
        self,
        latitude: float,
        longitude: float,
        models: list[str] | None = None,
        forecast_days: int | None = None,
    ) -> dict:
        """
        Get hourly forecast for location.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            models: List of models to use (default: from config)
            forecast_days: Number of days to forecast (default: from config)

        Returns:
            Dict with forecast data by model
        """
        if models is None:
            models = self.models

        if forecast_days is None:
            forecast_days = self.config["forecast_days"]

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": self.variables,
            "models": ",".join(models),
            # "timezone": self.config["timezone"],
            "forecast_days": forecast_days,
        }

        try:
            responses = self.client.weather_api(self.url, params=params)

            result = {"latitude": latitude, "longitude": longitude, "models": {}}

            # Process each model response
            for i, model in enumerate(models):
                if i < len(responses):
                    response = responses[i]
                    model_data = self._parse_hourly_response(response)
                    result["models"][model] = model_data

            return result

        except Exception as e:
            logger.error(f"Error fetching Open Meteo data: {e}")
            return {"error": str(e), "models": {}}

    def _parse_hourly_response(self, response) -> dict:
        """Parse hourly response from Open Meteo API."""
        try:
            hourly = response.Hourly()

            # Get variables dynamically based on config
            result = {}

            for i, var_config in enumerate(self.config["variables"]):
                var_id = var_config["id"]
                values = hourly.Variables(i).ValuesAsNumpy()

                # Use simplified key names
                if "temperature" in var_id:
                    result["temperature"] = values.tolist()
                elif "precipitation" in var_id:
                    result["precipitation"] = values.tolist()
                elif "wind" in var_id:
                    result["wind_speed"] = values.tolist()

            # Create timestamps in UTC
            timestamps_utc = pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )

            # Convert to Lima timezone (UTC-5)
            lima_tz = "America/Lima"
            timestamps_local = timestamps_utc.tz_convert(lima_tz)

            # Format as ISO strings without timezone info (already in local time)
            result["timestamps"] = [
                ts.strftime("%Y-%m-%dT%H:%M:%S") for ts in timestamps_local
            ]

            return result

        except Exception as e:
            logger.error(f"Error parsing Open Meteo response: {e}")
            return {
                "timestamps": [],
                "temperature": [],
                "precipitation": [],
                "wind_speed": [],
            }
