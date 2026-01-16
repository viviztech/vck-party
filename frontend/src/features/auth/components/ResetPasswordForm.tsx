/**
 * Reset Password Form Component
 * Password reset form with token validation
 */

import React from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Lock, ArrowLeft, AlertCircle, CheckCircle } from 'lucide-react';
import { authService } from '@/services/authService';
import { Button } from '@/components/Form/Button';
import { Input } from '@/components/Form/Input';
import { Alert } from '@/components/Feedback/Alert';

// Validation schema
const resetPasswordSchema = z.object({
  new_password: z.string().min(1, 'Password is required').min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export function ResetPasswordForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [loading, setLoading] = React.useState(false);
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      new_password: '',
      confirm_password: '',
    },
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) {
      setError('Invalid or expired reset token');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await authService.resetPassword({
        token,
        new_password: data.new_password,
        confirm_new_password: data.confirm_password,
      });
      if (response.success) {
        setSuccess(true);
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <Alert variant="error">
            This password reset link is invalid or has expired. Please request a new one.
          </Alert>
          <div className="mt-6 text-center">
            <Link
              to="/forgot-password"
              className="text-sm font-medium text-primary-600 hover:text-primary-500"
            >
              Request new reset link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="mx-auto w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="text-success-600" size={32} />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Password Reset</h1>
            <p className="text-gray-600 mt-2">
              Your password has been successfully reset. You can now sign in with your new password.
            </p>
          </div>

          <Alert variant="success" className="mb-6">
            Redirecting to login page in a few seconds...
          </Alert>

          <div className="mt-6 text-center">
            <Link
              to="/login"
              className="inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-500"
            >
              <ArrowLeft size={16} className="mr-2" />
              Go to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Reset Password</h1>
          <p className="text-gray-600 mt-2">Enter your new password below.</p>
        </div>

        {error && (
          <Alert variant="error" className="mb-6" dismissible onDismiss={() => setError(null)}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Input
            label="New Password"
            type="password"
            placeholder="Enter new password"
            leftIcon={<Lock size={18} />}
            error={errors.new_password?.message}
            {...register('new_password')}
          />

          <Input
            label="Confirm New Password"
            type="password"
            placeholder="Confirm new password"
            leftIcon={<Lock size={18} />}
            error={errors.confirm_password?.message}
            {...register('confirm_password')}
          />

          <Button type="submit" fullWidth loading={loading}>
            Reset Password
          </Button>
        </form>

        <div className="mt-6 text-center">
          <Link
            to="/login"
            className="inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-500"
          >
            <ArrowLeft size={16} className="mr-2" />
            Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
}

export default ResetPasswordForm;
