import React, { useState, useEffect } from 'react';
import { useAI } from '../contexts/AIContext';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { AIProvider, AIRequest } from '../contexts/AIContext';

type AIRequestStatus = 'pending' | 'processing' | 'completed' | 'failed';

const AI: React.FC = () => {
  const { 
    state: { providers, requests },
    loadProviders,
    toggleProvider,
    getProvidersByType,
    getBestProvider,
    generateContent,
    generateWithProvider,
    getQuotaUsage,
    isProviderAvailable,
    getRequestHistory
  } = useAI();
  
  const { user } = useAuth();
  const { theme, actualTheme } = useTheme();
  
  // Theme utility function
  const getThemeValue = (lightValue: string, darkValue: string) => {
    return actualTheme === 'dark' ? darkValue : lightValue;
  };
  
  // State for modals and forms
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<AIRequestStatus>('pending');
  const [activeProvider, setActiveProvider] = useState<AIProvider | null>(null);
  
  // Form data
  const [newProviderData, setNewProviderData] = useState({
    name: '',
    category: 'llm' as const,
    description: '',
    apiEndpoint: '',
    authType: 'api_key' as const,
    pricing: { model: 'pay_per_use' as const, cost: 0 },
    capabilities: [] as string[],
    limits: { requestsPerMinute: 60, tokensPerRequest: 4000 }
  });
  
  const [newRequestData, setNewRequestData] = useState({
    providerId: '',
    prompt: '',
    parameters: {},
    priority: 'medium' as const
  });
  
  // Get filtered data
  const filteredProviders = selectedCategory === 'all' 
    ? providers 
    : getProvidersByType(selectedCategory);
  
  const filteredRequests = requests.filter(r => r.status === selectedStatus);
  
  // Provider stats (mock implementation)
  const getProviderStats = (providerId: string) => {
    const providerRequests = requests.filter(r => r.providerId === providerId);
    const completed = providerRequests.filter(r => r.status === 'completed');
    return {
      totalRequests: providerRequests.length,
      successRate: providerRequests.length > 0 ? Math.round((completed.length / providerRequests.length) * 100) : 0
    };
  };
  
  const handleCreateProvider = async () => {
    try {
      // Mock provider creation - in real app this would call an API
      const newProvider: AIProvider = {
        id: `provider_${Date.now()}`,
        name: newProviderData.name,
        type: newProviderData.category === 'llm' ? 'text' : 'image',
        category: 'free',
        isActive: true,
        apiEndpoint: newProviderData.apiEndpoint,
        rateLimit: { 
          requestsPerMinute: newProviderData.limits.requestsPerMinute,
          requestsPerDay: newProviderData.limits.tokensPerRequest * 10
        },
        capabilities: newProviderData.capabilities,
        quality: 'good',
        responseTime: 'medium'
      };
      
      console.log('Created provider:', newProvider);
      setShowProviderModal(false);
      setNewProviderData({
        name: '',
        category: 'llm',
        description: '',
        apiEndpoint: '',
        authType: 'api_key',
        pricing: { model: 'pay_per_use', cost: 0 },
        capabilities: [],
        limits: { requestsPerMinute: 60, tokensPerRequest: 4000 }
      });
    } catch (error) {
      console.error('Failed to create provider:', error);
    }
  };
  
  const handleCreateRequest = async () => {
    if (!activeProvider) return;
    
    try {
      // Mock request creation - in real app this would call generateWithProvider
      const result = await generateWithProvider(activeProvider.id, newRequestData.prompt, newRequestData.parameters);
      console.log('Request result:', result);
      
      setShowRequestModal(false);
      setNewRequestData({
        providerId: '',
        prompt: '',
        parameters: {},
        priority: 'medium'
      });
    } catch (error) {
      console.error('Failed to create request:', error);
    }
  };
  
  const getCategoryIcon = (category: string) => {
    const icons = {
      llm: '🤖',
      image: '🎨',
      audio: '🎵',
      video: '🎬',
      code: '💻',
      data: '📊',
      other: '⚡'
    };
    return icons[category as keyof typeof icons] || '⚡';
  };
  
  const getStatusColor = (status: AIRequestStatus) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800'
    };
    return colors[status];
  };
  
  const getPriorityColor = (priority: string) => {
    const colors = {
      low: 'bg-gray-100 text-gray-800',
      medium: 'bg-blue-100 text-blue-800',
      high: 'bg-orange-100 text-orange-800',
      urgent: 'bg-red-100 text-red-800'
    };
    return colors[priority as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };
  
  return (
    <div className={`min-h-screen ${getThemeValue('bg-gray-50', 'bg-gray-900')} transition-colors duration-200`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className={`text-3xl font-bold ${getThemeValue('text-gray-900', 'text-white')}`}>
                AI Services
              </h1>
              <p className={`mt-2 ${getThemeValue('text-gray-600', 'text-gray-400')}`}>
                Manage AI providers and orchestrate intelligent workflows
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowRequestModal(true)}
                disabled={!activeProvider}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeProvider
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                New Request
              </button>
              <button
                onClick={() => setShowProviderModal(true)}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Add Provider
              </button>
            </div>
          </div>
        </div>
        
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className={`${getThemeValue('bg-white', 'bg-gray-800')} rounded-lg p-6 shadow-sm`}>
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-2xl">🤖</span>
              </div>
              <div className="ml-4">
                <p className={`text-sm font-medium ${getThemeValue('text-gray-600', 'text-gray-400')}`}>
                  Active Providers
                </p>
                <p className={`text-2xl font-bold ${getThemeValue('text-gray-900', 'text-white')}`}>
                  {providers.filter(p => p.isActive).length}
                </p>
              </div>
            </div>
          </div>
          
          <div className={`${getThemeValue('bg-white', 'bg-gray-800')} rounded-lg p-6 shadow-sm`}>
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-2xl">✅</span>
              </div>
              <div className="ml-4">
                <p className={`text-sm font-medium ${getThemeValue('text-gray-600', 'text-gray-400')}`}>
                  Completed Requests
                </p>
                <p className={`text-2xl font-bold ${getThemeValue('text-gray-900', 'text-white')}`}>
                  {requests.filter(r => r.status === 'completed').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className={`${getThemeValue('bg-white', 'bg-gray-800')} rounded-lg p-6 shadow-sm`}>
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <span className="text-2xl">⏳</span>
              </div>
              <div className="ml-4">
                <p className={`text-sm font-medium ${getThemeValue('text-gray-600', 'text-gray-400')}`}>
                  Pending Requests
                </p>
                <p className={`text-2xl font-bold ${getThemeValue('text-gray-900', 'text-white')}`}>
                  {requests.filter(r => r.status === 'pending').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className={`${getThemeValue('bg-white', 'bg-gray-800')} rounded-lg p-6 shadow-sm`}>
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <span className="text-2xl">💰</span>
              </div>
              <div className="ml-4">
                <p className={`text-sm font-medium ${getThemeValue('text-gray-600', 'text-gray-400')}`}>
                  Est. Monthly Cost
                </p>
                <p className={`text-2xl font-bold ${getThemeValue('text-gray-900', 'text-white')}`}>
                  ${Math.floor(Math.random() * 500) + 50}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Providers Panel */}
          <div className="lg:col-span-2">
            <div className={`${getThemeValue('bg-white', 'bg-gray-800')} rounded-lg shadow-sm`}>
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className={`text-xl font-semibold ${getThemeValue('text-gray-900', 'text-white')}`}>
                    AI Providers
                  </h2>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className={`px-3 py-2 border rounded-lg text-sm ${getThemeValue(
                      'border-gray-300 bg-white text-gray-900',
                      'border-gray-600 bg-gray-700 text-white'
                    )}`}
                  >
                    <option value="all">All Categories</option>
                    <option value="llm">Language Models</option>
                    <option value="image">Image Generation</option>
                    <option value="audio">Audio Processing</option>
                    <option value="video">Video Processing</option>
                    <option value="code">Code Generation</option>
                    <option value="data">Data Analysis</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
              
              <div className="p-6">
                <div className="space-y-4">
                  {filteredProviders.map((provider) => {
                    const stats = getProviderStats(provider.id);
                    const isActive = activeProvider?.id === provider.id;
                    
                    return (
                      <div
                        key={provider.id}
                        onClick={() => setActiveProvider(provider)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          isActive
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : getThemeValue(
                                'border-gray-200 hover:border-gray-300 bg-gray-50',
                                'border-gray-700 hover:border-gray-600 bg-gray-700/50'
                              )
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <span className="text-2xl">
                              {getCategoryIcon(provider.category)}
                            </span>
                            <div>
                              <h3 className={`font-semibold ${getThemeValue('text-gray-900', 'text-white')}`}>
                                {provider.name}
                              </h3>
                              <p className={`text-sm ${getThemeValue('text-gray-600', 'text-gray-400')}`}>
                                {provider.capabilities.join(', ') || 'No description available'}
                              </p>
                              <div className="flex items-center gap-2 mt-2">
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  provider.isActive
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {provider.isActive ? 'Active' : 'Inactive'}
                                </span>
                                <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                                  {provider.category.toUpperCase()}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className={`text-sm font-medium ${getThemeValue('text-gray-900', 'text-white')}`}>
                              {stats?.totalRequests || 0} requests
                            </p>
                            <p className={`text-xs ${getThemeValue('text-gray-600', 'text-gray-400')}`}>
                              {stats?.successRate || 0}% success
                            </p>
                          </div>
                        </div>
                        
                        {provider.capabilities.length > 0 && (
                          <div className="mt-3">
                            <div className="flex flex-wrap gap-1">
                              {provider.capabilities.slice(0, 3).map((capability, index) => (
                                <span
                                  key={index}
                                  className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded"
                                >
                                  {capability}
                                </span>
                              ))}
                              {provider.capabilities.length > 3 && (
                                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                                  +{provider.capabilities.length - 3} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
          
          {/* Requests Panel */}
          <div>
            <div className={`${getThemeValue('bg-white', 'bg-gray-800')} rounded-lg shadow-sm`}>
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className={`text-xl font-semibold ${getThemeValue('text-gray-900', 'text-white')}`}>
                    Recent Requests
                  </h2>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value as AIRequestStatus)}
                    className={`px-3 py-2 border rounded-lg text-sm ${getThemeValue(
                      'border-gray-300 bg-white text-gray-900',
                      'border-gray-600 bg-gray-700 text-white'
                    )}`}
                  >
                    <option value="pending">Pending</option>
                    <option value="processing">Processing</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              </div>
              
              <div className="p-6">
                <div className="space-y-4">
                  {filteredRequests.slice(0, 10).map((request) => {
                    const provider = providers.find(p => p.id === request.providerId);
                    
                    return (
                      <div
                        key={request.id}
                        className={`p-4 rounded-lg border ${getThemeValue(
                          'border-gray-200 bg-gray-50',
                          'border-gray-700 bg-gray-700/50'
                        )}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(request.status)}`}>
                                {request.status}
                              </span>
                              <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                                {request.type}
                              </span>
                            </div>
                            <p className={`text-sm font-medium ${getThemeValue('text-gray-900', 'text-white')}`}>
                              {provider?.name || 'Unknown Provider'}
                            </p>
                            <p className={`text-xs ${getThemeValue('text-gray-600', 'text-gray-400')} mt-1`}>
                              {request.prompt.length > 50 
                                ? `${request.prompt.substring(0, 50)}...` 
                                : request.prompt}
                            </p>
                            <p className={`text-xs ${getThemeValue('text-gray-500', 'text-gray-500')} mt-2`}>
                              {new Date(request.createdAt).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  
                  {filteredRequests.length === 0 && (
                    <div className="text-center py-8">
                      <p className={`${getThemeValue('text-gray-500', 'text-gray-400')}`}>
                        No {selectedStatus} requests found
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Provider Modal */}
      {showProviderModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className={`${getThemeValue('bg-white', 'bg-gray-800')} rounded-lg p-6 w-full max-w-md`}>
            <h3 className={`text-lg font-semibold mb-4 ${getThemeValue('text-gray-900', 'text-white')}`}>
              Add AI Provider
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-1 ${getThemeValue('text-gray-700', 'text-gray-300')}`}>
                  Provider Name
                </label>
                <input
                  type="text"
                  value={newProviderData.name}
                  onChange={(e) => setNewProviderData({ ...newProviderData, name: e.target.value })}
                  className={`w-full px-3 py-2 border rounded-lg ${getThemeValue(
                    'border-gray-300 bg-white text-gray-900',
                    'border-gray-600 bg-gray-700 text-white'
                  )}`}
                  placeholder="e.g., OpenAI GPT-4"
                />
              </div>
              
              <div>
                <label className={`block text-sm font-medium mb-1 ${getThemeValue('text-gray-700', 'text-gray-300')}`}>
                  Category
                </label>
                <select
                  value={newProviderData.category}
                  onChange={(e) => setNewProviderData({ ...newProviderData, category: e.target.value as any })}
                  className={`w-full px-3 py-2 border rounded-lg ${getThemeValue(
                    'border-gray-300 bg-white text-gray-900',
                    'border-gray-600 bg-gray-700 text-white'
                  )}`}
                >
                  <option value="llm">Language Model</option>
                  <option value="image">Image Generation</option>
                  <option value="audio">Audio Processing</option>
                  <option value="video">Video Processing</option>
                  <option value="code">Code Generation</option>
                  <option value="data">Data Analysis</option>
                  <option value="other">Other</option>
                </select>
              </div>
              
              <div>
                <label className={`block text-sm font-medium mb-1 ${getThemeValue('text-gray-700', 'text-gray-300')}`}>
                  Description
                </label>
                <textarea
                  value={newProviderData.description}
                  onChange={(e) => setNewProviderData({ ...newProviderData, description: e.target.value })}
                  className={`w-full px-3 py-2 border rounded-lg ${getThemeValue(
                    'border-gray-300 bg-white text-gray-900',
                    'border-gray-600 bg-gray-700 text-white'
                  )}`}
                  rows={3}
                  placeholder="Brief description of the AI provider..."
                />
              </div>
              
              <div>
                <label className={`block text-sm font-medium mb-1 ${getThemeValue('text-gray-700', 'text-gray-300')}`}>
                  API Endpoint
                </label>
                <input
                  type="url"
                  value={newProviderData.apiEndpoint}
                  onChange={(e) => setNewProviderData({ ...newProviderData, apiEndpoint: e.target.value })}
                  className={`w-full px-3 py-2 border rounded-lg ${getThemeValue(
                    'border-gray-300 bg-white text-gray-900',
                    'border-gray-600 bg-gray-700 text-white'
                  )}`}
                  placeholder="https://api.example.com/v1"
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowProviderModal(false)}
                className={`flex-1 px-4 py-2 border rounded-lg font-medium ${getThemeValue(
                  'border-gray-300 text-gray-700 hover:bg-gray-50',
                  'border-gray-600 text-gray-300 hover:bg-gray-700'
                )}`}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateProvider}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
              >
                Add Provider
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Request Modal */}
      {showRequestModal && activeProvider && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className={`${getThemeValue('bg-white', 'bg-gray-800')} rounded-lg p-6 w-full max-w-md`}>
            <h3 className={`text-lg font-semibold mb-4 ${getThemeValue('text-gray-900', 'text-white')}`}>
              New AI Request
            </h3>
            
            <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className={`text-sm ${getThemeValue('text-blue-800', 'text-blue-200')}`}>
                Provider: <span className="font-medium">{activeProvider.name}</span>
              </p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-1 ${getThemeValue('text-gray-700', 'text-gray-300')}`}>
                  Prompt
                </label>
                <textarea
                  value={newRequestData.prompt}
                  onChange={(e) => setNewRequestData({ ...newRequestData, prompt: e.target.value })}
                  className={`w-full px-3 py-2 border rounded-lg ${getThemeValue(
                    'border-gray-300 bg-white text-gray-900',
                    'border-gray-600 bg-gray-700 text-white'
                  )}`}
                  rows={4}
                  placeholder="Enter your prompt or request..."
                />
              </div>
              
              <div>
                <label className={`block text-sm font-medium mb-1 ${getThemeValue('text-gray-700', 'text-gray-300')}`}>
                  Priority
                </label>
                <select
                  value={newRequestData.priority}
                  onChange={(e) => setNewRequestData({ ...newRequestData, priority: e.target.value as any })}
                  className={`w-full px-3 py-2 border rounded-lg ${getThemeValue(
                    'border-gray-300 bg-white text-gray-900',
                    'border-gray-600 bg-gray-700 text-white'
                  )}`}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowRequestModal(false)}
                className={`flex-1 px-4 py-2 border rounded-lg font-medium ${getThemeValue(
                  'border-gray-300 text-gray-700 hover:bg-gray-50',
                  'border-gray-600 text-gray-300 hover:bg-gray-700'
                )}`}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRequest}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
              >
                Create Request
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AI;