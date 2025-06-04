from app.core.celery_config.celery_app import celery_app
from app.services.tomtom_service import tomtom_service
from app.repositories.station_repository import station_repository
from app.repositories.historical_repository import historical_repository
from app.models.station import Station
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.database.connection import get_database, connect_to_mongo

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
def batch_update_stations(self, latitude: float, longitude: float, radius: int, city_name: str = None):
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
        # Run async operations in sync context
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_async_batch_update(latitude, longitude, radius, city_name))
        return result
        
    except Exception as e:
        logger.error(f"Error in batch_update_stations task: {str(e)}")
        raise self.retry(exc=e)

async def _async_batch_update(latitude: float, longitude: float, radius: int, city_name: str = None):
    """Async implementation of batch update logic"""
    try:
        # Ensure MongoDB connection for this process
        await connect_to_mongo()
        # Initialize repositories
        await station_repository.initialize()
        await historical_repository.initialize()
        
        # Fetch stations from TomTom API
        stations = await tomtom_service.get_stations_in_area(latitude, longitude, radius)
        
        if not stations:
            logger.info("No stations returned from TomTom API")
            return {"status": "success", "message": "No stations to update", "updated": 0, "new": 0}
        
        inserted_count = 0
        updated_count = 0
        historical_saved = 0
        
        for station in stations:
            try:
                connectors = [conn.dict() for conn in station.connectors]
                status_snapshot = {
                    "station_status": map_status_for_schema(station.status),
                    "total_connectors": len(connectors),
                    "available_connectors": sum(1 for c in connectors if map_status_for_schema(c.get("status")) == "AVAILABLE"),
                    "occupied_connectors": sum(1 for c in connectors if map_status_for_schema(c.get("status")) == "OCCUPIED"),
                    "out_of_order_connectors": sum(1 for c in connectors if map_status_for_schema(c.get("status")) == "OFFLINE")
                }
                connector_details = [
                    {
                        "connector_id": str(conn.get("id", "")),
                        "type": conn.get("type", ""),
                        "status": conn.get("status", ""),
                        "power_kw": conn.get("max_power_kw", None)
                    }
                    for conn in connectors
                ]
                # Check if station exists
                existing_station = await station_repository.find_by_tomtom_id(station.tomtom_id)
                
                if existing_station:
                    # Update existing station if status changed
                    if existing_station.get('status') != station.status:
                        await station_repository.update_station_status(
                            station.tomtom_id,
                            station.status,
                            {
                                "connectors": connectors,
                                "last_updated": datetime.utcnow(),
                                "data_source": "TOMTOM"
                            }
                    )
                        updated_count += 1
                        # Save historical data
                        historical_data = {
                            "station_id": station.tomtom_id,
                            "timestamp": datetime.utcnow(),
                            "status_snapshot": status_snapshot,
                            "status": status_snapshot["station_status"],
                            "connector_details": connector_details,
                            "usage_metrics": {},
                            "weather_conditions": None,
                            "created_at": datetime.utcnow()
                        }
                        await historical_repository.save_historical_data(historical_data)
                        historical_saved += 1
                else:
                    # Insert new station
                    await station_repository.create_station(station)
                        inserted_count += 1
                    # Save initial historical data
                    historical_data = {
                        "station_id": station.tomtom_id,
                        "timestamp": datetime.utcnow(),
                        "status_snapshot": status_snapshot,
                        "status": status_snapshot["station_status"],
                        "connector_details": connector_details,
                        "usage_metrics": {},
                        "weather_conditions": None,
                        "created_at": datetime.utcnow()
                    }
                    await historical_repository.save_historical_data(historical_data)
                    historical_saved += 1
                        
            except Exception as e:
                logger.error(f"Error processing station {station.tomtom_id}: {str(e)}")
                continue
        
        logger.info(
            f"Batch update completed for {city_name or 'unknown region'}. "
            f"New: {inserted_count}, Updated: {updated_count}, Historical: {historical_saved}"
        )
        
        return {
            "status": "success",
            "message": f"Processed {len(stations)} stations",
            "new_stations": inserted_count,
            "updated_stations": updated_count,
            "historical_records": historical_saved,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius,
                "city": city_name
            }
        }
        
    except Exception as e:
        logger.error(f"Error in _async_batch_update: {str(e)}")
        raise

@celery_app.task(
    name="app.tasks.batch_tasks.cleanup_old_historical_data",
    queue="batch_queue",
    retry_backoff=True,
    retry_jitter=True,
    retry_max_delay=300,
    max_retries=3,
    bind=True
)
def cleanup_old_historical_data(self, days_threshold: int = 30):
    """
    Clean up old historical availability data (Batch Layer).
    
    Args:
        days_threshold (int): Number of days to keep historical data. Older records are deleted.
    """
    try:
        logger.info(f"Starting cleanup of historical data older than {days_threshold} days")
        
        # Run async operations in sync context
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_async_cleanup_historical(days_threshold))
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_historical_data task: {str(e)}")
        raise self.retry(exc=e)

async def _async_cleanup_historical(days_threshold: int):
    """Async implementation of historical data cleanup"""
    try:
        # Ensure MongoDB connection for this process
        await connect_to_mongo()
        # Initialize repository
        await historical_repository.initialize()
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        # Delete old records
        deleted_count = await historical_repository.delete_old_records(cutoff_date)
        
        logger.info(f"Successfully deleted {deleted_count} historical records older than {days_threshold} days")
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} old records",
            "days_threshold": days_threshold,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in _async_cleanup_historical: {str(e)}")
        raise

def map_status_for_schema(status):
    if status == "OUT_OF_ORDER":
        return "OFFLINE"
    if status in ("BUSY", "OCCUPIED"):
        return "OCCUPIED"
    if status == "AVAILABLE":
        return "AVAILABLE"
    if status == "MAINTENANCE":
        return "MAINTENANCE"
    return "OFFLINE" 