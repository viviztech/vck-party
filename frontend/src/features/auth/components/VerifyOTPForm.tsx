/**
 * Verify OTP Form Component
 * OTP verification form for phone number verification
 */

import React from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Phone, Lock, ArrowLeft, CheckCircle } from 'lucide-react';
import { useAppDispatch } from '@/store/hooks';
import { authService } from '@/services/authService';
import { Button } from '@/components/Form/Button';
import { Input } from '@/components/Form/Input';
import { Alert } from '@/components/Feedback/Alert';

// Validation schema
const verifyOTPSchema = z.object({
  phone: z.string().min(1, 'Phone number is required').regex(/^\+?[1-9]\d{9,14}$/, 'Please enter a valid phone number'),
  otp: z.string().min(1, 'OTP is required').length(6, 'OTP must be 6 digits'),
});

type VerifyOTPFormData = z.infer<typeof verifyOTPSchema>;

export function VerifyOTPForm() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialPhone = searchParams.get('phone') || '';

  const [loading, setLoading] = React.useState(false);
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [resending, setResending] = React.useState(false);
  const [resendSuccess, setResendSuccess] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<VerifyOTPFormData>({
    resolver: zodResolver(verifyOTPSchema),
    defaultValues: {
      phone: initialPhone,
      otp: '',
    },
  });

  const onSubmit = async (data: VerifyOTPFormData) => {
    try {
      setLoading(true);
      setError(null);
      const response = await authService.verifyOTP({
        phone: data.phone,
        otp: data.otp,
      });
      if (response) {
        setSuccess(true);
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    const phone = initialPhone;
    if (!phone) {
      setError('Phone number is required to resend OTP');
      return;
    }

    try {
      setResending(true);
      setError(null);
      await authService.sendOTP({
        phone,
        purpose: 'login',
      });
      setResendSuccess(true);
      setTimeout(() => setResendSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend OTP');
    } finally {
      setResending(false);
    }
  };

  if (success) {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="mx-auto w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="text-success-600" size={32} />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Verification Successful</h1>
            <p className="text-gray-600 mt-2">
              Your phone number has been verified. Redirecting to dashboard...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Verify Phone</h1>
          <p className="text-gray-600 mt-2">
            Enter the OTP sent to your phone number.
          </p>
        </div>

        {error && (
          <Alert variant="error" className="mb-6" dismissible onDismiss={() => setError(null)}>
            {error}
          </Alert>
        )}

        {resendSuccess && (
          <Alert variant="success" className="mb-6">
            OTP has been resent successfully.
          </Alert>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Input
            label="Phone Number"
            type="tel"
            placeholder="Enter your phone number"
            leftIcon={<Phone size={18} />}
            error={errors.phone?.message}
            {...register('phone')}
          />

          <Input
            label="OTP"
            type="text"
            placeholder="Enter 6-digit OTP"
            leftIcon={<Lock size={18} />}
            error={errors.otp?.message}
            maxLength={6}
            {...register('otp')}
          />

          <Button type="submit" fullWidth loading={loading}>
            Verify OTP
          </Button>
        </form>

        <div className="mt-6 space-y-4">
          <div className="text-center">
            <button
              type="button"
              onClick={handleResendOTP}
              disabled={resending || !initialPhone}
              className="text-sm font-medium text-primary-600 hover:text-primary-500 disabled:opacity-50"
            >
              {resending ? 'Sending...' : "Didn't receive OTP? Resend"}
            </button>
          </div>

          <div className="text-center">
            <Link
              to="/login"
              className="inline-flex items-center text-sm font-medium text-gray-600 hover:text-gray-500"
            >
              <ArrowLeft size={16} className="mr-2" />
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default VerifyOTPForm;
