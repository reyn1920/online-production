import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

// Types
interface Channel {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  color: string;
  isActive: boolean;
  isCore: boolean;
  createdAt: string;
  updatedAt: string;
  settings: Record<string, any>;
  permissions: string[];
}

interface ChannelContent {
  id: string;
  channelId: string;
  title: string;
  content: string;
  contentType: 'text' | 'image' | 'video' | 'audio' | 'document';
  status: 'draft' | 'published' | 'archived';
  tags: string[];
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

interface ChannelState {
  channels: Channel[];
  activeChannel: Channel | null;
  channelContent: Record<string, ChannelContent[]>;
  loading: boolean;
  error: string | null;
}

type ChannelAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CHANNELS'; payload: Channel[] }
  | { type: 'SET_ACTIVE_CHANNEL'; payload: Channel | null }
  | { type: 'ADD_CHANNEL'; payload: Channel }
  | { type: 'UPDATE_CHANNEL'; payload: { id: string; updates: Partial<Channel> } }
  | { type: 'DELETE_CHANNEL'; payload: string }
  | { type: 'SET_CHANNEL_CONTENT'; payload: { channelId: string; content: ChannelContent[] } }
  | { type: 'ADD_CONTENT'; payload: ChannelContent }
  | { type: 'UPDATE_CONTENT'; payload: { id: string; updates: Partial<ChannelContent> } }
  | { type: 'DELETE_CONTENT'; payload: string };

interface ChannelContextType {
  state: ChannelState;
  // Channel management
  loadChannels: () => Promise<void>;
  createChannel: (channelData: Omit<Channel, 'id' | 'createdAt' | 'updatedAt'>) => Promise<void>;
  updateChannel: (id: string, updates: Partial<Channel>) => Promise<void>;
  deleteChannel: (id: string) => Promise<void>;
  setActiveChannel: (channel: Channel | null) => void;
  // Content management
  loadChannelContent: (channelId: string) => Promise<void>;
  createContent: (contentData: Omit<ChannelContent, 'id' | 'createdAt' | 'updatedAt'>) => Promise<void>;
  updateContent: (id: string, updates: Partial<ChannelContent>) => Promise<void>;
  deleteContent: (id: string) => Promise<void>;
  // Utility functions
  getChannelById: (id: string) => Channel | undefined;
  getContentByChannel: (channelId: string) => ChannelContent[];
  getCoreChannels: () => Channel[];
  getCustomChannels: () => Channel[];
}

// Initial state
const initialState: ChannelState = {
  channels: [],
  activeChannel: null,
  channelContent: {},
  loading: false,
  error: null,
};

// Core channels (first 4 - preserved as requested)
const CORE_CHANNELS: Omit<Channel, 'id' | 'createdAt' | 'updatedAt'>[] = [
  {
    name: 'Information Hub',
    description: 'Central information and knowledge management',
    category: 'Core',
    icon: '📊',
    color: '#3B82F6',
    isActive: true,
    isCore: true,
    settings: {
      allowPublicAccess: true,
      enableNotifications: true,
      contentModeration: 'auto',
    },
    permissions: ['read', 'write', 'moderate'],
  },
  {
    name: 'Marketing Central',
    description: 'Marketing campaigns and promotional content',
    category: 'Core',
    icon: '📈',
    color: '#10B981',
    isActive: true,
    isCore: true,
    settings: {
      allowPublicAccess: false,
      enableNotifications: true,
      contentModeration: 'manual',
    },
    permissions: ['read', 'write', 'moderate', 'analytics'],
  },
  {
    name: 'Content Production',
    description: 'Content creation and production workflows',
    category: 'Core',
    icon: '🎬',
    color: '#8B5CF6',
    isActive: true,
    isCore: true,
    settings: {
      allowPublicAccess: false,
      enableNotifications: true,
      contentModeration: 'manual',
    },
    permissions: ['read', 'write', 'moderate', 'publish'],
  },
  {
    name: 'Analytics & Insights',
    description: 'Data analytics and business intelligence',
    category: 'Core',
    icon: '📊',
    color: '#F59E0B',
    isActive: true,
    isCore: true,
    settings: {
      allowPublicAccess: false,
      enableNotifications: false,
      contentModeration: 'auto',
    },
    permissions: ['read', 'analytics', 'export'],
  },
];

// Reducer
const channelReducer = (state: ChannelState, action: ChannelAction): ChannelState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };

    case 'SET_CHANNELS':
      return { ...state, channels: action.payload, loading: false, error: null };

    case 'SET_ACTIVE_CHANNEL':
      return { ...state, activeChannel: action.payload };

    case 'ADD_CHANNEL':
      return {
        ...state,
        channels: [...state.channels, action.payload],
        loading: false,
        error: null,
      };

    case 'UPDATE_CHANNEL':
      return {
        ...state,
        channels: state.channels.map(channel =>
          channel.id === action.payload.id
            ? { ...channel, ...action.payload.updates, updatedAt: new Date().toISOString() }
            : channel
        ),
        activeChannel: state.activeChannel?.id === action.payload.id
          ? { ...state.activeChannel, ...action.payload.updates, updatedAt: new Date().toISOString() }
          : state.activeChannel,
      };

    case 'DELETE_CHANNEL':
      return {
        ...state,
        channels: state.channels.filter(channel => channel.id !== action.payload),
        activeChannel: state.activeChannel?.id === action.payload ? null : state.activeChannel,
        channelContent: Object.fromEntries(
          Object.entries(state.channelContent).filter(([channelId]) => channelId !== action.payload)
        ),
      };

    case 'SET_CHANNEL_CONTENT':
      return {
        ...state,
        channelContent: {
          ...state.channelContent,
          [action.payload.channelId]: action.payload.content,
        },
      };

    case 'ADD_CONTENT':
      const channelId = action.payload.channelId;
      return {
        ...state,
        channelContent: {
          ...state.channelContent,
          [channelId]: [...(state.channelContent[channelId] || []), action.payload],
        },
      };

    case 'UPDATE_CONTENT':
      return {
        ...state,
        channelContent: Object.fromEntries(
          Object.entries(state.channelContent).map(([chId, contents]) => [
            chId,
            contents.map(content =>
              content.id === action.payload.id
                ? { ...content, ...action.payload.updates, updatedAt: new Date().toISOString() }
                : content
            ),
          ])
        ),
      };

    case 'DELETE_CONTENT':
      return {
        ...state,
        channelContent: Object.fromEntries(
          Object.entries(state.channelContent).map(([chId, contents]) => [
            chId,
            contents.filter(content => content.id !== action.payload),
          ])
        ),
      };

    default:
      return state;
  }
};

// Context
const ChannelContext = createContext<ChannelContextType | undefined>(undefined);

// Mock API functions (replace with actual API calls)
const mockApi = {
  getChannels: async (): Promise<Channel[]> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Return core channels with generated IDs and timestamps
    return CORE_CHANNELS.map((channel, index) => ({
      ...channel,
      id: `channel_${String(index + 1).padStart(3, '0')}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }));
  },

  createChannel: async (channelData: Omit<Channel, 'id' | 'createdAt' | 'updatedAt'>): Promise<Channel> => {
    await new Promise(resolve => setTimeout(resolve, 300));

    return {
      ...channelData,
      id: `channel_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  },

  updateChannel: async (id: string, updates: Partial<Channel>): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 300));
  },

  deleteChannel: async (id: string): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 300));
  },

  getChannelContent: async (channelId: string): Promise<ChannelContent[]> => {
    await new Promise(resolve => setTimeout(resolve, 300));

    // Return mock content
    return [
      {
        id: `content_${Date.now()}_1`,
        channelId,
        title: 'Sample Content',
        content: 'This is sample content for the channel.',
        contentType: 'text',
        status: 'published',
        tags: ['sample', 'demo'],
        metadata: {},
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];
  },

  createContent: async (contentData: Omit<ChannelContent, 'id' | 'createdAt' | 'updatedAt'>): Promise<ChannelContent> => {
    await new Promise(resolve => setTimeout(resolve, 300));

    return {
      ...contentData,
      id: `content_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  },

  updateContent: async (id: string, updates: Partial<ChannelContent>): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 300));
  },

  deleteContent: async (id: string): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 300));
  },
};

// Provider Component
export const ChannelProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(channelReducer, initialState);

  // Load channels on mount
  useEffect(() => {
    loadChannels();
  }, []);

  // Channel management functions
  const loadChannels = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const channels = await mockApi.getChannels();
      dispatch({ type: 'SET_CHANNELS', payload: channels });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load channels' });
    }
  };

  const createChannel = async (channelData: Omit<Channel, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const newChannel = await mockApi.createChannel(channelData);
      dispatch({ type: 'ADD_CHANNEL', payload: newChannel });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to create channel' });
    }
  };

  const updateChannel = async (id: string, updates: Partial<Channel>) => {
    try {
      await mockApi.updateChannel(id, updates);
      dispatch({ type: 'UPDATE_CHANNEL', payload: { id, updates } });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to update channel' });
    }
  };

  const deleteChannel = async (id: string) => {
    try {
      await mockApi.deleteChannel(id);
      dispatch({ type: 'DELETE_CHANNEL', payload: id });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to delete channel' });
    }
  };

  const setActiveChannel = (channel: Channel | null) => {
    dispatch({ type: 'SET_ACTIVE_CHANNEL', payload: channel });
  };

  // Content management functions
  const loadChannelContent = async (channelId: string) => {
    try {
      const content = await mockApi.getChannelContent(channelId);
      dispatch({ type: 'SET_CHANNEL_CONTENT', payload: { channelId, content } });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load channel content' });
    }
  };

  const createContent = async (contentData: Omit<ChannelContent, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      const newContent = await mockApi.createContent(contentData);
      dispatch({ type: 'ADD_CONTENT', payload: newContent });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to create content' });
    }
  };

  const updateContent = async (id: string, updates: Partial<ChannelContent>) => {
    try {
      await mockApi.updateContent(id, updates);
      dispatch({ type: 'UPDATE_CONTENT', payload: { id, updates } });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to update content' });
    }
  };

  const deleteContent = async (id: string) => {
    try {
      await mockApi.deleteContent(id);
      dispatch({ type: 'DELETE_CONTENT', payload: id });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to delete content' });
    }
  };

  // Utility functions
  const getChannelById = (id: string): Channel | undefined => {
    return state.channels.find(channel => channel.id === id);
  };

  const getContentByChannel = (channelId: string): ChannelContent[] => {
    return state.channelContent[channelId] || [];
  };

  const getCoreChannels = (): Channel[] => {
    return state.channels.filter(channel => channel.isCore);
  };

  const getCustomChannels = (): Channel[] => {
    return state.channels.filter(channel => !channel.isCore);
  };

  const contextValue: ChannelContextType = {
    state,
    loadChannels,
    createChannel,
    updateChannel,
    deleteChannel,
    setActiveChannel,
    loadChannelContent,
    createContent,
    updateContent,
    deleteContent,
    getChannelById,
    getContentByChannel,
    getCoreChannels,
    getCustomChannels,
  };

  return (
    <ChannelContext.Provider value={contextValue}>
      {children}
    </ChannelContext.Provider>
  );
};

// Hook to use channel context
export const useChannel = (): ChannelContextType => {
  const context = useContext(ChannelContext);

  if (context === undefined) {
    throw new Error('useChannel must be used within a ChannelProvider');
  }

  return context;
};

// Export types
export type { Channel, ChannelContent, ChannelState, ChannelContextType };
