from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models.station import Station
from app.repositories.station_repository import station_repository  # Use singleton
from app.core.config import Settings
from app.services.tomtom_service import tomtom_service
from app.core.exceptions import TomTomAPIException
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
settings = Settings()

# Remove prefix from router - it's added in main.py
router = APIRouter(tags=["stations"])

# Minimum stations threshold - if we have fewer, call TomTom API
MIN_STATIONS_THRESHOLD = 5

@router.get("/", response_model=List[Station])
async def get_all_stations(
    status: Optional[str] = None,  # Remove Query() for direct calls
    limit: Optional[int] = None    # Remove Query() for direct calls
):
    """
    Get all stations with real-time availability data.
    Updated every 30 minutes by the Batch Layer.
    """
    try:
        # Build filter
        filter_dict = {}
        if status is not None:
            filter_dict["status"] = status.upper()
        
        # Use async call with await
        stations = await station_repository.get_all_stations(filter_dict=filter_dict, limit=limit)
        
        if not stations:
            return []
            
        logger.info(f"Retrieved {len(stations)} stations with filter: {filter_dict}")
        return stations
        
    except Exception as e:
        logger.error(f"Error retrieving stations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{station_id}", response_model=Station)
async def get_station_by_id(station_id: str):
    """
    Get a specific station by its TomTom ID.
    """
    try:
        # Use async call with await
        station = await station_repository.get_station_by_id(station_id)
        
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")
            
        logger.info(f"Retrieved station: {station_id}")
        return station
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving station {station_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/nearby/search")
async def search_nearby_stations_enhanced(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"), 
    radius: int = Query(5000, description="Search radius in meters"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(150, description="Maximum number of results")
):
    """
    Enhanced nearby search with TomTom API integration
    - First searches local database
    - If insufficient results, calls TomTom API
    - Caches new results for future use
    """
    try:
        logger.info(f"Enhanced nearby search for ({lat}, {lon}) with radius {radius}m")
        
        # Step 1: Search existing database
        local_stations = await station_repository.find_nearby_stations(
            lat=lat,
            lon=lon, 
            radius_meters=radius,
            status_filter=status,
            limit=limit
        )
        
        logger.info(f"Found {len(local_stations)} stations in local database within {radius}m")
        
        # Step 2: If insufficient results, call TomTom API
        if len(local_stations) < MIN_STATIONS_THRESHOLD:
            logger.info(f"Insufficient local stations ({len(local_stations)} < {MIN_STATIONS_THRESHOLD}), calling TomTom API")
            
            try:
                # Get fresh data from TomTom
                tomtom_stations = await tomtom_service.get_stations_in_area(lat, lon, radius)
                logger.info(f"Retrieved {len(tomtom_stations)} stations from TomTom API")
                
                # Step 3: Cache new stations in database
                if tomtom_stations:
                    cached_count = await cache_tomtom_stations(tomtom_stations)
                    logger.info(f"Cached {cached_count} new stations")
                    
                    # Step 4: Re-search with updated database
                    updated_stations = await station_repository.find_nearby_stations(
                        lat=lat,
                        lon=lon,
                        radius_meters=radius, 
                        status_filter=status,
                        limit=limit
                    )
                    
                    # Log analytics event
                    await log_location_search(lat, lon, radius, len(updated_stations), "tomtom_enhanced")
                    
                    return {
                        "stations": updated_stations,
                        "search_params": {
                            "latitude": lat,
                            "longitude": lon,
                            "radius_meters": radius,
                            "status_filter": status,
                            "total_found": len(updated_stations),
                            "data_source": "local_plus_tomtom",
                            "tomtom_stations_added": len(tomtom_stations)
                        }
                    }
                    
            except TomTomAPIException as e:
                logger.warning(f"TomTom API failed: {e}, using local results only")
                # Continue with local results if TomTom fails
        
        # Step 5: Return local results (either sufficient or TomTom failed)
        await log_location_search(lat, lon, radius, len(local_stations), "local_only")
        
        return {
            "stations": local_stations,
            "search_params": {
                "latitude": lat,
                "longitude": lon, 
                "radius_meters": radius,
                "status_filter": status,
                "total_found": len(local_stations),
                "data_source": "local_database"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced nearby search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

async def cache_tomtom_stations(tomtom_stations: List[Station]) -> int:
    """Cache TomTom stations in current_stations collection"""
    cached_count = 0
    
    for station in tomtom_stations:
        try:
            # Check if station already exists
            existing = await station_repository.find_by_tomtom_id(station.tomtom_id)
            
            if not existing:
                # Add new station
                await station_repository.create_station(station)
                cached_count += 1
                logger.debug(f"Cached new station: {station.name}")
            else:
                # Update existing station with fresh data
                await station_repository.update_station_status(
                    station.tomtom_id,
                    station.status,
                    {
                        "connectors": [conn.dict() for conn in station.connectors],
                        "last_updated": datetime.utcnow(),
                        "data_source": "TOMTOM"
                    }
                )
                logger.debug(f"Updated existing station: {station.name}")
                
        except Exception as e:
            logger.error(f"Failed to cache station {station.tomtom_id}: {e}")
            continue
            
    return cached_count

async def log_location_search(lat: float, lon: float, radius: int, results_count: int, search_type: str):
    """Log search analytics for optimization"""
    try:
        from app.repositories.analytics_repository import analytics_repository
        
        analytics_data = {
            "event_type": "location_search",
            "location": {
                "lat": lat,
                "lon": lon,
                "radius": radius
            },
            "results_count": results_count,
            "search_type": search_type,
            "timestamp": datetime.utcnow()
        }
        
        await analytics_repository.log_event(analytics_data)
        
    except Exception as e:
        logger.error(f"Failed to log analytics: {e}")
        # Don't fail the main request if analytics fails

@router.get("/stats/summary")
async def get_stations_summary():
    """
    Get summary statistics of all stations.
    """
    try:
        # Get all stations and calculate stats
        all_stations = await station_repository.get_all_stations()
        
        total_stations = len(all_stations)
        available_stations = len([s for s in all_stations if s.status == "AVAILABLE"])
        busy_stations = len([s for s in all_stations if s.status == "BUSY"])
        out_of_order_stations = len([s for s in all_stations if s.status == "OUT_OF_ORDER"])
        
        return {
            "total_stations": total_stations,
            "available": available_stations,
            "busy": busy_stations,
            "out_of_order": out_of_order_stations,
            "last_updated": "Updated every 30 minutes by Batch Layer"
        }
        
    except Exception as e:
        logger.error(f"Error getting stations summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 