// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
// import logo from './logo.svg'; // Αφαιρέθηκε το logo προς το παρόν
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Register from './components/Register';
import Login from './components/Login';
import Dashboard from './components/Dashboard';

function Navigation() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <nav style={{ padding: '1rem', borderBottom: '1px solid #ccc' }}>
      <Link to="/" style={{ marginRight: '1rem' }}>Home</Link>
      {!isAuthenticated ? (
        <>
          <Link to="/login" style={{ marginRight: '1rem' }}>Login</Link>
          <Link to="/register" style={{ marginRight: '1rem' }}>Register</Link>
        </>
      ) : (
        <>
          <Link to="/dashboard" style={{ marginRight: '1rem' }}>Dashboard</Link>
          <span style={{ marginRight: '1rem' }}>
            Welcome, {user?.first_name} ({user?.subscription_tier})
          </span>
          <button onClick={logout}>Logout</button>
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