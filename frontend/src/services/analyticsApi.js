const API_BASE_URL = 'http://127.0.0.1:8000';

export const fetchUserAnalytics = async () => {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/users/me/analytics`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
    }

    const analytics = await response.json();
    console.log('Received user analytics:', analytics);
    return analytics;
  } catch (error) {
    console.error('Error fetching user analytics:', error);
    throw error;
  }
}; 