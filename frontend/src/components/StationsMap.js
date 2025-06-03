import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../styles/StationsMap.css';

// Fix for default markers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom icons for different station statuses
const createCustomIcon = (status) => {
  let color = '#6c757d'; // default gray
  
  switch (status?.toUpperCase()) {
    case 'AVAILABLE':
      color = '#28a745'; // green
      break;
    case 'OCCUPIED':
    case 'BUSY':
      color = '#dc3545'; // red
      break;
    case 'OUT_OF_ORDER':
    case 'OUTOFORDER':
      color = '#6c757d'; // gray
      break;
    case 'UNKNOWN':
    default:
      color = '#ffc107'; // yellow
      break;
  }

  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${color};
      width: 20px;
      height: 20px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    "></div>`,
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

const StationsMap = ({ 
  userLocation, 
  locationPermission, 
  stations = [], 
  currentRadius = 500,
  onRefresh, 
  onRadiusChange 
}) => {
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');
  const [radius, setRadius] = useState(currentRadius);

  // Update local radius when currentRadius prop changes
  useEffect(() => {
    setRadius(currentRadius);
  }, [currentRadius]);

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
    console.log(`StationsMap: Refreshing with current radius ${radius}m`);
    if (onRefresh) {
      onRefresh(radius);
    }
  };

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
  };

  const handleRadiusChange = (newRadius) => {
    console.log(`StationsMap: Radius changed from ${radius}m to ${newRadius}m`);
    setRadius(newRadius);
    if (onRadiusChange) {
      onRadiusChange(newRadius);
    }
  };

  // Get status counts for the current filtered stations
  const getStatusCounts = (stations) => {
    const counts = {
      total: stations.length,
      available: 0,
      busy: 0,
      outOfOrder: 0,
      unknown: 0
    };

    stations.forEach(station => {
      const status = station.status?.toUpperCase();
      switch (status) {
        case 'AVAILABLE':
          counts.available++;
          break;
        case 'OCCUPIED':
        case 'BUSY':
          counts.busy++;
          break;
        case 'OUT_OF_ORDER':
        case 'OUTOFORDER':
          counts.outOfOrder++;
          break;
        case 'UNKNOWN':
        default:
          counts.unknown++;
          break;
      }
    });

    return counts;
  };

  const statusCounts = getStatusCounts(filteredStations);

  if (!userLocation) {
    return (
      <div className="stations-map-container">
        <div className="location-error">
          <h3>Location Required</h3>
          <p>Please allow location access to view nearby charging stations.</p>
          <ol>
            <li>Click the location icon in your browser's address bar</li>
            <li>Select "Allow" for location access</li>
            <li>Refresh the page</li>
          </ol>
        </div>
      </div>
    );
  }

  return (
    <div className="stations-map-container">
      {/* Map Controls */}
      <div className="map-controls">
        <div className="location-info">
          <div className="current-location">
            <span className="location-icon">📍Your Location</span>
            <span>
              {userLocation.lat.toFixed(4)}, {userLocation.lon.toFixed(4)}
            </span>
            {userLocation.accuracy && (
              <span className="accuracy">
                (±{Math.round(userLocation.accuracy)}m)
              </span>
            )}
          </div>
          
          <div className="filter-section">
            <select 
              className="radius-filter"
              value={radius}
              onChange={(e) => handleRadiusChange(parseInt(e.target.value))}
            >
              <option value={500}>500m radius</option>
              <option value={1000}>1km radius</option>
              <option value={2000}>2km radius</option>
              <option value={3000}>3km radius</option>
            </select>
            
          
          </div>
        </div>

        {/* Status Filter */}
        <div className="status-filters">
          <button 
            className={`filter-btn ${filter === '' ? 'active' : ''}`}
            onClick={() => handleFilterChange('')}
          >
            All ({statusCounts.total})
          </button>
          <button 
            className={`filter-btn available ${filter === 'available' ? 'active' : ''}`}
            onClick={() => handleFilterChange('available')}
          >
            Available ({statusCounts.available})
          </button>
          <button 
            className={`filter-btn busy ${filter === 'busy' ? 'active' : ''}`}
            onClick={() => handleFilterChange('busy')}
          >
            Busy ({statusCounts.busy})
          </button>
          <button 
            className={`filter-btn out-of-order ${filter === 'out_of_order' ? 'active' : ''}`}
            onClick={() => handleFilterChange('out_of_order')}
          >
            Out of Order ({statusCounts.outOfOrder})
          </button>
          <button 
            className={`filter-btn unknown ${filter === 'unknown' ? 'active' : ''}`}
            onClick={() => handleFilterChange('unknown')}
          >
            Unknown ({statusCounts.unknown})
          </button>
        </div>
      </div>

      {/* Search Info */}
      <div className="search-info">
        <p>
          Showing {filteredStations.length} stations within {radius}m 
          {filter && ` (filtered by: ${filter})`}
        </p>
      </div>

      {/* Map */}
      <div className="map-wrapper">
        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner">
              Loading stations...
            </div>
          </div>
        )}
        
        <MapContainer
          center={[userLocation.lat, userLocation.lon]}
          zoom={radius <= 500 ? 16 : radius <= 1000 ? 15 : radius <= 2000 ? 14 : radius <= 5000 ? 13 : 12}
          className="stations-map"
          style={{ height: '500px', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {/* User location marker */}
          <Marker position={[userLocation.lat, userLocation.lon]}>
            <Popup>
              <div className="user-location-popup">
                <h4>Your Location</h4>
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
                      <p><strong>Operator:</strong> {station.operator.name}</p>
                    </div>
                  )}

                  <div className="station-meta">
                    <p>Distance: ~{Math.round(station.distance || 0)}m</p>
                    {station.last_updated && (
                      <p className="last-updated">
                        Updated: {new Date(station.last_updated).toLocaleString()}
                      </p>
                    )}
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