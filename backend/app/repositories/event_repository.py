from typing import List, Optional
from datetime import datetime, timedelta
from app.repositories.base_repository import BaseRepository
from app.models.event import Event
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class EventRepository(BaseRepository[Event]):
    def __init__(self):
        # Lazy initialization
        self._collection = None
        self._model_class = Event
    
    @property
    def collection(self):
        if self._collection is None:
            from app.database.connection import get_database
            db = get_database()
            self._collection = db.events
        return self._collection
    
    @property
    def model_class(self):
        return self._model_class
    
    async def get_unprocessed_events(self, limit: int = 1000) -> List[Event]:
        """Get unprocessed events for batch processing"""
        return await self.get_many(
            {"processed": False},
            limit=limit,
            sort_by="timestamp",
            sort_order=1
        )
    
    async def mark_events_processed(self, event_ids: List[str], batch_id: str) -> int:
        """Mark multiple events as processed"""
        try:
            object_ids = [ObjectId(id) for id in event_ids]
            result = await self.collection.update_many(
                {"_id": {"$in": object_ids}},
                {
                    "$set": {
                        "processed": True,
                        "processing_batch": batch_id
                    }
                }
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"Error marking events as processed: {e}")
            raise
    
    async def get_station_events(
        self,
        station_id: str,
        event_type: Optional[str] = None,
        hours_back: int = 24
    ) -> List[Event]:
        """Get events for a specific station"""
        since = datetime.utcnow() - timedelta(hours=hours_back)
        filter_dict = {
            "station_id": station_id,
            "timestamp": {"$gte": since}
        }
        
        if event_type:
            filter_dict["event_type"] = event_type
        
        return await self.get_many(
            filter_dict,
            sort_by="timestamp",
            sort_order=-1
        )
    
    async def create_station_status_change_event(
        self,
        station_id: str,
        old_status: str,
        new_status: str,
        connector_id: str = "",
        **kwargs
    ) -> Event:
        """Create a station status change event"""
        # Always ensure connector_id is a string
        if connector_id is None:
            connector_id = ""
        event = Event(
            event_type="STATION_STATUS_CHANGE",
            station_id=station_id,
            old_status=old_status,
            new_status=new_status,
            connector_id=connector_id,
            **kwargs
        )
        return await self.create(event)

# Singleton instance
event_repository = EventRepository() 