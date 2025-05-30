from typing import List, Optional
from datetime import datetime, timedelta
from app.database.connection import get_database
from app.models.station import Station

class HistoricalStationRepository:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db["historical_stations"]
    
    async def save_historical_data(self, station: Station) -> str:
        """Save historical data for a station"""
        station_dict = station.dict(by_alias=True)
        station_dict["timestamp"] = datetime.utcnow()
        result = await self.collection.insert_one(station_dict)
        return str(result.inserted_id)
    
    async def save_historical_batch(self, stations: List[Station]) -> int:
        """Save historical data for multiple stations"""
        if not stations:
            return 0
            
        documents = []
        timestamp = datetime.utcnow()
        for station in stations:
            doc = station.dict(by_alias=True)
            doc["timestamp"] = timestamp
            documents.append(doc)
            
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