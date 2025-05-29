from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]

class Address(BaseModel):
    street: str
    city: str
    postal_code: Optional[str] = None
    country: str

class Connector(BaseModel):
    id: str
    type: str  # CCS, CHAdeMO, Type2, Type1, Tesla
    power_kw: Optional[float] = None
    status: str  # AVAILABLE, OCCUPIED, OUT_OF_ORDER

class Operator(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

class Pricing(BaseModel):
    currency: Optional[str] = "EUR"
    price_per_kwh: Optional[float] = None
    connection_fee: Optional[float] = None

class OpeningHours(BaseModel):
    is_24_7: Optional[bool] = True
    schedule: Optional[str] = None

class Station(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    tomtom_id: str
    name: str
    location: Location
    address: Address
    status: str  # AVAILABLE, OCCUPIED, OFFLINE, MAINTENANCE
    connectors: List[Connector]
    operator: Optional[Operator] = None
    pricing: Optional[Pricing] = None
    amenities: Optional[List[str]] = []
    opening_hours: Optional[OpeningHours] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data_source: Optional[str] = "tomtom_api"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}