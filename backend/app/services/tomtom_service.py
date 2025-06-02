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

# Constants
TOMTOM_AVAILABILITY_CHUNK_SIZE = 20 # Max IDs per call to availability endpoint

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
                created_at=datetime.utcnow(),
                data_source="TOMTOM"
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

    def _api_key_sync(self) -> str:
        return self.ev_api_key if self.ev_api_key else self.search_api_key

    def _make_request_sync(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if params is None:
            params = {}
        
        # Ensure the API key is included in the parameters
        if 'key' not in params:
            params['key'] = self._api_key_sync()

        try:
            with httpx.Client(base_url=self.ev_base_url, timeout=30.0) as client:
                response = client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"TomTom API HTTPStatusError for {e.request.url}: {e.response.status_code} - {e.response.text}")
            raise TomTomAPIException(f"TomTom API error: {e.response.status_code} - {e.response.text}", status_code=e.response.status_code)
        except httpx.RequestError as e:
            logger.error(f"TomTom API RequestError for {e.request.url}: {str(e)}")
            raise TomTomAPIException(f"TomTom API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during TomTom API sync request: {str(e)}")
            raise TomTomAPIException(f"Unexpected error: {str(e)}")

    def _parse_station_data(self, api_station_data: Dict[str, Any]) -> Optional[Station]:
        try:
            station_id = api_station_data.get("id")
            if not station_id:
                logger.warning("Station data missing ID, skipping.")
                return None

            poi_data = api_station_data.get("poi", {})
            address_data = api_station_data.get("address", {})
            position_data = api_station_data.get("position", {})
            charging_park_data = api_station_data.get("chargingPark", {})
            
            if not all([poi_data, address_data, position_data, charging_park_data]):
                 logger.warning(f"Station {station_id} missing core data (poi, address, position, or chargingPark), skipping.")
                 return None

            # Location
            location = StationLocation(
                coordinates=[position_data.get("lon"), position_data.get("lat")]
            )

            # Connectors
            api_connector_data_list = charging_park_data.get("connectors", [])
            parsed_connectors = []
            for api_connector_data in api_connector_data_list:
                connector_id = api_connector_data.get("id") # Crucial for matching with availability API
                connector_type_str = api_connector_data.get("connectorType", "UNKNOWN")
                # Simple mapping, can be expanded
                if "IEC_62196_TYPE_2" in connector_type_str.upper(): # Handles TYPE_2_SOCKET and TYPE_2_CABLE
                    connector_type_str = "Type2"
                elif "TESLA" in connector_type_str.upper():
                    connector_type_str = "Tesla"
                elif "CCS" in connector_type_str.upper() or "COMBO" in connector_type_str.upper() : # Handles CCS_COMBO_1, CCS_COMBO_2
                     connector_type_str = "CCS"
                elif "CHADEMO" in connector_type_str.upper():
                    connector_type_str = "CHAdeMO"
                
                current_type_str = api_connector_data.get("currentType", "UNKNOWN").upper()
                if current_type_str not in ["AC", "DC"]:
                    current_type_str = "UNKNOWN"

                connector_status = "UNKNOWN"
                # TomTom POI search provides initial availability.
                # It can be at chargingPark level or per-connector level.
                cp_availability = charging_park_data.get("availability", {})
                conn_availability = api_connector_data.get("availability", {})

                if conn_availability and "status" in conn_availability: # Prefer connector-specific status if available
                    connector_status = conn_availability["status"].upper()
                elif cp_availability.get("perConnector", False) and "status" in conn_availability: # Should have been caught by above
                     connector_status = conn_availability.get("status", "UNKNOWN").upper()
                elif not cp_availability.get("perConnector", True) and "status" in cp_availability: # Use overall if not perConnector
                    connector_status = cp_availability["status"].upper()
                else: # Fallback if logic is complex or data missing
                    connector_status = cp_availability.get("status", "UNKNOWN").upper()


                if connector_status not in ["AVAILABLE", "BUSY", "OCCUPIED", "OUT_OF_ORDER", "UNKNOWN"]:
                    logger.warning(f"Unknown connector status '{connector_status}' for station {station_id}, connector {connector_id}. Defaulting to UNKNOWN.")
                    connector_status = "UNKNOWN"
                if connector_status == "BUSY": # Normalize BUSY to OCCUPIED
                    connector_status = "OCCUPIED"


                parsed_connectors.append(ConnectorInfo(
                    id=connector_id, # Ensure this is correctly populated
                    type=connector_type_str,
                    max_power_kw=float(api_connector_data.get("ratedPowerKW", 0.0)),
                    current_type=current_type_str,
                    status=connector_status
                ))
            
            if not parsed_connectors:
                logger.warning(f"Station {station_id} has no connectors defined in API data, skipping.")
                return None

            # Operator
            # TomTom API might not always provide detailed operator info directly in POI search.
            # This part might need adjustment based on actual API response structure for operator.
            # For now, using a placeholder if not found.
            # The `brandName` in `poi` might be the operator.
            operator_name = poi_data.get("brandName", "Unknown Operator") 
            operator_info = OperatorInfo(name=operator_name)

            # Overall Station Status from POI search (initial status)
            overall_status_info = charging_park_data.get("availability", {})
            overall_status = overall_status_info.get("status", "UNKNOWN").upper()
            if overall_status not in ["AVAILABLE", "BUSY", "OCCUPIED", "OUT_OF_ORDER", "UNKNOWN"]:
                logger.warning(f"Unknown overall station status '{overall_status}' for station {station_id}. Defaulting to UNKNOWN.")
                overall_status = "UNKNOWN"
            if overall_status == "BUSY": # Normalize BUSY to OCCUPIED
                overall_status = "OCCUPIED"


            return Station(
                tomtom_id=station_id,
                name=poi_data.get("name", "Unknown Station Name"),
                location=location,
                address=f"{address_data.get('streetNumber', '')} {address_data.get('streetName', '')}, {address_data.get('municipality', '')}, {address_data.get('countryCodeISO3', '')}".strip(),
                connectors=parsed_connectors,
                operator=operator_info,
                status=overall_status, # Initial overall status
                # access_type, opening_hours, amenities might need more specific parsing if available
            )
        except Exception as e:
            logger.error(f"Error parsing station data for ID {api_station_data.get('id')}: {e}", exc_info=True)
            return None

    def get_stations_availability_sync(self, station_tomtom_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetches real-time availability for a list of stations from TomTom.
        Handles API calls in chunks if the list of IDs is large.
        """
        if not station_tomtom_ids:
            return []

        all_availability_data = []
        
        for i in range(0, len(station_tomtom_ids), TOMTOM_AVAILABILITY_CHUNK_SIZE):
            chunk_ids = station_tomtom_ids[i:i + TOMTOM_AVAILABILITY_CHUNK_SIZE]
            ids_param = ",".join(chunk_ids)
            
            endpoint = "/search/2/chargingAvailability.json"
            params = {
                "chargingAvailability": ids_param,
                "key": self._api_key_sync() # Ensure key is passed directly
            }
            
            try:
                logger.debug(f"Fetching availability for station IDs (chunk {i // TOMTOM_AVAILABILITY_CHUNK_SIZE + 1}): {chunk_ids}")
                # We call _make_request_sync without params['key'] because it adds it.
                # However, for this specific endpoint, the key is part of the main params.
                # Let's adjust _make_request_sync or how we call it.
                # For now, let's ensure the key is in params and _make_request_sync doesn't duplicate.
                # The current _make_request_sync adds key if not present. So this is fine.

                api_response = self._make_request_sync(endpoint, params)
                
                if api_response and "chargingAvailability" in api_response:
                    parsed_chunk_data = []
                    for station_avail_data in api_response["chargingAvailability"]:
                        station_id = station_avail_data.get("id")
                        overall_status_obj = station_avail_data.get("availability", {})
                        overall_status = overall_status_obj.get("status", "UNKNOWN").upper()
                        if overall_status == "BUSY": # Normalize
                            overall_status = "OCCUPIED"

                        connectors_availability = []
                        for conn_data in station_avail_data.get("connectors", []):
                            conn_id = conn_data.get("id")
                            conn_status_obj = conn_data.get("availability", {})
                            conn_status = conn_status_obj.get("status", "UNKNOWN").upper()
                            if conn_status == "BUSY": # Normalize
                                conn_status = "OCCUPIED"
                            
                            if conn_id:
                                connectors_availability.append({
                                    "id": conn_id,
                                    "status": conn_status
                                })
                        
                        if station_id:
                            parsed_chunk_data.append({
                                "tomtom_id": station_id,
                                "overall_status": overall_status,
                                "connectors": connectors_availability
                            })
                    all_availability_data.extend(parsed_chunk_data)
                    logger.info(f"Successfully fetched and parsed availability for {len(parsed_chunk_data)} stations in chunk.")
                else:
                    logger.warning(f"Received empty or invalid availability response for chunk: {chunk_ids}")

            except TomTomAPIException as e:
                logger.error(f"TomTom API Exception while fetching availability for IDs {chunk_ids}: {e}")
                # Continue to next chunk, or re-raise? For now, log and continue.
            except Exception as e:
                logger.error(f"Unexpected error fetching availability for IDs {chunk_ids}: {e}", exc_info=True)
        
        logger.info(f"Total availability data fetched for {len(all_availability_data)} stations across all chunks.")
        return all_availability_data

# Singleton instance
tomtom_service = TomTomService() 