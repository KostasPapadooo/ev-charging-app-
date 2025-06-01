import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
    const { user, logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    if (!isAuthenticated) {
        navigate('/login');
        return null;
    }

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <div>
            <h2>Dashboard</h2>
            <div>
                <h3>Welcome, {user.first_name} {user.last_name}!</h3>
                <p><strong>Email:</strong> {user.email}</p>
                <p><strong>Phone:</strong> {user.phone}</p>
                <p><strong>Subscription Tier:</strong> {user.subscription_tier}</p>
                <p><strong>Account Status:</strong> {user.is_active ? 'Active' : 'Inactive'}</p>
                <p><strong>Member Since:</strong> {new Date(user.created_at).toLocaleDateString()}</p>
            </div>
            <button onClick={handleLogout}>Logout</button>
        </div>
    );
};

export default Dashboard; 