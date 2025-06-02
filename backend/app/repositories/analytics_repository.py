from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from app.database.connection import get_database

logger = logging.getLogger(__name__)

class AnalyticsRepository:
    def __init__(self):
        self.db = None
        self.collection: AsyncIOMotorCollection = None
        
    async def initialize(self):
        """Initialize repository with database connection"""
        self.db = get_database()
        self.collection = self.db.analytics
        await self._ensure_indexes()
        
    async def _ensure_indexes(self):
        """Ensure indexes for analytics queries"""
        try:
            # Index for event type and timestamp
            await self.collection.create_index([
                ("event_type", 1),
                ("timestamp", -1)
            ])
            
            # Geospatial index for location-based analytics
            await self.collection.create_index([("location.coordinates", "2dsphere")])
            
            # TTL index to automatically clean old analytics data (30 days)
            await self.collection.create_index(
                "timestamp", 
                expireAfterSeconds=30 * 24 * 60 * 60  # 30 days
            )
            
            logger.info("Analytics indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating analytics indexes: {e}")

    async def log_event(self, event_data: Dict[str, Any]) -> bool:
        """Log analytics event"""
        try:
            event_doc = {
                **event_data,
                "timestamp": datetime.utcnow()
            }
            
            await self.collection.insert_one(event_doc)
            return True
            
        except Exception as e:
            logger.error(f"Error logging analytics event: {e}")
            return False

    async def get_popular_locations(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most searched locations in the last N days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "event_type": "location_search",
                        "timestamp": {"$gte": cutoff_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "lat": {"$round": ["$location.lat", 3]},  # Round to ~100m precision
                            "lon": {"$round": ["$location.lon", 3]}
                        },
                        "search_count": {"$sum": 1},
                        "avg_results": {"$avg": "$results_count"},
                        "last_search": {"$max": "$timestamp"}
                    }
                },
                {
                    "$sort": {"search_count": -1}
                },
                {
                    "$limit": limit
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=limit)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting popular locations: {e}")
            return []

    async def log_search_event(self, user_id: str, search_params: Dict[str, Any], results_count: int):
        """Log a search event with proper validation"""
        try:
            from datetime import datetime
            
            event_data = {
                "station_id": "search_event",  # Add required field
                "date": datetime.utcnow(),     # Add required field
                "user_id": user_id,
                "event_type": "station_search",
                "search_params": search_params,
                "results_count": results_count,
                "timestamp": datetime.utcnow(),
                "metrics": {                   # Add required field
                    "results_count": results_count,
                    "search_radius": search_params.get("radius", 0),
                    "search_lat": search_params.get("lat", 0),
                    "search_lon": search_params.get("lon", 0)
                },
                "computed_at": datetime.utcnow()  # Add required field
            }
            
            await self.collection.insert_one(event_data)
            logger.info(f"Search event logged for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error logging search event: {e}")

# Global repository instance
analytics_repository = AnalyticsRepository() 