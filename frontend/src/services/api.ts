/**
 * Base API Configuration
 * Axios instance with interceptors for authentication and error handling
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// Environment variables
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const TOKEN_KEY = import.meta.env.VITE_TOKEN_KEY || 'vck_auth_token';
const REFRESH_TOKEN_KEY = import.meta.env.VITE_REFRESH_TOKEN_KEY || 'vck_refresh_token';

// ============================================================================
// Types
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}

export interface ErrorResponse {
  success: boolean;
  error: {
    code?: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  status: string;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
  roles: Role[];
}

export interface Role {
  id: string;
  name: string;
  description?: string;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  description?: string;
  resource: string;
  action: string;
}

// ============================================================================
// API Client
// ============================================================================

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: Error) => void;
  }> = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getAccessToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add request ID for tracing
        config.headers['X-Request-ID'] = crypto.randomUUID();
        
        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ErrorResponse>) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized - token refresh
        if (error.response?.status === 401 && originalRequest) {
          return this.handle401Error(originalRequest);
        }

        // Handle other errors
        return Promise.reject(this.parseError(error));
      }
    );
  }

  /**
   * Handle 401 error with token refresh logic
   */
  private async handle401Error(
    originalRequest: InternalAxiosRequestConfig
  ): Promise<any> {
    // Prevent multiple refresh attempts
    if (this.isRefreshing) {
      return new Promise((resolve, reject) => {
        this.failedQueue.push({
          resolve: (token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(this.client(originalRequest));
          },
          reject: (error: Error) => {
            reject(error);
          },
        });
      });
    }

    this.isRefreshing = true;

    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      // Refresh the token
      const response = await this.refreshTokenRequest(refreshToken);
      const { access_token, refresh_token, expires_in } = response.data;

      // Store new tokens
      this.setTokens({ access_token, refresh_token, token_type: 'Bearer', expires_in });

      // Retry original request
      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      
      // Process queued requests
      this.processQueue(null, access_token);

      return this.client(originalRequest);
    } catch (error) {
      // Clear tokens and redirect to login
      this.clearTokens();
      this.processQueue(error as Error, '');

      // Dispatch logout event
      window.dispatchEvent(new CustomEvent('vck:logout'));

      return Promise.reject(error);
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * Process queued requests after token refresh
   */
  private processQueue(error: Error | null, token: string): void {
    this.failedQueue.forEach((promise) => {
      if (error) {
        promise.reject(error);
      } else {
        promise.resolve(token);
      }
    });
    this.failedQueue = [];
  }

  /**
   * Parse error response
   */
  private parseError(error: AxiosError<ErrorResponse>): ApiError {
    const message =
      error.response?.data?.error?.message ||
      error.message ||
      'An unexpected error occurred';

    const code = error.response?.data?.error?.code;
    const details = error.response?.data?.error?.details;
    const status = error.response?.status || 500;

    return new ApiError({
      message,
      code,
      details,
      status,
    });
  }

  /**
   * Refresh token request
   */
  private async refreshTokenRequest(
    refreshToken: string
  ): Promise<{ data: AuthTokens }> {
    return axios.post(`${API_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
  }

  // =========================================================================
  // Token Management
  // =========================================================================

  /**
   * Get access token from storage
   */
  getAccessToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  /**
   * Get refresh token from storage
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  /**
   * Set tokens in storage
   */
  setTokens(tokens: AuthTokens): void {
    localStorage.setItem(TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }

  /**
   * Clear tokens from storage
   */
  clearTokens(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  // =========================================================================
  // HTTP Methods
  // =========================================================================

  /**
   * GET request
   */
  async get<T>(url: string, params?: Record<string, any>): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  /**
   * POST request
   */
  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  /**
   * PUT request
   */
  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data);
    return response.data;
  }

  /**
   * PATCH request
   */
  async patch<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.patch<T>(url, data);
    return response.data;
  }

  /**
   * DELETE request
   */
  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }

  /**
   * Upload file
   */
  async uploadFile<T>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  }
}

// ============================================================================
// Custom Error Class
// ============================================================================

export class ApiError extends Error {
  code?: string;
  details?: Record<string, string[]>;
  status: number;
  isAxiosError: boolean;

  constructor(options: {
    message: string;
    code?: string;
    details?: Record<string, string[]>;
    status?: number;
  }) {
    super(options.message);
    this.name = 'ApiError';
    this.code = options.code;
    this.details = options.details;
    this.status = options.status || 500;
    this.isAxiosError = false;
  }
}

// ============================================================================
// Export singleton instance
// ============================================================================

export const api = new ApiClient();

// Export for testing
export { ApiClient };
