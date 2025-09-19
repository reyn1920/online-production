import React, { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Upload,
  File,
  Image,
  Video,
  Music,
  FileText,
  X,
  Check,
  AlertCircle,
  Loader2,
  Download,
  Trash2,
  Eye,
  Copy,
  RefreshCw
} from 'lucide-react';

const UploaderPanel = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadResults, setUploadResults] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploadHistory, setUploadHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  // File type configurations
  const fileTypeConfig = {
    image: {
      icon: Image,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
      extensions: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
      maxSize: 10 * 1024 * 1024 // 10MB
    },
    video: {
      icon: Video,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50',
      extensions: ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
      maxSize: 100 * 1024 * 1024 // 100MB
    },
    audio: {
      icon: Music,
      color: 'text-green-500',
      bgColor: 'bg-green-50',
      extensions: ['.mp3', '.wav', '.ogg', '.m4a', '.flac'],
      maxSize: 50 * 1024 * 1024 // 50MB
    },
    document: {
      icon: FileText,
      color: 'text-orange-500',
      bgColor: 'bg-orange-50',
      extensions: ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
      maxSize: 25 * 1024 * 1024 // 25MB
    },
    other: {
      icon: File,
      color: 'text-gray-500',
      bgColor: 'bg-gray-50',
      extensions: [],
      maxSize: 50 * 1024 * 1024 // 50MB
    }
  };

  // Get file type based on extension
  const getFileType = (filename) => {
    const ext = filename.toLowerCase().substring(filename.lastIndexOf('.'));
    for (const [type, config] of Object.entries(fileTypeConfig)) {
      if (config.extensions.includes(ext)) {
        return type;
      }
    }
    return 'other';
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Validate file
  const validateFile = (file) => {
    const fileType = getFileType(file.name);
    const config = fileTypeConfig[fileType];

    if (file.size > config.maxSize) {
      return {
        valid: false,
        error: `File size exceeds ${formatFileSize(config.maxSize)} limit`
      };
    }

    return { valid: true };
  };

  // Handle file selection
  const handleFileSelect = (selectedFiles) => {
    const newFiles = Array.from(selectedFiles).map(file => {
      const validation = validateFile(file);
      return {
        id: Math.random().toString(36).substr(2, 9),
        file,
        name: file.name,
        size: file.size,
        type: getFileType(file.name),
        status: validation.valid ? 'ready' : 'error',
        error: validation.error,
        progress: 0
      };
    });

    setFiles(prev => [...prev, ...newFiles]);
  };

  // Handle drag and drop
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files);
    }
  }, []);

  // Remove file from list
  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[fileId];
      return newProgress;
    });
  };

  // Upload files
  const uploadFiles = async () => {
    const validFiles = files.filter(f => f.status === 'ready');
    if (validFiles.length === 0) return;

    setUploading(true);
    setError(null);
    const results = [];

    for (const fileItem of validFiles) {
      try {
        // Update file status
        setFiles(prev => prev.map(f =>
          f.id === fileItem.id ? { ...f, status: 'uploading' } : f
        ));

        const formData = new FormData();
        formData.append('file', fileItem.file);
        formData.append('metadata', JSON.stringify({
          originalName: fileItem.name,
          fileType: fileItem.type,
          uploadedAt: new Date().toISOString()
        }));

        const response = await fetch('/api/upload/single', {
          method: 'POST',
          body: formData,
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(prev => ({
              ...prev,
              [fileItem.id]: progress
            }));
          }
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = await response.json();

        // Update file status to success
        setFiles(prev => prev.map(f =>
          f.id === fileItem.id ? { ...f, status: 'success', uploadResult: result } : f
        ));

        results.push({
          fileId: fileItem.id,
          fileName: fileItem.name,
          success: true,
          result
        });

      } catch (error) {
        console.error('Upload error:', error);

        // Update file status to error
        setFiles(prev => prev.map(f =>
          f.id === fileItem.id ? { ...f, status: 'error', error: error.message } : f
        ));

        results.push({
          fileId: fileItem.id,
          fileName: fileItem.name,
          success: false,
          error: error.message
        });
      }
    }

    setUploadResults(results);
    setUploading(false);

    // Refresh upload history
    fetchUploadHistory();
  };

  // Fetch upload history
  const fetchUploadHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/upload/history');
      if (!response.ok) throw new Error('Failed to fetch upload history');
      const data = await response.json();
      setUploadHistory(data.uploads || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Delete uploaded file
  const deleteUploadedFile = async (fileId) => {
    if (!confirm('Are you sure you want to delete this file?')) return;

    try {
      const response = await fetch(`/api/upload/${fileId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete file');

      // Refresh history
      fetchUploadHistory();
    } catch (err) {
      setError(err.message);
    }
  };

  // Copy file URL to clipboard
  const copyFileUrl = async (fileUrl) => {
    try {
      await navigator.clipboard.writeText(fileUrl);
      // You might want to show a toast notification here
    } catch (err) {
      console.error('Failed to copy URL:', err);
    }
  };

  // Clear all files
  const clearAllFiles = () => {
    setFiles([]);
    setUploadProgress({});
    setUploadResults([]);
  };

  // Get file icon component
  const getFileIcon = (type) => {
    const config = fileTypeConfig[type] || fileTypeConfig.other;
    const IconComponent = config.icon;
    return <IconComponent className={`h-8 w-8 ${config.color}`} />;
  };

  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'ready':
        return <File className="h-4 w-4 text-gray-500" />;
      case 'uploading':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'success':
        return <Check className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <File className="h-4 w-4 text-gray-500" />;
    }
  };

  React.useEffect(() => {
    fetchUploadHistory();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">File Uploader</h1>
          <p className="text-muted-foreground">
            Upload and manage your files with drag-and-drop support
          </p>
        </div>
        <Button onClick={fetchUploadHistory} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="upload" className="space-y-4">
        <TabsList>
          <TabsTrigger value="upload">Upload Files</TabsTrigger>
          <TabsTrigger value="history">Upload History</TabsTrigger>
        </TabsList>

        {/* Upload Tab */}
        <TabsContent value="upload" className="space-y-4">
          {/* Drop Zone */}
          <Card>
            <CardContent className="p-6">
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">Drop files here or click to browse</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Support for images, videos, audio, documents and more
                </p>
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                >
                  Select Files
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => handleFileSelect(e.target.files)}
                />
              </div>
            </CardContent>
          </Card>

          {/* File List */}
          {files.length > 0 && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Selected Files ({files.length})</CardTitle>
                <div className="flex gap-2">
                  <Button
                    onClick={uploadFiles}
                    disabled={uploading || files.filter(f => f.status === 'ready').length === 0}
                  >
                    {uploading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Upload className="h-4 w-4 mr-2" />
                    )}
                    Upload Files
                  </Button>
                  <Button onClick={clearAllFiles} variant="outline">
                    <X className="h-4 w-4 mr-2" />
                    Clear All
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {files.map((fileItem) => (
                    <div key={fileItem.id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <div className={`p-2 rounded ${fileTypeConfig[fileItem.type]?.bgColor || 'bg-gray-50'}`}>
                        {getFileIcon(fileItem.type)}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium truncate">{fileItem.name}</p>
                          {getStatusIcon(fileItem.status)}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(fileItem.size)} • {fileItem.type}
                        </p>

                        {fileItem.status === 'uploading' && uploadProgress[fileItem.id] && (
                          <Progress value={uploadProgress[fileItem.id]} className="mt-2" />
                        )}

                        {fileItem.error && (
                          <p className="text-xs text-red-500 mt-1">{fileItem.error}</p>
                        )}

                        {fileItem.status === 'success' && fileItem.uploadResult && (
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="secondary" className="text-xs">
                              Uploaded
                            </Badge>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => copyFileUrl(fileItem.uploadResult.url)}
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        )}
                      </div>

                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => removeFile(fileItem.id)}
                        disabled={fileItem.status === 'uploading'}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upload History</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <span>Loading upload history...</span>
                </div>
              ) : uploadHistory.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Upload className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No uploads yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {uploadHistory.map((upload) => (
                    <div key={upload.id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <div className={`p-2 rounded ${fileTypeConfig[getFileType(upload.filename)]?.bgColor || 'bg-gray-50'}`}>
                        {getFileIcon(getFileType(upload.filename))}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium truncate">{upload.filename}</p>
                          <Badge variant="secondary" className="text-xs">
                            {upload.status}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(upload.file_size)} • Uploaded {new Date(upload.upload_time).toLocaleDateString()}
                        </p>
                      </div>

                      <div className="flex gap-1">
                        {upload.url && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => window.open(upload.url, '_blank')}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                        {upload.url && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => copyFileUrl(upload.url)}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => deleteUploadedFile(upload.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default UploaderPanel;
