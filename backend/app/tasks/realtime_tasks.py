from app.core.celery_config.celery_app import celery_app
import logging
from datetime import datetime
from app.core.config import Settings
from pymongo import MongoClient
import os

logger = logging.getLogger(__name__)

@celery_app.task(
    name="app.tasks.realtime_tasks.poll_station_availability_new_version",
    queue="realtime_queue",
    retry_backoff=True,
    retry_jitter=True,
    retry_max_delay=300,
    max_retries=3,
    bind=True
)
def poll_station_availability_new_version(self):
    """
    Periodically poll the availability of charging stations in real-time (Speed Layer).
    This task fetches the latest availability data for all stations and updates the database if there are changes.
    """
    try:
        logger.info("Starting real-time availability poll for stations.")
        logger.info("NEW CODE VERSION: Using direct MongoClient without repositories.")
        logger.info(f"Executing code from file: {os.path.abspath(__file__)}")
        
        # Load settings
        settings = Settings()
        
        # Use synchronous MongoClient for database operations
        client = MongoClient(settings.mongodb_url)
        db = client[settings.database_name]
        stations_collection = db["current_stations"]
        historical_collection = db["historical_station_availability"]
        
        # Get all stations to check their availability
        stations = list(stations_collection.find())
        if not stations:
            logger.info("No stations found to check for availability.")
            client.close()
            return {"status": "success", "message": "No stations to check."}
        
        logger.info(f"Found {len(stations)} stations to check for availability.")
        updated_count = 0
        
        for station in stations:
            tomtom_id = station.get("tomtom_id")
            if not tomtom_id:
                logger.warning(f"Station missing TomTom ID. Skipping: {station}")
                continue
            
            try:
                # Fetch real-time availability for this station
                # (Assuming there's a method to do this; replace with actual API call)
                availability_data = fetch_station_availability(tomtom_id)
                if not availability_data:
                    logger.warning(f"No availability data returned for station {tomtom_id}. Skipping.")
                    continue
                
                # Extract relevant information (adjust based on actual API response structure)
                current_status = availability_data.get("status", "unknown")
                last_updated = availability_data.get("last_updated", datetime.utcnow().isoformat())
                
                # Check if the status has changed since the last update
                if station.get("status") != current_status:
                    # Update the station's availability in the database
                    stations_collection.update_one(
                        {"tomtom_id": tomtom_id},
                        {"$set": {
                            "status": current_status,
                            "last_updated": last_updated
                        }}
                    )
                    
                    # Record the availability change in historical data
                    historical_collection.insert_one({
                        "tomtom_id": tomtom_id,
                        "status": current_status,
                        "timestamp": last_updated
                    })
                    
                    logger.info(f"Updated availability for station {tomtom_id} to '{current_status}'.")
                    updated_count += 1
                else:
                    logger.debug(f"Station {tomtom_id}: Status unchanged ('{current_status}').")
            
            except Exception as e:
                logger.error(f"Error updating availability for station {tomtom_id}: {str(e)}")
                continue
        
        logger.info(f"Real-time availability poll finished. Checked: {len(stations)} stations. Updated: {updated_count} stations.")
        client.close()
        return {"status": "success", "message": f"Checked {len(stations)} stations, updated {updated_count}."}
    
    except Exception as e:
        logger.error(f"Error in poll_station_availability task: {str(e)}")
        raise self.retry(exc=e)

# Placeholder function - replace with actual TomTom API call
def fetch_station_availability(tomtom_id):
    """
    Placeholder function to fetch station availability.
    Replace this with actual TomTom API call.
    """
    # For now, return mock data
    import random
    statuses = ["AVAILABLE", "BUSY", "OUT_OF_ORDER"]
    return {
        "status": random.choice(statuses),
        "last_updated": datetime.utcnow().isoformat()
    } 