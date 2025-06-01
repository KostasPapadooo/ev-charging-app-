from typing import List, Optional, Dict, Any
from pymongo import ASCENDING, DESCENDING, GEOSPHERE
import pymongo
from app.repositories.base_repository import BaseRepository
from app.models.station import Station, StationLocation, ConnectorInfo
from datetime import datetime
import logging
from app.core.config import settings  # Προσθήκη για να πάρουμε τη MongoDB URL

logger = logging.getLogger(__name__)

class StationRepository(BaseRepository[Station]):
    def __init__(self):
        # Lazy initialization
        self._model_class = Station
        # Δημιουργία σύνδεσης απευθείας, χωρίς χρήση get_database()
        logger.info("Creating database connection for StationRepository")
        try:
            import motor.motor_asyncio
            client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
            self.db = client[settings.database_name]
        except Exception as e:
            logger.error(f"Error creating database connection: {str(e)}")
            raise
        self._collection = self.db["current_stations"]
        # Δημιουργία geospatial index για location-based queries
        self._collection.create_index([("location", GEOSPHERE)])
        # Προσθήκη σύγχρονου client για pymongo
        self.sync_db = pymongo.MongoClient(settings.mongodb_url)  # Ρύθμιση με τη σωστή URL σύνδεσης
        self.sync_collection = self.sync_db[settings.database_name]["current_stations"]
    
    @property
    def collection(self):
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
        
        operations = []
        for station in stations:
            station_data = station.dict(by_alias=True)
            if '_id' in station_data:
                del station_data['_id']
            operation = pymongo.UpdateOne(
                filter={"tomtom_id": station.tomtom_id},
                update={"$set": station_data},
                upsert=True
            )
            operations.append(operation)
        
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

    def upsert_stations_batch_sync(self, stations: List[Station]) -> Dict[str, int]:
        """Upsert multiple stations at once (synchronous)"""
        try:
            operations = []
            for station in stations:
                station_dict = station.dict(by_alias=True)
                if '_id' in station_dict:
                    del station_dict['_id']
                operations.append(
                    pymongo.UpdateOne(
                        {"tomtom_id": station.tomtom_id},
                        {"$set": station_dict},
                        upsert=True
                    )
                )
            
            result = self.sync_collection.bulk_write(operations)
            return {
                "matched": result.matched_count,
                "modified": result.modified_count,
                "upserted": result.upserted_count
            }
        except Exception as e:
            logger.error(f"Error upserting stations batch (sync): {e}")
            raise

    async def get_station_by_tomtom_id(self, tomtom_id: str) -> Optional[Station]:
        """Get a single station by its TomTom ID"""
        station_data = await self.collection.find_one({"tomtom_id": tomtom_id})
        if station_data:
            return Station(**station_data)
        return None

    def get_station_by_tomtom_id_sync(self, tomtom_id: str) -> Optional[Station]:
        """Get a single station by its TomTom ID (synchronous)"""
        try:
            doc = self.sync_collection.find_one({"tomtom_id": tomtom_id})
            if doc:
                return self.model_class(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting station by tomtom_id {tomtom_id} (sync): {e}")
            raise

    def get_all_station_tomtom_ids_sync(self) -> List[str]:
        """Get all TomTom IDs from current stations (synchronous)"""
        try:
            stations = self.sync_collection.find({}, {"tomtom_id": 1, "_id": 0})
            return [s["tomtom_id"] for s in stations if "tomtom_id" in s]
        except Exception as e:
            logger.error(f"Error getting all station TomTom IDs (sync): {e}")
            return []

    async def get_all_stations(self, skip: int = 0, limit: int = 100) -> List[Station]:
        """Get all stations with pagination"""
        cursor = self.collection.find().skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model_class(**doc) for doc in docs]

    def upsert_station_sync(self, station: Station) -> str:
        """Upsert a station based on tomtom_id (synchronous)"""
        try:
            station_data = station.model_dump(by_alias=True, exclude_none=True)
            if '_id' in station_data: # remove internal MongoDB id if present
                del station_data['_id']
            if 'id' in station_data and station_data['id'] is None: # remove pydantic id if it's None
                 del station_data['id']


            self.sync_collection.update_one(
                {"tomtom_id": station.tomtom_id},
                {"$set": station_data},
                upsert=True
            )
            return station.tomtom_id
        except Exception as e:
            logger.error(f"Error upserting station {station.tomtom_id} (sync): {e}")
            raise
            
    def update_station_sync(self, station: Station) -> bool:
        """
        Updates an existing station in the database using its tomtom_id.
        This method assumes the station object provided contains all fields to be set.
        It does not upsert; the station must exist.
        """
        try:
            station_data = station.model_dump(by_alias=True, exclude_none=True)
            # Remove fields that should not be in $set or are immutable
            if '_id' in station_data:
                del station_data['_id']
            if 'id' in station_data and station_data['id'] is None: # Pydantic's own 'id' if not ObjectId
                del station_data['id']
            # tomtom_id is used in filter, not in $set
            if 'tomtom_id' in station_data:
                del station_data['tomtom_id']
            # created_at should generally not be updated
            if 'created_at' in station_data:
                del station_data['created_at']

            if not station_data: # Nothing to set
                logger.warning(f"No data to update for station {station.tomtom_id} after filtering fields.")
                return False

            result = self.sync_collection.update_one(
                {"tomtom_id": station.tomtom_id},
                {"$set": station_data}
            )
            if result.modified_count > 0:
                logger.info(f"Successfully updated station {station.tomtom_id} (sync).")
                return True
            elif result.matched_count > 0:
                logger.info(f"Station {station.tomtom_id} matched but no fields were modified (sync).")
                return False # No actual change in DB
            else:
                logger.warning(f"Station {station.tomtom_id} not found for update (sync).")
                return False
        except Exception as e:
            logger.error(f"Error updating station {station.tomtom_id} (sync): {e}", exc_info=True)
            raise # Re-raise the exception

# Μην αρχικοποιούμε εδώ το instance
# station_repository = StationRepository() 