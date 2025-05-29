from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.core.config import settings
from app.database.connection import connect_to_mongo, close_mongo_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EV Charging Stations API",
    description="API for managing EV charging stations with real-time notifications",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Αλλαγή εδώ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await connect_to_mongo()
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_mongo_connection()
    logger.info("Application shutdown complete")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "EV Charging Stations API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    from app.database.connection import get_database
    
    try:
        db = get_database()
        # Test database connection
        collections = await db.list_collection_names()
        
        return {
            "status": "healthy",
            "database": "connected",
            "collections": len(collections),
            "collections_list": collections
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )