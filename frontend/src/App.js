// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useLocation } from 'react-router-dom';
// import logo from './logo.svg'; // Αφαιρέθηκε το logo προς το παρόν
import './App.css';
import './styles/header.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Register from './pages/Register';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import HomePage from './pages/HomePage';
import Footer from './components/Footer';
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

function AppContent() {
  const location = useLocation();
  const showFooter = location.pathname === '/' || location.pathname === '/dashboard';

  return (
    <>
      <Navigation />
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/" element={<HomePage />} />
      </Routes>
      {showFooter && <Footer />}
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <AppContent />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;