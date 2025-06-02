import React from 'react';
import '../styles/LocationPermission.css';

const LocationPermissionModal = ({ onAllow, onDeny }) => {
  return (
    <div className="location-modal-overlay">
      <div className="location-modal">
        <div className="location-modal-header">
          <h2>📍 Location Access Required</h2>
        </div>
        
        <div className="location-modal-content">
          <div className="location-icon">
            🗺️
          </div>
          
          <p className="location-message">
            To show you nearby EV charging stations, we need access to your location.
          </p>
          
          <div className="location-benefits">
            <h4>This will help us:</h4>
            <ul>
              <li>🎯 Find charging stations near you</li>
              <li>📍 Show accurate distances</li>
              <li>🔄 Provide real-time availability</li>
              <li>🚗 Optimize your charging route</li>
            </ul>
          </div>
          
          <div className="location-privacy">
            <p className="privacy-note">
              <strong>Privacy:</strong> Your location is only used to find nearby stations 
              and is not stored or shared with third parties.
            </p>
          </div>
        </div>
        
        <div className="location-modal-actions">
          <button 
            className="location-allow-btn"
            onClick={onAllow}
          >
            Allow Location Access
          </button>
          
          <button 
            className="location-deny-btn"
            onClick={onDeny}
          >
            Use Default Location
          </button>
        </div>
      </div>
    </div>
  );
};

export default LocationPermissionModal; 