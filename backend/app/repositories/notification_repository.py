from typing import List, Optional
from datetime import datetime, timedelta
from app.repositories.base_repository import BaseRepository
from app.models.notification import Notification
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class NotificationRepository(BaseRepository[Notification]):
    def __init__(self):
        # Lazy initialization
        self._collection = None
        self._model_class = Notification
    
    @property
    def collection(self):
        if self._collection is None:
            from app.database.connection import get_database
            db = get_database()
            self._collection = db.notifications
        return self._collection
    
    @property
    def model_class(self):
        return self._model_class
    
    async def get_pending_notifications(self, limit: int = 100) -> List[Notification]:
        """Get pending notifications for processing"""
        return await self.get_many(
            {"status": "PENDING"},
            limit=limit,
            sort_by="sent_at",
            sort_order=1
        )
    
    async def get_user_notifications(
        self, 
        user_id: str, 
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Notification]:
        """Get notifications for a specific user"""
        filter_dict = {"user_id": ObjectId(user_id)}
        if status:
            filter_dict["status"] = status
        
        return await self.get_many(
            filter_dict,
            limit=limit,
            sort_by="sent_at",
            sort_order=-1
        )
    
    async def mark_as_sent(self, notification_id: str) -> Optional[Notification]:
        """Mark notification as sent"""
        return await self.update_by_id(
            notification_id,
            {
                "status": "SENT",
                "delivered_at": datetime.utcnow()
            }
        )
    
    async def mark_as_failed(self, notification_id: str, error_message: str) -> Optional[Notification]:
        """Mark notification as failed"""
        return await self.update_by_id(
            notification_id,
            {
                "status": "FAILED",
                "error_message": error_message,
                "retry_count": {"$inc": 1}
            }
        )
    
    async def get_daily_notification_count(self, user_id: str, date: datetime = None) -> int:
        """Get notification count for user for a specific day"""
        if date is None:
            date = datetime.utcnow()
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        return await self.count({
            "user_id": ObjectId(user_id),
            "sent_at": {
                "$gte": start_of_day,
                "$lt": end_of_day
            }
        })

# Singleton instance
notification_repository = NotificationRepository() 