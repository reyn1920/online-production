import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ChannelManager.css';

const ChannelManager = () => {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingChannel, setEditingChannel] = useState(null);
  const [filter, setFilter] = useState('all'); // all, active, inactive
  const [sortBy, setSortBy] = useState('newest'); // newest, oldest, name
  const [processingChannels, setProcessingChannels] = useState(new Set());

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    channel_type: 'general',
    config: {}
  });

  // API base URL - should be configured via environment variables
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchChannels();
  }, [filter, sortBy]);

  const fetchChannels = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter !== 'all') {
        params.append('active_only', filter === 'active' ? 'true' : 'false');
      }
      if (sortBy) params.append('sort_by', sortBy);
      
      const response = await axios.get(`${API_BASE}/api/channels/?${params}`);
      setChannels(response.data.channels || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch channels');
      console.error('Error fetching channels:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateChannel = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_BASE}/api/channels/`, formData);
      setChannels(prev => [response.data, ...prev]);
      setShowCreateModal(false);
      resetForm();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create channel');
      console.error('Create channel error:', err);
    }
  };

  const handleUpdateChannel = async (e) => {
    e.preventDefault();
    if (!editingChannel) return;
    
    try {
      const response = await axios.put(`${API_BASE}/api/channels/${editingChannel.id}`, formData);
      setChannels(prev => prev.map(ch => ch.id === editingChannel.id ? response.data : ch));
      setEditingChannel(null);
      resetForm();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update channel');
      console.error('Update channel error:', err);
    }
  };

  const handleDeleteChannel = async (channelId) => {
    if (!window.confirm('Are you sure you want to delete this channel?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE}/api/channels/${channelId}`);
      setChannels(prev => prev.filter(ch => ch.id !== channelId));
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete channel');
      console.error('Delete channel error:', err);
    }
  };

  const handleToggleActive = async (channelId, isActive) => {
    try {
      const endpoint = isActive ? 'deactivate' : 'activate';
      const response = await axios.post(`${API_BASE}/api/channels/${channelId}/${endpoint}`);
      setChannels(prev => prev.map(ch => ch.id === channelId ? response.data : ch));
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to ${isActive ? 'deactivate' : 'activate'} channel`);
      console.error('Toggle active error:', err);
    }
  };

  const handleProcessChannel = async (channelId) => {
    try {
      setProcessingChannels(prev => new Set([...prev, channelId]));
      const response = await axios.post(`${API_BASE}/api/channels/${channelId}/process`);
      
      // Show success message or handle response
      if (response.data.task_id) {
        // Could implement task tracking here
// DEBUG_REMOVED: console.log('Processing started with task ID:', response.data.task_id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process channel');
      console.error('Process channel error:', err);
    } finally {
      setProcessingChannels(prev => {
        const newSet = new Set(prev);
        newSet.delete(channelId);
        return newSet;
      });
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      channel_type: 'general',
      config: {}
    });
  };

  const openEditModal = (channel) => {
    setEditingChannel(channel);
    setFormData({
      name: channel.name,
      description: channel.description || '',
      channel_type: channel.channel_type,
      config: channel.config || {}
    });
  };

  const closeModals = () => {
    setShowCreateModal(false);
    setEditingChannel(null);
    resetForm();
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getChannelTypeIcon = (type) => {
    switch (type) {
      case 'avatar': return '🎭';
      case 'upload': return '📁';
      case 'processing': return '⚙️';
      case 'notification': return '🔔';
      default: return '📢';
    }
  };

  const getChannelTypeColor = (type) => {
    switch (type) {
      case 'avatar': return 'type-avatar';
      case 'upload': return 'type-upload';
      case 'processing': return 'type-processing';
      case 'notification': return 'type-notification';
      default: return 'type-general';
    }
  };

  const getFilteredChannels = () => {
    let filtered = channels;
    
    // Apply filter
    if (filter === 'active') {
      filtered = channels.filter(ch => ch.is_active);
    } else if (filter === 'inactive') {
      filtered = channels.filter(ch => !ch.is_active);
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'oldest':
          return new Date(a.created_at) - new Date(b.created_at);
        case 'name':
          return a.name.localeCompare(b.name);
        case 'newest':
        default:
          return new Date(b.created_at) - new Date(a.created_at);
      }
    });
    
    return filtered;
  };

  return (
    <div className="channel-manager">
      {/* Header */}
      <div className="channel-header">
        <div>
          <h2 className="channel-title">Channel Manager</h2>
          <p className="channel-subtitle">Manage your communication channels</p>
        </div>
        <div className="header-actions">
          <button
            onClick={fetchChannels}
            disabled={loading}
            className="btn btn-secondary"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            Create Channel
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-error">
          <div className="alert-content">
            <h3 className="alert-title">Error</h3>
            <p className="alert-message">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="alert-close"
          >
            ×
          </button>
        </div>
      )}

      {/* Filters and Sorting */}
      <div className="controls-section">
        <div className="filter-controls">
          <label htmlFor="filter-select">Filter:</label>
          <select
            id="filter-select"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="control-select"
          >
            <option value="all">All Channels</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
        </div>
        
        <div className="sort-controls">
          <label htmlFor="sort-select">Sort by:</label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="control-select"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="name">Name</option>
          </select>
        </div>
      </div>

      {/* Channels List */}
      <div className="channels-section">
        <h3>Channels ({getFilteredChannels().length})</h3>
        
        {loading && channels.length === 0 ? (
          <div className="loading-state">
            <div className="loading-spinner large"></div>
            <p>Loading channels...</p>
          </div>
        ) : getFilteredChannels().length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📢</div>
            <h4>No channels found</h4>
            <p>Create your first channel to get started</p>
          </div>
        ) : (
          <div className="channels-grid">
            {getFilteredChannels().map((channel) => (
              <div key={channel.id} className="channel-card">
                <div className="channel-header-card">
                  <div className="channel-icon">
                    {getChannelTypeIcon(channel.channel_type)}
                  </div>
                  <div className="channel-status">
                    <span className={`status-badge ${channel.is_active ? 'active' : 'inactive'}`}>
                      {channel.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <span className={`type-badge ${getChannelTypeColor(channel.channel_type)}`}>
                      {channel.channel_type}
                    </span>
                  </div>
                </div>
                
                <div className="channel-info">
                  <h4 className="channel-name">{channel.name}</h4>
                  
                  {channel.description && (
                    <p className="channel-description">{channel.description}</p>
                  )}
                  
                  <div className="channel-meta">
                    <span className="channel-date">
                      Created: {formatDate(channel.created_at)}
                    </span>
                    {channel.updated_at && channel.updated_at !== channel.created_at && (
                      <span className="channel-date">
                        Updated: {formatDate(channel.updated_at)}
                      </span>
                    )}
                  </div>
                  
                  {channel.stats && (
                    <div className="channel-stats">
                      <div className="stat-item">
                        <span className="stat-label">Messages:</span>
                        <span className="stat-value">{channel.stats.message_count || 0}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Last Activity:</span>
                        <span className="stat-value">
                          {channel.stats.last_activity ? formatDate(channel.stats.last_activity) : 'Never'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="channel-actions">
                  <button
                    onClick={() => handleToggleActive(channel.id, channel.is_active)}
                    className={`action-btn ${channel.is_active ? 'deactivate-btn' : 'activate-btn'}`}
                    title={channel.is_active ? 'Deactivate' : 'Activate'}
                  >
                    {channel.is_active ? '⏸️' : '▶️'}
                  </button>
                  
                  <button
                    onClick={() => handleProcessChannel(channel.id)}
                    disabled={processingChannels.has(channel.id)}
                    className="action-btn process-btn"
                    title="Process Channel"
                  >
                    {processingChannels.has(channel.id) ? '⏳' : '⚙️'}
                  </button>
                  
                  <button
                    onClick={() => openEditModal(channel)}
                    className="action-btn edit-btn"
                    title="Edit"
                  >
                    ✏️
                  </button>
                  
                  <button
                    onClick={() => handleDeleteChannel(channel.id)}
                    className="action-btn delete-btn"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingChannel) && (
        <div className="modal-overlay" onClick={closeModals}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingChannel ? 'Edit Channel' : 'Create New Channel'}</h3>
              <button onClick={closeModals} className="modal-close">×</button>
            </div>
            
            <form onSubmit={editingChannel ? handleUpdateChannel : handleCreateChannel}>
              <div className="form-group">
                <label htmlFor="channel-name">Name *</label>
                <input
                  id="channel-name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  required
                  className="form-input"
                  placeholder="Enter channel name"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="channel-description">Description</label>
                <textarea
                  id="channel-description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="form-textarea"
                  placeholder="Enter channel description"
                  rows={3}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="channel-type">Type *</label>
                <select
                  id="channel-type"
                  value={formData.channel_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, channel_type: e.target.value }))}
                  required
                  className="form-select"
                >
                  <option value="general">General</option>
                  <option value="avatar">Avatar</option>
                  <option value="upload">Upload</option>
                  <option value="processing">Processing</option>
                  <option value="notification">Notification</option>
                </select>
              </div>
              
              <div className="modal-actions">
                <button type="button" onClick={closeModals} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingChannel ? 'Update Channel' : 'Create Channel'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChannelManager;