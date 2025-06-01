// frontend/src/components/Dashboard.js
import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import '../styles/dashboard.css';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for marker icons not displaying
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const Dashboard = () => {
    const { user, logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [stations, setStations] = useState([]);

    useEffect(() => {
        // Fetch charging stations data (mock data for now)
        const fetchStations = async () => {
            // Replace with your API call to fetch stations
            const mockStations = [
                { id: 1, name: "Station 1", position: [51.505, -0.09] },
                { id: 2, name: "Station 2", position: [51.51, -0.1] },
            ];
            setStations(mockStations);
        };

        fetchStations();
    }, []);

    if (!isAuthenticated) {
        navigate('/login');
        return null;
    }

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <div className="dashboard-container">
            <h2>Charging Stations</h2>
            <div className="charging-station-map">
                <MapContainer center={[51.505, -0.09]} zoom={13} style={{ height: "400px", width: "100%" }}>
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                    {stations.map(station => (
                        <Marker key={station.id} position={station.position}>
                            <Popup>{station.name}</Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>
            <button onClick={handleLogout} className="logout-button">Logout</button>
        </div>
    );
};

export default Dashboard;