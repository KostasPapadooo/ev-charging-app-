from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.station import Station
import pymongo
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class HistoricalStationRepository:
    def __init__(self):
        # Δημιουργία σύνδεσης απευθείας, χωρίς χρήση get_database()
        logger.info("Creating database connection for HistoricalStationRepository")
        try:
            import motor.motor_asyncio
            client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
            self.db = client[settings.database_name]
        except Exception as e:
            logger.error(f"Error creating database connection: {str(e)}")
            raise
        self.collection = self.db["historical_stations"]
        # Προσθήκη σύγχρονου client για pymongo
        self.sync_db = pymongo.MongoClient(settings.mongodb_url)
        self.sync_collection = self.sync_db[settings.database_name]["historical_stations"]
    
    async def save_historical_data(self, data: dict) -> str:
        """Save historical data for a station"""
        data["timestamp"] = datetime.utcnow()
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)
    
    async def save_historical_batch(self, data: List[dict]) -> int:
        """Save historical data for multiple stations"""
        if not data:
            return 0
            
        documents = data.copy()  # Create a copy to avoid modifying the original data
        timestamp = datetime.utcnow()
        for doc in documents:
            doc["timestamp"] = timestamp
            
        result = await self.collection.insert_many(documents)
        return len(result.inserted_ids)
    
    async def get_station_history(
        self, 
        tomtom_id: str, 
        start_date: datetime, 
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get historical data for a specific station"""
        if end_date is None:
            end_date = datetime.utcnow()
            
        query = {
            "tomtom_id": tomtom_id,
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        data = await self.collection.find(query).sort("timestamp", 1).to_list(length=1000)
        return data
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Remove historical data older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        result = await self.collection.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        return result.deleted_count
    
    def save_historical_batch_sync(self, historical_data: List[Dict[str, Any]]) -> int:
        """Save a batch of historical data to the database (synchronous)"""
        try:
            if not historical_data:
                return 0
            result = self.sync_collection.insert_many(historical_data, ordered=False)
            return len(result.inserted_ids)
        except Exception as e:
            logger.error(f"Error saving historical batch (sync): {e}")
            raise 