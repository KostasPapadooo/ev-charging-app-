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
    cors_origins: List[str] = []
    
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
    celery_broker_url: str
    celery_result_backend: str
    
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

logger.info(f"Loaded Celery Broker URL: {settings.celery_broker_url}")
logger.info(f"Loaded Celery Result Backend: {settings.celery_result_backend}")
logger.info(f"CORS Origins: {settings.cors_origins}")
logger.info(f"Debug mode: {settings.debug}")