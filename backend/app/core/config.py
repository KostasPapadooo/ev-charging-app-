from pydantic_settings import BaseSettings
from typing import List
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
    redis_url: str = "redis://localhost:6379"
    
    # App settings
    app_name: str = "EV Charging Stations API"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()