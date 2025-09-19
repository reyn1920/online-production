import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './RuntimeHQ.css';

const RuntimeHQ = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [migrationStatus, setMigrationStatus] = useState(null);

  // API base URL - should be configured via environment variables
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchSystemData();
    const interval = setInterval(fetchSystemData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchSystemData = async () => {
    try {
      setLoading(true);
      const [statusResponse, dashboardResponse] = await Promise.all([
        axios.get(`${API_BASE}/api/runtimehq/system/status`),
        axios.get(`${API_BASE}/api/runtimehq/dashboard`)
      ]);

      setSystemStatus(statusResponse.data);
      setDashboardData(dashboardResponse.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch system data');
      console.error('Error fetching system data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMigration = async () => {
    try {
      setMigrationStatus('running');
      const response = await axios.post(`${API_BASE}/api/runtimehq/database/migrate`);
      setMigrationStatus('completed');

      // Refresh system data after migration
      setTimeout(fetchSystemData, 1000);
    } catch (err) {
      setMigrationStatus('failed');
      setError(err.response?.data?.detail || 'Migration failed');
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'completed':
      case 'success':
        return 'text-green-600';
      case 'warning':
      case 'pending':
        return 'text-yellow-600';
      case 'error':
      case 'failed':
      case 'unhealthy':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* System Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">System Status</h3>
          <p className={`text-2xl font-bold ${getStatusColor(systemStatus?.overall_status)}`}>
            {systemStatus?.overall_status || 'Unknown'}
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Database</h3>
          <p className={`text-2xl font-bold ${getStatusColor(systemStatus?.database?.status)}`}>
            {systemStatus?.database?.status || 'Unknown'}
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Queue Tasks</h3>
          <p className="text-2xl font-bold text-blue-600">
            {dashboardData?.queue_stats?.total_tasks || 0}
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Revenue</h3>
          <p className="text-2xl font-bold text-green-600">
            ${dashboardData?.revenue_stats?.total_revenue?.toFixed(2) || '0.00'}
          </p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
        </div>
        <div className="p-6">
          {dashboardData?.recent_activity?.length > 0 ? (
            <div className="space-y-3">
              {dashboardData.recent_activity.map((activity, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <div className={`w-2 h-2 rounded-full ${
                      activity.type === 'upload' ? 'bg-blue-400' :
                      activity.type === 'revenue' ? 'bg-green-400' :
                      activity.type === 'queue' ? 'bg-yellow-400' :
                      'bg-gray-400'
                    }`}></div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">{activity.description}</p>
                    <p className="text-xs text-gray-500">{formatDate(activity.timestamp)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No recent activity</p>
          )}
        </div>
      </div>
    </div>
  );

  const renderSystemDetails = () => (
    <div className="space-y-6">
      {/* System Health Details */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">System Health</h3>
        </div>
        <div className="p-6">
          {systemStatus ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium text-gray-900">Database</h4>
                  <p className={`text-sm ${getStatusColor(systemStatus.database?.status)}`}>
                    Status: {systemStatus.database?.status}
                  </p>
                  {systemStatus.database?.connection_time && (
                    <p className="text-sm text-gray-600">
                      Connection Time: {systemStatus.database.connection_time}ms
                    </p>
                  )}
                </div>

                <div>
                  <h4 className="font-medium text-gray-900">Storage</h4>
                  {systemStatus.storage && (
                    <div className="text-sm text-gray-600">
                      <p>Free Space: {formatBytes(systemStatus.storage.free_space)}</p>
                      <p>Total Space: {formatBytes(systemStatus.storage.total_space)}</p>
                    </div>
                  )}
                </div>
              </div>

              {systemStatus.services && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Services</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {Object.entries(systemStatus.services).map(([service, status]) => (
                      <div key={service} className="flex justify-between">
                        <span className="text-sm text-gray-600">{service}:</span>
                        <span className={`text-sm ${getStatusColor(status)}`}>{status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Loading system status...</p>
          )}
        </div>
      </div>

      {/* Database Migration */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Database Management</h3>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-gray-900">Run Migration</h4>
              <p className="text-sm text-gray-600">Update database schema to latest version</p>
            </div>
            <button
              onClick={handleMigration}
              disabled={migrationStatus === 'running'}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                migrationStatus === 'running'
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {migrationStatus === 'running' ? 'Running...' : 'Run Migration'}
            </button>
          </div>

          {migrationStatus && (
            <div className={`mt-4 p-3 rounded-md ${
              migrationStatus === 'completed' ? 'bg-green-50 text-green-800' :
              migrationStatus === 'failed' ? 'bg-red-50 text-red-800' :
              'bg-blue-50 text-blue-800'
            }`}>
              Migration {migrationStatus}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderStats = () => (
    <div className="space-y-6">
      {/* Queue Statistics */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Queue Statistics</h3>
        </div>
        <div className="p-6">
          {dashboardData?.queue_stats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {dashboardData.queue_stats.pending_tasks}
                </p>
                <p className="text-sm text-gray-600">Pending</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">
                  {dashboardData.queue_stats.in_progress_tasks}
                </p>
                <p className="text-sm text-gray-600">In Progress</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {dashboardData.queue_stats.completed_tasks}
                </p>
                <p className="text-sm text-gray-600">Completed</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">
                  {dashboardData.queue_stats.failed_tasks}
                </p>
                <p className="text-sm text-gray-600">Failed</p>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">Loading queue statistics...</p>
          )}
        </div>
      </div>

      {/* Revenue Statistics */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Revenue Statistics</h3>
        </div>
        <div className="p-6">
          {dashboardData?.revenue_stats ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  ${dashboardData.revenue_stats.total_revenue?.toFixed(2) || '0.00'}
                </p>
                <p className="text-sm text-gray-600">Total Revenue</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {dashboardData.revenue_stats.total_entries || 0}
                </p>
                <p className="text-sm text-gray-600">Total Entries</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">
                  ${dashboardData.revenue_stats.average_amount?.toFixed(2) || '0.00'}
                </p>
                <p className="text-sm text-gray-600">Average Amount</p>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">Loading revenue statistics...</p>
          )}
        </div>
      </div>

      {/* Storage Statistics */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Storage Statistics</h3>
        </div>
        <div className="p-6">
          {dashboardData?.storage_stats ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-indigo-600">
                  {dashboardData.storage_stats.total_files || 0}
                </p>
                <p className="text-sm text-gray-600">Total Files</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-cyan-600">
                  {formatBytes(dashboardData.storage_stats.total_size || 0)}
                </p>
                <p className="text-sm text-gray-600">Total Size</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-teal-600">
                  {formatBytes(dashboardData.storage_stats.average_size || 0)}
                </p>
                <p className="text-sm text-gray-600">Average Size</p>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">Loading storage statistics...</p>
          )}
        </div>
      </div>
    </div>
  );

  if (loading && !systemStatus) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading RuntimeHQ...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">RuntimeHQ</h1>
              <p className="text-gray-600">System Management Dashboard</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={fetchSystemData}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-400 hover:text-red-600"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', name: 'Overview' },
              { id: 'system', name: 'System' },
              { id: 'stats', name: 'Statistics' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'system' && renderSystemDetails()}
        {activeTab === 'stats' && renderStats()}
      </div>
    </div>
  );
};

export default RuntimeHQ;
