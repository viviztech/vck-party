/**
 * UI Slice
 * Redux slice for managing UI state
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { UIState, Theme, Toast, Modal } from './types';

// =============================================================================
// Initial State
// =============================================================================

const initialState: UIState = {
  sidebarOpen: true,
  theme: 'system',
  toasts: [],
  modals: [],
  loading: {
    global: false,
  },
};

// =============================================================================
// Slice
// =============================================================================

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Sidebar
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },

    // Theme
    setTheme: (state, action: PayloadAction<Theme>) => {
      state.theme = action.payload;
      // Persist theme preference
      localStorage.setItem('theme', action.payload);
    },
    loadTheme: (state) => {
      const savedTheme = localStorage.getItem('theme') as Theme;
      if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
        state.theme = savedTheme;
      }
    },

    // Toasts
    addToast: (state, action: PayloadAction<Omit<Toast, 'id'>>) => {
      const id = crypto.randomUUID();
      state.toasts.push({
        ...action.payload,
        id,
        duration: action.payload.duration ?? 5000,
      });
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter((toast) => toast.id !== action.payload);
    },
    clearToasts: (state) => {
      state.toasts = [];
    },

    // Modals
    openModal: (state, action: PayloadAction<Omit<Modal, 'id'>>) => {
      const id = crypto.randomUUID();
      state.modals.push({ ...action.payload, id });
    },
    closeModal: (state, action: PayloadAction<string>) => {
      state.modals = state.modals.filter((modal) => modal.id !== action.payload);
    },
    closeAllModals: (state) => {
      state.modals = [];
    },

    // Global Loading
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.global = action.payload;
    },
    setLoading: (state, action: PayloadAction<{ key: string; loading: boolean }>) => {
      state.loading[action.payload.key] = action.payload.loading;
    },
    clearAllLoading: (state) => {
      state.loading = { global: false };
    },
  },
});

// =============================================================================
// Actions
// =============================================================================

export const {
  toggleSidebar,
  setSidebarOpen,
  setTheme,
  loadTheme,
  addToast,
  removeToast,
  clearToasts,
  openModal,
  closeModal,
  closeAllModals,
  setGlobalLoading,
  setLoading,
  clearAllLoading,
} = uiSlice.actions;

// =============================================================================
// Selectors
// =============================================================================

export const selectSidebarOpen = (state: { ui: UIState }) => state.ui.sidebarOpen;
export const selectTheme = (state: { ui: UIState }) => state.ui.theme;
export const selectToasts = (state: { ui: UIState }) => state.ui.toasts;
export const selectModals = (state: { ui: UIState }) => state.ui.modals;
export const selectGlobalLoading = (state: { ui: UIState }) => state.ui.loading.global;

// =============================================================================
// Reducer
// =============================================================================

export default uiSlice.reducer;
