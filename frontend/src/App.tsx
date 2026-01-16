/**
 * App Component
 * Main application component with routing configuration
 */

import React, { Suspense, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import type { RouteObject } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { initializeAuth, selectIsAuthenticated, selectAuthLoading } from '@/store/authSlice';
import { Spinner } from '@/components/Feedback/Spinner';

// Import routes from configuration
import { routes } from './routes';

// =============================================================================
// Loading Fallback Component
// =============================================================================

const LoadingFallback: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Suspense fallback={
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Spinner size="lg" />
    </div>
  }>
    {children}
  </Suspense>
);

// =============================================================================
// Root Route Loader
// =============================================================================

const RootLoader: React.FC = () => {
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const loading = useAppSelector(selectAuthLoading);

  if (loading === 'pending') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Spinner size="lg" />
      </div>
    );
  }

  // Redirect to dashboard if authenticated, otherwise to login
  return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />;
};

// =============================================================================
// Recursive Route Renderer
// =============================================================================

const renderRoute = (route: RouteObject): React.ReactNode => {
  const { element, children, path, index, caseSensitive, id } = route;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const typedChildren = children as RouteObject[] | undefined;

  // Build props for Route component
  const routeProps: Record<string, unknown> = {};
  if (path !== undefined) routeProps.path = path;
  if (index !== undefined) routeProps.index = index;
  if (caseSensitive !== undefined) routeProps.caseSensitive = caseSensitive;
  if (id !== undefined) routeProps.id = id;

  return (
    <Route
      key={`${path || ''}-${index || ''}`}
      element={<LoadingFallback>{element}</LoadingFallback>}
      {...routeProps}
    >
      {typedChildren?.map((child, i) => renderRoute(child))}
    </Route>
  );
};

// =============================================================================
// App Routes Component
// =============================================================================

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Root redirect */}
      <Route path="/" element={<RootLoader />} />
      
      {/* Render all routes from configuration */}
      {routes.map((route) => renderRoute(route))}
    </Routes>
  );
};

// =============================================================================
// Main App Component
// =============================================================================

export function App() {
  const dispatch = useAppDispatch();

  // Initialize authentication on app mount
  useEffect(() => {
    dispatch(initializeAuth());
  }, [dispatch]);

  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}

export default App;
