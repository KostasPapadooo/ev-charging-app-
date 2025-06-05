import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import '../styles/Dashboard.css';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend);

const AvailabilityRate = ({ userLocation, radius = 3000 }) => {
  const [availabilityRate, setAvailabilityRate] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAvailabilityRate = async () => {
      if (!userLocation) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const url = `http://localhost:8000/api/stations/analytics/availability-rate?lat=${userLocation.lat}&lon=${userLocation.lon}&radius=${radius}`;
        
        // Debug: Check if we have an auth token
        const token = localStorage.getItem('token');
        console.log('Auth token available:', !!token);
        
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        if (data.availability_rate !== undefined) {
          // Convert to percentage
          setAvailabilityRate(data.availability_rate * 100);
        } else {
          setAvailabilityRate(0);
        }
        setLoading(false);
      } catch (error) {
        console.error('Error fetching availability rate:', error);
        setLoading(false);
      }
    };

    fetchAvailabilityRate();
    // Set up an interval for periodic updates
    const interval = setInterval(fetchAvailabilityRate, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [userLocation, radius]);

  // Gauge chart data
  const data = {
    datasets: [
      {
        data: [availabilityRate, 100 - availabilityRate],
        backgroundColor: ['#36A2EB', '#E0E0E0'],
        borderWidth: 0,
        cutout: '90%',
        rotation: -90,
        circumference: 180,
      },
    ],
    labels: ['Available', 'Unavailable'],
  };

  // Gauge chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: false,
      },
    },
  };

  // Text plugin to display percentage in the center
  const textCenter = {
    id: 'textCenter',
    beforeDatasetsDraw(chart) {
      const { ctx, data } = chart;
      ctx.save();
      ctx.font = 'bold 24px sans-serif';
      ctx.fillStyle = '#333';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${Math.round(data.datasets[0].data[0])}%`, chart.getDatasetMeta(0).data[0].x, chart.getDatasetMeta(0).data[0].y);
      ctx.restore();
    },
  };

  if (loading) {
    return <div className="loading">Loading availability rate...</div>;
  }

  return (
    <div className="availability-rate-container" style={{ textAlign: 'center', marginBottom: '20px' }}>
      <h3>Station Availability Rate</h3>
      <div style={{ height: '220px', width: '400px', margin: '0 auto' }}>
        <Doughnut data={data} options={options} plugins={[textCenter]} />
      </div>
      <p>Percentage of available charging stations in your area.</p>
    </div>
  );
};

export default AvailabilityRate; 