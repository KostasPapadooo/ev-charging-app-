from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Database settings
    mongodb_url: str
    database_name: str
    
    # TomTom API Keys
    tomtom_api_key: str
    tomtom_ev_api_key: Optional[str] = None
    tomtom_base_url: str = "https://api.tomtom.com"
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # JWT settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Email settings (for notifications)
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Redis settings (for caching or other purposes)
    redis_url: str
    
    # App settings
    app_name: str = "EV Charging Stations API"
    debug: bool = True
    
    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Batch update settings
    BATCH_UPDATE_INTERVAL_MINUTES: int = int(os.getenv("BATCH_UPDATE_INTERVAL_MINUTES", "30"))
    ATHENS_CENTER_LAT: float = float(os.getenv("ATHENS_CENTER_LAT", "37.9838"))
    ATHENS_CENTER_LON: float = float(os.getenv("ATHENS_CENTER_LON", "23.7275"))
    ATHENS_RADIUS_METERS: int = int(os.getenv("ATHENS_RADIUS_METERS", "50000"))
    ATHENS_CITY_NAME: str = os.getenv("ATHENS_CITY_NAME", "Athens")
    
    THESSALONIKI_CENTER_LAT: float = float(os.getenv("THESSALONIKI_CENTER_LAT", "40.6401"))
    THESSALONIKI_CENTER_LON: float = float(os.getenv("THESSALONIKI_CENTER_LON", "22.9444"))
    THESSALONIKI_RADIUS_METERS: int = int(os.getenv("THESSALONIKI_RADIUS_METERS", "50000"))
    THESSALONIKI_CITY_NAME: str = os.getenv("THESSALONIKI_CITY_NAME", "Thessaloniki")
    
    DEFAULT_SPEED_LAYER_POLLING_INTERVAL_SECONDS: int = int(os.getenv("DEFAULT_SPEED_LAYER_POLLING_INTERVAL_SECONDS", "60"))
    HISTORICAL_DATA_RETENTION_DAYS: int = int(os.getenv("HISTORICAL_DATA_RETENTION_DAYS", "30"))
    
    # Realtime Layer (Pusher)
    pusher_app_id: Optional[str] = None
    pusher_key: Optional[str] = None
    pusher_secret: Optional[str] = None
    pusher_cluster: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = Settings()

# Logging για επιβεβαίωση
import logging
logger = logging.getLogger(__name__)

if settings.tomtom_ev_api_key:
    logger.info("TomTom EV API key configured.")
else:
    # Αν το tomtom_ev_api_key είναι Optional και η απουσία του δεν είναι πρόβλημα,
    # ίσως δεν χρειάζεται warning, αλλά ένα info ή debug log.
    logger.info("TomTom EV API key not configured (optional).")

logger.info(f"Loaded Celery Broker URL: {settings.CELERY_BROKER_URL}")
logger.info(f"Loaded Celery Result Backend: {settings.CELERY_RESULT_BACKEND}")
logger.info(f"CORS Origins: {settings.cors_origins}")
logger.info(f"Debug mode: {settings.debug}")