// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
// import logo from './logo.svg'; // Αφαιρέθηκε το logo προς το παρόν
import './App.css';
import './styles/header.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Register from './pages/Register';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import './styles/Dashboard.css';

function Navigation() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <nav className="navigation">
      <Link to="/" className="nav-link">Home</Link>
      {!isAuthenticated ? (
        <>
          <Link to="/login" className="nav-link">Login</Link>
          <Link to="/register" className="nav-link">Register</Link>
        </>
      ) : (
        <>
          <Link to="/dashboard" className="nav-link">Dashboard</Link>
          <span className="nav-link">
            Welcome, {user?.first_name} 
            {user?.subscription_tier === 'premium' && (
              <span className="premium-badge">👑 Premium</span>
            )}
            {user?.subscription_tier === 'free' && (
              <span className="free-badge">Free</span>
            )}
          </span>
          <button onClick={logout} className="logout-button">Logout</button>
        </>
      )}
    </nav>
  );
}

function HomePage() {
  const { isAuthenticated, user } = useAuth();

  return (
    <header className="App-header">
      <h1>Welcome to EV Charging Stations</h1>
      {isAuthenticated ? (
        <div>
          <p>Hello, {user.first_name}! You have a {user.subscription_tier} subscription.</p>
          <Link to="/dashboard" className="App-link">Go to Dashboard</Link>
        </div>
      ) : (
        <div>
          <p>Please login or register to access the platform.</p>
          <Link to="/login" className="App-link">Login</Link>
          {' | '}
          <Link to="/register" className="App-link">Register</Link>
        </div>
      )}
    </header>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Navigation />
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/" element={<HomePage />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;