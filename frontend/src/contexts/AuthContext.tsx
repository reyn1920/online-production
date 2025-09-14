import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
// import { toast } from 'react-hot-toast';
// import Cookies from 'js-cookie';
// import { apiClient } from '../services/apiClient';

// Temporary mock implementations until dependencies are installed
const toast = {
  success: (message: string) => console.log('Success:', message),
  error: (message: string) => console.error('Error:', message),
};

const Cookies = {
  get: (key: string) => localStorage.getItem(key),
  set: (key: string, value: string, options?: any) => localStorage.setItem(key, value),
  remove: (key: string) => localStorage.removeItem(key),
};

const apiClient = {
  get: async (url: string) => ({ data: {} }),
  post: async <T = any>(url: string, data?: any) => ({ 
    data: {
      access_token: process.env.REACT_APP_MOCK_ACCESS_TOKEN || 'dev_token',
      refresh_token: process.env.REACT_APP_MOCK_REFRESH_TOKEN || 'dev_refresh_token',
      user_info: {
        user_id: process.env.REACT_APP_MOCK_USER_ID || 'dev_user_id',
        username: process.env.REACT_APP_MOCK_USERNAME || 'dev_user',
        roles: ['user'],
        channel_access: ['channel_001', 'channel_002', 'channel_003', 'channel_004']
      },
      expires_in: 3600
    } as T
  }),
  setAuthToken: (token: string) => {},
  clearAuthToken: () => {},
  setupAuthInterceptor: (refresh: () => Promise<void>, logout: () => Promise<void>) => () => {},
};

// Types
interface User {
  user_id: string;
  username: string;
  roles: string[];
  channel_access?: string[];
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  accessToken: string | null;
  refreshToken: string | null;
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user_info: User;
  expires_in: number;
}

// Action Types
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: LoginResponse }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'REFRESH_TOKEN_SUCCESS'; payload: { access_token: string; expires_in: number } }
  | { type: 'REFRESH_TOKEN_FAILURE' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'CLEAR_ERROR' };

// Initial State
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  accessToken: null,
  refreshToken: null,
};

// Reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user_info,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        accessToken: action.payload.access_token,
        refreshToken: action.payload.refresh_token,
      };
    
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
        accessToken: null,
        refreshToken: null,
      };
    
    case 'LOGOUT':
      return {
        ...initialState,
        isLoading: false,
      };
    
    case 'REFRESH_TOKEN_SUCCESS':
      return {
        ...state,
        accessToken: action.payload.access_token,
        error: null,
      };
    
    case 'REFRESH_TOKEN_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        accessToken: null,
        refreshToken: null,
        error: 'Session expired. Please login again.',
      };
    
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    
    default:
      return state;
  }
};

// Context
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  accessToken: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuthToken: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider Props
interface AuthProviderProps {
  children: ReactNode;
}

// Token Storage Keys
const ACCESS_TOKEN_KEY = 'trae_access_token';
const REFRESH_TOKEN_KEY = 'trae_refresh_token';
const USER_KEY = 'trae_user';

// Provider Component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state from stored tokens
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedAccessToken = Cookies.get(ACCESS_TOKEN_KEY);
        const storedRefreshToken = Cookies.get(REFRESH_TOKEN_KEY);
        const storedUser = localStorage.getItem(USER_KEY);

        if (storedAccessToken && storedRefreshToken && storedUser) {
          const user = JSON.parse(storedUser);
          
          // Set tokens in API client
          apiClient.setAuthToken(storedAccessToken);
          
          // Verify token is still valid by making a test request
          try {
            await apiClient.get('/health');
            
            dispatch({
              type: 'LOGIN_SUCCESS',
              payload: {
                access_token: storedAccessToken,
                refresh_token: storedRefreshToken,
                user_info: user,
                expires_in: 3600, // Default expiry
              },
            });
          } catch (error) {
            // Token might be expired, try to refresh
            await refreshTokens();
          }
        } else {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = async (credentials: LoginCredentials): Promise<void> => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
      const { access_token, refresh_token, user_info, expires_in } = response.data;
      
      // Store tokens and user info
      Cookies.set(ACCESS_TOKEN_KEY, access_token, { 
        expires: expires_in / (24 * 60 * 60), // Convert seconds to days
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict'
      });
      Cookies.set(REFRESH_TOKEN_KEY, refresh_token, { 
        expires: 7, // 7 days
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict'
      });
      localStorage.setItem(USER_KEY, JSON.stringify(user_info));
      
      // Set auth token in API client
      apiClient.setAuthToken(access_token);
      
      dispatch({ type: 'LOGIN_SUCCESS', payload: response.data });
      toast.success(`Welcome back, ${user_info.username}!`);
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Login failed. Please try again.';
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMessage });
      toast.error(errorMessage);
      throw error;
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      // Call logout endpoint
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Clear stored data regardless of API call success
      Cookies.remove(ACCESS_TOKEN_KEY);
      Cookies.remove(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      
      // Clear auth token from API client
      apiClient.clearAuthToken();
      
      dispatch({ type: 'LOGOUT' });
      toast.success('Logged out successfully');
    }
  };

  // Refresh token function
  const refreshTokens = async (): Promise<void> => {
    try {
      const storedRefreshToken = Cookies.get(REFRESH_TOKEN_KEY);
      
      if (!storedRefreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await apiClient.post('/auth/refresh', {
        refresh_token: storedRefreshToken,
      });
      
      const { access_token, expires_in } = response.data;
      
      // Update stored access token
      Cookies.set(ACCESS_TOKEN_KEY, access_token, { 
        expires: expires_in / (24 * 60 * 60),
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict'
      });
      
      // Update auth token in API client
      apiClient.setAuthToken(access_token);
      
      dispatch({ 
        type: 'REFRESH_TOKEN_SUCCESS', 
        payload: { access_token, expires_in } 
      });
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      dispatch({ type: 'REFRESH_TOKEN_FAILURE' });
      
      // Clear all stored data
      Cookies.remove(ACCESS_TOKEN_KEY);
      Cookies.remove(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      apiClient.clearAuthToken();
      
      toast.error('Session expired. Please login again.');
    }
  };

  // Clear error function
  const clearError = (): void => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  // Setup automatic token refresh
  useEffect(() => {
    if (!state.accessToken) return;

    // Set up automatic token refresh 5 minutes before expiry
    const refreshInterval = setInterval(() => {
      refreshTokens();
    }, 55 * 60 * 1000); // 55 minutes

    return () => clearInterval(refreshInterval);
  }, [state.accessToken]);

  // Setup API client interceptor for automatic token refresh on 401
  useEffect(() => {
    const cleanup = apiClient.setupAuthInterceptor(refreshTokens, logout);
    
    return () => {
      // Cleanup interceptor if needed
      if (cleanup && typeof cleanup === 'function') {
        cleanup();
      }
    };
  }, []);

  const contextValue: AuthContextType = {
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    loading: state.isLoading,
    error: state.error,
    accessToken: state.accessToken,
    login,
    logout,
    refreshAuthToken: refreshTokens,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

// Export types
export type { User, LoginCredentials, AuthState };