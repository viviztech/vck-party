/**
 * Typed Redux Hooks
 * Type-safe hooks for Redux store access
 */

import { TypedUseSelectorHook, useDispatch, useSelector, useStore } from 'react-redux';
import type { RootState } from './types';
import type { ThunkDispatch } from '@reduxjs/toolkit';
import type { UnknownAction } from 'redux';

// =============================================================================
// Typed Hooks
// =============================================================================

/**
 * Typed useDispatch hook
 * Use throughout your app instead of plain useDispatch
 */
export const useAppDispatch = useDispatch as () => ThunkDispatch<RootState, unknown, UnknownAction>;

/**
 * Typed useSelector hook
 * Use throughout your app instead of plain useSelector
 */
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

/**
 * Typed useStore hook
 * Use throughout your app instead of plain useStore
 */
export const useAppStore = useStore;

// =============================================================================
// Auth Hooks
// =============================================================================

/**
 * Hook to access auth state
 */
export const useAuth = () => {
  const user = useAppSelector((state) => state.auth.user);
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const loading = useAppSelector((state) => state.auth.loading);
  const error = useAppSelector((state) => state.auth.error);

  return {
    user,
    isAuthenticated,
    loading,
    error,
  };
};

/**
 * Hook to check if user has specific role
 */
export const useHasRole = (roleName: string): boolean => {
  const user = useAppSelector((state) => state.auth.user);
  return user?.roles?.some((role) => role.name === roleName) ?? false;
};

/**
 * Hook to check if user has specific permission
 */
export const useHasPermission = (resource: string, action: string): boolean => {
  const user = useAppSelector((state) => state.auth.user);
  const permissions = user?.roles?.flatMap((role) => role.permissions) ?? [];
  return permissions.some((perm) => perm.resource === resource && perm.action === action);
};

/**
 * Hook to get user role names
 */
export const useUserRoles = (): string[] => {
  const user = useAppSelector((state) => state.auth.user);
  return user?.roles?.map((role) => role.name) ?? [];
};

// =============================================================================
// UI Hooks
// =============================================================================

/**
 * Hook to access UI state
 */
export const useUI = () => {
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);
  const theme = useAppSelector((state) => state.ui.theme);
  const toasts = useAppSelector((state) => state.ui.toasts);
  const modals = useAppSelector((state) => state.ui.modals);
  const globalLoading = useAppSelector((state) => state.ui.loading.global);

  return {
    sidebarOpen,
    theme,
    toasts,
    modals,
    globalLoading,
  };
};

/**
 * Hook to manage theme
 */
export const useTheme = () => {
  const theme = useAppSelector((state) => state.ui.theme);
  const dispatch = useAppDispatch();

  const setTheme = (newTheme: 'light' | 'dark' | 'system') => {
    dispatch({ type: 'ui/setTheme', payload: newTheme });
  };

  return { theme, setTheme };
};

/**
 * Hook to manage toasts
 */
export const useToasts = () => {
  const toasts = useAppSelector((state) => state.ui.toasts);
  const dispatch = useAppDispatch();

  const showToast = (toast: Omit<import('./types').Toast, 'id'>) => {
    dispatch({ type: 'ui/addToast', payload: toast });
  };

  const hideToast = (id: string) => {
    dispatch({ type: 'ui/removeToast', payload: id });
  };

  const clearToasts = () => {
    dispatch({ type: 'ui/clearToasts' });
  };

  return { toasts, showToast, hideToast, clearToasts };
};

/**
 * Hook to manage sidebar
 */
export const useSidebar = () => {
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);
  const dispatch = useAppDispatch();

  const toggleSidebar = () => {
    dispatch({ type: 'ui/toggleSidebar' });
  };

  const setSidebarOpen = (open: boolean) => {
    dispatch({ type: 'ui/setSidebarOpen', payload: open });
  };

  return { sidebarOpen, toggleSidebar, setSidebarOpen };
};
