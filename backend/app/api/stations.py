from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.station import Station
from app.repositories.station_repository import StationRepository
from app.core.config import Settings
import logging

logger = logging.getLogger(__name__)
settings = Settings()

router = APIRouter(prefix="/api/stations", tags=["stations"])

@router.get("/", response_model=List[Station])
async def get_all_stations(
    status: Optional[str] = Query(None, description="Filter by status: AVAILABLE, BUSY, OUT_OF_ORDER"),
    limit: Optional[int] = Query(None, description="Limit number of results")
):
    """
    Get all stations with real-time availability data.
    Updated every 5 minutes by the Speed Layer.
    """
    try:
        station_repo = StationRepository()
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["status"] = status.upper()
        
        stations = station_repo.get_all_stations(filter_dict=filter_dict, limit=limit)
        
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
    Get a specific station by its ID.
    """
    try:
        station_repo = StationRepository()
        station = station_repo.get_station_by_id(station_id)
        
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
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"), 
    radius: int = Query(5000, description="Search radius in meters"),
    status: Optional[str] = Query(None, description="Filter by status: AVAILABLE, BUSY, OUT_OF_ORDER"),
    limit: Optional[int] = Query(50, description="Limit number of results")
):
    """
    Find nearby stations within specified radius.
    Uses real-time data from our database.
    """
    try:
        station_repo = StationRepository()
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["status"] = status.upper()
            
        stations = station_repo.get_nearby_stations(
            latitude=lat,
            longitude=lon,
            radius_meters=radius,
            filter_dict=filter_dict,
            limit=limit
        )
        
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
        station_repo = StationRepository()
        
        total_stations = station_repo.count_stations()
        available_stations = station_repo.count_stations({"status": "AVAILABLE"})
        busy_stations = station_repo.count_stations({"status": "BUSY"})
        out_of_order_stations = station_repo.count_stations({"status": "OUT_OF_ORDER"})
        
        return {
            "total_stations": total_stations,
            "available": available_stations,
            "busy": busy_stations,
            "out_of_order": out_of_order_stations,
            "last_updated": "Updated every 5 minutes by Speed Layer"
        }
        
    except Exception as e:
        logger.error(f"Error getting stations summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 