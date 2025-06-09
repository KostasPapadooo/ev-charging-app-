import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const FavoriteStationHistory = ({ stationId, stationName, hours = 24 }) => {
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!stationId) return;

      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch(
          `http://localhost:8000/api/stations/analytics/favorite-history?station_id=${stationId}&hours=${hours}`
        );
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setHistoryData(data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching station history:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchHistory();
  }, [stationId, hours]);

  const prepareChartData = () => {
    if (!historyData || !historyData.history || historyData.history.length === 0) {
      return null;
    }

    // Status mapping for y-axis values
    const statusValues = {
      'AVAILABLE': 3,
      'OCCUPIED': 2,
      'BUSY': 2,
      'OUT_OF_ORDER': 1,
      'OUTOFORDER': 1,
      'UNKNOWN': 0
    };

    // Status colors for visualization
    const statusColors = {
      'AVAILABLE': '#28a745',
      'OCCUPIED': '#dc3545',
      'BUSY': '#dc3545',
      'OUT_OF_ORDER': '#6c757d',
      'OUTOFORDER': '#6c757d',
      'UNKNOWN': '#ffc107'
    };

    const labels = [];
    const dataPoints = [];
    const pointColors = [];

    historyData.history.forEach((point) => {
      const date = new Date(point.timestamp);
      const timeLabel = date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });
      
      labels.push(timeLabel);
      dataPoints.push(statusValues[point.status.toUpperCase()] || 0);
      pointColors.push(statusColors[point.status.toUpperCase()] || '#ffc107');
    });

    return {
      labels,
      datasets: [
        {
          label: 'Station Status',
          data: dataPoints,
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          pointBackgroundColor: pointColors,
          pointBorderColor: pointColors,
          pointRadius: 4,
          pointHoverRadius: 6,
          tension: 0.1,
          fill: false,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        marginBottom: '10px',
        text: `${hours}h Status History`,
        font: {
          size: 14,
          weight: 'bold'
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const statusNames = ['Unknown', 'Out of Order', 'Busy/Occupied', 'Available'];
            return `Status: ${statusNames[context.parsed.y] || 'Unknown'}`;
          }
        }
      }
    },
    scales: {
      y: {
        min: 0,
        max: 3,
        ticks: {
          stepSize: 1,
          callback: function(value) {
            const statusNames = ['Unknown', 'Out of Order', 'Busy/Occupied', 'Available'];
            return statusNames[value] || '';
          }
        },
        grid: {
          color: 'rgba(0,0,0,0.1)'
        }
      },
      x: {
        ticks: {
          maxTicksLimit: 8,
          font: {
            size: 10
          }
        },
        grid: {
          display: false
        }
      }
    },
    elements: {
      point: {
        hoverRadius: 8
      }
    }
  };

  if (loading) {
    return (
      <div className="favorite-history-container" style={{ padding: '15px', textAlign: 'center' }}>
        <div className="loading-spinner" style={{ fontSize: '12px', color: '#6c757d' }}>
          Loading history...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="favorite-history-container" style={{ padding: '15px', textAlign: 'center' }}>
        <div className="error-message" style={{ fontSize: '12px', color: '#dc3545' }}>
          Failed to load history: {error}
        </div>
      </div>
    );
  }

  const chartData = prepareChartData();

  if (!chartData || chartData.datasets[0].data.length === 0) {
    return (
      <div className="favorite-history-container" style={{ padding: '15px', textAlign: 'center' }}>
        <div style={{ fontSize: '12px', color: '#6c757d' }}>
          No history data available for the last {hours} hours
        </div>
      </div>
    );
  }

  return (
    <div className="favorite-history-container" style={{ padding: '15px' }}>
      <div style={{ height: '200px', width: '100%' }}>
        <Line data={chartData} options={chartOptions} />
      </div>
      <div style={{ 
        marginTop: '10px', 
        fontSize: '11px', 
        color: '#6c757d',
        textAlign: 'center' 
      }}>
        {historyData.history.length} data points over {hours} hours
      </div>
    </div>
  );
};

export default FavoriteStationHistory; 