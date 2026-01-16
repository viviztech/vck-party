/**
 * Redux Store Types
 * TypeScript types for Redux store and slices
 */

// =============================================================================
// Auth Types (matching backend schemas)
// =============================================================================

export interface Permission {
  id: string; // UUID as string
  name: string;
  description?: string;
  resource: string;
  action: string;
  created_at: string;
}

export interface Role {
  id: string; // UUID as string
  name: string;
  description?: string;
  is_active: boolean;
  is_system: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
  permissions: Permission[];
}

export interface User {
  id: string; // UUID as string
  email?: string;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  status: string;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
  roles: Role[];
}

export interface DeviceInfo {
  device_id?: string;
  device_type?: string;
  app_version?: string;
  os_version?: string;
  browser?: string;
}

// =============================================================================
// Auth API Types
// =============================================================================

export interface LoginRequest {
  email: string;
  password: string;
  device_info?: DeviceInfo;
}

export interface RegisterRequest {
  email: string;
  phone: string;
  password: string;
  confirm_password: string;
  device_info?: DeviceInfo;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// =============================================================================
// Auth State
// =============================================================================

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: string | null;
}

// =============================================================================
// UI State
// =============================================================================

export type Theme = 'light' | 'dark' | 'system';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export interface Modal {
  id: string;
  component: string;
  props?: Record<string, unknown>;
}

export interface UIState {
  sidebarOpen: boolean;
  theme: Theme;
  toasts: Toast[];
  modals: Modal[];
  loading: {
    global: boolean;
    [key: string]: boolean;
  };
}

// =============================================================================
// Root State
// =============================================================================

export interface RootState {
  auth: AuthState;
  ui: UIState;
}

// =============================================================================
// App Dispatch
// =============================================================================

export type AppDispatch = unknown; // Will be typed after store creation
