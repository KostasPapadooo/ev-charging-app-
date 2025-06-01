from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.opencharge_service import OpenChargeMapService
from backend.models.station import Station

router = APIRouter()

@router.get("/stations", response_model=List[Station])
async def get_stations(lat: float, lon: float, radius: int = 5000):
    """Get charging stations in a specific area"""
    try:
        stations = await opencharge_service.get_stations_in_area(lat, lon, radius)
        return stations
    except Exception as e:
        logger.error(f"Error fetching stations: {e}")
        raise HTTPException(status_code=500, detail="Error fetching stations")
