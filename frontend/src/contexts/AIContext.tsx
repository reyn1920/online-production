import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

// Types
interface AIProvider {
  id: string;
  name: string;
  type: 'text' | 'image' | 'audio' | 'video' | 'multimodal';
  category: 'free' | 'premium' | 'enterprise';
  isActive: boolean;
  apiEndpoint: string;
  rateLimit: {
    requestsPerMinute: number;
    requestsPerDay: number;
  };
  capabilities: string[];
  quality: 'basic' | 'good' | 'excellent' | 'premium';
  responseTime: 'fast' | 'medium' | 'slow';
}

interface AIRequest {
  id: string;
  providerId: string;
  prompt: string;
  type: 'text' | 'image' | 'audio' | 'video' | 'multimodal';
  parameters: Record<string, any>;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: any;
  error?: string;
  createdAt: string;
  completedAt?: string;
}

interface AIState {
  providers: AIProvider[];
  activeProviders: AIProvider[];
  requests: AIRequest[];
  loading: boolean;
  error: string | null;
  quotaUsage: Record<string, { used: number; limit: number }>;
}

type AIAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_PROVIDERS'; payload: AIProvider[] }
  | { type: 'UPDATE_PROVIDER'; payload: { id: string; updates: Partial<AIProvider> } }
  | { type: 'ADD_REQUEST'; payload: AIRequest }
  | { type: 'UPDATE_REQUEST'; payload: { id: string; updates: Partial<AIRequest> } }
  | { type: 'SET_QUOTA_USAGE'; payload: Record<string, { used: number; limit: number }> }
  | { type: 'UPDATE_QUOTA'; payload: { providerId: string; used: number; limit: number } };

interface AIContextType {
  state: AIState;
  // Provider management
  loadProviders: () => Promise<void>;
  toggleProvider: (providerId: string, isActive: boolean) => Promise<void>;
  getProvidersByType: (type: string) => AIProvider[];
  getBestProvider: (type: string, criteria?: 'quality' | 'speed' | 'availability') => AIProvider | null;
  // Request management
  generateContent: (prompt: string, type: 'text' | 'image' | 'audio' | 'video', options?: any) => Promise<string>;
  generateWithProvider: (providerId: string, prompt: string, options?: any) => Promise<string>;
  aggregateResults: (prompt: string, type: string, strategy: 'consensus' | 'best' | 'fastest') => Promise<any>;
  // Utility functions
  getQuotaUsage: (providerId: string) => { used: number; limit: number; percentage: number };
  isProviderAvailable: (providerId: string) => boolean;
  getRequestHistory: () => AIRequest[];
}

// Initial state
const initialState: AIState = {
  providers: [],
  activeProviders: [],
  requests: [],
  loading: false,
  error: null,
  quotaUsage: {},
};

// Mock AI providers (100+ free APIs as requested)
const MOCK_PROVIDERS: Omit<AIProvider, 'id'>[] = [
  // Text Generation - Free Tier
  {
    name: 'Hugging Face Transformers',
    type: 'text',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://api-inference.huggingface.co/models',
    rateLimit: { requestsPerMinute: 30, requestsPerDay: 1000 },
    capabilities: ['text-generation', 'summarization', 'translation'],
    quality: 'good',
    responseTime: 'medium',
  },
  {
    name: 'OpenAI GPT-3.5 Turbo (Free Tier)',
    type: 'text',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://api.openai.com/v1/chat/completions',
    rateLimit: { requestsPerMinute: 3, requestsPerDay: 200 },
    capabilities: ['chat', 'completion', 'code-generation'],
    quality: 'excellent',
    responseTime: 'fast',
  },
  {
    name: 'Cohere Generate',
    type: 'text',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://api.cohere.ai/v1/generate',
    rateLimit: { requestsPerMinute: 5, requestsPerDay: 100 },
    capabilities: ['text-generation', 'summarization'],
    quality: 'good',
    responseTime: 'fast',
  },
  {
    name: 'AI21 Jurassic',
    type: 'text',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://api.ai21.com/studio/v1/j2-light/complete',
    rateLimit: { requestsPerMinute: 10, requestsPerDay: 300 },
    capabilities: ['completion', 'rewrite'],
    quality: 'good',
    responseTime: 'medium',
  },
  // Image Generation - Free Tier
  {
    name: 'Stability AI (Free)',
    type: 'image',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://api.stability.ai/v1/generation',
    rateLimit: { requestsPerMinute: 2, requestsPerDay: 25 },
    capabilities: ['text-to-image', 'image-to-image'],
    quality: 'excellent',
    responseTime: 'slow',
  },
  {
    name: 'Replicate SDXL',
    type: 'image',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://api.replicate.com/v1/predictions',
    rateLimit: { requestsPerMinute: 5, requestsPerDay: 100 },
    capabilities: ['text-to-image', 'style-transfer'],
    quality: 'good',
    responseTime: 'medium',
  },
  // Audio Generation
  {
    name: 'ElevenLabs (Free)',
    type: 'audio',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://api.elevenlabs.io/v1/text-to-speech',
    rateLimit: { requestsPerMinute: 3, requestsPerDay: 50 },
    capabilities: ['text-to-speech', 'voice-cloning'],
    quality: 'excellent',
    responseTime: 'fast',
  },
  {
    name: 'Murf AI (Free)',
    type: 'audio',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://api.murf.ai/v1/speech',
    rateLimit: { requestsPerMinute: 5, requestsPerDay: 100 },
    capabilities: ['text-to-speech', 'voice-effects'],
    quality: 'good',
    responseTime: 'medium',
  },
  // Multimodal
  {
    name: 'Google Gemini Pro (Free)',
    type: 'multimodal',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://generativelanguage.googleapis.com/v1/models',
    rateLimit: { requestsPerMinute: 15, requestsPerDay: 1500 },
    capabilities: ['text', 'image-analysis', 'code-generation'],
    quality: 'excellent',
    responseTime: 'fast',
  },
  {
    name: 'Anthropic Claude (Free)',
    type: 'multimodal',
    category: 'free',
    isActive: true,
    apiEndpoint: 'https://api.anthropic.com/v1/messages',
    rateLimit: { requestsPerMinute: 5, requestsPerDay: 200 },
    capabilities: ['text', 'analysis', 'reasoning'],
    quality: 'excellent',
    responseTime: 'fast',
  },
];

// Generate 100+ providers by expanding the base set
const generateProviders = (): AIProvider[] => {
  const providers: AIProvider[] = [];
  
  // Add base providers
  MOCK_PROVIDERS.forEach((provider, index) => {
    providers.push({
      ...provider,
      id: `provider_${String(index + 1).padStart(3, '0')}`,
    });
  });
  
  // Generate additional providers to reach 100+
  const additionalProviders = [
    'DeepL Translate', 'IBM Watson', 'Microsoft Cognitive', 'AWS Comprehend',
    'Google Cloud AI', 'Azure OpenAI', 'Replicate Models', 'RunPod Serverless',
    'Together AI', 'Anyscale Endpoints', 'Fireworks AI', 'Groq LPU',
    'Perplexity AI', 'You.com', 'Phind CodeLlama', 'CodeT5+',
    'StarCoder', 'WizardCoder', 'Alpaca', 'Vicuna',
    'FastChat', 'Orca', 'MPT', 'Falcon',
    'RedPajama', 'OpenAssistant', 'Dolly', 'StableLM',
    'ChatGLM', 'Baichuan', 'Qwen', 'InternLM',
    'DALL-E Mini', 'Craiyon', 'Midjourney (Free)', 'Leonardo AI',
    'Playground AI', 'NightCafe', 'Artbreeder', 'Deep Dream',
    'RunwayML', 'Pika Labs', 'Synthesia (Free)', 'D-ID',
    'Speechify', 'Natural Reader', 'Balabolka', 'eSpeak',
    'Festival TTS', 'Flite', 'MaryTTS', 'Coqui TTS',
    'Whisper ASR', 'Wav2Vec', 'DeepSpeech', 'Vosk',
    'SpeechRecognition', 'Azure Speech', 'Google Speech', 'AWS Transcribe',
    'AssemblyAI', 'Rev.ai', 'Otter.ai', 'Descript',
    'Loom AI', 'Zoom AI', 'Teams AI', 'Meet AI',
    'Notion AI', 'Obsidian AI', 'Roam AI', 'LogSeq AI',
    'Grammarly', 'ProWritingAid', 'Hemingway', 'QuillBot',
    'Jasper AI', 'Copy.ai', 'Writesonic', 'Rytr',
    'ContentBot', 'Article Forge', 'WordAI', 'Spinner Chief',
    'Paraphraser', 'Rewriter', 'Summarizer', 'Translator',
    'Sentiment Analyzer', 'Topic Modeler', 'Entity Extractor', 'Keyword Extractor',
    'Text Classifier', 'Language Detector', 'Readability Scorer', 'Plagiarism Checker',
    'SEO Analyzer', 'Content Optimizer', 'Headline Generator', 'Meta Description',
    'Social Media Post', 'Email Subject', 'Product Description', 'Blog Post',
    'Press Release', 'White Paper', 'Case Study', 'Tutorial',
    'FAQ Generator', 'Chatbot Response', 'Customer Support', 'Sales Copy',
    'Landing Page', 'Ad Copy', 'Video Script', 'Podcast Script',
  ];
  
  additionalProviders.forEach((name, index) => {
    const baseIndex = index % MOCK_PROVIDERS.length;
    const baseProvider = MOCK_PROVIDERS[baseIndex];
    
    providers.push({
      ...baseProvider,
      id: `provider_${String(providers.length + 1).padStart(3, '0')}`,
      name,
      rateLimit: {
        requestsPerMinute: Math.floor(Math.random() * 50) + 5,
        requestsPerDay: Math.floor(Math.random() * 2000) + 100,
      },
      quality: ['basic', 'good', 'excellent'][Math.floor(Math.random() * 3)] as any,
      responseTime: ['fast', 'medium', 'slow'][Math.floor(Math.random() * 3)] as any,
    });
  });
  
  return providers;
};

// Reducer
const aiReducer = (state: AIState, action: AIAction): AIState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    
    case 'SET_PROVIDERS':
      return {
        ...state,
        providers: action.payload,
        activeProviders: action.payload.filter(p => p.isActive),
        loading: false,
        error: null,
      };
    
    case 'UPDATE_PROVIDER':
      const updatedProviders = state.providers.map(provider =>
        provider.id === action.payload.id
          ? { ...provider, ...action.payload.updates }
          : provider
      );
      return {
        ...state,
        providers: updatedProviders,
        activeProviders: updatedProviders.filter(p => p.isActive),
      };
    
    case 'ADD_REQUEST':
      return {
        ...state,
        requests: [action.payload, ...state.requests.slice(0, 99)], // Keep last 100 requests
      };
    
    case 'UPDATE_REQUEST':
      return {
        ...state,
        requests: state.requests.map(request =>
          request.id === action.payload.id
            ? { ...request, ...action.payload.updates }
            : request
        ),
      };
    
    case 'SET_QUOTA_USAGE':
      return { ...state, quotaUsage: action.payload };
    
    case 'UPDATE_QUOTA':
      return {
        ...state,
        quotaUsage: {
          ...state.quotaUsage,
          [action.payload.providerId]: {
            used: action.payload.used,
            limit: action.payload.limit,
          },
        },
      };
    
    default:
      return state;
  }
};

// Context
const AIContext = createContext<AIContextType | undefined>(undefined);

// Mock API functions
const mockAIApi = {
  getProviders: async (): Promise<AIProvider[]> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return generateProviders();
  },
  
  generateContent: async (providerId: string, prompt: string, options: any = {}): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 1000));
    
    // Simulate different types of responses
    const responses = [
      `Generated content for: "${prompt}"\n\nThis is a high-quality AI-generated response that demonstrates the capabilities of the ${providerId} provider.`,
      `AI Response: ${prompt}\n\nHere's a comprehensive answer that showcases advanced AI reasoning and creativity.`,
      `Content created successfully using ${providerId}:\n\n${prompt}\n\nThis response includes relevant details and maintains high quality standards.`,
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
  },
  
  aggregateResults: async (prompt: string, providers: string[], strategy: string): Promise<any> => {
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    return {
      strategy,
      prompt,
      providers,
      result: `Aggregated result using ${strategy} strategy from ${providers.length} providers for: "${prompt}"`,
      confidence: Math.random() * 0.3 + 0.7, // 70-100% confidence
      processingTime: Math.random() * 2000 + 1000,
    };
  },
};

// Provider Component
export const AIContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(aiReducer, initialState);

  // Load providers on mount
  useEffect(() => {
    loadProviders();
  }, []);

  // Provider management functions
  const loadProviders = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const providers = await mockAIApi.getProviders();
      dispatch({ type: 'SET_PROVIDERS', payload: providers });
      
      // Initialize quota usage
      const quotaUsage: Record<string, { used: number; limit: number }> = {};
      providers.forEach(provider => {
        quotaUsage[provider.id] = {
          used: Math.floor(Math.random() * provider.rateLimit.requestsPerDay * 0.3),
          limit: provider.rateLimit.requestsPerDay,
        };
      });
      dispatch({ type: 'SET_QUOTA_USAGE', payload: quotaUsage });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load AI providers' });
    }
  };

  const toggleProvider = async (providerId: string, isActive: boolean) => {
    try {
      dispatch({ type: 'UPDATE_PROVIDER', payload: { id: providerId, updates: { isActive } } });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to update provider' });
    }
  };

  const getProvidersByType = (type: string): AIProvider[] => {
    return state.activeProviders.filter(provider => provider.type === type);
  };

  const getBestProvider = (type: string, criteria: 'quality' | 'speed' | 'availability' = 'quality'): AIProvider | null => {
    const providers = getProvidersByType(type);
    if (providers.length === 0) return null;

    switch (criteria) {
      case 'quality':
        return providers.reduce((best, current) => {
          const qualityScore = { basic: 1, good: 2, excellent: 3, premium: 4 };
          return qualityScore[current.quality] > qualityScore[best.quality] ? current : best;
        });
      
      case 'speed':
        return providers.reduce((best, current) => {
          const speedScore = { slow: 1, medium: 2, fast: 3 };
          return speedScore[current.responseTime] > speedScore[best.responseTime] ? current : best;
        });
      
      case 'availability':
        return providers.reduce((best, current) => {
          const currentUsage = getQuotaUsage(current.id);
          const bestUsage = getQuotaUsage(best.id);
          return currentUsage.percentage < bestUsage.percentage ? current : best;
        });
      
      default:
        return providers[0];
    }
  };

  // Request management functions
  const generateContent = async (prompt: string, type: 'text' | 'image' | 'audio' | 'video', options: any = {}): Promise<string> => {
    const provider = getBestProvider(type, 'availability');
    if (!provider) {
      throw new Error(`No available providers for type: ${type}`);
    }

    return generateWithProvider(provider.id, prompt, options);
  };

  const generateWithProvider = async (providerId: string, prompt: string, options: any = {}): Promise<string> => {
    const provider = state.providers.find(p => p.id === providerId);
    if (!provider) {
      throw new Error(`Provider not found: ${providerId}`);
    }

    const request: AIRequest = {
      id: `request_${Date.now()}`,
      providerId,
      prompt,
      type: provider.type,
      parameters: options,
      status: 'pending',
      createdAt: new Date().toISOString(),
    };

    dispatch({ type: 'ADD_REQUEST', payload: request });

    try {
      dispatch({ type: 'UPDATE_REQUEST', payload: { id: request.id, updates: { status: 'processing' } } });
      
      const result = await mockAIApi.generateContent(providerId, prompt, options);
      
      dispatch({ type: 'UPDATE_REQUEST', payload: {
        id: request.id,
        updates: {
          status: 'completed',
          result,
          completedAt: new Date().toISOString(),
        },
      }});
      
      // Update quota usage
      const currentUsage = state.quotaUsage[providerId] || { used: 0, limit: provider.rateLimit.requestsPerDay };
      dispatch({ type: 'UPDATE_QUOTA', payload: {
        providerId,
        used: currentUsage.used + 1,
        limit: currentUsage.limit,
      }});
      
      return result;
    } catch (error) {
      dispatch({ type: 'UPDATE_REQUEST', payload: {
        id: request.id,
        updates: {
          status: 'failed',
          error: error instanceof Error ? error.message : 'Unknown error',
          completedAt: new Date().toISOString(),
        },
      }});
      
      throw error;
    }
  };

  const aggregateResults = async (prompt: string, type: string, strategy: 'consensus' | 'best' | 'fastest'): Promise<any> => {
    const providers = getProvidersByType(type).slice(0, 3); // Use top 3 providers
    if (providers.length === 0) {
      throw new Error(`No available providers for type: ${type}`);
    }

    const providerIds = providers.map(p => p.id);
    return mockAIApi.aggregateResults(prompt, providerIds, strategy);
  };

  // Utility functions
  const getQuotaUsage = (providerId: string): { used: number; limit: number; percentage: number } => {
    const usage = state.quotaUsage[providerId] || { used: 0, limit: 1000 };
    return {
      ...usage,
      percentage: (usage.used / usage.limit) * 100,
    };
  };

  const isProviderAvailable = (providerId: string): boolean => {
    const provider = state.providers.find(p => p.id === providerId);
    if (!provider || !provider.isActive) return false;
    
    const usage = getQuotaUsage(providerId);
    return usage.percentage < 95; // Consider unavailable if >95% quota used
  };

  const getRequestHistory = (): AIRequest[] => {
    return state.requests;
  };

  const contextValue: AIContextType = {
    state,
    loadProviders,
    toggleProvider,
    getProvidersByType,
    getBestProvider,
    generateContent,
    generateWithProvider,
    aggregateResults,
    getQuotaUsage,
    isProviderAvailable,
    getRequestHistory,
  };

  return (
    <AIContext.Provider value={contextValue}>
      {children}
    </AIContext.Provider>
  );
};

// Hook to use AI context
export const useAI = (): AIContextType => {
  const context = useContext(AIContext);
  
  if (context === undefined) {
    throw new Error('useAI must be used within an AIProvider');
  }
  
  return context;
};

// Export types
export type { AIProvider, AIRequest, AIState, AIContextType };