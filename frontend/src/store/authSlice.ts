/**
 * Authentication Slice
 * Redux slice for managing authentication state
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { AuthState, User, LoginRequest, RegisterRequest, TokenResponse } from './types';

// API base URL - should be from environment
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

// =============================================================================
// Async Thunks
// =============================================================================

/**
 * Login user with email and password
 */
export const login = createAsyncThunk<
  TokenResponse,
  LoginRequest,
  { rejectValue: string }
>(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (!response.ok) {
        return rejectWithValue(data.detail || 'Login failed');
      }

      // Store tokens in localStorage
      if (data.access_token) {
        localStorage.setItem('accessToken', data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem('refreshToken', data.refresh_token);
      }

      return data;
    } catch {
      return rejectWithValue('Network error occurred');
    }
  }
);

/**
 * Register new user
 */
export const register = createAsyncThunk<
  TokenResponse,
  RegisterRequest,
  { rejectValue: string }
>(
  'auth/register',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (!response.ok) {
        return rejectWithValue(data.detail || 'Registration failed');
      }

      // Store tokens in localStorage
      if (data.access_token) {
        localStorage.setItem('accessToken', data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem('refreshToken', data.refresh_token);
      }

      return data;
    } catch {
      return rejectWithValue('Network error occurred');
    }
  }
);

/**
 * Logout user
 */
export const logout = createAsyncThunk<void, void, { rejectValue: string }>(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (refreshToken) {
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed, continuing with local logout');
    } finally {
      // Clear local storage regardless of API result
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }
);

/**
 * Refresh access token
 */
export const refreshToken = createAsyncThunk<
  { access_token: string; refresh_token: string },
  void,
  { rejectValue: string }
>(
  'auth/refreshToken',
  async (_, { rejectWithValue }) => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (!refreshToken) {
        return rejectWithValue('No refresh token available');
      }

      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      const data = await response.json();

      if (!response.ok) {
        return rejectWithValue(data.detail || 'Token refresh failed');
      }

      // Update stored tokens
      if (data.access_token) {
        localStorage.setItem('accessToken', data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem('refreshToken', data.refresh_token);
      }

      return {
        access_token: data.access_token,
        refresh_token: data.refresh_token || refreshToken,
      };
    } catch {
      return rejectWithValue('Network error occurred');
    }
  }
);

/**
 * Update user profile
 */
export const updateProfile = createAsyncThunk<
  User,
  Partial<User>,
  { rejectValue: string }
>(
  'auth/updateProfile',
  async (userData, { rejectWithValue }) => {
    try {
      const accessToken = localStorage.getItem('accessToken');
      
      const response = await fetch(`${API_URL}/auth/profile`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (!response.ok) {
        return rejectWithValue(data.detail || 'Profile update failed');
      }

      return data;
    } catch {
      return rejectWithValue('Network error occurred');
    }
  }
);

/**
 * Initialize auth from stored tokens
 */
export const initializeAuth = createAsyncThunk<
  { user: User; token: string },
  void,
  { rejectValue: string }
>(
  'auth/initialize',
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('accessToken');
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (!token || !refreshToken) {
        return rejectWithValue('No tokens found');
      }

      // Validate token by fetching user profile
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        // Try to refresh token
        const refreshResponse = await fetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!refreshResponse.ok) {
          return rejectWithValue('Session expired');
        }

        const refreshData = await refreshResponse.json();
        
        if (refreshData.access_token) {
          localStorage.setItem('accessToken', refreshData.access_token);
        }
        if (refreshData.refresh_token) {
          localStorage.setItem('refreshToken', refreshData.refresh_token);
        }

        // Fetch user profile with new token
        const userResponse = await fetch(`${API_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${refreshData.access_token}`,
          },
        });

        if (!userResponse.ok) {
          return rejectWithValue('Failed to fetch user data');
        }

        const userData = await userResponse.json();
        return {
          user: userData,
          token: refreshData.access_token,
        };
      }

      const userData = await response.json();
      return {
        user: userData,
        token,
      };
    } catch {
      return rejectWithValue('Failed to initialize auth');
    }
  }
);

// =============================================================================
// Initial State
// =============================================================================

const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  loading: 'idle',
  error: null,
};

// =============================================================================
// Slice
// =============================================================================

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setCredentials: (state, action: PayloadAction<{ user: User; token: string; refreshToken: string }>) => {
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
      state.isAuthenticated = true;
      state.loading = 'succeeded';
      state.error = null;
    },
    setLoading: (state, action: PayloadAction<AuthState['loading']>) => {
      state.loading = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(login.pending, (state) => {
        state.loading = 'pending';
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.isAuthenticated = true;
        state.loading = 'succeeded';
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload || 'Login failed';
      });

    // Register
    builder
      .addCase(register.pending, (state) => {
        state.loading = 'pending';
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.isAuthenticated = true;
        state.loading = 'succeeded';
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload || 'Registration failed';
      });

    // Logout
    builder.addCase(logout.fulfilled, (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.loading = 'idle';
      state.error = null;
    });

    // Refresh Token
    builder
      .addCase(refreshToken.pending, (state) => {
        state.loading = 'pending';
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.token = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.loading = 'succeeded';
      })
      .addCase(refreshToken.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload || 'Token refresh failed';
        // Force logout on refresh failure
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
      });

    // Update Profile
    builder
      .addCase(updateProfile.pending, (state) => {
        state.loading = 'pending';
      })
      .addCase(updateProfile.fulfilled, (state, action) => {
        state.user = action.payload;
        state.loading = 'succeeded';
      })
      .addCase(updateProfile.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload || 'Profile update failed';
      });

    // Initialize Auth
    builder
      .addCase(initializeAuth.pending, (state) => {
        state.loading = 'pending';
      })
      .addCase(initializeAuth.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.refreshToken = localStorage.getItem('refreshToken');
        state.isAuthenticated = true;
        state.loading = 'succeeded';
        state.error = null;
      })
      .addCase(initializeAuth.rejected, (state, action) => {
        state.loading = 'idle';
        state.error = action.payload || null;
        state.isAuthenticated = false;
      });
  },
});

// =============================================================================
// Actions
// =============================================================================

export const { clearError, setCredentials, setLoading } = authSlice.actions;

// =============================================================================
// Selectors
// =============================================================================

export const selectUser = (state: { auth: AuthState }) => state.auth.user;
export const selectToken = (state: { auth: AuthState }) => state.auth.token;
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated;
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.loading;
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error;
export const selectUserRoles = (state: { auth: AuthState }) => state.auth.user?.roles || [];
export const selectUserPermissions = (state: { auth: AuthState }) => 
  state.auth.user?.roles?.flatMap(role => role.permissions) || [];

// =============================================================================
// Reducer
// =============================================================================

export default authSlice.reducer;
