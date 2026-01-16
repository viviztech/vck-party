/**
 * Redux Store Configuration
 * Main store setup with reducers and hot module replacement
 */

import { configureStore, combineReducers } from '@reduxjs/toolkit';

// Import reducers
import authReducer from './authSlice';
import uiReducer from './uiSlice';
import type { RootState } from './types';

// =============================================================================
// Reducers Map
// =============================================================================

export const rootReducers = {
  auth: authReducer,
  ui: uiReducer,
};

// =============================================================================
// Root Reducer
// =============================================================================

const rootReducer = combineReducers(rootReducers);

// =============================================================================
// Store Factory
// =============================================================================

/**
 * Create the store with optional preloaded state
 * Used for both production and testing
 */
export const createStore = () => {
  return configureStore({
    reducer: rootReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          // Ignore these action types for serializable check
          ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
        },
      }),
    devTools: import.meta.env.DEV,
  });
};

// =============================================================================
// Create Store Instance
// =============================================================================

export const store = createStore();

// =============================================================================
// Type Exports for Hooks
// =============================================================================

// Re-export for typed hooks
export type { RootState };

// =============================================================================
// Default Export
// =============================================================================

export default store;
