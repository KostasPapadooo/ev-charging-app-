import React, { useState } from 'react';
import axios from 'axios';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            // Το API endpoint είναι τώρα /api/auth/login
            // Για OAuth2PasswordRequestForm, τα δεδομένα στέλνονται ως form-data
            const params = new URLSearchParams();
            params.append('username', email);
            params.append('password', password);

            const response = await axios.post('http://localhost:8000/api/auth/login', params, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });
            localStorage.setItem('token', response.data.access_token); // Αποθήκευση token
            console.log("Login successful, token:", response.data.access_token);
            // TODO: Redirect ή ενημέρωση UI
        } catch (error) {
            console.error("Login failed", error.response ? error.response.data : error.message);
            // TODO: Εμφάνιση μηνύματος σφάλματος στο UI
        }
    };

    return (
        <form onSubmit={handleLogin}>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
            <button type="submit">Login</button>
        </form>
    );
};

export default Login;
