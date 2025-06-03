import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../styles/StationsMap.css';

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
  switch (status?.toUpperCase()) {
    case 'AVAILABLE':
      return 'green';
    case 'OCCUPIED':
    case 'BUSY':
      return 'red';
    case 'OUT_OF_ORDER':
    case 'OUTOFORDER':
      return 'gray';
    case 'UNKNOWN':
    default:
      return 'orange';
  }
};

const StationsMap = ({ userLocation, locationPermission, stations = [], onRefresh }) => {
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');
  const [radius, setRadius] = useState(5000); // Επαναφορά του radius state

  const loadNearbyStations = useCallback(async (lat, lon) => {
    if (!lat || !lon) return;
    
    try {
      setLoading(true);
      // Just set loading to false since stations come from props
      setLoading(false);
    } catch (err) {
      console.error('Error loading stations:', err);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (userLocation?.lat && userLocation?.lon) {
      loadNearbyStations(userLocation.lat, userLocation.lon);
    }
  }, [userLocation, loadNearbyStations]);

  useEffect(() => {
    if (userLocation?.lat && userLocation?.lon && filter) {
      loadNearbyStations(userLocation.lat, userLocation.lon);
    }
  }, [filter, userLocation, loadNearbyStations]);

  const filteredStations = stations.filter(station => {
    if (!filter) return true;
    return station.status?.toLowerCase() === filter.toLowerCase();
  });

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
  };

  const handleRadiusChange = (newRadius) => {
    console.log(`Changing radius from ${radius}m to ${newRadius}m`);
    setRadius(newRadius);
    // The useEffect will automatically trigger loadNearbyStations
  };

  // Calculate stats for filtered stations
  const getStatusStats = () => {
    return {
      total: filteredStations.length,
      available: filteredStations.filter(s => s.status?.toUpperCase() === 'AVAILABLE').length,
      busy: filteredStations.filter(s => ['OCCUPIED', 'BUSY'].includes(s.status?.toUpperCase())).length,
      outOfOrder: filteredStations.filter(s => ['OUT_OF_ORDER', 'OUTOFORDER'].includes(s.status?.toUpperCase())).length,
      unknown: filteredStations.filter(s => !s.status || s.status?.toUpperCase() === 'UNKNOWN').length
    };
  };

  const stats = getStatusStats();

  // Don't render anything if we don't have user location
  if (!userLocation || locationPermission !== 'granted') {
    return null;
  }

  if (!userLocation) {
    return (
      <div className="map-container">
        <div className="loading-message">
          Getting your location...
        </div>
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
            onChange={(e) => handleFilterChange(e.target.value)}
            className="status-filter"
          >
            <option value="">All Stations</option>
            <option value="AVAILABLE">Available</option>
            <option value="OCCUPIED">Busy</option>
            <option value="OUT_OF_ORDER">Out of Order</option>
          </select>
          
          <label htmlFor="radius-filter">Search Radius:</label>
          <select
            id="radius-filter"
            value={radius}
            onChange={(e) => handleRadiusChange(parseInt(e.target.value))}
            className="radius-filter"
          >
            <option value="500">500m</option>
            <option value="1000">1 km</option>
            <option value="2000">2 km</option>
            <option value="3000">3 km</option>
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


        <button onClick={handleRefresh} className="refresh-button" disabled={loading}>
          {loading ? '🔄 Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

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
          {filteredStations.map((station) => (
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
                    <span className={`status-badge ${station.status?.toLowerCase()}`}>
                      {station.status || 'Unknown'}
                    </span>
                  </div>

                  <div className="connectors-info">
                    <h5>Connectors:</h5>
                    {station.connectors && station.connectors.length > 0 ? (
                      station.connectors.map((connector, index) => (
                        <div key={index} className="connector">
                          <span className="connector-type">{connector.type}</span>
                          <span className="connector-power">{connector.power_kw}kW</span>
                          <span className={`connector-status ${connector.status?.toLowerCase()}`}>
                            {connector.status || 'Unknown'}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p>No connector information available</p>
                    )}
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
                      {station.last_updated ? new Date(station.last_updated).toLocaleString() : 'N/A'}
                    </p>
                    <p className="data-source">
                      <strong>Source:</strong> {station.data_source || 'TomTom'}
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