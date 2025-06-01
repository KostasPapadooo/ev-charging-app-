import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Register = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [phone, setPhone] = useState('');
    const [subscriptionTier, setSubscriptionTier] = useState('free');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const result = await register({
                email,
                password,
                first_name: firstName,
                last_name: lastName,
                phone: phone || undefined,
                subscription_tier: subscriptionTier,
            });

            if (result.success) {
                console.log('User registered:', result.user);
                navigate('/login'); // Redirect to login after successful registration
            } else {
                const errorMessage = typeof result.error === 'object' 
                    ? JSON.stringify(result.error) 
                    : result.error;
                setError(errorMessage);
            }
        } catch (error) {
            setError('An unexpected error occurred');
        } finally {
            setLoading(false);
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
                    disabled={loading}
                />
                <input
                    type="text"
                    placeholder="Last Name"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                    disabled={loading}
                />
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={loading}
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                />
                <input
                    type="tel"
                    placeholder="Phone (e.g., +1234567890)"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    disabled={loading}
                />
                <div>
                    <label htmlFor="subscriptionTier">Subscription Tier:</label>
                    <select 
                        id="subscriptionTier"
                        value={subscriptionTier} 
                        onChange={(e) => setSubscriptionTier(e.target.value)}
                        disabled={loading}
                    >
                        <option value="free">Free</option>
                        <option value="premium">Premium</option>
                    </select>
                </div>
                <button type="submit" disabled={loading}>
                    {loading ? 'Registering...' : 'Register'}
                </button>
            </form>
        </div>
    );
};

export default Register;
