import React, { useState, useEffect } from 'react';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  Title, 
  Tooltip, 
  Legend,
  ArcElement 
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { fetchUserAnalytics } from '../services/analyticsApi';
import '../styles/UserAnalytics.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const UserAnalytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoading(true);
        const data = await fetchUserAnalytics();
        setAnalyticsData(data);
        setError(null);
      } catch (err) {
        console.error('Failed to load analytics:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="analytics-container">
        <div className="analytics-loading">
          <div className="loading-spinner"></div>
          <p>Loading your analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-container">
        <div className="analytics-error">
          <h3>📊 Your Analytics</h3>
          <p>Unable to load analytics data: {error}</p>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return null;
  }

  // Prepare data for search success rate chart
  const searchData = {
    labels: ['Successful', 'Unsuccessful'],
    datasets: [
      {
        label: 'Search Results',
        data: [
          analyticsData.successful_searches,
          analyticsData.total_searches - analyticsData.successful_searches
        ],
        backgroundColor: [
          '#4CAF50', // Green for successful
          '#f44336'  // Red for unsuccessful
        ],
        borderColor: [
          '#388E3C',
          '#d32f2f'
        ],
        borderWidth: 2,
      },
    ],
  };

  // Prepare data for activity overview (Recharts)
  const activityData = [
    { name: 'Total Searches', value: analyticsData.total_searches, color: '#2196F3' },
    { name: 'Favorite Changes', value: analyticsData.favorite_changes, color: '#FF9800' },
  ];

  // Chart options
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Search Success Rate',
      },
    },
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="label">{`${payload[0].name}: ${payload[0].value}`}</p>
        </div>
      );
    }
    return null;
  };

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }) => {
    if (percent < 0.05) return null; // Don't show labels for very small slices
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize="12"
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  const successRate = analyticsData.total_searches > 0 
    ? ((analyticsData.successful_searches / analyticsData.total_searches) * 100).toFixed(1)
    : 0;

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h3>📊 Your Analytics</h3>
        <p>Insights into your charging station usage</p>
      </div>

      <div className="analytics-grid">
        {/* Key Metrics Cards */}
        <div className="metric-card">
          <div className="metric-icon">🔍</div>
          <div className="metric-content">
            <h4>Total Searches</h4>
            <span className="metric-value">{analyticsData.total_searches}</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">✅</div>
          <div className="metric-content">
            <h4>Success Rate</h4>
            <span className="metric-value">{successRate}%</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">⚡</div>
          <div className="metric-content">
            <h4>Avg Availability</h4>
            <span className="metric-value">{analyticsData.avg_availability}</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">❤️</div>
          <div className="metric-content">
            <h4>Favorite Changes</h4>
            <span className="metric-value">{analyticsData.favorite_changes}</span>
          </div>
        </div>

        {/* Search Success Rate Chart */}
        {analyticsData.total_searches > 0 && (
          <div className="chart-container">
            <div className="chart-content">
              <Doughnut data={searchData} options={chartOptions} />
            </div>
          </div>
        )}

        {/* Activity Overview Chart */}
        {(analyticsData.total_searches > 0 || analyticsData.favorite_changes > 0) && (
          <div className="chart-container">
            <h4>Activity Overview</h4>
            <div className="chart-content">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={activityData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderCustomLabel}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {activityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* No data message */}
      {analyticsData.total_searches === 0 && analyticsData.favorite_changes === 0 && (
        <div className="no-data-message">
          <p>🌟 Start using the app to see your analytics!</p>
          <small>Search for stations and add favorites to generate insights.</small>
        </div>
      )}
    </div>
  );
};

export default UserAnalytics; 