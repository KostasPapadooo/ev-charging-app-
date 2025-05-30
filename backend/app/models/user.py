from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from bson import ObjectId
from app.models.station import PyObjectId

class UserPreferences(BaseModel):
    preferred_connector_types: List[str] = []  # ["Type2", "CCS", etc.]
    max_distance_km: float = 10.0
    min_power_kw: Optional[float] = None
    notification_methods: List[str] = ["push"]  # ["push", "email", "sms"]
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"

class UserLocation(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]
    address: Optional[str] = None

class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    password_hash: str
    first_name: str
    last_name: str
    phone: str = "+1234567890"  # Έγκυρος αριθμός τηλεφώνου που ταιριάζει με το regex
    is_active: bool = True
    is_verified: bool = False
    subscription_tier: str = "free"  # "free", "premium"
    location: dict = {  # Έγκυρο location object
        "type": "Point",
        "coordinates": [0.0, 0.0],
        "address": ""
    }
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str} 