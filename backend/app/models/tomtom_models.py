from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TomTomCoordinates(BaseModel):
    lat: float
    lon: float

class TomTomAddress(BaseModel):
    streetNumber: Optional[str] = None
    streetName: Optional[str] = None
    municipality: Optional[str] = None
    countrySubdivision: Optional[str] = None
    postalCode: Optional[str] = None
    countryCode: Optional[str] = None
    country: Optional[str] = None
    freeformAddress: Optional[str] = None

class TomTomConnector(BaseModel):
    connectorType: str
    ratedPowerKW: Optional[float] = None
    currentType: Optional[str] = None
    voltageV: Optional[int] = None

class TomTomChargingPark(BaseModel):
    connectors: List[TomTomConnector] = []

class TomTomOperatingHours(BaseModel):
    mode: Optional[str] = None
    timeRanges: Optional[List[Dict[str, Any]]] = None

class TomTomPOI(BaseModel):
    name: str
    phone: Optional[str] = None
    url: Optional[str] = None
    categories: Optional[List[str]] = None
    classifications: Optional[List[Dict[str, Any]]] = None

class TomTomChargingStation(BaseModel):
    id: str
    position: TomTomCoordinates
    address: TomTomAddress
    poi: Optional[TomTomPOI] = None
    chargingPark: Optional[TomTomChargingPark] = None
    operatingHours: Optional[TomTomOperatingHours] = None
    timeZone: Optional[Dict[str, Any]] = None
    dataSources: Optional[Dict[str, Any]] = None

class TomTomSearchResponse(BaseModel):
    summary: Dict[str, Any]
    results: List[TomTomChargingStation]

class TomTomAvailabilityConnector(BaseModel):
    id: str
    type: str
    status: str  # Available, Occupied, OutOfOrder, Unknown
    ratedPowerKW: Optional[float] = None

class TomTomStationAvailability(BaseModel):
    id: str
    connectors: List[TomTomAvailabilityConnector]
    lastUpdated: Optional[str] = None

class TomTomAvailabilityResponse(BaseModel):
    connectors: List[TomTomStationAvailability] 