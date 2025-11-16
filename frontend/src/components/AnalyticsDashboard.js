import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './AnalyticsDashboard.css';

const API_BASE = 'http://localhost:5001/api';

const COLORS = ['#232D4B', '#1B1B3A', '#4caf50', '#2196f3', '#ff9800', '#f44336', '#9c27b0', '#00bcd4'];

function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsRes, coursesRes] = await Promise.all([
          axios.get(`${API_BASE}/analytics`),
          axios.get(`${API_BASE}/courses`)
        ]);
        setAnalytics(analyticsRes.data);
        setCourses(coursesRes.data);
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="dashboard-container">Loading analytics...</div>;
  }

  if (!analytics) {
    return <div className="dashboard-container">No analytics data available</div>;
  }

  // Prepare data for charts
  const engagementData = analytics.topCourses?.map(item => {
    const course = courses.find(c => c.id === item.courseId);
    return {
      name: course?.title || item.courseId,
      likes: item.likes,
      dislikes: item.dislikes,
      cartAdds: item.cart_adds,
      total: item.total
    };
  }).filter(item => item.total > 0) || [];

  const actionDistribution = [
    { name: 'Likes', value: Object.values(analytics.courseEngagement || {}).reduce((sum, item) => sum + item.likes, 0) },
    { name: 'Dislikes', value: Object.values(analytics.courseEngagement || {}).reduce((sum, item) => sum + item.dislikes, 0) },
    { name: 'Cart Adds', value: Object.values(analytics.courseEngagement || {}).reduce((sum, item) => sum + item.cart_adds, 0) }
  ].filter(item => item.value > 0);

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>📊 Faculty Analytics Dashboard</h2>
        <p className="dashboard-subtitle">Real-time insights into student course preferences and demand</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{analytics.totalFeedback}</div>
          <div className="stat-label">Total Interactions</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{Object.keys(analytics.courseEngagement || {}).length}</div>
          <div className="stat-label">Courses Engaged</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {Object.values(analytics.courseEngagement || {}).reduce((sum, item) => sum + item.likes, 0)}
          </div>
          <div className="stat-label">Total Likes</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {Object.values(analytics.courseEngagement || {}).reduce((sum, item) => sum + item.cart_adds, 0)}
          </div>
          <div className="stat-label">Cart Additions</div>
        </div>
      </div>

      {engagementData.length > 0 && (
        <>
          <div className="chart-section">
            <h3>Course Engagement Overview</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={engagementData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="likes" fill="#4caf50" name="Likes" />
                <Bar dataKey="dislikes" fill="#f44336" name="Dislikes" />
                <Bar dataKey="cartAdds" fill="#2196f3" name="Cart Adds" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {actionDistribution.length > 0 && (
            <div className="chart-section">
              <h3>Action Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={actionDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {actionDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="table-section">
            <h3>Top Engaged Courses</h3>
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Course</th>
                  <th>Likes</th>
                  <th>Dislikes</th>
                  <th>Cart Adds</th>
                  <th>Total Engagement</th>
                  <th>Sentiment</th>
                </tr>
              </thead>
              <tbody>
                {engagementData
                  .sort((a, b) => b.total - a.total)
                  .map((item, idx) => {
                    const sentiment = item.total > 0 
                      ? ((item.likes - item.dislikes) / item.total * 100).toFixed(0)
                      : 0;
                    return (
                      <tr key={idx}>
                        <td>{item.name}</td>
                        <td>{item.likes}</td>
                        <td>{item.dislikes}</td>
                        <td>{item.cartAdds}</td>
                        <td>{item.total}</td>
                        <td>
                          <span className={`sentiment ${sentiment >= 0 ? 'positive' : 'negative'}`}>
                            {sentiment >= 0 ? '+' : ''}{sentiment}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </>
      )}

      {engagementData.length === 0 && (
        <div className="empty-state">
          <p>No engagement data yet. Start chatting and rating courses to see analytics!</p>
        </div>
      )}

      <div className="info-box">
        <strong>💡 For Faculty & Administrators:</strong>
        <ul>
          <li>Track which courses students are most interested in</li>
          <li>Understand demand patterns for curriculum planning</li>
          <li>Identify opportunities for new course development</li>
          <li>Make data-driven decisions about course scheduling and capacity</li>
        </ul>
      </div>
    </div>
  );
}

export default AnalyticsDashboard;

