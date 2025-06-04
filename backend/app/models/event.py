from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from app.models.station import PyObjectId

class EventData(BaseModel):
    session_ended: Optional[bool] = None
    session_duration_minutes: Optional[int] = Field(None, ge=0)
    energy_delivered_kwh: Optional[float] = Field(None, ge=0)
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    affected_connectors: Optional[int] = None

class Event(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    event_type: str
    station_id: str
    connector_id: Optional[str] = ""
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = {}
    processing_batch: Optional[str] = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()
        yield cls.ensure_connector_id_string

    @staticmethod
    def ensure_connector_id_string(values):
        if "connector_id" in values and values["connector_id"] is None:
            values["connector_id"] = ""
        return values

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str} 