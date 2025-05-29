from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "ev_charging_db"
    
    # TomTom API
    TOMTOM_API_KEY: str = "f4ox7ygPosfpB1r6UbOMeVjq662iK9W6"
    TOMTOM_BASE_URL: str = "https://api.tomtom.com"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()