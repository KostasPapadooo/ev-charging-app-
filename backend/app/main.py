from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import time
from datetime import datetime
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import socketio

from app.core.config import settings
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.services.tomtom_service import tomtom_service
from app.core.exceptions import TomTomAPIException
from app.repositories import repositories
from app.models.user import User, UserPreferences
from app.models.event import Event
from app.models.station import Station, StationLocation, ConnectorInfo, OperatorInfo
from app.api import stations
from app.api.auth import router as auth_router
# Import celery tasks
from app.tasks.realtime_tasks import poll_station_availability_bulk
from app.tasks.batch_tasks import batch_update_stations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    # Αρχικοποίηση των repositories μετά τη σύνδεση στη βάση δεδομένων
    from app.repositories import init_repositories
    await init_repositories()  # Make it async
    
    # Get Athens config from settings
    athens_lat = settings.ATHENS_CENTER_LAT
    athens_lon = settings.ATHENS_CENTER_LON
    athens_radius = settings.ATHENS_RADIUS_METERS
    athens_city_name = settings.ATHENS_CITY_NAME
    
    # Ξεκινάμε τον scheduler ΜΕΤΑ την αρχικοποίηση
    try:
        # Schedule Speed Layer task (every 5 minutes)
        scheduler.add_job(
            lambda: poll_station_availability_bulk.delay(),
            IntervalTrigger(minutes=5),
            id="speed_layer_bulk_poll",
            name="Real-time availability bulk poll (Speed Layer)",
            replace_existing=True
        )
        logger.info("🚀 Speed Layer (bulk poll) scheduler started - runs every 5 minutes")
        
        # Schedule Batch Layer task for Athens (every 5 hours)
        scheduler.add_job(
            lambda: batch_update_stations.delay(
                latitude=athens_lat,
                longitude=athens_lon,
                radius=athens_radius,
                city_name=athens_city_name
            ),
            IntervalTrigger(hours=5),
            id="batch_layer_update_athens",
            name="Batch station update for Athens (Batch Layer)",
            replace_existing=True
        )
        logger.info("🚀 Batch Layer (Athens) scheduler started - runs every 5 hours")
        
        scheduler.start()
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
    
    logger.info("✅ Application startup complete")
    yield
    # Shutdown
    try:
        scheduler.shutdown()
        logger.info("🛑 Scheduler stopped")
    except:
        pass
    await close_mongo_connection()
    await tomtom_service.close()
    logger.info("Application shutdown complete")

# --- Application Setup ---

# 1. Create the FastAPI instance without the lifespan context initially
fastapi_app = FastAPI(
    title=settings.app_name,
    description="API for managing EV charging stations with real-time notifications",
    version="1.0.0"
)

# Parse the comma-separated string from settings into a list of origins
origins_list = [origin.strip() for origin in settings.cors_origins.split(',')]
logger.info(f"CORS origins configured: {origins_list}")

# 2. Re-add the CORSMiddleware to the FastAPI app.
# This will handle CORS for the REST API endpoints.
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Initialize Socket.IO server WITH its OWN CORS enabled.
# This will handle CORS for WebSocket transport requests.
mgr = socketio.AsyncRedisManager(settings.redis_url)
sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=mgr,
    cors_allowed_origins=origins_list
)

# 4. Wrap the FastAPI app with the Socket.IO app.
# This makes Socket.IO the main entry point.
socket_io_app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# 5. Add the lifespan context manager to the main wrapped app
# This ensures startup/shutdown events still run for the FastAPI part.
fastapi_app.router.lifespan_context = lifespan

# 6. Include API routers on the FastAPI instance
fastapi_app.include_router(stations.router, prefix="/api/stations", tags=["stations"])
fastapi_app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])


# --- Socket.IO Event Handlers ---

@sio.event
async def connect(sid, environ):
    logger.info(f'Client connected: {sid}')
    # Log the received headers for debugging
    logger.debug(f"Connection headers: {environ.get('asgi.scope', {}).get('headers', [])}")
    await sio.emit('connection_response', {'message': 'Connected to server'}, room=sid)

@sio.event
async def disconnect(sid):
    logger.info(f'Client disconnected: {sid}')

# --- Health Check Endpoints on the FastAPI instance ---

@fastapi_app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "EV Charging Stations API",
        "status": "running",
        "version": "1.0.0"
    }

@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# --- Test Endpoints on the FastAPI instance ---

@fastapi_app.get("/test/tomtom")
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

@fastapi_app.get("/test/tomtom/raw")
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

@fastapi_app.get("/test/repositories")
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

@fastapi_app.get("/test/station-operations")
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

@fastapi_app.get("/test/historical-save")
async def test_historical_save():
    from app.repositories import historical_repo
    from app.models.station import Station, StationLocation, ConnectorInfo, OperatorInfo
    from datetime import datetime
    
    test_station = Station(
        tomtom_id="test_historical_123",
        name="Test Historical Station",
        location=StationLocation(
            type="Point",
            coordinates=[23.7348, 37.9755]
        ),
        address="Test Historical Address",
        connectors=[ConnectorInfo(
            type="Type2",
            max_power_kw=22.0,
            current_type="AC",
            status="AVAILABLE"
        )],
        operator=OperatorInfo(
            name="Test Operator",
            website="https://example.com"
        ),
        status="AVAILABLE",
        access_type="PUBLIC"
    )
    
    # Προσθήκη των απαιτούμενων πεδίων για την ιστορική εγγραφή
    historical_data = test_station.dict(by_alias=True)
    historical_data['station_id'] = test_station.tomtom_id
    historical_data['status_snapshot'] = {
        "station_status": test_station.status,
        "total_connectors": len(test_station.connectors),
        "available_connectors": sum(1 for c in test_station.connectors if c.status == "AVAILABLE"),
        "occupied_connectors": sum(1 for c in test_station.connectors if c.status == "OCCUPIED"),
        "out_of_order_connectors": sum(1 for c in test_station.connectors if c.status == "OUT_OF_ORDER")
    }
    historical_data['timestamp'] = datetime.utcnow()
    
    if '_id' in historical_data:
        del historical_data['_id']
    
    saved_id = await historical_repo.save_historical_data(historical_data)
    return {
        "success": True,
        "message": "Historical data saved",
        "saved_id": str(saved_id)
    }

@fastapi_app.get("/batch/update-stations")
async def trigger_batch_update_stations(
    lat: float = 37.9755,  # Κέντρο Αθήνας
    lon: float = 23.7348,
    radius: int = 50000    # 50km εμβέλεια
):
    """Trigger batch update of stations data"""
    try:
        from app.tasks.batch_tasks import batch_update_stations
        
        logger.info(f"Triggering batch update for stations at ({lat}, {lon}) with radius {radius}m")
        
        # Trigger the Celery task asynchronously without await
        task = batch_update_stations.apply_async(args=(lat, lon, radius))
        
        return {
            "success": True,
            "message": f"Batch update task triggered for stations at ({lat}, {lon})",
            "task_id": task.id,
            "location": {"latitude": lat, "longitude": lon, "radius": radius}
        }
        
    except Exception as e:
        logger.error(f"Error triggering batch update: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error triggering batch update: {str(e)}"
        )

# --- Main execution ---
if __name__ == "__main__":
    uvicorn.run(
        "main:socket_io_app",  # Run the wrapped Socket.IO app
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )