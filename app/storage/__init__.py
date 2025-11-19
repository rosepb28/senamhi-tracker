"""Storage package for database operations."""

from app.storage import crud, models
from config.settings import settings

# Import geo_models only if PostGIS is available
if settings.supports_postgis:
    from app.storage import geo_models

    __all__ = ["crud", "models", "geo_models"]
else:
    __all__ = ["crud", "models"]
