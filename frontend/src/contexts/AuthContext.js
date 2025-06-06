import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);
    const [favoriteStations, setFavoriteStations] = useState([]);
    const [isPremium, setIsPremium] = useState(false);

    // Set up axios interceptor for authentication
    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        } else {
            delete axios.defaults.headers.common['Authorization'];
        }
    }, [token]);

    // Check premium status
    const checkPremiumStatus = async () => {
        if (!token) {
            setIsPremium(false);
            return;
        }
        
        try {
            const response = await axios.get('http://127.0.0.1:8000/api/auth/premium-status');
            setIsPremium(response.data.is_premium);
        } catch (error) {
            console.error('Failed to check premium status:', error);
            setIsPremium(false);
        }
    };

    // Check if user is logged in on app start
    useEffect(() => {
        const checkAuth = async () => {
            if (token) {
                try {
                    const response = await axios.get('http://127.0.0.1:8000/api/auth/me');
                    setUser(response.data);
                    // Check premium status
                    setIsPremium(response.data.subscription_tier === 'premium');
                    // Fetch favorite stations if available and user is premium
                    if (response.data.subscription_tier === 'premium' && response.data.favorite_stations) {
                        setFavoriteStations(response.data.favorite_stations);
                    }
                } catch (error) {
                    console.error('Auth check failed:', error);
                    logout();
                }
            }
            setLoading(false);
        };

        checkAuth();
    }, [token]);

    const login = async (email, password) => {
        try {
            const params = new URLSearchParams();
            params.append('username', email);
            params.append('password', password);

            const response = await axios.post('http://127.0.0.1:8000/api/auth/login', params, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            const { access_token, user: userData } = response.data;
            
            setToken(access_token);
            setUser(userData);
            // Check premium status
            setIsPremium(userData.subscription_tier === 'premium');
            // Load favorite stations only for premium users
            if (userData.subscription_tier === 'premium' && userData.favorite_stations) {
                setFavoriteStations(userData.favorite_stations);
            }
            localStorage.setItem('token', access_token);
            
            return { success: true, user: userData };
        } catch (error) {
            console.error('Login failed:', error);
            return { 
                success: false, 
                error: error.response?.data?.detail || 'Login failed' 
            };
        }
    };

    const register = async (userData) => {
        try {
            const response = await axios.post('http://127.0.0.1:8000/api/auth/register', userData);
            return { success: true, user: response.data };
        } catch (error) {
            console.error('Registration failed:', error);
            return { 
                success: false, 
                error: error.response?.data?.detail || 'Registration failed' 
            };
        }
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        setFavoriteStations([]);
        setIsPremium(false);
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
        
        // Force a page reload to clear any cached data
        window.location.href = '/';
    };

    const toggleFavoriteStation = async (stationId) => {
        if (!user) return { success: false, error: 'User not logged in' };
        
        // Check if user is premium
        if (!isPremium) {
            return { 
                success: false, 
                error: 'Favorite stations feature is available only for premium users. Please upgrade your subscription.' 
            };
        }

        try {
            const isFavorite = favoriteStations.includes(stationId);
            const action = isFavorite ? 'remove' : 'add';
            
            // Debug logging
            console.log('Toggle Favorite Station Debug:');
            console.log('- Station ID:', stationId);
            console.log('- Action:', action);
            console.log('- Current token:', !!token);
            console.log('- Current user:', !!user);
            console.log('- Is Premium:', isPremium);
            console.log('- Authorization header:', axios.defaults.headers.common['Authorization']);
            
            const response = await axios.post('http://127.0.0.1:8000/api/auth/favorites', {
                station_id: stationId,
                action: action
            });

            if (response.data) {
                setUser(response.data);
                if (action === 'add') {
                    setFavoriteStations([...favoriteStations, stationId]);
                } else {
                    setFavoriteStations(favoriteStations.filter(id => id !== stationId));
                }
                return { success: true, isFavorite: !isFavorite };
            }
            return { success: false, error: 'Failed to update favorites' };
        } catch (error) {
            console.error('Failed to toggle favorite station:', error);
            console.error('Error response:', error.response?.data);
            console.error('Error status:', error.response?.status);
            
            // Handle 403 Forbidden specifically
            if (error.response?.status === 403) {
                return { 
                    success: false, 
                    error: error.response.data.detail || 'Premium feature - please upgrade your subscription' 
                };
            }
            
            return { success: false, error: error.message };
        }
    };

    const value = {
        user,
        token,
        login,
        register,
        logout,
        loading,
        isAuthenticated: !!user && !!token,
        isPremium,
        favoriteStations,
        toggleFavoriteStation
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}; 