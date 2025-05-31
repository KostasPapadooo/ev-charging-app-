from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Database settings
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "ev_charging_db"
    
    # TomTom API Keys
    tomtom_api_key: str = ""
    tomtom_ev_api_key: str = ""  # Νέο πεδίο
    
    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    
    # JWT settings
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Email settings (for notifications)
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    # Redis settings (for caching)
    redis_url: str = "redis://localhost:6379/0"
    
    # App settings
    app_name: str = "EV Charging Stations API"
    debug: bool = True
    
    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Realtime Layer
    pusher_app_id: Optional[str] = None
    pusher_key: Optional[str] = None
    pusher_secret: Optional[str] = None
    pusher_cluster: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = Settings()

# Προαιρετικό: Ένα log για να επιβεβαιώσεις ότι φορτώθηκαν οι ρυθμίσεις του Celery
import logging
logger = logging.getLogger(__name__)
logger.info(f"Loaded Celery Broker URL: {settings.celery_broker_url}")
logger.info(f"Loaded Celery Result Backend: {settings.celery_result_backend}")