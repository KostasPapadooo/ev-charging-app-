// frontend/src/components/Dashboard.js
import React, { useState, useEffect } from 'react';
import StationsMap from '../components/StationsMap';
import LocationPermissionModal from '../components/LocationPermissionModal';
import { useAuth } from '../contexts/AuthContext';
import '../styles/StationsMap.css';
import '../styles/LocationPermission.css';

const Dashboard = () => {
  const { user } = useAuth();
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [locationPermission, setLocationPermission] = useState('prompt'); // 'prompt', 'granted', 'denied'
  const [userLocation, setUserLocation] = useState(null);
  const [isGettingLocation, setIsGettingLocation] = useState(false);
  const [locationError, setLocationError] = useState(null);

  // Check location permission status when component mounts
  useEffect(() => {
    checkLocationPermission();
  }, []);

  const checkLocationPermission = async () => {
    if (!navigator.geolocation) {
      setLocationPermission('denied');
      setLocationError('Geolocation is not supported by this browser');
      return;
    }

    try {
      // Check if permission API is available
      if ('permissions' in navigator) {
        const permission = await navigator.permissions.query({ name: 'geolocation' });
        
        console.log('Current permission state:', permission.state);
        
        if (permission.state === 'granted') {
          // Permission already granted, get location immediately
          await getCurrentLocationAndProceed();
        } else if (permission.state === 'denied') {
          setLocationPermission('denied');
          setLocationError('Location access has been denied. Please enable it in your browser settings.');
        } else {
          // Permission is 'prompt' - show modal
          setLocationPermission('prompt');
          setShowLocationModal(true);
        }
      } else {
        // Fallback for browsers without permissions API
        setLocationPermission('prompt');
        setShowLocationModal(true);
      }
    } catch (error) {
      console.error('Error checking location permission:', error);
      setLocationPermission('prompt');
      setShowLocationModal(true);
    }
  };

  const getCurrentLocationAndProceed = async () => {
    setIsGettingLocation(true);
    setLocationError(null);
    
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        setIsGettingLocation(false);
        setLocationPermission('denied');
        setLocationError('Location request timed out. Please try again.');
        reject(new Error('Timeout'));
      }, 15000);

      navigator.geolocation.getCurrentPosition(
        (position) => {
          clearTimeout(timeoutId);
          const location = {
            lat: position.coords.latitude,
            lon: position.coords.longitude,
            accuracy: position.coords.accuracy
          };
          
          console.log('GPS location obtained:', location);
          setUserLocation(location);
          setLocationPermission('granted');
          setIsGettingLocation(false);
          setLocationError(null);
          resolve(location);
        },
        (error) => {
          clearTimeout(timeoutId);
          console.error('Geolocation error:', error);
          setLocationPermission('denied');
          setIsGettingLocation(false);
          
          let errorMessage = 'Unable to get your location. ';
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage += 'Location access was denied. Please enable location access in your browser settings and refresh the page.';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage += 'Location information is unavailable. Please check your GPS settings.';
              break;
            case error.TIMEOUT:
              errorMessage += 'Location request timed out. Please try again.';
              break;
            default:
              errorMessage += 'An unknown error occurred.';
              break;
          }
          
          setLocationError(errorMessage);
          reject(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 300000 // 5 minutes
        }
      );
    });
  };

  const handleLocationRequest = async () => {
    try {
      setShowLocationModal(false);
      await getCurrentLocationAndProceed();
    } catch (error) {
      console.error('Failed to get location:', error);
      // Error handling is done in getCurrentLocationAndProceed
    }
  };

  const handleLocationDenied = () => {
    setShowLocationModal(false);
    setLocationPermission('denied');
    setLocationError('Location access is required to show nearby charging stations. You can still use the app with a default location (Athens center).');
  };

  const handleRetryLocation = () => {
    setLocationError(null);
    setLocationPermission('prompt');
    setShowLocationModal(true);
  };

  // Show location permission modal
  if (showLocationModal) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h1>Welcome back, {user?.first_name}!</h1>
          <p className="dashboard-subtitle">
            Real-time monitoring of electric vehicle charging stations
          </p>
        </div>
        
        <LocationPermissionModal
          onAllow={handleLocationRequest}
          onDeny={handleLocationDenied}
        />
      </div>
    );
  }

  // Show GPS detection loading
  if (isGettingLocation) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h1>Welcome back, {user?.first_name}!</h1>
          <p className="dashboard-subtitle">
            Real-time monitoring of electric vehicle charging stations
          </p>
        </div>
        
        <div className="location-detecting">
          <div className="location-detecting-spinner"></div>
          <span className="location-detecting-text">
            📍 Detecting your GPS location...
          </span>
        </div>
      </div>
    );
  }

  // Show error state if location was denied
  if (locationPermission === 'denied') {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h1>Welcome back, {user?.first_name}!</h1>
          <p className="dashboard-subtitle">
            Real-time monitoring of electric vehicle charging stations
          </p>
        </div>
        
        <div className="location-error-container">
          <div className="location-error">
            <h3>📍 Location Access Required</h3>
            <p className="error-message">
              {locationError || 'To show you nearby EV charging stations, we need access to your location.'}
            </p>
            
            <div className="location-instructions">
              <h4>To enable location access:</h4>
              <ol>
                <li>Click the location icon (🔒 or 🌐) in your browser's address bar</li>
                <li>Select "Allow" for location access</li>
                <li>Refresh the page or click "Try Again" below</li>
              </ol>
              
              <p className="alternative-note">
                <strong>Alternative:</strong> You can still use the app with a default location (Athens center), 
                but you won't see personalized nearby stations.
              </p>
            </div>
            
            <div className="location-error-actions">
              <button 
                onClick={handleRetryLocation}
                className="retry-location-button primary"
              >
                🔄 Try Again
              </button>
              
              <button 
                onClick={() => {
                  setLocationPermission('granted');
                  setUserLocation({ lat: 37.9755, lon: 23.7348 }); // Athens center
                }}
                className="retry-location-button secondary"
              >
                📍 Use Default Location (Athens)
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Only show map when we have user location and permission is granted
  if (locationPermission === 'granted' && userLocation) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h1>Welcome back, {user?.first_name}!</h1>
          <p className="dashboard-subtitle">
            Real-time monitoring of electric vehicle charging stations
          </p>
        </div>
        
        <StationsMap 
          userLocation={userLocation}
          locationPermission={locationPermission}
        />
      </div>
    );
  }

  // Fallback loading state
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome back, {user?.first_name}!</h1>
        <p className="dashboard-subtitle">
          Real-time monitoring of electric vehicle charging stations
        </p>
      </div>
      
      <div className="loading-overlay">
        <div className="loading-spinner">
          Initializing...
        </div>
      </div>
    </div>
  );
};

export default Dashboard;