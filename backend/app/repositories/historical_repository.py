from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.station import Station
import pymongo
from app.core.config import settings
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
from app.database.connection import get_database

logger = logging.getLogger(__name__)

class HistoricalRepository:
    def __init__(self):
        self.db = None
        self.collection: AsyncIOMotorCollection = None

    async def initialize(self):
        """Initialize repository with database connection"""
        self.db = get_database()
        self.collection = self.db.historical_stations
        await self._ensure_indexes()
        logger.info("HistoricalRepository initialized successfully")

    async def _ensure_indexes(self):
        """Create necessary indexes for historical data"""
        try:
            # Check existing indexes
            existing_indexes = await self.collection.list_indexes().to_list(length=None)
            index_names = [idx['name'] for idx in existing_indexes]
            
            # Compound index for station_id and timestamp
            if 'station_id_1_timestamp_-1' not in index_names:
                await self.collection.create_index(
                    [("station_id", 1), ("timestamp", -1)],
                    background=True
                )
                logger.info("Created station_id and timestamp compound index")
            
            # TTL index for automatic data cleanup
            if 'timestamp_ttl' not in index_names:
                await self.collection.create_index(
                    "timestamp",
                    expireAfterSeconds=90 * 24 * 60 * 60,  # 90 days
                    name="timestamp_ttl",
                    background=True
                )
                logger.info("Created TTL index for automatic cleanup")
            
            # Index for status queries
            if 'status_1_timestamp_-1' not in index_names:
                await self.collection.create_index(
                    [("status", 1), ("timestamp", -1)],
                    background=True
                )
                logger.info("Created status and timestamp compound index")
            
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")
            raise
    
    async def save_historical_data(self, data: Dict[str, Any]) -> str:
        """Save historical station data"""
        try:
            # Ensure required fields
            if not all(k in data for k in ["station_id", "timestamp", "status"]):
                raise ValueError("Missing required fields in historical data")
            result = await self.collection.insert_one(data)
            logger.debug(f"Saved historical data for station {data['station_id']}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving historical data: {e}")
            raise
    
    async def get_station_history(
        self, 
        station_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific station"""
        try:
            query = {"station_id": station_id}
            
            if start_date or end_date:
                query["timestamp"] = {}
                if start_date:
                    query["timestamp"]["$gte"] = start_date
                if end_date:
                    query["timestamp"]["$lte"] = end_date
            
            cursor = self.collection.find(query)\
                .sort("timestamp", -1)\
                .limit(limit)
            
            history = await cursor.to_list(length=limit)
            return history
            
        except Exception as e:
            logger.error(f"Error getting station history: {e}")
            return []

    async def get_status_changes(
        self,
        station_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get status change history for a station"""
        try:
            pipeline = [
                {
                    "$match": {
                        "station_id": station_id,
                        "timestamp": {
                            "$gte": start_date,
                            "$lte": end_date
                        }
                    }
                },
                {
                    "$sort": {"timestamp": 1}
                },
                {
                    "$group": {
                        "_id": "$station_id",
                        "changes": {
                            "$push": {
                                "status": "$status",
                                "timestamp": "$timestamp"
                            }
                        }
                    }
                }
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=1)
            return result[0]["changes"] if result else []
            
        except Exception as e:
            logger.error(f"Error getting status changes: {e}")
            return []

    async def get_availability_stats(
        self,
        station_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get availability statistics for a station"""
        try:
            pipeline = [
                {
                    "$match": {
                        "station_id": station_id,
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
                },
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "total_duration_minutes": {
                            "$sum": {
                                "$divide": [
                                    {"$subtract": [
                                        {"$ifNull": ["$next_timestamp", end_date]},
                                        "$timestamp"
                                    ]},
                                    60000  # Convert ms to minutes
                                ]
                            }
                        }
                    }
                }
            ]
            
            results = await self.collection.aggregate(pipeline).to_list(length=None)
            
            stats = {
                "total_records": sum(r["count"] for r in results),
                "status_distribution": {
                    r["_id"]: {
                        "count": r["count"],
                        "duration_minutes": round(r["total_duration_minutes"], 2)
                    } for r in results
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting availability stats: {e}")
            return {"total_records": 0, "status_distribution": {}}
    
    async def delete_old_records(self, cutoff_date: datetime) -> int:
        """Delete historical records older than cutoff date"""
        try:
            result = await self.collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            deleted_count = result.deleted_count
            logger.info(f"Deleted {deleted_count} historical records older than {cutoff_date}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting old records: {e}")
            return 0

# Global instance
historical_repository = HistoricalRepository() 