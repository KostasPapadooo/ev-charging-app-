import logging
from datetime import datetime
from typing import List
import asyncio

from app.core.celery_config import celery_app
from app.services.tomtom_service import tomtom_service
from app.repositories import station_repo, historical_repo
from app.models.station import Station
from app.database.connection import get_database
from app.repositories.station_repository import StationRepository
from app.repositories.historical_repository import HistoricalStationRepository
from app.core.config import settings  # Προσθήκη για να πάρουμε τη MongoDB URL
import motor.motor_asyncio  # Προσθήκη για χειροκίνητη σύνδεση

logger = logging.getLogger(__name__)

# Αρχικοποίηση της σύνδεσης με τη βάση δεδομένων
def init_database():
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        logger.info("Database connection initialized manually")
        return db
    except Exception as e:
        logger.error(f"Error initializing database connection: {str(e)}")
        raise

# Αρχικοποίηση των repositories αν δεν είναι ήδη αρχικοποιημένα
def init_repositories():
    global station_repo, historical_repo
    if station_repo is None:
        logger.info("Initializing station repository")
        station_repo = StationRepository()
    if historical_repo is None:
        logger.info("Initializing historical repository")
        historical_repo = HistoricalStationRepository()

@celery_app.task(
    name='app.tasks.batch_tasks.batch_update_stations',
    retry_backoff=True,
    retry_jitter=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff_max=600,
)
def batch_update_stations(latitude: float, longitude: float, radius: int) -> dict:
    """
    Batch update stations from TomTom API for a given location and radius.
    This task fetches station data, upserts it to current_stations collection,
    and saves historical data to historical_stations collection.
    
    Args:
        latitude (float): Latitude of the center point for search
        longitude (float): Longitude of the center point for search
        radius (int): Search radius in meters
        
    Returns:
        dict: Summary of the batch operation
    """
    try:
        logger.info(f"Starting batch update for stations at ({latitude}, {longitude}) with radius {radius}m")
        
        # Αρχικοποίηση των repositories πριν από τη χρήση
        init_repositories()
        
        # Fetch stations from TomTom API using synchronous method
        stations: List[Station] = tomtom_service.search_charging_stations_sync(
            latitude=latitude,
            longitude=longitude,
            radius=radius
        )
        
        logger.info(f"Fetched {len(stations)} stations from TomTom API")
        
        # Upsert stations to current_stations collection using synchronous method
        upsert_result = station_repo.upsert_stations_batch_sync(stations)
        logger.info(f"Upserted stations to current_stations: {upsert_result}")
        
        # Prepare historical data with status snapshot
        historical_data = []
        for station in stations:
            station_dict = station.dict(by_alias=True)
            station_dict['station_id'] = station.tomtom_id
            station_dict['status_snapshot'] = {
                "station_status": station.status,
                "total_connectors": len(station.connectors),
                "available_connectors": sum(1 for c in station.connectors if c.status == "AVAILABLE"),
                "occupied_connectors": sum(1 for c in station.connectors if c.status == "OCCUPIED"),
                "out_of_order_connectors": sum(1 for c in station.connectors if c.status == "OUT_OF_ORDER")
            }
            station_dict['timestamp'] = datetime.utcnow()
            if '_id' in station_dict:
                del station_dict['_id']
            historical_data.append(station_dict)
        
        # Save to historical_stations collection using synchronous method
        historical_count = historical_repo.save_historical_batch_sync(historical_data)
        logger.info(f"Saved {historical_count} records to historical_stations")
        
        return {
            "status": "success",
            "message": f"Batch update completed for {len(stations)} stations",
            "location": {"latitude": latitude, "longitude": longitude, "radius": radius},
            "upsert_result": upsert_result,
            "historical_records_saved": historical_count
        }
        
    except Exception as e:
        logger.error(f"Error in batch_update_stations: {str(e)}")
        raise 

@celery_app.task(name='app.tasks.batch_tasks.cleanup_old_historical_data')
def cleanup_old_historical_data_task(days_to_keep: int = 30):
    logger.info(f"Starting cleanup of historical data older than {days_to_keep} days.")
    try:
        init_repositories() # Διασφαλίζει ότι τα repositories είναι αρχικοποιημένα

        # Η μέθοδος cleanup_old_data στο HistoricalStationRepository είναι async.
        # Την καλούμε από ένα σύγχρονο Celery task χρησιμοποιώντας asyncio.run().
        # Σημείωση: Σε πιο σύνθετα σενάρια, ίσως χρειαστεί διαφορετική διαχείριση του event loop.
        # Για την τρέχουσα δομή, αυτό είναι το πιο άμεσο.
        # Μια εναλλακτική θα ήταν να υπάρχει μια σύγχρονη μέθοδος cleanup_old_data_sync στο repository.
        if historical_repo:
            deleted_count = asyncio.run(historical_repo.cleanup_old_data(days_to_keep))
            logger.info(f"Cleanup complete. Deleted {deleted_count} old historical records.")
            return {"status": "success", "deleted_count": deleted_count}
        else:
            logger.error("Historical repository not initialized during cleanup task.")
            return {"status": "error", "message": "Historical repository not initialized"}
    except Exception as e:
        logger.error(f"Error during historical data cleanup: {str(e)}")
        raise # Επιτρέπει στη Celery να δει το task ως αποτυχημένο και να εφαρμόσει retries αν υπάρχουν 