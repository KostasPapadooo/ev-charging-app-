from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import time
from datetime import datetime

from app.core.config import settings
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.services.tomtom_service import tomtom_service
from app.core.exceptions import TomTomAPIException
from app.repositories import repositories
from app.models.user import User, UserPreferences
from app.models.event import Event
from app.services.opencharge_service import opencharge_service
from app.models.station import Station, StationLocation, ConnectorInfo, OperatorInfo

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
    await tomtom_service.close()
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
    try:
        from app.database.connection import get_database
        
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

@app.get("/test/tomtom")
async def test_tomtom_api(lat: float = 37.9755, lon: float = 23.7348, radius: int = 5000):
    """
    Test endpoint for TomTom API integration
    Default coordinates are for Athens, Greece
    """
    try:
        logger.info(f"Testing TomTom API with coordinates: {lat}, {lon}, radius: {radius}m")
        
        # Get stations from TomTom API
        stations = await tomtom_service.get_stations_in_area(lat, lon, radius)
        
        return {
            "success": True,
            "message": f"Successfully retrieved {len(stations)} charging stations",
            "coordinates": {"lat": lat, "lon": lon, "radius": radius},
            "stations_count": len(stations),
            "stations": [
                {
                    "tomtom_id": station.tomtom_id,
                    "name": station.name,
                    "address": {
                        "street": station.address.street,
                        "city": station.address.city,
                        "country": station.address.country
                    },
                    "location": {
                        "lat": station.location.coordinates[1],
                        "lon": station.location.coordinates[0]
                    },
                    "status": station.status,
                    "connectors_count": len(station.connectors),
                    "connectors": [
                        {
                            "id": conn.id,
                            "type": conn.type,
                            "power_kw": conn.power_kw,
                            "status": conn.status
                        } for conn in station.connectors
                    ],
                    "operator": station.operator.name if station.operator else None,
                    "data_source": station.data_source
                } for station in stations[:5]  # Show only first 5 stations for readability
            ]
        }
        
    except TomTomAPIException as e:
        logger.error(f"TomTom API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TomTom API Error",
                "message": str(e),
                "status_code": getattr(e, 'status_code', None)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in TomTom test: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )

@app.get("/test/tomtom/raw")
async def test_tomtom_raw(lat: float = 37.9755, lon: float = 23.7348, radius: int = 5000):
    """
    Test endpoint to see raw TomTom API response
    """
    try:
        logger.info(f"Testing raw TomTom API response")
        
        # Get raw TomTom stations
        tomtom_stations = await tomtom_service.search_charging_stations(lat, lon, radius)
        
        return {
            "success": True,
            "message": f"Raw TomTom API response with {len(tomtom_stations)} stations",
            "coordinates": {"lat": lat, "lon": lon, "radius": radius},
            "raw_stations": [station.dict() for station in tomtom_stations[:3]]  # Show first 3 raw stations
        }
        
    except Exception as e:
        logger.error(f"Error in raw TomTom test: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TomTom Raw API Error",
                "message": str(e)
            }
        )

@app.get("/test/repositories")
async def test_repositories():
    """Test repository functionality"""
    try:
        # Test station repository
        stations_count = await repositories.stations.count()
        
        # Generate unique email για κάθε test
        unique_email = f"test_{int(time.time())}@example.com"
        
        # Test creating a sample user με έγκυρα δεδομένα
        test_user = await repositories.users.create_user(
            email=unique_email,
            password="testpassword123",
            first_name="Test",
            last_name="User",
            phone="+306912345678"
        )
        
        # Test creating an event με όλα τα απαιτούμενα πεδία
        test_event = Event(
            event_type="STATION_STATUS_CHANGE",
            station_id="test_station_123",
            connector_id="connector_1",  # Προσθήκη
            old_status="AVAILABLE",
            new_status="OCCUPIED",
            event_data={"test": "data"},  # Προσθήκη
            processing_batch="batch_1"  # Προσθήκη
        )
        created_event = await repositories.events.create(test_event)
        
        return {
            "success": True,
            "message": "Repository tests completed",
            "results": {
                "stations_in_db": stations_count,
                "test_user_created": {
                    "id": str(test_user.id),
                    "email": test_user.email,
                    "first_name": test_user.first_name,
                    "last_name": test_user.last_name,
                    "phone": test_user.phone
                },
                "test_event_created": {
                    "id": str(created_event.id),
                    "event_type": created_event.event_type,
                    "station_id": created_event.station_id,
                    "connector_id": created_event.connector_id
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Repository test error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Repository Test Error",
                "message": str(e)
            }
        )

@app.get("/test/station-operations")
async def test_station_operations():
    """Test station operations"""
    try:
        from app.repositories import station_repo
        
        # Κέντρο Αθήνας με μεγάλη εμβέλεια
        athens_lat = 37.9755  # Κέντρο Αθήνας
        athens_lon = 23.7348  # Κέντρο Αθήνας
        radius = 50000        # 50km εμβέλεια (όλη η Αττική)
        
        logger.info(f"Testing station operations at Athens center: ({athens_lat}, {athens_lon}) with {radius}m radius")
        
        # Test TomTom API
        tomtom_stations = await tomtom_service.search_charging_stations(
            latitude=athens_lat,
            longitude=athens_lon,
            radius=radius
        )
        
        logger.info(f"TomTom returned {len(tomtom_stations)} stations")
        
        # Upsert stations to database using repository
        upsert_result = await station_repo.upsert_stations_batch(tomtom_stations)
        logger.info(f"Upserted stations: {upsert_result}")
        
        # Get nearby stations using repository
        nearby_stations = await station_repo.get_nearby_stations(
            latitude=athens_lat,
            longitude=athens_lon,
            radius_meters=radius,
            limit=5
        )
        
        return {
            "success": True,
            "message": "Station operations test completed",
            "results": {
                "test_location": f"Athens Center ({athens_lat}, {athens_lon})",
                "search_radius_km": radius/1000.0,
                "tomtom_stations_fetched": len(tomtom_stations),
                "upsert_result": upsert_result,
                "nearby_stations_found": len(nearby_stations),
                "sample_nearby_stations": [
                    {
                        "tomtom_id": station.tomtom_id,
                        "name": station.name,
                        "address": station.address,
                        "operator": station.operator.name,
                        "status": station.status
                    }
                    for station in nearby_stations
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error in station operations test: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in station operations test: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )