from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class StationLocation(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]

class ConnectorInfo(BaseModel):
    id: Optional[str] = None
    type: str = "Type2"
    max_power_kw: float = 22.0
    current_type: str = "AC"
    status: str = "AVAILABLE"

class OperatorInfo(BaseModel):
    name: str
    website: Optional[str] = None
    phone: Optional[str] = None

class PricingInfo(BaseModel):
    currency: str = "EUR"
    price_per_kwh: Optional[float] = None
    price_per_minute: Optional[float] = None
    connection_fee: Optional[float] = None

class Station(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    tomtom_id: str = Field(..., unique=True)
    name: str
    location: StationLocation
    address: str
    connectors: List[ConnectorInfo]
    operator: OperatorInfo
    pricing: Optional[PricingInfo] = None
    status: str = "AVAILABLE"  # "AVAILABLE", "BUSY", "OUT_OF_ORDER", "UNKNOWN"
    access_type: str = "PUBLIC"  # "PUBLIC", "PRIVATE", "RESTRICTED"
    opening_hours: Optional[str] = None
    amenities: List[str] = []  # ["parking", "restaurant", "wifi", etc.]
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    availability_status_changes_count: int = Field(default=0, description="Cumulative count of availability status changes")
    data_source: str = "UNKNOWN"
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "tomtom_id": "12345",
                "name": "EV Station Downtown",
                "location": {
                    "type": "Point",
                    "coordinates": [23.7275, 37.9755]
                },
                "address": "123 Main St, Athens, Greece",
                "connectors": [
                    {
                        "type": "Type2",
                        "max_power_kw": 22.0,
                        "current_type": "AC",
                        "status": "AVAILABLE"
                    }
                ],
                "operator": {
                    "name": "EV Network",
                    "website": "https://evnetwork.com",
                    "phone": "+30210123456"
                },
                "status": "AVAILABLE"
            }
        }