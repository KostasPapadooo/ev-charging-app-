import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import '../styles/Dashboard.css';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend);

const AvailabilityRate = ({ stations = [] }) => {
  const [availabilityRate, setAvailabilityRate] = useState(0);

  useEffect(() => {
    if (!stations || stations.length === 0) {
      setAvailabilityRate(0);
      return;
    }

    const total = stations.length;
    const available = stations.filter(s => s.status?.toUpperCase() === 'AVAILABLE').length;
    const rate = total > 0 ? (available / total) * 100 : 0;
    
    setAvailabilityRate(rate);
  }, [stations]); // Re-calculate when stations array changes

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