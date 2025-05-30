from typing import List, Optional, Dict, Any
from pymongo import ASCENDING, DESCENDING, GEOSPHERE
import pymongo
from app.repositories.base_repository import BaseRepository
from app.models.station import Station, StationLocation
from datetime import datetime
import logging
from app.database.connection import get_database

logger = logging.getLogger(__name__)

class StationRepository(BaseRepository[Station]):
    def __init__(self):
        # Lazy initialization
        self._collection = None
        self._model_class = Station
        self.db = get_database()
        self.collection = self.db["current_stations"]
        # Δημιουργία geospatial index για location-based queries
        self.collection.create_index([("location", GEOSPHERE)])
    
    @property
    def collection(self):
        if self._collection is None:
            from app.database.connection import get_database
            db = get_database()
            self._collection = db.current_stations
        return self._collection
    
    @property
    def model_class(self):
        return self._model_class
    
    async def get_stations_by_location(
        self, 
        longitude: float, 
        latitude: float, 
        radius_meters: int = 5000,
        limit: int = 50
    ) -> List[Station]:
        """Get stations within radius of a location using geospatial query"""
        try:
            query = {
                "location": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [longitude, latitude]
                        },
                        "$maxDistance": radius_meters
                    }
                }
            }
            
            cursor = self.collection.find(query).limit(limit)
            docs = await cursor.to_list(length=limit)
            
            return [self.model_class(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error getting stations by location: {e}")
            raise
    
    async def bulk_upsert_stations(self, stations: List[Station]) -> Dict[str, Any]:
        """Bulk upsert stations to database"""
        if not stations:
            return {"upserted": 0, "modified": 0}
        
        try:
            operations = []
            for station in stations:
                # Χρησιμοποιούμε το Pydantic serialization
                station_dict = station.model_dump(exclude={"id"}, mode="json")
                
                # Σωστό MongoDB operation format
                operation = pymongo.ReplaceOne(
                    filter={"tomtom_id": station.tomtom_id},
                    replacement=station_dict,
                    upsert=True
                )
                operations.append(operation)
            
            # Execute bulk operation
            result = await self.collection.bulk_write(operations)
            
            return {
                "upserted": result.upserted_count,
                "modified": result.modified_count,
                "matched": result.matched_count
            }
        
        except Exception as e:
            logger.error(f"Error in bulk upsert: {e}")
            raise
    
    async def get_by_tomtom_id(self, tomtom_id: str) -> Optional[Station]:
        """Get station by TomTom ID"""
        try:
            doc = await self.collection.find_one({"tomtom_id": tomtom_id})
            if doc:
                return self.model_class(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting station by tomtom_id {tomtom_id}: {e}")
            raise
    
    async def get_stations_by_status(self, status: str) -> List[Station]:
        """Get stations by status"""
        return await self.get_many({"status": status})
    
    async def get_stations_by_operator(self, operator_name: str) -> List[Station]:
        """Get stations by operator"""
        return await self.get_many({"operator.name": operator_name})
    
    async def update_station_status(self, tomtom_id: str, new_status: str) -> Optional[Station]:
        """Update station status"""
        try:
            result = await self.collection.find_one_and_update(
                {"tomtom_id": tomtom_id},
                {
                    "$set": {
                        "status": new_status,
                        "last_updated": datetime.utcnow()
                    }
                },
                return_document=True
            )
            
            if result:
                return self.model_class(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating station status: {e}")
            raise

    async def upsert_station(self, station: Station) -> str:
        """Upsert a station based on tomtom_id"""
        station_dict = station.dict(by_alias=True)
        result = await self.collection.update_one(
            {"tomtom_id": station.tomtom_id},
            {"$set": station_dict},
            upsert=True
        )
        return station.tomtom_id
    
    async def upsert_stations_batch(self, stations: List[Station]) -> dict:
        """Upsert multiple stations at once"""
        if not stations:
            return {"matched": 0, "modified": 0, "upserted": 0}
            
        operations = [
            {
                "updateOne": {
                    "filter": {"tomtom_id": station.tomtom_id},
                    "update": {"$set": station.dict(by_alias=True)},
                    "upsert": True
                }
            }
            for station in stations
        ]
        
        result = await self.collection.bulk_write(operations)
        return {
            "matched": result.matched_count,
            "modified": result.modified_count,
            "upserted": result.upserted_count
        }
    
    async def get_station_by_id(self, tomtom_id: str) -> Optional[Station]:
        """Get a station by its TomTom ID"""
        station_data = await self.collection.find_one({"tomtom_id": tomtom_id})
        if station_data:
            return Station(**station_data)
        return None
    
    async def get_nearby_stations(
        self, 
        latitude: float, 
        longitude: float, 
        radius_meters: float, 
        limit: int = 10
    ) -> List[Station]:
        """Get nearby stations within radius sorted by distance"""
        stations_data = await self.collection.find({
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude]
                    },
                    "$maxDistance": radius_meters
                }
            }
        }).limit(limit).to_list(length=limit)
        
        return [Station(**data) for data in stations_data]
    
    async def get_stations_count(self) -> int:
        """Get total count of stations"""
        return await self.collection.count_documents({})
    
    async def delete_station(self, tomtom_id: str) -> bool:
        """Delete a station by TomTom ID"""
        result = await self.collection.delete_one({"tomtom_id": tomtom_id})
        return result.deleted_count > 0

# Singleton instance
station_repository = StationRepository() 