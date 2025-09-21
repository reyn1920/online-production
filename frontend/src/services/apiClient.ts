import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { toast } from 'react-hot-toast';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds

// Request/Response Types
interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  error?: string;
}

interface ApiError {
  message: string;
  status: number;
  code?: string;
}

// API Client Class
class ApiClient {
  private instance: AxiosInstance;
  private authToken: string | null = null;
  private refreshTokenCallback: (() => Promise<void>) | null = null;
  private logoutCallback: (() => Promise<void>) | null = null;

  constructor() {
    this.instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        // Add auth token if available
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }

        // Add request timestamp
        config.metadata = { startTime: new Date() };

        return config;
      },
      (error) => {
        return Promise.reject(this.handleError(error));
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response) => {
        // Log response time in development
        if (import.meta.env.DEV && response.config.metadata) {
          const duration = new Date().getTime() - response.config.metadata.startTime.getTime();
          console.log(`API ${response.config.method?.toUpperCase()} ${response.config.url}: ${duration}ms`);
        }

        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Try to refresh token
            if (this.refreshTokenCallback) {
              await this.refreshTokenCallback();
              // Retry original request with new token
              return this.instance(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, logout user
            if (this.logoutCallback) {
              await this.logoutCallback();
            }
            return Promise.reject(this.handleError(error));
          }
        }

        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: AxiosError): ApiError {
    let apiError: ApiError;

    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      apiError = {
        message: (data as any)?.error || (data as any)?.message || 'An error occurred',
        status,
        code: (data as any)?.code,
      };
    } else if (error.request) {
      // Request made but no response received
      apiError = {
        message: 'Network error. Please check your connection.',
        status: 0,
        code: 'NETWORK_ERROR',
      };
    } else {
      // Something else happened
      apiError = {
        message: error.message || 'An unexpected error occurred',
        status: 0,
        code: 'UNKNOWN_ERROR',
      };
    }

    // Show error toast for non-auth errors
    if (apiError.status !== 401 && apiError.status !== 403) {
      toast.error(apiError.message);
    }

    return apiError;
  }

  // Auth token management
  setAuthToken(token: string): void {
    this.authToken = token;
  }

  clearAuthToken(): void {
    this.authToken = null;
  }

  getAuthToken(): string | null {
    return this.authToken;
  }

  // Setup auth interceptor callbacks
  setupAuthInterceptor(
    refreshTokenCallback: () => Promise<void>,
    logoutCallback: () => Promise<void>
  ): void {
    this.refreshTokenCallback = refreshTokenCallback;
    this.logoutCallback = logoutCallback;
  }

  // HTTP Methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.get<T>(url, config);
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.post<T>(url, data, config);
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.put<T>(url, data, config);
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.patch<T>(url, data, config);
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.delete<T>(url, config);
  }

  // File upload
  async uploadFile<T = any>(
    url: string,
    file: File,
    onUploadProgress?: (progressEvent: any) => void,
    additionalData?: Record<string, any>
  ): Promise<AxiosResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    // Add additional data if provided
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    return this.instance.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
  }

  // Download file
  async downloadFile(
    url: string,
    filename?: string,
    onDownloadProgress?: (progressEvent: any) => void
  ): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob',
      onDownloadProgress,
    });

    // Create download link
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.get('/health');
      return true;
    } catch (error) {
      return false;
    }
  }

  // Get API base URL
  getBaseURL(): string {
    return API_BASE_URL;
  }

  // Update base URL (useful for environment switching)
  updateBaseURL(newBaseURL: string): void {
    this.instance.defaults.baseURL = newBaseURL;
  }

  // Get instance for advanced usage
  getInstance(): AxiosInstance {
    return this.instance;
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Export types
export type { ApiResponse, ApiError };
export { ApiClient };

// Utility functions
export const createApiClient = (baseURL?: string): ApiClient => {
  const client = new ApiClient();
  if (baseURL) {
    client.updateBaseURL(baseURL);
  }
  return client;
};

// Request helpers
export const withAuth = (token: string) => ({
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

export const withContentType = (contentType: string) => ({
  headers: {
    'Content-Type': contentType,
  },
});

// Error handling utilities
export const isApiError = (error: any): error is ApiError => {
  return error && typeof error.message === 'string' && typeof error.status === 'number';
};

export const getErrorMessage = (error: any): string => {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};
