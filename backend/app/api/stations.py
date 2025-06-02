from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.station import Station
from app.repositories.station_repository import station_repository  # Use singleton
from app.core.config import Settings
import logging

logger = logging.getLogger(__name__)
settings = Settings()

# Remove prefix from router - it's added in main.py
router = APIRouter(tags=["stations"])

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
async def get_nearby_stations(
    lat: float,                    # Remove Query() for direct calls
    lon: float,                    # Remove Query() for direct calls
    radius: int = 5000,            # Remove Query() for direct calls
    status: Optional[str] = None,  # Remove Query() for direct calls
    limit: Optional[int] = 50      # Remove Query() for direct calls
):
    """
    Find nearby stations within specified radius.
    Uses geospatial indexing for fast queries.
    """
    try:
        # Use correct method signature
        stations = await station_repository.find_nearby_stations(
            longitude=lon,  # Note: longitude first in MongoDB
            latitude=lat,
            max_distance_meters=radius
        )
        
        # Apply status filter if provided
        if status is not None:
            stations = [s for s in stations if s.status.upper() == status.upper()]
        
        # Apply limit if provided
        if limit is not None:
            stations = stations[:limit]
        
        logger.info(f"Found {len(stations)} nearby stations within {radius}m of ({lat}, {lon})")
        return {
            "stations": stations,
            "search_params": {
                "latitude": lat,
                "longitude": lon,
                "radius_meters": radius,
                "status_filter": status,
                "total_found": len(stations)
            }
        }
        
    except Exception as e:
        logger.error(f"Error finding nearby stations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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