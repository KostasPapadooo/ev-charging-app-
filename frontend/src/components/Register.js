import React, { useState } from 'react';
import axios from 'axios';

const Register = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [phone, setPhone] = useState('');
    const [subscriptionTier, setSubscriptionTier] = useState('free');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(''); // Καθαρισμός προηγούμενων σφαλμάτων
        try {
            // Το API endpoint είναι τώρα /api/auth/register
            const response = await axios.post('http://localhost:8000/api/auth/register', { 
                email,
                password: password, // Αλλαγή από password_hash σε password
                first_name: firstName,
                last_name: lastName,
                phone: phone,
                subscription_tier: subscriptionTier,
            });
            console.log('User registered:', response.data);
            // TODO: Redirect to login page or show success message
            // history.push('/login'); // Αν χρησιμοποιείτε useHistory από react-router-dom v5
            // Για v6, χρησιμοποιήστε useNavigate
        } catch (err) {
            if (err.response && err.response.data && err.response.data.detail) {
                setError(err.response.data.detail);
            } else {
                setError('Registration failed. Please try again.');
            }
            console.error("Registration failed", err);
        }
    };

    return (
        <div>
            <h2>Register</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    placeholder="First Name"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                />
                <input
                    type="text"
                    placeholder="Last Name"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                />
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <input
                    type="tel"
                    placeholder="Phone (e.g., +1234567890)"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                />
                <div>
                    <label htmlFor="subscriptionTier">Subscription Tier:</label>
                    <select 
                        id="subscriptionTier"
                        value={subscriptionTier} 
                        onChange={(e) => setSubscriptionTier(e.target.value)}
                    >
                        <option value="free">Free</option>
                        <option value="premium">Premium</option>
                    </select>
                </div>
                <button type="submit">Register</button>
            </form>
        </div>
    );
};

export default Register;
