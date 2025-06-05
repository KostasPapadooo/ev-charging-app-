import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/HomePage.css';

const HomePage = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="homepage-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">⚡ EV Charging Stations</h1>
          <p className="hero-subtitle">
            Find, monitor, and manage electric vehicle charging stations in real-time
          </p>
          
          {isAuthenticated ? (
            <div className="welcome-section">
              <h2>Welcome back, {user.first_name}! 👋</h2>
              <p className="user-info">
                You have a <span className={`subscription-${user.subscription_tier}`}>
                  {user.subscription_tier}
                </span> subscription
              </p>
              <Link to="/dashboard" className="cta-button primary">
                Go to Dashboard
              </Link>
            </div>
          ) : (
            <div className="auth-section">
              <p className="auth-message">
                Join thousands of EV drivers finding charging stations effortlessly
              </p>
              <div className="auth-buttons">
                <Link to="/register" className="cta-button primary">
                  Get Started
                </Link>
                <Link to="/login" className="cta-button secondary">
                  Sign In
                </Link>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="container">
          <h2 className="section-title">Why Choose Our Platform?</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🗺️</div>
              <h3>Real-time Map</h3>
              <p>Interactive map showing all available charging stations with live status updates</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Live Analytics</h3>
              <p>Monitor availability rates and station statistics in real-time</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">📍</div>
              <h3>Location-based</h3>
              <p>Find nearby stations based on your current location with customizable radius</p>
            </div>
            
            <div className="feature-card premium-feature">
              <div className="feature-icon">❤️</div>
              <h3>Favorites <span className="premium-tag">Premium</span></h3>
              <p>Save your favorite stations for quick access (Premium feature)</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🔄</div>
              <h3>Auto-refresh</h3>
              <p>Station data updates automatically every 5 seconds for accurate information</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">📱</div>
              <h3>Mobile Friendly</h3>
              <p>Responsive design that works perfectly on all devices</p>
            </div>
          </div>
        </div>
      </section>

      {/* Subscription Plans */}
      {!isAuthenticated && (
        <section className="plans-section">
          <div className="container">
            <h2 className="section-title">Choose Your Plan</h2>
            <div className="plans-grid">
              <div className="plan-card">
                <h3>Free</h3>
                <div className="plan-price">€0<span>/month</span></div>
                <ul className="plan-features">
                  <li>✅ View all charging stations</li>
                  <li>✅ Real-time availability</li>
                  <li>✅ Location-based search</li>
                  <li>✅ Live analytics</li>
                  <li>❌ Favorite stations</li>
                </ul>
                <Link to="/register" className="plan-button secondary">
                  Start Free
                </Link>
              </div>
              
              <div className="plan-card premium">
                <div className="plan-badge">Most Popular</div>
                <h3>Premium</h3>
                <div className="plan-price">€9.99<span>/month</span></div>
                <ul className="plan-features">
                  <li>✅ Everything in Free</li>
                  <li>✅ Favorite stations</li>
                  <li>✅ Priority support</li>
                  <li>✅ Advanced filters</li>
                  <li>✅ Export data</li>
                </ul>
                <Link to="/register" className="plan-button primary">
                  Go Premium
                </Link>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Stats Section */}
      <section className="stats-section">
        <div className="container">
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-number">1000+</div>
              <div className="stat-label">Charging Stations</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">24/7</div>
              <div className="stat-label">Real-time Monitoring</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">5s</div>
              <div className="stat-label">Update Frequency</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">3km</div>
              <div className="stat-label">Max Search Radius</div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="homepage-footer">
        <div className="container">
          <p>&copy; 2024 EV Charging Stations. All rights reserved.</p>
          <div className="footer-links">
            <a href="#privacy">Privacy Policy</a>
            <a href="#terms">Terms of Service</a>
            <a href="#contact">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage; 