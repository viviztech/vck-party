/**
 * Forgot Password Page
 * Password reset request page
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAppSelector } from '@/store/hooks';
import { selectIsAuthenticated } from '@/store/authSlice';
import { ForgotPasswordForm } from '../components/ForgotPasswordForm';

export function ForgotPasswordPage() {
  const isAuthenticated = useAppSelector(selectIsAuthenticated);

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <ForgotPasswordForm />
    </div>
  );
}

export default ForgotPasswordPage;
