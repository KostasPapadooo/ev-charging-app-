// frontend/src/components/Dashboard.js
import React from 'react';
import StationsMap from '../components/StationsMap';
import '../styles/StationsMap.css';

const Dashboard = () => {
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>EV Charging Stations Dashboard</h1>
        <p className="dashboard-subtitle">
          Real-time monitoring of electric vehicle charging stations
        </p>
      </div>
      
      <StationsMap />
    </div>
  );
};

export default Dashboard;