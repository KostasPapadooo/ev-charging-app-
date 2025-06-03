// frontend/src/components/Dashboard.js
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import StationsMap from '../components/StationsMap';
import '../styles/Dashboard.css';

const Dashboard = () => {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [userLocation, setUserLocation] = useState(null);
  const [locationPermission, setLocationPermission] = useState('prompt');
  const [locationError, setLocationError] = useState(null);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);

  // Redirect to home if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, authLoading, navigate]);

  // Fetch stations data
  const fetchStations = useCallback(async (lat, lon) => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/api/stations/nearby/search?lat=${lat}&lon=${lon}&radius=5000&limit=1000`
      );
      const data = await response.json();
      setStations(data.stations || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stations:', error);
      setStations([]);
      setLoading(false);
    }
  }, []);

  // Get status counts from actual stations data
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

  const getCurrentLocationAndProceed = useCallback(() => {
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
          
          // Fetch stations when location is obtained
          fetchStations(location.lat, location.lon);
        },
        (error) => {
          console.error('Geolocation error:', error);
          setLocationError(`Location error: ${error.message}`);
          setLocationPermission('denied');
          
          // Use default location (Athens center)
          const defaultLocation = { lat: 37.9838, lon: 23.7275 };
          setUserLocation(defaultLocation);
          fetchStations(defaultLocation.lat, defaultLocation.lon);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
      );
    } else {
      setLocationError('Geolocation is not supported by this browser.');
      setLocationPermission('denied');
      
      // Use default location
      const defaultLocation = { lat: 37.9838, lon: 23.7275 };
      setUserLocation(defaultLocation);
      fetchStations(defaultLocation.lat, defaultLocation.lon);
    }
  }, [fetchStations]);

  useEffect(() => {
    // Only proceed if user is authenticated
    if (isAuthenticated && user) {
      getCurrentLocationAndProceed();
    }
  }, [getCurrentLocationAndProceed, isAuthenticated, user]);

  const handleLocationRequest = async () => {
    setShowLocationModal(false);
    await getCurrentLocationAndProceed();
  };

  const handleLocationDenied = async () => {
    setShowLocationModal(false);
    setLocationPermission('denied');
    
    // Use default location
    const defaultLocation = { lat: 37.9838, lng: 23.7275, accuracy: null };
    setUserLocation(defaultLocation);
    await fetchStations(defaultLocation.lat, defaultLocation.lng);
    setLoading(false);
    
    setLocationError('Location access denied. Using Athens center as default.');
  };

  const handleRetryLocation = () => {
    setLocationError(null);
    setLocationPermission('prompt');
    setShowLocationModal(true);
  };

  // Manual refresh function
  const handleRefresh = useCallback(() => {
    if (userLocation) {
      fetchStations(userLocation.lat, userLocation.lon);
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

  // Show loading state
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
            Loading stations...
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
      
      <StationsMap 
        userLocation={userLocation}
        locationPermission={locationPermission}
        stations={stations}
        onRefresh={handleRefresh}
      />
    </div>
  );
};

export default Dashboard;