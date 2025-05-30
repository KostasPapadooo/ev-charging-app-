import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.exceptions import TomTomAPIException
from app.models.station import (
    Station, 
    StationLocation, 
    ConnectorInfo, 
    OperatorInfo
)

logger = logging.getLogger(__name__)

class OpenChargeMapService:
    def __init__(self):
        self.base_url = "https://api.openchargemap.io/v3/poi"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def search_charging_stations(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 5000
    ) -> List[Station]:
        """Search for charging stations using OpenChargeMap API"""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "distance": radius / 1000,  # Convert to km
                "maxresults": 20,
                "compact": "false",
                "verbose": "false"
            }
            
            logger.info(f"Searching charging stations at ({latitude}, {longitude}) with radius {radius}m")
            
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            stations = []
            
            for result in data:
                try:
                    station = self._parse_opencharge_station(result)
                    stations.append(station)
                except Exception as e:
                    logger.warning(f"Failed to parse station: {e}")
                    continue
            
            logger.info(f"Found {len(stations)} charging stations")
            return stations
            
        except Exception as e:
            logger.error(f"Error searching charging stations: {e}")
            raise TomTomAPIException(f"Failed to search charging stations: {str(e)}")
    
    def _parse_opencharge_station(self, result: Dict[str, Any]) -> Station:
        """Parse OpenChargeMap API result into Station model"""
        try:
            # Extract basic info
            address_info = result.get("AddressInfo", {})
            connections = result.get("Connections", [])
            operator_info = result.get("OperatorInfo", {})
            
            # Create location
            location = StationLocation(
                type="Point",
                coordinates=[
                    address_info.get("Longitude", 0.0), 
                    address_info.get("Latitude", 0.0)
                ]
            )
            
            # Create address string
            address_parts = []
            if address_info.get("AddressLine1"):
                address_parts.append(address_info["AddressLine1"])
            if address_info.get("Town"):
                address_parts.append(address_info["Town"])
            if address_info.get("Country", {}).get("Title"):
                address_parts.append(address_info["Country"]["Title"])
            
            address_str = ", ".join(address_parts) if address_parts else "Unknown Address"
            
            # Create connectors from connections
            connectors = []
            for conn in connections[:3]:  # Limit to 3 connectors
                connector_type = conn.get("ConnectionType", {}).get("Title", "Unknown")
                power_kw = conn.get("PowerKW", 22.0) or 22.0
                current_type = conn.get("CurrentType", {}).get("Title", "AC")
                
                connectors.append(ConnectorInfo(
                    type=connector_type,
                    max_power_kw=float(power_kw),
                    current_type=current_type,
                    status="AVAILABLE"
                ))
            
            # Default connector if none found
            if not connectors:
                connectors = [ConnectorInfo(
                    type="Type2",
                    max_power_kw=22.0,
                    current_type="AC",
                    status="AVAILABLE"
                )]
            
            # Create operator info
            operator = OperatorInfo(
                name=operator_info.get("Title", "Unknown Operator"),
                website=operator_info.get("WebsiteURL"),
                phone=operator_info.get("PhonePrimaryContact")
            )
            
            # Determine status
            status_type = result.get("StatusType", {})
            status = "AVAILABLE"
            if status_type:
                if status_type.get("IsOperational") == False:
                    status = "OUT_OF_ORDER"
                elif status_type.get("ID") == 50:  # Operational
                    status = "AVAILABLE"
                else:
                    status = "UNKNOWN"
            
            # Create station
            station = Station(
                tomtom_id=f"ocm_{result.get('ID', '')}",  # Use OCM prefix
                name=address_info.get("Title", "EV Charging Station"),
                location=location,
                address=address_str,
                connectors=connectors,
                operator=operator,
                status=status,
                access_type="PUBLIC",
                opening_hours=address_info.get("AccessComments"),
                amenities=[],
                last_updated=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            return station
            
        except Exception as e:
            logger.error(f"Error parsing OpenChargeMap station: {e}")
            raise
    
    async def get_stations_in_area(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 5000
    ) -> List[Station]:
        """Get all charging stations in a specific area"""
        return await self.search_charging_stations(latitude, longitude, radius)

# Singleton instance
opencharge_service = OpenChargeMapService() 