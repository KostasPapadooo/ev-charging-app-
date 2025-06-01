// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
// import logo from './logo.svg'; // Αφαιρέθηκε το logo προς το παρόν
import './App.css';
import Register from './components/Register';
import Login from './components/Login';

function HomePage() {
  return (
    <header className="App-header">
      <h1>Welcome to EV Charging Stations</h1>
      <nav>
        <ul>
          <li>
            <Link to="/login" className="App-link">Login</Link>
          </li>
          <li>
            <Link to="/register" className="App-link">Register</Link>
          </li>
        </ul>
      </nav>
    </header>
  );
}

function App() {
  return (
    <Router>
      <div className="App">
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<HomePage />} />
          </Routes>
      </div>
    </Router>
  );
}

export default App;