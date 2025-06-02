const API_BASE_URL = 'http://localhost:8000';

export const fetchAllStations = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    
    if (filters.status) {
      params.append('status', filters.status);
    }
    if (filters.limit) {
      params.append('limit', filters.limit);
    }

    const url = `${API_BASE_URL}/api/stations/?${params}`;
    console.log('Fetching from URL:', url);
    
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
    }
    
    const stations = await response.json();
    return stations;
  } catch (error) {
    console.error('Error fetching stations:', error);
    throw error;
  }
};

// Νέα function για nearby search
export const fetchNearbyStations = async (lat, lon, filters = {}) => {
  try {
    const params = new URLSearchParams();
    
    // Required parameters
    params.append('lat', lat.toString());
    params.append('lon', lon.toString());
    
    // Optional parameters
    if (filters.radius) {
      params.append('radius', filters.radius.toString());
    } else {
      params.append('radius', '5000'); // Default 5km
    }
    
    if (filters.status) {
      params.append('status', filters.status);
    }
    
    if (filters.limit) {
      params.append('limit', filters.limit.toString());
    } else {
      params.append('limit', '50'); // Default limit
    }

    const url = `${API_BASE_URL}/api/stations/nearby/search?${params}`;
    console.log('Fetching nearby stations from URL:', url);
    
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
    }
    
    const data = await response.json();
    console.log('Received nearby stations data:', data);
    
    // Return both stations and search params
    return {
      stations: data.stations,
      searchParams: data.search_params
    };
  } catch (error) {
    console.error('Error fetching nearby stations:', error);
    throw error;
  }
};

// Helper function για geolocation
export const getCurrentLocation = () => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          accuracy: position.coords.accuracy
        });
      },
      (error) => {
        let errorMessage = 'Unable to retrieve location';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location access denied by user';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information unavailable';
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out';
            break;
        }
        reject(new Error(errorMessage));
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    );
  });
};
