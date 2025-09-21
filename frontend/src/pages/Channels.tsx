import React, { useState, useEffect } from 'react';
import { useChannel } from '../contexts/ChannelContext';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Channel, ChannelContent } from '../contexts/ChannelContext';

const Channels: React.FC = () => {
  const {
    state: { channels, activeChannel },
    setActiveChannel,
    createChannel,
    updateChannel,
    deleteChannel,
    createContent,
    updateContent,
    deleteContent,
    getContentByChannel
  } = useChannel();

  const { user } = useAuth();
  const { actualTheme } = useTheme();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showContentModal, setShowContentModal] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
  const [newChannelData, setNewChannelData] = useState({
    name: '',
    description: '',
    category: 'custom' as const,
    isPublic: true
  });
  const [newContentData, setNewContentData] = useState({
    title: '',
    content: '',
    type: 'text' as const,
    tags: [] as string[]
  });
  const [tagInput, setTagInput] = useState('');

  // Get content for active channel
  const channelContent = activeChannel ? getContentByChannel(activeChannel.id) : [];

  // Mock stats calculation
  const channelStats = activeChannel ? {
    contentCount: channelContent.length,
    memberCount: Math.floor(Math.random() * 50) + 10,
    totalViews: Math.floor(Math.random() * 1000) + 100,
    avgEngagement: Math.random() * 100
  } : null;

  const handleCreateChannel = async () => {
    try {
      await createChannel({
        ...newChannelData,
        icon: getCategoryIcon(newChannelData.category),
        color: '#6B7280',
        isActive: true,
        isCore: false,
        settings: {},
        permissions: ['read', 'write']
      });
      setShowCreateModal(false);
      setNewChannelData({ name: '', description: '', category: 'custom', isPublic: true });
    } catch (error) {
      console.error('Failed to create channel:', error);
    }
  };

  const handleCreateContent = async () => {
    if (!activeChannel) return;

    try {
      await createContent({
        ...newContentData,
        channelId: activeChannel.id,
        contentType: newContentData.type,
        status: 'published' as const,
        metadata: {}
      });
      setShowContentModal(false);
      setNewContentData({ title: '', content: '', type: 'text', tags: [] });
      setTagInput('');
    } catch (error) {
      console.error('Failed to create content:', error);
    }
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !newContentData.tags.includes(tagInput.trim())) {
      setNewContentData(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setNewContentData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'research': return '🔬';
      case 'content': return '📝';
      case 'business': return '💼';
      case 'ai': return '🤖';
      default: return '📁';
    }
  };

  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'text': return '📄';
      case 'image': return '🖼️';
      case 'video': return '🎥';
      case 'audio': return '🎵';
      case 'document': return '📋';
      default: return '📄';
    }
  };

  return (
    <div className={`min-h-screen p-6 ${
      actualTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
    }`}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className={`text-3xl font-bold ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              Channel Management
            </h1>
            <p className={`mt-2 ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Manage your content channels and organize your AI-powered workflows
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <span>➕</span>
            Create Channel
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Channels List */}
          <div className={`lg:col-span-1 ${
            actualTheme === 'dark' ? 'bg-gray-800' : 'bg-white'
          } rounded-lg shadow p-6`}>
            <h2 className={`text-xl font-semibold mb-4 ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              Channels ({channels.length})
            </h2>

            <div className="space-y-3">
              {channels.map((channel) => {
                const content = getContentByChannel(channel.id);
                const stats = {
                  contentCount: content.length,
                  memberCount: Math.floor(Math.random() * 50) + 10
                };
                const isActive = activeChannel?.id === channel.id;

                return (
                  <div
                    key={channel.id}
                    onClick={() => setActiveChannel(channel)}
                    className={`p-4 rounded-lg cursor-pointer transition-all ${
                      isActive
                        ? 'bg-blue-100 border-2 border-blue-500'
                        : actualTheme === 'dark'
                        ? 'bg-gray-700 hover:bg-gray-600 border border-gray-600'
                        : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">
                          {getCategoryIcon(channel.category)}
                        </span>
                        <div>
                          <h3 className={`font-medium ${
                            actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                          }`}>
                            {channel.name}
                          </h3>
                          <p className={`text-sm ${
                            actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                          }`}>
                            {channel.description}
                          </p>
                        </div>
                      </div>
                      {channel.isCore && (
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                          Core
                        </span>
                      )}
                    </div>

                    {stats && (
                      <div className="mt-3 flex gap-4 text-sm">
                        <span className={actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                          📄 {stats.contentCount} items
                        </span>
                        <span className={actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                          👥 {stats.memberCount} members
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Channel Content */}
          <div className={`lg:col-span-2 ${
            actualTheme === 'dark' ? 'bg-gray-800' : 'bg-white'
          } rounded-lg shadow p-6`}>
            {activeChannel ? (
              <>
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h2 className={`text-xl font-semibold flex items-center gap-2 ${
                      actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>
                      <span>{getCategoryIcon(activeChannel.category)}</span>
                      {activeChannel.name}
                    </h2>
                    <p className={`mt-1 ${
                      actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      {activeChannel.description}
                    </p>
                  </div>
                  <button
                    onClick={() => setShowContentModal(true)}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                  >
                    <span>➕</span>
                    Add Content
                  </button>
                </div>

                {/* Channel Stats */}
                {channelStats && (
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className={`p-4 rounded-lg ${
                      actualTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                    }`}>
                      <div className={`text-2xl font-bold ${
                        actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                      }`}>
                        {channelStats.contentCount}
                      </div>
                      <div className={`text-sm ${
                        actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        Content Items
                      </div>
                    </div>
                    <div className={`p-4 rounded-lg ${
                      actualTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                    }`}>
                      <div className={`text-2xl font-bold ${
                        actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                      }`}>
                        {channelStats.memberCount}
                      </div>
                      <div className={`text-sm ${
                        actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        Members
                      </div>
                    </div>
                    <div className={`p-4 rounded-lg ${
                      actualTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                    }`}>
                      <div className={`text-2xl font-bold ${
                        actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                      }`}>
                        {channelStats.totalViews}
                      </div>
                      <div className={`text-sm ${
                        actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        Total Views
                      </div>
                    </div>
                    <div className={`p-4 rounded-lg ${
                      actualTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                    }`}>
                      <div className={`text-2xl font-bold ${
                        actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                      }`}>
                        {channelStats.avgEngagement.toFixed(1)}%
                      </div>
                      <div className={`text-sm ${
                        actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        Engagement
                      </div>
                    </div>
                  </div>
                )}

                {/* Content List */}
                <div className="space-y-4">
                  {channelContent.length > 0 ? (
                    channelContent.map((content) => (
                      <div
                        key={content.id}
                        className={`p-4 rounded-lg border ${
                          actualTheme === 'dark'
                            ? 'bg-gray-700 border-gray-600'
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <span className="text-xl">
                              {getContentTypeIcon(content.contentType)}
                            </span>
                            <div>
                              <h3 className={`font-medium ${
                                actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                              }`}>
                                {content.title}
                              </h3>
                              <p className={`text-sm mt-1 ${
                                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                              }`}>
                                {content.content.substring(0, 150)}...
                              </p>
                              {content.tags.length > 0 && (
                                <div className="flex gap-2 mt-2">
                                  {content.tags.map((tag) => (
                                    <span
                                      key={tag}
                                      className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <button className="text-blue-600 hover:text-blue-800 text-sm">
                              Edit
                            </button>
                            <button className="text-red-600 hover:text-red-800 text-sm">
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className={`text-center py-12 ${
                      actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      <div className="text-4xl mb-4">📭</div>
                      <p>No content in this channel yet.</p>
                      <p className="text-sm mt-1">Click "Add Content" to get started.</p>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className={`text-center py-12 ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
              }`}>
                <div className="text-4xl mb-4">📋</div>
                <p>Select a channel to view its content</p>
                <p className="text-sm mt-1">Choose from the channels on the left to get started.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Channel Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`max-w-md w-full mx-4 p-6 rounded-lg ${
            actualTheme === 'dark' ? 'bg-gray-800' : 'bg-white'
          }`}>
            <h3 className={`text-lg font-semibold mb-4 ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              Create New Channel
            </h3>

            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-1 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Channel Name
                </label>
                <input
                  type="text"
                  value={newChannelData.name}
                  onChange={(e) => setNewChannelData(prev => ({ ...prev, name: e.target.value }))}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    actualTheme === 'dark'
                      ? 'bg-gray-700 border-gray-600 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}
                  placeholder="Enter channel name"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Description
                </label>
                <textarea
                  value={newChannelData.description}
                  onChange={(e) => setNewChannelData(prev => ({ ...prev, description: e.target.value }))}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    actualTheme === 'dark'
                      ? 'bg-gray-700 border-gray-600 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}
                  rows={3}
                  placeholder="Describe your channel"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Category
                </label>
                <select
                  value={newChannelData.category}
                  onChange={(e) => setNewChannelData(prev => ({ ...prev, category: e.target.value as any }))}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    actualTheme === 'dark'
                      ? 'bg-gray-700 border-gray-600 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}
                >
                  <option value="custom">📁 Custom</option>
                  <option value="research">🔬 Research</option>
                  <option value="content">📝 Content</option>
                  <option value="business">💼 Business</option>
                  <option value="ai">🤖 AI</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="isPublic"
                  checked={newChannelData.isPublic}
                  onChange={(e) => setNewChannelData(prev => ({ ...prev, isPublic: e.target.checked }))}
                  className="mr-2"
                />
                <label htmlFor="isPublic" className={`text-sm ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Make channel public
                </label>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className={`flex-1 px-4 py-2 border rounded-lg ${
                  actualTheme === 'dark'
                    ? 'border-gray-600 text-gray-300 hover:bg-gray-700'
                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateChannel}
                disabled={!newChannelData.name.trim()}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg"
              >
                Create Channel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Content Modal */}
      {showContentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`max-w-lg w-full mx-4 p-6 rounded-lg ${
            actualTheme === 'dark' ? 'bg-gray-800' : 'bg-white'
          }`}>
            <h3 className={`text-lg font-semibold mb-4 ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              Add Content to {activeChannel?.name}
            </h3>

            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-1 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Title
                </label>
                <input
                  type="text"
                  value={newContentData.title}
                  onChange={(e) => setNewContentData(prev => ({ ...prev, title: e.target.value }))}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    actualTheme === 'dark'
                      ? 'bg-gray-700 border-gray-600 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}
                  placeholder="Enter content title"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Content
                </label>
                <textarea
                  value={newContentData.content}
                  onChange={(e) => setNewContentData(prev => ({ ...prev, content: e.target.value }))}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    actualTheme === 'dark'
                      ? 'bg-gray-700 border-gray-600 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}
                  rows={4}
                  placeholder="Enter your content"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Content Type
                </label>
                <select
                  value={newContentData.type}
                  onChange={(e) => setNewContentData(prev => ({ ...prev, type: e.target.value as any }))}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    actualTheme === 'dark'
                      ? 'bg-gray-700 border-gray-600 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}
                >
                  <option value="text">📄 Text</option>
                  <option value="image">🖼️ Image</option>
                  <option value="video">🎥 Video</option>
                  <option value="audio">🎵 Audio</option>
                  <option value="document">📋 Document</option>
                </select>
              </div>

              <div>
                <label className={`block text-sm font-medium mb-1 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Tags
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                    className={`flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      actualTheme === 'dark'
                        ? 'bg-gray-700 border-gray-600 text-white'
                        : 'bg-white border-gray-300 text-gray-900'
                    }`}
                    placeholder="Add a tag"
                  />
                  <button
                    onClick={handleAddTag}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg"
                  >
                    Add
                  </button>
                </div>
                {newContentData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {newContentData.tags.map((tag) => (
                      <span
                        key={tag}
                        className="bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded-full flex items-center gap-1"
                      >
                        {tag}
                        <button
                          onClick={() => handleRemoveTag(tag)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowContentModal(false)}
                className={`flex-1 px-4 py-2 border rounded-lg ${
                  actualTheme === 'dark'
                    ? 'border-gray-600 text-gray-300 hover:bg-gray-700'
                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateContent}
                disabled={!newContentData.title.trim() || !newContentData.content.trim()}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg"
              >
                Add Content
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Channels;
