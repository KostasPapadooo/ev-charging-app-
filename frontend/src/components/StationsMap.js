import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { fetchNearbyStations } from '../services/stationsApi';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix για τα default icons του Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom icons για διαφορετικά status
const createCustomIcon = (status) => {
  const color = getMarkerColor(status);
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
};

// User location icon
const createUserIcon = () => {
  return L.divIcon({
    className: 'user-marker',
    html: `<div style="background-color: #007bff; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
};

const getMarkerColor = (status) => {
  switch (status) {
    case 'AVAILABLE': return '#28a745';
    case 'BUSY': return '#dc3545';
    case 'OUT_OF_ORDER': return '#6c757d';
    default: return '#007bff';
  }
};

const StationsMap = ({ userLocation, locationPermission }) => {
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [error, setError] = useState(null);
  const [searchParams, setSearchParams] = useState(null);
  const [radius, setRadius] = useState(5000);

  // Load stations when component mounts or when filters change
  useEffect(() => {
    if (userLocation && locationPermission === 'granted') {
      loadNearbyStations(userLocation.lat, userLocation.lon);
    }
  }, [userLocation, locationPermission, filter, radius]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (userLocation && locationPermission === 'granted') {
      const interval = setInterval(() => {
        loadNearbyStations(userLocation.lat, userLocation.lon);
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [userLocation, locationPermission, filter, radius]);

  const loadNearbyStations = async (lat, lon) => {
    try {
      setLoading(true);
      setError(null);
      
      const filters = {
        radius: radius,
        ...(filter && { status: filter })
      };
      
      console.log(`Loading stations near (${lat}, ${lon}) with radius ${radius}m`);
      const data = await fetchNearbyStations(lat, lon, filters);
      
      setStations(data.stations);
      setSearchParams(data.search_params);
      
      console.log(`Loaded ${data.stations.length} nearby stations`);
    } catch (error) {
      console.error('Failed to load nearby stations:', error);
      setError('Failed to load nearby stations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (userLocation) {
      loadNearbyStations(userLocation.lat, userLocation.lon);
    }
  };

  const handleRadiusChange = (newRadius) => {
    setRadius(newRadius);
  };

  const getStatusStats = () => {
    return {
      total: stations.length,
      available: stations.filter(s => s.status === 'AVAILABLE').length,
      busy: stations.filter(s => s.status === 'BUSY').length,
      outOfOrder: stations.filter(s => s.status === 'OUT_OF_ORDER').length,
      unknown: stations.filter(s => s.status === 'UNKNOWN').length
    };
  };

  const stats = getStatusStats();

  // Don't render anything if we don't have user location
  if (!userLocation || locationPermission !== 'granted') {
    return null;
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">{error}</p>
        <button onClick={handleRefresh} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="stations-map-container">
      <div className="map-controls">
        <div className="filter-section">
          <label htmlFor="status-filter">Filter by Status:</label>
          <select
            id="status-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="status-filter"
          >
            <option value="">All Stations</option>
            <option value="AVAILABLE">Available</option>
            <option value="BUSY">Busy</option>
            <option value="OUT_OF_ORDER">Out of Order</option>
          </select>
          
          <label htmlFor="radius-filter">Search Radius:</label>
          <select
            id="radius-filter"
            value={radius}
            onChange={(e) => handleRadiusChange(parseInt(e.target.value))}
            className="radius-filter"
          >
            <option value="1000">1 km</option>
            <option value="2000">2 km</option>
            <option value="5000">5 km</option>
            <option value="10000">10 km</option>
            <option value="20000">20 km</option>
          </select>
        </div>

        <div className="location-info">
          <div className="current-location">
            <span className="location-icon">📍</span>
            <span>
              Your Location: {userLocation.lat.toFixed(4)}, {userLocation.lon.toFixed(4)}
            </span>
            {userLocation.accuracy && (
              <span className="accuracy">
                (±{Math.round(userLocation.accuracy)}m)
              </span>
            )}
          </div>
        </div>

        <div className="stations-stats">
          <div className="stat">
            <span className="stat-label">Total:</span>
            <span className="stat-value">{stats.total}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Available:</span>
            <span className="stat-value available">{stats.available}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Busy:</span>
            <span className="stat-value busy">{stats.busy}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Out of Order:</span>
            <span className="stat-value out-of-order">{stats.outOfOrder}</span>
          </div>
        </div>

        <button onClick={handleRefresh} className="refresh-button" disabled={loading}>
          {loading ? '⏳ Loading...' : '🔄 Refresh'}
        </button>
      </div>

      {searchParams && (
        <div className="search-info">
          <p>
            Showing {searchParams.total_found} stations within {(searchParams.radius_meters / 1000).toFixed(1)}km 
            {searchParams.status_filter && ` (${searchParams.status_filter} only)`}
          </p>
        </div>
      )}

      <div className="map-wrapper">
        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner">
              Loading nearby stations...
            </div>
          </div>
        )}
        
        <MapContainer
          center={[userLocation.lat, userLocation.lon]}
          zoom={13}
          style={{ height: '600px', width: '100%' }}
          className="stations-map"
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          {/* User location marker */}
          <Marker
            position={[userLocation.lat, userLocation.lon]}
            icon={createUserIcon()}
          >
            <Popup>
              <div className="user-location-popup">
                <h4>📍 Your Location</h4>
                <p>Lat: {userLocation.lat.toFixed(6)}</p>
                <p>Lon: {userLocation.lon.toFixed(6)}</p>
                {userLocation.accuracy && (
                  <p>Accuracy: ±{Math.round(userLocation.accuracy)}m</p>
                )}
              </div>
            </Popup>
          </Marker>
          
          {/* Search radius circle */}
          <Circle
            center={[userLocation.lat, userLocation.lon]}
            radius={radius}
            pathOptions={{
              color: '#007bff',
              fillColor: '#007bff',
              fillOpacity: 0.1,
              weight: 2
            }}
          />
          
          {/* Station markers */}
          {stations.map((station) => (
            <Marker
              key={station.tomtom_id}
              position={[
                station.location.coordinates[1], // latitude
                station.location.coordinates[0]  // longitude
              ]}
              icon={createCustomIcon(station.status)}
            >
              <Popup maxWidth={300}>
                <div className="station-popup">
                  <h4>{station.name}</h4>
                  <p className="station-address">{station.address}</p>
                  
                  <div className="station-status">
                    <span className={`status-badge ${station.status.toLowerCase()}`}>
                      {station.status}
                    </span>
                  </div>

                  <div className="connectors-info">
                    <h5>Connectors:</h5>
                    {station.connectors.map((connector, index) => (
                      <div key={index} className="connector">
                        <span className="connector-type">{connector.type}</span>
                        <span className="connector-power">{connector.max_power_kw}kW</span>
                        <span className={`connector-status ${connector.status.toLowerCase()}`}>
                          {connector.status}
                        </span>
                      </div>
                    ))}
                  </div>

                  {station.operator && (
                    <div className="operator-info">
                      <h5>Operator:</h5>
                      <p>{station.operator.name}</p>
                      {station.operator.phone && (
                        <p>📞 {station.operator.phone}</p>
                      )}
                      {station.operator.website && (
                        <p>
                          <a href={station.operator.website} target="_blank" rel="noopener noreferrer">
                            🌐 Website
                          </a>
                        </p>
                      )}
                    </div>
                  )}

                  {station.amenities && station.amenities.length > 0 && (
                    <div className="amenities">
                      <h5>Amenities:</h5>
                      <div className="amenity-tags">
                        {station.amenities.map((amenity, index) => (
                          <span key={index} className="amenity-tag">{amenity}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="station-meta">
                    <p className="last-updated">
                      <strong>Last Updated:</strong> {' '}
                      {new Date(station.last_updated).toLocaleString()}
                    </p>
                    <p className="data-source">
                      <strong>Source:</strong> {station.data_source}
                    </p>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};

export default StationsMap; 