from typing import List, Optional, Dict, Any
from pymongo import ASCENDING, DESCENDING, GEOSPHERE
import pymongo
from app.repositories.base_repository import BaseRepository
from app.models.station import Station, StationLocation, ConnectorInfo
from datetime import datetime
import logging
from app.core.config import Settings
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)
settings = Settings()

class StationRepository(BaseRepository[Station]):
    def __init__(self):
        # Create direct connection for repository
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.client[settings.database_name]
        collection = self.db.current_stations
        
        super().__init__(collection, Station)
        
        # Create indexes (async, will be called later)
        self._indexes_created = False
        
    async def _ensure_indexes(self):
        """Ensure required indexes exist"""
        if self._indexes_created:
            return
            
        try:
            # Create geospatial index for location-based queries
            await self.collection.create_index([("location", GEOSPHERE)])
            # Create index for tomtom_id for fast lookups
            await self.collection.create_index("tomtom_id", unique=True)
            self._indexes_created = True
            logger.info("Indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation failed (may already exist): {e}")

    async def get_all_stations(
        self, 
        filter_dict: Optional[Dict[str, Any]] = None, 
        limit: Optional[int] = None
    ) -> List[Station]:
        """Get all stations with optional filtering"""
        try:
            await self._ensure_indexes()  # Ensure indexes on first use
            
            query = filter_dict or {}
            cursor = self.collection.find(query)
            
            if limit:
                cursor = cursor.limit(limit)
                
            documents = await cursor.to_list(length=None)
            return [Station(**doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Error getting stations: {e}")
            return []

    async def get_station_by_id(self, tomtom_id: str) -> Optional[Station]:
        """Get station by TomTom ID"""
        try:
            await self._ensure_indexes()
            doc = await self.collection.find_one({"tomtom_id": tomtom_id})
            return Station(**doc) if doc else None
        except Exception as e:
            logger.error(f"Error getting station {tomtom_id}: {e}")
            return None

    async def create_station(self, station: Station) -> Optional[Station]:
        """Create new station"""
        try:
            await self._ensure_indexes()
            station_dict = station.model_dump(exclude={"id"})
            station_dict["created_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(station_dict)
            if result.inserted_id:
                return await self.get_station_by_id(station.tomtom_id)
            return None
        except Exception as e:
            logger.error(f"Error creating station: {e}")
            return None

    async def update_station(self, tomtom_id: str, update_data: Dict[str, Any]) -> Optional[Station]:
        """Update station by TomTom ID"""
        try:
            await self._ensure_indexes()
            update_data["last_updated"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"tomtom_id": tomtom_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_station_by_id(tomtom_id)
            return None
        except Exception as e:
            logger.error(f"Error updating station {tomtom_id}: {e}")
            return None

    async def find_nearby_stations(
        self, 
        longitude: float, 
        latitude: float, 
        max_distance_meters: int = 5000
    ) -> List[Station]:
        """Find stations near given coordinates"""
        try:
            await self._ensure_indexes()
            query = {
                "location": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [longitude, latitude]
                        },
                        "$maxDistance": max_distance_meters
                    }
                }
            }
            
            cursor = self.collection.find(query)
            documents = await cursor.to_list(length=None)
            return [Station(**doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Error finding nearby stations: {e}")
            return []

    async def get_stations_by_status(self, status: str) -> List[Station]:
        """Get stations by status"""
        return await self.get_all_stations(filter_dict={"status": status.upper()})

    async def bulk_update_stations(self, stations: List[Station]) -> int:
        """Bulk update multiple stations"""
        try:
            await self._ensure_indexes()
            operations = []
            for station in stations:
                operations.append({
                    "updateOne": {
                        "filter": {"tomtom_id": station.tomtom_id},
                        "update": {
                            "$set": {
                                **station.model_dump(exclude={"id", "created_at"}),
                                "last_updated": datetime.utcnow()
                            }
                        },
                        "upsert": True
                    }
                })
            
            if operations:
                result = await self.collection.bulk_write(operations)
                return result.modified_count + result.upserted_count
            return 0
            
        except Exception as e:
            logger.error(f"Error bulk updating stations: {e}")
            return 0

# Create singleton instance
station_repository = StationRepository() 