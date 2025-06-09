// frontend/src/components/Dashboard.js
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import StationsMap from '../components/StationsMap';
import AvailabilityRate from '../components/AvailabilityRate';
import UserAnalytics from '../components/UserAnalytics';
import '../styles/Dashboard.css';
import { io } from 'socket.io-client';

const Dashboard = () => {
  const { user, isAuthenticated, isPremium, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [userLocation, setUserLocation] = useState(null);
  const [locationPermission, setLocationPermission] = useState('prompt');
  const [locationError, setLocationError] = useState(null);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [stations, setStations] = useState([]); // Single source of truth for stations
  const [loading, setLoading] = useState(true);
  const [currentRadius, setCurrentRadius] = useState(500);
  const socketRef = useRef(null);

  // Redirect to home if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, authLoading, navigate]);

  // Unified function to fetch stations data
  const fetchStations = useCallback(async (lat, lon, radius, showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/stations/nearby/search?lat=${lat}&lon=${lon}&radius=${radius}&limit=1000`
      );
      const data = await response.json();
      console.log(`[DEBUG] Fetched ${data.stations?.length || 0} stations for radius ${radius}m:`, data.stations);
      setStations(data.stations || []); // Always update the single source of truth
      setCurrentRadius(radius);
    } catch (error) {
      console.error('Error fetching stations:', error);
      setStations([]);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  // Get status counts from the single source of truth
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
  
  const getCurrentLocationAndProceed = useCallback((radius = 500) => {
    if (navigator.geolocation) {
      setLocationPermission('requesting');
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lon: position.coords.longitude,
            accuracy: position.coords.accuracy
          };
          setUserLocation(location);
          setLocationPermission('granted');
          setLocationError(null);
          setShowLocationModal(false);
          fetchStations(location.lat, location.lon, radius);
        },
        (error) => {
          console.error('Geolocation error:', error);
          setLocationError(`Location error: ${error.message}`);
          setLocationPermission('denied');
          const defaultLocation = { lat: 37.9838, lon: 23.7275 };
          setUserLocation(defaultLocation);
          fetchStations(defaultLocation.lat, defaultLocation.lon, radius);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
      );
    } else {
      setLocationError('Geolocation is not supported by this browser.');
      setLocationPermission('denied');
      const defaultLocation = { lat: 37.9838, lon: 23.7275 };
      setUserLocation(defaultLocation);
      fetchStations(defaultLocation.lat, defaultLocation.lon, radius);
    }
  }, [fetchStations]);

  // WebSocket integration
  useEffect(() => {
    // With the new backend architecture, Socket.IO is the main entry point.
    // We can connect directly without specifying a path, as it's now at the root.
    const socket = io('http://127.0.0.1:8000');

    socket.on('connect', () => {
      console.log('Successfully connected to WebSocket server!');
    });

    socket.on('connection_response', (data) => {
      console.log('Server says:', data.message);
    });

    socket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err.message);
    });

    socketRef.current = socket;

    // Listen for status updates
    socketRef.current.on('status_update', (data) => {
      if (!data || !data.stations) return;

      setStations((prevStations) => {
        // Create a map for quick lookups
        const updatesMap = new Map(data.stations.map(s => [s.station_id, s.new_status]));
        
        // Return a new array with updated statuses
        return prevStations.map(station => {
          if (updatesMap.has(station.tomtom_id)) {
            return { ...station, status: updatesMap.get(station.tomtom_id) };
          }
          return station;
        });
      });
    });

    // Disconnect on cleanup
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []); // Empty dependency array ensures this runs only once

  // Initial load effect
  useEffect(() => {
    if (isAuthenticated && user) {
      getCurrentLocationAndProceed();
    }
  }, [isAuthenticated, user, getCurrentLocationAndProceed]);


  const handleLocationRequest = () => {
    setShowLocationModal(false);
    getCurrentLocationAndProceed();
  };

  const handleLocationDenied = () => {
    setShowLocationModal(false);
    setLocationPermission('denied');
    const defaultLocation = { lat: 37.9838, lon: 23.7275, accuracy: null };
    setUserLocation(defaultLocation);
    fetchStations(defaultLocation.lat, defaultLocation.lon, 500);
    setLoading(false);
    setLocationError('Location access denied. Using Athens center as default.');
  };

  const handleRetryLocation = () => {
    setLocationError(null);
    setLocationPermission('prompt');
    setShowLocationModal(true);
  };

  // Callback for when the radius is changed in the map component
  const handleRadiusChange = useCallback((newRadius) => {
    if (userLocation) {
      fetchStations(userLocation.lat, userLocation.lon, newRadius, true);
    }
  }, [userLocation, fetchStations]);

  // Show loading state while checking authentication
  if (authLoading) {
    return (
      <div className="dashboard-container">
        <div className="loading-overlay">
          <div className="loading-spinner">
            Loading...
          </div>
        </div>
      </div>
    );
  }

  // Don't render anything if not authenticated (will redirect)
  if (!isAuthenticated || !user) {
    return null;
  }
  
  // Show main loading state for station fetching
  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-header">
          <h1>Welcome back, {user?.first_name}!</h1>
          <p className="dashboard-subtitle">
            Real-time monitoring of electric vehicle charging stations
          </p>
        </div>
        <div className="loading-overlay">
          <div className="loading-spinner">
            Finding nearby stations...
          </div>
        </div>
      </div>
    );
  }

  // Show location permission modal
  if (showLocationModal) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-header">
          <h1>Welcome back, {user?.first_name}!</h1>
          <p className="dashboard-subtitle">
            Real-time monitoring of electric vehicle charging stations
          </p>
        </div>
        
        <div className="location-modal">
          <div className="modal-content">
            <h3>📍 Location Access</h3>
            <p>We need your location to show nearby charging stations.</p>
            <div className="modal-buttons">
              <button onClick={handleLocationRequest} className="btn-primary">
                Allow Location
              </button>
              <button onClick={handleLocationDenied} className="btn-secondary">
                Use Default Location
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main dashboard view
  const statusCounts = getStatusCounts(stations);

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Welcome back, {user?.first_name}!</h1>
        <p className="dashboard-subtitle">
          Real-time monitoring of electric vehicle charging stations
        </p>
      </div>
      
      {locationError && (
        <div className="location-error">
          <span>{locationError}</span>
          <button onClick={handleRetryLocation} className="retry-btn">
            Retry
          </button>
        </div>
      )}

      {!isPremium && (
        <div className="premium-upgrade-banner">
          <div className="upgrade-content">
            <span className="upgrade-icon">👑</span>
            <div className="upgrade-text">
              <strong>Upgrade to Premium</strong>
              <p>Unlock favorite stations and exclusive features!</p>
            </div>
            <button className="upgrade-btn">Upgrade Now</button>
          </div>
        </div>
      )}

      <div className="search-radius-info">
        <p>Showing stations within <strong>{currentRadius}m</strong> from your location</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total</h3>
          <span className="stat-number">{statusCounts.total}</span>
        </div>
        <div className="stat-card available">
          <h3>Available</h3>
          <span className="stat-number">{statusCounts.available}</span>
        </div>
        <div className="stat-card busy">
          <h3>Busy</h3>
          <span className="stat-number">{statusCounts.busy}</span>
        </div>
        <div className="stat-card out-of-order">
          <h3>Out of Order</h3>
          <span className="stat-number">{statusCounts.outOfOrder}</span>
        </div>
        <div className="stat-card unknown">
          <h3>Unknown</h3>
          <span className="stat-number">{statusCounts.unknown}</span>
        </div>
      </div>
      
      <AvailabilityRate stations={stations} />
      
      <StationsMap 
        userLocation={userLocation}
        locationPermission={locationPermission}
        stations={stations} // Pass the single source of truth
        currentRadius={currentRadius}
        onRadiusChange={handleRadiusChange} // Pass the handler
      />
      
      <UserAnalytics />
    </div>
  );
};

export default Dashboard;