from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from app.models.station import PyObjectId

class NotificationSettings(BaseModel):
    on_available: bool = True
    on_occupied: bool = False
    on_offline: bool = True
    on_maintenance: bool = True
    on_high_demand: bool = False
    max_notifications_per_day: int = 10

class UserSubscription(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    station_id: str  # TomTom station ID
    station_name: str
    notification_settings: NotificationSettings = Field(default_factory=NotificationSettings)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_notification_sent: Optional[datetime] = None
    notification_count_today: int = 0
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str} 