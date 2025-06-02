from typing import List, Optional, Dict, Any
from pymongo import ASCENDING, DESCENDING, GEOSPHERE
import pymongo
from app.repositories.base_repository import BaseRepository
from app.models.station import Station, StationLocation, ConnectorInfo, OperatorInfo
from datetime import datetime, timedelta
import logging
from app.core.config import Settings
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from app.database.connection import get_database

logger = logging.getLogger(__name__)
settings = Settings()

class StationRepository:
    def __init__(self):
        self.collection_name = "current_stations"
        self.db = None
        self.collection: AsyncIOMotorCollection = None

    async def initialize(self):
        """Initialize repository with database connection"""
        try:
            self.db = get_database()
            self.collection = self.db[self.collection_name]
            await self._create_indexes()
            logger.info("StationRepository initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing StationRepository: {e}")
            raise

    async def _create_indexes(self):
        """Create necessary indexes for the stations collection"""
        try:
            # Check existing indexes first
            existing_indexes = await self.collection.list_indexes().to_list(length=None)
            index_names = [idx['name'] for idx in existing_indexes]
            
            # Only create indexes that don't exist
            if 'location.coordinates_2dsphere' not in index_names:
                await self.collection.create_index([("location.coordinates", "2dsphere")])
                logger.info("Created location.coordinates 2dsphere index")
            
            if 'tomtom_id_1' not in index_names:
                await self.collection.create_index("tomtom_id", unique=True)
                logger.info("Created tomtom_id unique index")
            
            if 'data_source_1_last_updated_-1' not in index_names:
                await self.collection.create_index([("data_source", 1), ("last_updated", -1)])
                logger.info("Created data_source compound index")
            
            # Remove any old problematic indexes
            for idx in existing_indexes:
                if idx['name'] in ['location_2dsphere', 'location_2dsphere_status_1_last_updated_-1']:
                    try:
                        await self.collection.drop_index(idx['name'])
                        logger.info(f"Dropped problematic index: {idx['name']}")
                    except Exception as e:
                        logger.warning(f"Could not drop index {idx['name']}: {e}")
            
            logger.info("Station indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating station indexes: {e}")
            raise

    def _station_to_dict(self, station_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB station document to dictionary for API response"""
        # Convert ObjectId to string
        if '_id' in station_doc:
            station_doc['_id'] = str(station_doc['_id'])
        
        # Ensure all fields are JSON serializable
        result = {
            'id': str(station_doc.get('_id', '')),
            'tomtom_id': station_doc.get('tomtom_id', ''),
            'name': station_doc.get('name', ''),
            'location': station_doc.get('location', {}),
            'address': station_doc.get('address', ''),
            'connectors': station_doc.get('connectors', []),
            'operator': station_doc.get('operator', {}),
            'pricing': station_doc.get('pricing'),
            'status': station_doc.get('status', 'UNKNOWN'),
            'access_type': station_doc.get('access_type', 'PUBLIC'),
            'opening_hours': station_doc.get('opening_hours'),
            'amenities': station_doc.get('amenities', []),
            'last_updated': str(station_doc.get('last_updated', '')),
            'data_source': station_doc.get('data_source', 'UNKNOWN'),
            'distance': station_doc.get('distance_meters')  # For nearby search results
        }
        
        return result

    async def find_nearby_stations(
        self,
        lat: float,
        lon: float,
        radius_meters: int = 5000,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find stations within radius of coordinates"""
        try:
            # Build query
            query = {}
            
            # Add status filter if provided
            if status_filter:
                query["status"] = status_filter.upper()
            
            # Execute query with distance calculation
            pipeline = [
                {"$geoNear": {
                    "near": {
                        "type": "Point", 
                        "coordinates": [lon, lat]  # GeoJSON format: [longitude, latitude]
                    },
                    "distanceField": "distance_meters",
                    "maxDistance": radius_meters,
                    "spherical": True,
                    "query": query,
                    "key": "location.coordinates"  # Specify which index to use
                }},
                {"$limit": limit},
                {"$sort": {"distance_meters": 1}}
            ]
            
            cursor = self.collection.aggregate(pipeline)
            stations = await cursor.to_list(length=None)
            
            # Convert to JSON-serializable format using _station_to_dict
            result = [self._station_to_dict(station) for station in stations]
            
            logger.info(f"Found {len(result)} nearby stations within {radius_meters}m of ({lat}, {lon})")
            return result
            
        except Exception as e:
            logger.error(f"Error finding nearby stations: {e}")
            return []

    async def find_by_tomtom_id(self, tomtom_id: str) -> Optional[Dict[str, Any]]:
        """Find station by TomTom ID"""
        try:
            station = await self.collection.find_one({"tomtom_id": tomtom_id})
            return station
        except Exception as e:
            logger.error(f"Error finding station by TomTom ID {tomtom_id}: {e}")
            return None

    async def create_station(self, station: Station) -> bool:
        """Create new station from TomTom data"""
        try:
            station_doc = {
                "tomtom_id": station.tomtom_id,
                "name": station.name,
                "location": {
                    "type": "Point",
                    "coordinates": station.location.coordinates
                },
                "address": station.address if station.address else "",
                "connectors": [
                    {
                        "id": conn.id,
                        "type": conn.type,
                        "max_power_kw": conn.max_power_kw,
                        "current_type": conn.current_type,
                        "status": conn.status
                    } for conn in station.connectors
                ],
                "operator": {
                    "name": station.operator.name if station.operator else "Unknown",
                    "website": station.operator.website if station.operator else None
                },
                "pricing": station.pricing,
                "status": station.status,
                "access_type": station.access_type,
                "opening_hours": station.opening_hours,
                "amenities": station.amenities or [],
                "last_updated": datetime.utcnow(),
                "data_source": "TOMTOM"
            }
            
            await self.collection.insert_one(station_doc)
            logger.info(f"Created station {station.tomtom_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating station {station.tomtom_id}: {e}")
            return False

    async def update_station_status(
        self,
        tomtom_id: str,
        new_status: str,
        additional_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update station status and other fields"""
        try:
            update_doc = {
                "status": new_status,
                "last_updated": datetime.utcnow()
            }
            
            if additional_updates:
                update_doc.update(additional_updates)
            
            result = await self.collection.update_one(
                {"tomtom_id": tomtom_id},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated station {tomtom_id} status to {new_status}")
                return True
            else:
                logger.warning(f"No station found with TomTom ID {tomtom_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating station {tomtom_id}: {e}")
            return False

    async def cleanup_old_cache(self, hours: int = 24) -> int:
        """Remove old cached stations to keep database clean"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            result = await self.collection.delete_many({
                "data_source": "TOMTOM",
                "last_updated": {"$lt": cutoff_time}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old cached stations")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old cache: {e}")
            return 0

    async def get_popular_search_areas(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most searched geographic areas for batch processing"""
        try:
            # This would typically come from analytics data
            # For now, return some default popular areas in Athens
            popular_areas = [
                {"lat": 37.9755, "lon": 23.7348, "name": "Syntagma", "search_count": 100},
                {"lat": 37.9838, "lon": 23.7275, "name": "Omonia", "search_count": 85},
                {"lat": 37.9908, "lon": 23.7383, "name": "Exarchia", "search_count": 70},
                {"lat": 37.9755, "lon": 23.7621, "name": "Kolonaki", "search_count": 65},
                {"lat": 37.9442, "lon": 23.6475, "name": "Piraeus", "search_count": 60}
            ]
            
            return popular_areas[:limit]
            
        except Exception as e:
            logger.error(f"Error getting popular search areas: {e}")
            return []

    async def get_all_stations(self, filter_dict: Optional[Dict] = None, limit: Optional[int] = None) -> List[Station]:
        """Get all stations with optional filtering"""
        try:
            query = filter_dict or {}
            
            if limit:
                cursor = self.collection.find(query).limit(limit)
            else:
                cursor = self.collection.find(query)
                
            stations_data = await cursor.to_list(length=None)
            
            # Convert to Station objects
            stations = []
            for station_data in stations_data:
                try:
                    # Convert MongoDB document to Station object
                    station = self._convert_to_station_object(station_data)
                    stations.append(station)
                except Exception as e:
                    logger.warning(f"Error converting station {station_data.get('tomtom_id', 'unknown')}: {e}")
                    continue
                    
            return stations
            
        except Exception as e:
            logger.error(f"Error getting all stations: {e}")
            return []

    async def get_station_by_id(self, station_id: str) -> Optional[Station]:
        """Get station by TomTom ID"""
        try:
            station_data = await self.collection.find_one({"tomtom_id": station_id})
            
            if not station_data:
                return None
                
            return self._convert_to_station_object(station_data)
            
        except Exception as e:
            logger.error(f"Error getting station by ID {station_id}: {e}")
            return None

    def _convert_to_station_object(self, station_data: Dict[str, Any]) -> Station:
        """Convert MongoDB document to Station object"""
        try:
            # Convert connectors
            connectors = []
            for conn_data in station_data.get('connectors', []):
                connector = ConnectorInfo(
                    id=conn_data.get('id'),
                    type=conn_data.get('type'),
                    max_power_kw=conn_data.get('max_power_kw'),
                    current_type=conn_data.get('current_type'),
                    status=conn_data.get('status', 'UNKNOWN')
                )
                connectors.append(connector)
            
            # Convert location
            location_data = station_data.get('location', {})
            location = StationLocation(
                type=location_data.get('type', 'Point'),
                coordinates=location_data.get('coordinates', [0, 0])
            )
            
            # Create Station object
            station = Station(
                tomtom_id=station_data.get('tomtom_id'),
                name=station_data.get('name'),
                location=location,
                connectors=connectors,
                status=station_data.get('status', 'UNKNOWN'),
                data_source=station_data.get('data_source', 'UNKNOWN'),
                last_updated=station_data.get('last_updated', datetime.utcnow())
            )
            
            return station
            
        except Exception as e:
            logger.error(f"Error converting station data to object: {e}")
            raise

    def _convert_tomtom_to_station(self, tomtom_data: Dict[str, Any]) -> Station:
        """Convert TomTom API data to Station object"""
        try:
            # Extract address information
            address_data = tomtom_data.get('address', {})
            
            # Create address string - FIXED
            address_parts = []
            if address_data.get('streetName'):
                street_part = address_data.get('streetName', '')
                if address_data.get('streetNumber'):
                    street_part = f"{address_data.get('streetNumber')} {street_part}"
                address_parts.append(street_part)
            
            if address_data.get('municipality'):
                address_parts.append(address_data.get('municipality'))
            
            if address_data.get('postalCode'):
                address_parts.append(address_data.get('postalCode'))
            
            # Join address parts
            full_address = ', '.join(filter(None, address_parts))
            if not full_address:
                full_address = address_data.get('freeformAddress', 'Unknown Address')

            # Extract position
            position = tomtom_data.get('position', {})
            
            # Create station location
            location = StationLocation(
                coordinates=[
                    float(position.get('lon', 0)),
                    float(position.get('lat', 0))
                ],
                address=full_address,  # Use string instead of object
                city=address_data.get('municipality', ''),
                country=address_data.get('country', ''),
                postal_code=address_data.get('postalCode', '')
            )
            
            # Extract POI information
            poi_data = tomtom_data.get('poi', {})
            
            # Extract charging park information
            charging_park = tomtom_data.get('chargingPark', {})
            connectors_data = charging_park.get('connectors', [])
            
            # Convert connectors
            connectors = []
            for conn_data in connectors_data:
                connector = ConnectorInfo(
                    type=conn_data.get('connectorType', 'Unknown'),
                    power_kw=float(conn_data.get('ratedPowerKW', 0)),
                    voltage=conn_data.get('voltageV', 0),
                    current=conn_data.get('currentA', 0),
                    current_type=conn_data.get('currentType', 'Unknown')
                )
                connectors.append(connector)
            
            # Create operator info
            brands = poi_data.get('brands', [])
            operator_name = brands[0].get('name') if brands else 'Unknown'
            
            operator = OperatorInfo(
                name=operator_name,
                website=poi_data.get('url', ''),
                phone='',
                email=''
            )
            
            # Create station
            station = Station(
                station_id=tomtom_data.get('id'),
                name=poi_data.get('name', 'Unknown Station'),
                location=location,
                connectors=connectors,
                operator=operator,
                status='AVAILABLE',  # Default status
                last_updated=datetime.utcnow(),
                data_source='tomtom'
            )
            
            return station
            
        except Exception as e:
            logger.error(f"Error converting station data to object: {e}")
            raise

# Create singleton instance
station_repository = StationRepository() 