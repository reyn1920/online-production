import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './UploaderPanel.css';

const UploaderPanel = () => {
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [filter, setFilter] = useState('all'); // all, images, audio, video, documents
  const [sortBy, setSortBy] = useState('newest'); // newest, oldest, name, size
  const fileInputRef = useRef(null);

  // API base URL - should be configured via environment variables
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchUploads();
  }, [filter, sortBy]);

  const fetchUploads = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter !== 'all') params.append('file_type', filter);
      if (sortBy) params.append('sort_by', sortBy);

      const response = await axios.get(`${API_BASE}/api/upload/list?${params}`);
      setUploads(response.data.uploads || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch uploads');
      console.error('Error fetching uploads:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files) => {
    const fileArray = Array.from(files);

    for (const file of fileArray) {
      await uploadFile(file);
    }
  };

  const uploadFile = async (file) => {
    const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      // Initialize progress tracking
      setUploadProgress(prev => ({ ...prev, [uploadId]: 0 }));

      const formData = new FormData();
      formData.append('file', file);
      formData.append('description', `Uploaded: ${file.name}`);

      const response = await axios.post(`${API_BASE}/api/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(prev => ({ ...prev, [uploadId]: percentCompleted }));
        },
      });

      // Remove progress tracking on completion
      setUploadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[uploadId];
        return newProgress;
      });

      // Refresh uploads list
      await fetchUploads();

    } catch (err) {
      setError(err.response?.data?.detail || `Failed to upload ${file.name}`);
      console.error('Upload error:', err);

      // Remove progress tracking on error
      setUploadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[uploadId];
        return newProgress;
      });
    }
  };

  const deleteUpload = async (uploadId) => {
    if (!window.confirm('Are you sure you want to delete this upload?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE}/api/upload/${uploadId}`);
      await fetchUploads();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete upload');
      console.error('Delete error:', err);
    }
  };

  const downloadUpload = async (uploadId, filename) => {
    try {
      const response = await axios.get(`${API_BASE}/api/upload/${uploadId}/download`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to download file');
      console.error('Download error:', err);
    }
  };

  const getFileIcon = (fileType) => {
    if (fileType?.startsWith('image/')) return '🖼️';
    if (fileType?.startsWith('audio/')) return '🎵';
    if (fileType?.startsWith('video/')) return '🎬';
    if (fileType?.includes('pdf')) return '📄';
    if (fileType?.includes('text')) return '📝';
    return '📁';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getFilteredUploads = () => {
    let filtered = uploads;

    // Apply filter
    if (filter !== 'all') {
      filtered = uploads.filter(upload => {
        const fileType = upload.file_type?.toLowerCase() || '';
        switch (filter) {
          case 'images':
            return fileType.startsWith('image/');
          case 'audio':
            return fileType.startsWith('audio/');
          case 'video':
            return fileType.startsWith('video/');
          case 'documents':
            return fileType.includes('pdf') || fileType.includes('text') || fileType.includes('document');
          default:
            return true;
        }
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'oldest':
          return new Date(a.created_at) - new Date(b.created_at);
        case 'name':
          return a.filename.localeCompare(b.filename);
        case 'size':
          return (b.file_size || 0) - (a.file_size || 0);
        case 'newest':
        default:
          return new Date(b.created_at) - new Date(a.created_at);
      }
    });

    return filtered;
  };

  return (
    <div className="uploader-panel">
      {/* Header */}
      <div className="uploader-header">
        <div>
          <h2 className="uploader-title">File Uploader</h2>
          <p className="uploader-subtitle">Manage your uploaded files</p>
        </div>
        <button
          onClick={fetchUploads}
          disabled={loading}
          className="btn btn-primary"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
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

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="upload-progress-section">
          <h3>Uploading Files...</h3>
          {Object.entries(uploadProgress).map(([uploadId, progress]) => (
            <div key={uploadId} className="progress-item">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <span className="progress-text">{progress}%</span>
            </div>
          ))}
        </div>
      )}

      {/* Upload Area */}
      <div
        className={`upload-area ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <div className="upload-content">
          <div className="upload-icon">📁</div>
          <h3>Drop files here or click to browse</h3>
          <p>Support for images, audio, video, and documents</p>
        </div>
      </div>

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
            <option value="all">All Files</option>
            <option value="images">Images</option>
            <option value="audio">Audio</option>
            <option value="video">Video</option>
            <option value="documents">Documents</option>
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
            <option value="size">Size</option>
          </select>
        </div>
      </div>

      {/* Files List */}
      <div className="files-section">
        <h3>Uploaded Files ({getFilteredUploads().length})</h3>

        {loading && uploads.length === 0 ? (
          <div className="loading-state">
            <div className="loading-spinner large"></div>
            <p>Loading uploads...</p>
          </div>
        ) : getFilteredUploads().length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📂</div>
            <h4>No files found</h4>
            <p>Upload some files to get started</p>
          </div>
        ) : (
          <div className="files-grid">
            {getFilteredUploads().map((upload) => (
              <div key={upload.id} className="file-card">
                <div className="file-header">
                  <div className="file-icon">
                    {getFileIcon(upload.file_type)}
                  </div>
                  <div className="file-actions">
                    <button
                      onClick={() => downloadUpload(upload.id, upload.filename)}
                      className="action-btn download-btn"
                      title="Download"
                    >
                      ⬇️
                    </button>
                    <button
                      onClick={() => deleteUpload(upload.id)}
                      className="action-btn delete-btn"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <div className="file-info">
                  <h4 className="file-name" title={upload.filename}>
                    {upload.filename}
                  </h4>

                  {upload.description && (
                    <p className="file-description">{upload.description}</p>
                  )}

                  <div className="file-meta">
                    <span className="file-size">
                      {formatFileSize(upload.file_size || 0)}
                    </span>
                    <span className="file-type">
                      {upload.file_type || 'Unknown'}
                    </span>
                  </div>

                  <div className="file-dates">
                    <span className="upload-date">
                      Uploaded: {formatDate(upload.created_at)}
                    </span>
                    {upload.updated_at && upload.updated_at !== upload.created_at && (
                      <span className="update-date">
                        Updated: {formatDate(upload.updated_at)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Preview for images */}
                {upload.file_type?.startsWith('image/') && upload.file_path && (
                  <div className="file-preview">
                    <img
                      src={`${API_BASE}/api/upload/${upload.id}/download`}
                      alt={upload.filename}
                      className="preview-image"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UploaderPanel;
