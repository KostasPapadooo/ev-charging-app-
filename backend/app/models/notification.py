from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from app.models.station import PyObjectId

class NotificationMetadata(BaseModel):
    station_name: Optional[str] = None
    available_connectors: Optional[int] = None
    distance_km: Optional[float] = None
    estimated_wait_time: Optional[int] = None  # minutes

class Notification(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    station_id: str
    notification_type: str  # "STATION_AVAILABLE", "STATION_OCCUPIED", etc.
    title: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)
    delivery_method: str  # "push", "email", "sms"
    status: str = "PENDING"  # "PENDING", "SENT", "FAILED", "DELIVERED"
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    metadata: Optional[NotificationMetadata] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str} 