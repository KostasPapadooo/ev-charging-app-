from app.core.celery_config.celery_app import celery_app
from app.repositories.station_repository import StationRepository
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(
    name="app.tasks.batch_tasks.batch_update_stations",
    queue="batch_queue",
    retry_backoff=True,
    retry_jitter=True,
    retry_max_delay=300,
    max_retries=3,
    bind=True
)
def batch_update_stations(self, latitude, longitude, radius, city_name=None):
    """
    Batch update charging stations data for a specific geographic area (Batch Layer).
    
    Args:
        latitude (float): Center latitude
        longitude (float): Center longitude  
        radius (int): Search radius in meters
        city_name (str, optional): Name of the city/region
    """
    logger.info(f"Starting batch update for {city_name or 'unknown region'} at ({latitude}, {longitude}) with radius {radius}m")
    try:
        # Create a new instance of StationRepository directly in the task
        station_repo = StationRepository()
        
        # Check if station_repo is properly initialized
        if not hasattr(station_repo, 'collection') or station_repo.collection is None:
            logger.error("StationRepository failed to initialize properly in batch_update_stations task.")
            return {"status": "error", "message": "StationRepository not initialized."}
        
        # Fetch station data from TomTom API for the specified area
        # (This is a placeholder - implement actual TomTom API call)
        stations_data = fetch_stations_from_tomtom(latitude, longitude, radius)
        
        if not stations_data:
            logger.info("No station data returned from TomTom API.")
            return {"status": "success", "message": "No stations to update."}
        
        inserted_count = 0
        updated_count = 0
        
        for station_data in stations_data:
            try:
                # Check if station already exists
                existing_station = station_repo.sync_collection.find_one({"tomtom_id": station_data.get("tomtom_id")})
                
                if existing_station:
                    # Update existing station
                    result = station_repo.sync_collection.update_one(
                        {"tomtom_id": station_data.get("tomtom_id")},
                        {"$set": station_data}
                    )
                    if result.modified_count > 0:
                        updated_count += 1
                        logger.debug(f"Updated station {station_data.get('tomtom_id')}")
                else:
                    # Insert new station
                    station_data["created_at"] = datetime.utcnow()
                    result = station_repo.sync_collection.insert_one(station_data)
                    if result.inserted_id:
                        inserted_count += 1
                        logger.debug(f"Inserted new station {station_data.get('tomtom_id')}")
                        
            except Exception as e:
                logger.error(f"Error processing station {station_data.get('tomtom_id', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Batch update finished for {city_name or 'unknown region'}. Inserted: {inserted_count}, Updated: {updated_count}")
        return {"status": "success", "message": f"Inserted {inserted_count} new stations, updated {updated_count} existing stations."}
        
    except Exception as e:
        logger.error(f"Error in batch_update_stations task: {str(e)}")
        raise self.retry(exc=e)

@celery_app.task(
    name="app.tasks.batch_tasks.cleanup_old_historical_data",
    queue="batch_queue",
    retry_backoff=True,
    retry_jitter=True,
    retry_max_delay=300,
    max_retries=3,
    bind=True
)
def cleanup_old_historical_data(self, days_threshold):
    """
    Clean up old historical availability data (Batch Layer).
    This task removes historical availability records older than a specified number of days.
    
    Args:
        days_threshold (int): Number of days to keep historical data. Older records are deleted.
    """
    try:
        logger.info(f"Starting cleanup of historical data older than {days_threshold} days.")
        # Create a new instance of HistoricalStationRepository directly in the task
        from app.repositories.historical_repository import HistoricalStationRepository
        historical_repo = HistoricalStationRepository()
        
        # Delete old historical data
        # (Assuming there's a method in historical_repo to do this)
        deleted_count = historical_repo.delete_old_records(days_threshold)
        
        logger.info(f"Cleanup finished. Deleted {deleted_count} old historical records.")
        return {"status": "success", "message": f"Deleted {deleted_count} old records."}
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_historical_data task: {str(e)}")
        raise self.retry(exc=e)

# Placeholder function - replace with actual TomTom API call
def fetch_stations_from_tomtom(latitude, longitude, radius):
    """
    Placeholder function to fetch stations from TomTom API.
    Replace this with actual TomTom API call.
    """
    # For now, return empty list
    logger.info(f"Mock: Fetching stations from TomTom API for ({latitude}, {longitude}) with radius {radius}m")
    return [] 