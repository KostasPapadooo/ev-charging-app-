import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.config import settings
from app.core.exceptions import TomTomAPIException

# Ενημερωμένα imports
from app.models.station import (
    Station, 
    StationLocation, 
    ConnectorInfo, 
    OperatorInfo, 
    PricingInfo
)

logger = logging.getLogger(__name__)

class TomTomService:
    def __init__(self):
        self.search_api_key = getattr(settings, 'tomtom_api_key', '') or "demo_key"
        self.ev_api_key = getattr(settings, 'tomtom_ev_api_key', '') or "demo_key"
        self.search_base_url = "https://api.tomtom.com/search/2/search"
        self.ev_base_url = "https://api.tomtom.com/search/2/chargingAvailability"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.sync_client = httpx.Client(timeout=30.0)  # Προσθήκη σύγχρονου client
        
        if not self.search_api_key or self.search_api_key == "demo_key":
            logger.warning("TomTom Search API key not configured.")
        if not self.ev_api_key or self.ev_api_key == "demo_key":
            logger.warning("TomTom EV API key not configured.")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        self.sync_client.close()  # Κλείσιμο του σύγχρονου client
    
    async def search_charging_stations(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 50000
    ) -> List[Station]:
        """Search for charging stations using TomTom Search API (async)"""
        try:
            print(f"🔍 DEBUGGING: API Key = {self.search_api_key}")
            print(f"🔍 DEBUGGING: Search URL = {self.search_base_url}")
            print(f"🔍 DEBUGGING: Coordinates = ({latitude}, {longitude})")
            print(f"🔍 DEBUGGING: Radius = {radius}")
            
            # ΑΚΡΙΒΩΣ όπως στο Node-RED
            params = {
                "key": self.search_api_key,
                "limit": 100,
                "lat": latitude,
                "lon": longitude,
                "radius": radius,
                "categorySet": "7309"
            }
            
            logger.info(f"TomTom API Request:")
            logger.info(f"URL: {self.search_base_url}/electric%20vehicle%20charging%20station.json")
            logger.info(f"Params: {params}")
            logger.info(f"API Key: {self.search_api_key}")
            
            response = await self.client.get(
                f"{self.search_base_url}/electric%20vehicle%20charging%20station.json", 
                params=params
            )
            
            logger.info(f"Response Status: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Response Data Keys: {list(data.keys())}")
            logger.info(f"Results Count: {len(data.get('results', []))}")
            
            if data.get('results'):
                logger.info(f"First Result: {data['results'][0]}")
            
            stations = []
            for result in data.get("results", []):
                try:
                    station = self._parse_tomtom_station(result)
                    stations.append(station)
                except Exception as e:
                    logger.warning(f"Failed to parse station: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(stations)} charging stations")
            return stations
            
        except httpx.HTTPStatusError as e:
            logger.error(f"TomTom API HTTP error: {e}")
            logger.error(f"Response content: {e.response.text}")
            raise TomTomAPIException(f"TomTom API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error searching charging stations: {e}")
            raise TomTomAPIException(f"Failed to search charging stations: {str(e)}")
    
    def search_charging_stations_sync(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 50000
    ) -> List[Station]:
        """Search for charging stations using TomTom Search API (synchronous)"""
        try:
            print(f"🔍 DEBUGGING: API Key = {self.search_api_key}")
            print(f"🔍 DEBUGGING: Search URL = {self.search_base_url}")
            print(f"🔍 DEBUGGING: Coordinates = ({latitude}, {longitude})")
            print(f"🔍 DEBUGGING: Radius = {radius}")
            
            # ΑΚΡΙΒΩΣ όπως στο Node-RED
            params = {
                "key": self.search_api_key,
                "limit": 100,
                "lat": latitude,
                "lon": longitude,
                "radius": radius,
                "categorySet": "7309"
            }
            
            logger.info(f"TomTom API Request:")
            logger.info(f"URL: {self.search_base_url}/electric%20vehicle%20charging%20station.json")
            logger.info(f"Params: {params}")
            logger.info(f"API Key: {self.search_api_key}")
            
            response = self.sync_client.get(
                f"{self.search_base_url}/electric%20vehicle%20charging%20station.json", 
                params=params
            )
            
            logger.info(f"Response Status: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Response Data Keys: {list(data.keys())}")
            logger.info(f"Results Count: {len(data.get('results', []))}")
            
            if data.get('results'):
                logger.info(f"First Result: {data['results'][0]}")
            
            stations = []
            for result in data.get("results", []):
                try:
                    station = self._parse_tomtom_station(result)
                    stations.append(station)
                except Exception as e:
                    logger.warning(f"Failed to parse station: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(stations)} charging stations")
            return stations
            
        except httpx.HTTPStatusError as e:
            logger.error(f"TomTom API HTTP error: {e}")
            logger.error(f"Response content: {e.response.text}")
            raise TomTomAPIException(f"TomTom API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error searching charging stations: {e}")
            raise TomTomAPIException(f"Failed to search charging stations: {str(e)}")
    
    def _parse_tomtom_station(self, result: Dict[str, Any]) -> Station:
        """Parse TomTom API result into Station model"""
        try:
            # Extract basic info
            poi = result.get("poi", {})
            position = result.get("position", {})
            address = result.get("address", {})
            
            # Create location
            location = StationLocation(
                type="Point",
                coordinates=[position.get("lon", 0.0), position.get("lat", 0.0)]
            )
            
            # Create address string
            address_parts = []
            if address.get("streetName"):
                address_parts.append(address["streetName"])
            if address.get("municipality"):
                address_parts.append(address["municipality"])
            if address.get("country"):
                address_parts.append(address["country"])
            
            address_str = ", ".join(address_parts) if address_parts else "Unknown Address"
            
            # ΔΙΟΡΘΩΣΗ: Σωστά field names για ConnectorInfo
            connectors = [
                ConnectorInfo(
                    type="Type2",           # ✅ type αντί για connector_type
                    max_power_kw=22.0,
                    current_type="AC",
                    status="AVAILABLE"      # ✅ status αντί για availability
                )
            ]
            
            # Create operator info
            operator = OperatorInfo(
                name=poi.get("brands", [{}])[0].get("name", "Unknown Operator") if poi.get("brands") else "Unknown Operator",
                website=poi.get("url"),
                phone=poi.get("phone")
            )
            
            # Create station
            station = Station(
                tomtom_id=result.get("id", ""),
                name=poi.get("name", "EV Charging Station"),
                location=location,
                address=address_str,
                connectors=connectors,
                operator=operator,
                status="AVAILABLE",
                access_type="PUBLIC",
                opening_hours=None,
                amenities=[],
                last_updated=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            return station
            
        except Exception as e:
            logger.error(f"Error parsing TomTom station: {e}")
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
tomtom_service = TomTomService() 