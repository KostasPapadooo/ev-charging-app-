from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from app.models.station import PyObjectId

class StatusSnapshot(BaseModel):
    station_status: str  # "AVAILABLE", "OCCUPIED", "OFFLINE", "MAINTENANCE"
    total_connectors: int = Field(..., ge=0)
    available_connectors: int = Field(..., ge=0)
    occupied_connectors: int = Field(..., ge=0)
    out_of_order_connectors: int = Field(..., ge=0)

class ConnectorDetail(BaseModel):
    connector_id: str
    type: str
    status: str
    session_duration_minutes: Optional[int] = Field(None, ge=0)
    power_kw: Optional[float] = None

class UsageMetrics(BaseModel):
    sessions_today: int = Field(0, ge=0)
    avg_session_duration: float = Field(0, ge=0)
    peak_hour: Optional[str] = None
    utilization_rate: float = Field(0, ge=0, le=1)
    revenue_today: float = Field(0, ge=0)

class HistoricalStation(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    station_id: str  # Reference to current_stations.tomtom_id
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status_snapshot: StatusSnapshot
    connector_details: Optional[List[ConnectorDetail]] = []
    usage_metrics: Optional[UsageMetrics] = None
    weather_conditions: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str} 