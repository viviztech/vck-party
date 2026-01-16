/**
 * Authentication Service
 * API endpoints for user authentication and profile management
 */

import { api, ApiResponse, AuthTokens, User, ApiError } from './api';

// ============================================================================
// Types
// ============================================================================

export interface LoginRequest {
  email: string;
  password: string;
  device_info?: Record<string, unknown>;
}

export interface PhoneLoginRequest {
  phone: string;
  device_info?: Record<string, unknown>;
}

export interface RegisterRequest {
  email: string;
  phone: string;
  password: string;
  confirm_password: string;
}

export interface UserUpdateRequest {
  email?: string;
  phone?: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
  confirm_new_password: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
  confirm_new_password: string;
}

export interface OTPRequest {
  phone: string;
  purpose: 'login' | 'registration' | 'reset';
}

export interface OTPVerifyRequest {
  phone: string;
  otp: string;
  device_info?: Record<string, unknown>;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  data?: AuthTokens & { user: User };
}

// ============================================================================
// Auth Service
// ============================================================================

export const authService = {
  /**
   * Login with email and password
   */
  async login(data: LoginRequest): Promise<AuthTokens & { user: User }> {
    const response = await api.post<AuthResponse>('/auth/login', data);
    
    if (response.success && response.data) {
      api.setTokens(response.data);
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Login failed',
      status: 400,
    });
  },

  /**
   * Login with phone number (OTP-based)
   */
  async loginWithPhone(data: PhoneLoginRequest): Promise<{ success: boolean; message: string }> {
    return api.post('/auth/login/phone', data);
  },

  /**
   * Verify OTP for phone login
   */
  async verifyOTP(data: OTPVerifyRequest): Promise<AuthTokens & { user: User }> {
    const response = await api.post<AuthResponse>('/auth/verify-otp', data);
    
    if (response.success && response.data) {
      api.setTokens(response.data);
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'OTP verification failed',
      status: 400,
    });
  },

  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<AuthTokens & { user: User }> {
    const response = await api.post<AuthResponse>('/auth/register', data);
    
    if (response.success && response.data) {
      api.setTokens(response.data);
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Registration failed',
      status: 400,
    });
  },

  /**
   * Send OTP for phone verification
   */
  async sendOTP(data: OTPRequest): Promise<{ success: boolean; expires_in: number }> {
    return api.post('/auth/send-otp', data);
  },

  /**
   * Logout user
   */
  async logout(refresh_token?: string): Promise<void> {
    try {
      await api.post('/auth/logout', { refresh_token });
    } finally {
      api.clearTokens();
    }
  },

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<AuthTokens> {
    const refresh_token = api.getRefreshToken();
    
    if (!refresh_token) {
      throw new ApiError({
        message: 'No refresh token available',
        status: 401,
      });
    }

    const response = await api.post<AuthResponse>('/auth/refresh', { refresh_token });
    
    if (response.success && response.data) {
      api.setTokens(response.data);
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Token refresh failed',
      status: 400,
    });
  },

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<ApiResponse<User>>('/auth/me');
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Failed to get user',
      status: 400,
    });
  },

  /**
   * Update user profile
   */
  async updateProfile(data: UserUpdateRequest): Promise<User> {
    const response = await api.patch<ApiResponse<User>>('/auth/me', data);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new ApiError({
      message: response.message || 'Profile update failed',
      status: 400,
    });
  },

  /**
   * Change password
   */
  async changePassword(data: PasswordChangeRequest): Promise<{ success: boolean; message: string }> {
    return api.post('/auth/change-password', data);
  },

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<{ success: boolean; message: string }> {
    return api.post('/auth/password-reset/request', { email });
  },

  /**
   * Reset password with token
   */
  async resetPassword(data: PasswordResetConfirmRequest): Promise<{ success: boolean; message: string }> {
    return api.post('/auth/password-reset/confirm', data);
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!api.getAccessToken();
  },

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return api.getAccessToken();
  },
};

export default authService;
