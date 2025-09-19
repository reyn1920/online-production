import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Plus,
  Settings,
  Trash2,
  Edit,
  Eye,
  Upload,
  BarChart3,
  Users,
  Calendar,
  Globe,
  Lock,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Loader2,
  Copy,
  ExternalLink,
  TrendingUp,
  MessageSquare,
  Heart,
  Share
} from 'lucide-react';

const ChannelManager = () => {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [channelStats, setChannelStats] = useState({});
  const [contentItems, setContentItems] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  // Form states
  const [newChannel, setNewChannel] = useState({
    name: '',
    description: '',
    platform: 'youtube',
    visibility: 'public',
    category: 'general',
    tags: ''
  });

  const [uploadContent, setUploadContent] = useState({
    title: '',
    description: '',
    file: null,
    thumbnail: null,
    tags: '',
    scheduled_time: '',
    visibility: 'public'
  });

  // Platform configurations
  const platformConfig = {
    youtube: {
      name: 'YouTube',
      color: 'bg-red-500',
      textColor: 'text-red-600',
      bgColor: 'bg-red-50',
      icon: '📺',
      features: ['videos', 'shorts', 'live', 'community']
    },
    tiktok: {
      name: 'TikTok',
      color: 'bg-black',
      textColor: 'text-gray-900',
      bgColor: 'bg-gray-50',
      icon: '🎵',
      features: ['videos', 'live']
    },
    instagram: {
      name: 'Instagram',
      color: 'bg-gradient-to-r from-purple-500 to-pink-500',
      textColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
      icon: '📸',
      features: ['posts', 'stories', 'reels', 'igtv']
    },
    twitter: {
      name: 'Twitter/X',
      color: 'bg-blue-500',
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      icon: '🐦',
      features: ['tweets', 'threads', 'spaces']
    },
    linkedin: {
      name: 'LinkedIn',
      color: 'bg-blue-700',
      textColor: 'text-blue-700',
      bgColor: 'bg-blue-50',
      icon: '💼',
      features: ['posts', 'articles', 'videos']
    }
  };

  // Fetch channels
  const fetchChannels = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('/api/channels');
      if (!response.ok) throw new Error('Failed to fetch channels');
      const data = await response.json();
      setChannels(data.channels || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  };

  // Fetch channel statistics
  const fetchChannelStats = async (channelId) => {
    try {
      const response = await fetch(`/api/channels/${channelId}/stats`);
      if (!response.ok) throw new Error('Failed to fetch channel stats');
      const data = await response.json();
      setChannelStats(prev => ({ ...prev, [channelId]: data }));
    } catch (err) {
      console.error('Failed to fetch channel stats:', err);
    }
  };

  // Fetch channel content
  const fetchChannelContent = async (channelId) => {
    try {
      const response = await fetch(`/api/channels/${channelId}/content`);
      if (!response.ok) throw new Error('Failed to fetch channel content');
      const data = await response.json();
      setContentItems(data.content || []);
    } catch (err) {
      console.error('Failed to fetch channel content:', err);
    }
  };

  // Create new channel
  const createChannel = async () => {
    try {
      const response = await fetch('/api/channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newChannel,
          tags: newChannel.tags.split(',').map(tag => tag.trim()).filter(Boolean)
        })
      });

      if (!response.ok) throw new Error('Failed to create channel');

      const result = await response.json();
      setChannels(prev => [...prev, result.channel]);
      setShowCreateDialog(false);
      setNewChannel({
        name: '',
        description: '',
        platform: 'youtube',
        visibility: 'public',
        category: 'general',
        tags: ''
      });
    } catch (err) {
      setError(err.message);
    }
  };

  // Delete channel
  const deleteChannel = async (channelId) => {
    if (!confirm('Are you sure you want to delete this channel? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/channels/${channelId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete channel');

      setChannels(prev => prev.filter(c => c.id !== channelId));
      if (selectedChannel?.id === channelId) {
        setSelectedChannel(null);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  // Upload content to channel
  const uploadToChannel = async () => {
    if (!selectedChannel || !uploadContent.file) return;

    try {
      const formData = new FormData();
      formData.append('file', uploadContent.file);
      if (uploadContent.thumbnail) {
        formData.append('thumbnail', uploadContent.thumbnail);
      }
      formData.append('metadata', JSON.stringify({
        title: uploadContent.title,
        description: uploadContent.description,
        tags: uploadContent.tags.split(',').map(tag => tag.trim()).filter(Boolean),
        scheduled_time: uploadContent.scheduled_time,
        visibility: uploadContent.visibility
      }));

      const response = await fetch(`/api/channels/${selectedChannel.id}/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Failed to upload content');

      const result = await response.json();
      setShowUploadDialog(false);
      setUploadContent({
        title: '',
        description: '',
        file: null,
        thumbnail: null,
        tags: '',
        scheduled_time: '',
        visibility: 'public'
      });

      // Refresh channel content
      fetchChannelContent(selectedChannel.id);
    } catch (err) {
      setError(err.message);
    }
  };

  // Get platform badge
  const getPlatformBadge = (platform) => {
    const config = platformConfig[platform] || platformConfig.youtube;
    return (
      <Badge className={`${config.bgColor} ${config.textColor} border-0`}>
        <span className="mr-1">{config.icon}</span>
        {config.name}
      </Badge>
    );
  };

  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'inactive':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  // Format number with K/M suffix
  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  useEffect(() => {
    fetchChannels();
  }, []);

  useEffect(() => {
    if (selectedChannel) {
      fetchChannelStats(selectedChannel.id);
      fetchChannelContent(selectedChannel.id);
    }
  }, [selectedChannel]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading channels...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Channel Manager</h1>
          <p className="text-muted-foreground">
            Manage your content channels across multiple platforms
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchChannels} variant="outline" disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Channel
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Create New Channel</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="name">Channel Name</Label>
                  <Input
                    id="name"
                    value={newChannel.name}
                    onChange={(e) => setNewChannel(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter channel name"
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newChannel.description}
                    onChange={(e) => setNewChannel(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Channel description"
                  />
                </div>
                <div>
                  <Label htmlFor="platform">Platform</Label>
                  <Select value={newChannel.platform} onValueChange={(value) => setNewChannel(prev => ({ ...prev, platform: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(platformConfig).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          <span className="flex items-center">
                            <span className="mr-2">{config.icon}</span>
                            {config.name}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="visibility">Visibility</Label>
                  <Select value={newChannel.visibility} onValueChange={(value) => setNewChannel(prev => ({ ...prev, visibility: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="public">🌍 Public</SelectItem>
                      <SelectItem value="private">🔒 Private</SelectItem>
                      <SelectItem value="unlisted">👁️ Unlisted</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="tags">Tags (comma-separated)</Label>
                  <Input
                    id="tags"
                    value={newChannel.tags}
                    onChange={(e) => setNewChannel(prev => ({ ...prev, tags: e.target.value }))}
                    placeholder="gaming, entertainment, tutorial"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={createChannel} disabled={!newChannel.name}>
                    Create Channel
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Channels List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Your Channels ({channels.length})</CardTitle>
            </CardHeader>
            <CardContent>
              {channels.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Globe className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No channels yet</p>
                  <p className="text-sm">Create your first channel to get started</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {channels.map((channel) => (
                    <div
                      key={channel.id}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedChannel?.id === channel.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'hover:bg-gray-50'
                      }`}
                      onClick={() => setSelectedChannel(channel)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium truncate">{channel.name}</h3>
                            {getStatusIcon(channel.status)}
                          </div>
                          <div className="flex items-center gap-2 mb-2">
                            {getPlatformBadge(channel.platform)}
                            <Badge variant="outline" className="text-xs">
                              {channel.visibility}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {channel.description}
                          </p>
                        </div>
                        <div className="flex gap-1 ml-2">
                          <Button size="sm" variant="ghost" onClick={(e) => {
                            e.stopPropagation();
                            // Handle edit
                          }}>
                            <Edit className="h-3 w-3" />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={(e) => {
                            e.stopPropagation();
                            deleteChannel(channel.id);
                          }}>
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Channel Details */}
        <div className="lg:col-span-2">
          {selectedChannel ? (
            <Tabs defaultValue="overview" className="space-y-4">
              <div className="flex items-center justify-between">
                <TabsList>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="content">Content</TabsTrigger>
                  <TabsTrigger value="analytics">Analytics</TabsTrigger>
                  <TabsTrigger value="settings">Settings</TabsTrigger>
                </TabsList>
                <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
                  <DialogTrigger asChild>
                    <Button>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload Content
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-lg">
                    <DialogHeader>
                      <DialogTitle>Upload Content to {selectedChannel.name}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="title">Title</Label>
                        <Input
                          id="title"
                          value={uploadContent.title}
                          onChange={(e) => setUploadContent(prev => ({ ...prev, title: e.target.value }))}
                          placeholder="Content title"
                        />
                      </div>
                      <div>
                        <Label htmlFor="description">Description</Label>
                        <Textarea
                          id="description"
                          value={uploadContent.description}
                          onChange={(e) => setUploadContent(prev => ({ ...prev, description: e.target.value }))}
                          placeholder="Content description"
                        />
                      </div>
                      <div>
                        <Label htmlFor="file">Content File</Label>
                        <Input
                          id="file"
                          type="file"
                          onChange={(e) => setUploadContent(prev => ({ ...prev, file: e.target.files[0] }))}
                          accept="video/*,image/*,audio/*"
                        />
                      </div>
                      <div>
                        <Label htmlFor="thumbnail">Thumbnail (optional)</Label>
                        <Input
                          id="thumbnail"
                          type="file"
                          onChange={(e) => setUploadContent(prev => ({ ...prev, thumbnail: e.target.files[0] }))}
                          accept="image/*"
                        />
                      </div>
                      <div>
                        <Label htmlFor="tags">Tags</Label>
                        <Input
                          id="tags"
                          value={uploadContent.tags}
                          onChange={(e) => setUploadContent(prev => ({ ...prev, tags: e.target.value }))}
                          placeholder="tag1, tag2, tag3"
                        />
                      </div>
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" onClick={() => setShowUploadDialog(false)}>
                          Cancel
                        </Button>
                        <Button onClick={uploadToChannel} disabled={!uploadContent.title || !uploadContent.file}>
                          Upload
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>

              {/* Overview Tab */}
              <TabsContent value="overview">
                <div className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <span className="text-2xl">{platformConfig[selectedChannel.platform]?.icon}</span>
                        {selectedChannel.name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <p className="text-sm text-muted-foreground mb-2">Description</p>
                          <p>{selectedChannel.description}</p>
                        </div>
                        <div className="flex gap-4">
                          <div>
                            <p className="text-sm text-muted-foreground">Platform</p>
                            {getPlatformBadge(selectedChannel.platform)}
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Status</p>
                            <div className="flex items-center gap-1">
                              {getStatusIcon(selectedChannel.status)}
                              <span className="text-sm capitalize">{selectedChannel.status}</span>
                            </div>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Visibility</p>
                            <Badge variant="outline">{selectedChannel.visibility}</Badge>
                          </div>
                        </div>
                        {selectedChannel.tags && selectedChannel.tags.length > 0 && (
                          <div>
                            <p className="text-sm text-muted-foreground mb-2">Tags</p>
                            <div className="flex flex-wrap gap-1">
                              {selectedChannel.tags.map((tag, index) => (
                                <Badge key={index} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Quick Stats */}
                  {channelStats[selectedChannel.id] && (
                    <div className="grid gap-4 md:grid-cols-4">
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            <Users className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">Subscribers</span>
                          </div>
                          <p className="text-2xl font-bold">
                            {formatNumber(channelStats[selectedChannel.id].subscribers || 0)}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            <Eye className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">Views</span>
                          </div>
                          <p className="text-2xl font-bold">
                            {formatNumber(channelStats[selectedChannel.id].total_views || 0)}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            <Upload className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">Content</span>
                          </div>
                          <p className="text-2xl font-bold">
                            {channelStats[selectedChannel.id].content_count || 0}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">Engagement</span>
                          </div>
                          <p className="text-2xl font-bold">
                            {channelStats[selectedChannel.id].engagement_rate || '0'}%
                          </p>
                        </CardContent>
                      </Card>
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Content Tab */}
              <TabsContent value="content">
                <Card>
                  <CardHeader>
                    <CardTitle>Channel Content</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {contentItems.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <Upload className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No content uploaded yet</p>
                        <p className="text-sm">Upload your first piece of content to get started</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {contentItems.map((item) => (
                          <div key={item.id} className="flex items-center gap-3 p-3 border rounded-lg">
                            <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                              {item.thumbnail ? (
                                <img src={item.thumbnail} alt={item.title} className="w-full h-full object-cover rounded" />
                              ) : (
                                <Upload className="h-6 w-6 text-gray-400" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h3 className="font-medium truncate">{item.title}</h3>
                              <p className="text-sm text-muted-foreground line-clamp-2">{item.description}</p>
                              <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                                <span>📅 {new Date(item.created_at).toLocaleDateString()}</span>
                                <span>👁️ {formatNumber(item.views || 0)} views</span>
                                <span>❤️ {formatNumber(item.likes || 0)} likes</span>
                                <span>💬 {formatNumber(item.comments || 0)} comments</span>
                              </div>
                            </div>
                            <div className="flex gap-1">
                              <Button size="sm" variant="ghost">
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button size="sm" variant="ghost">
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                              <Button size="sm" variant="ghost">
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

              {/* Analytics Tab */}
              <TabsContent value="analytics">
                <Card>
                  <CardHeader>
                    <CardTitle>Channel Analytics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-8 text-muted-foreground">
                      <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Analytics dashboard coming soon</p>
                      <p className="text-sm">Detailed insights and performance metrics will be available here</p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Settings Tab */}
              <TabsContent value="settings">
                <Card>
                  <CardHeader>
                    <CardTitle>Channel Settings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-8 text-muted-foreground">
                      <Settings className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Channel settings coming soon</p>
                      <p className="text-sm">Configure your channel preferences and automation settings</p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-center text-muted-foreground">
                  <Globe className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Select a channel to view details</p>
                  <p className="text-sm">Choose a channel from the list to manage its content and settings</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChannelManager;
