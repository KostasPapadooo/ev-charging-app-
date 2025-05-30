from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from app.models.station import PyObjectId

class HourlyData(BaseModel):
    hour: str  # "00", "01", ..., "23"
    sessions: int = Field(0, ge=0)
    avg_duration: float = Field(0, ge=0)
    utilization: float = Field(0, ge=0, le=1)
    revenue: float = Field(0, ge=0)

class DailyMetrics(BaseModel):
    total_sessions: int = Field(..., ge=0)
    avg_session_duration: float = Field(..., ge=0)
    peak_hours: List[str] = []
    utilization_rate: float = Field(..., ge=0, le=1)
    revenue_eur: float = Field(0, ge=0)
    unique_users: Optional[int] = Field(None, ge=0)
    busiest_connector_type: Optional[str] = None

class Analytics(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    station_id: str
    date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')  # YYYY-MM-DD format
    metrics: DailyMetrics
    hourly_data: Optional[List[HourlyData]] = []
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: float = Field(1.0, ge=0, le=1)  # 0-1 score
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str} 