/**
 * Register Form Component
 * User registration form with email, phone, and password
 */

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, Phone, Lock, User, AlertCircle } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { register, selectAuthLoading, selectAuthError, clearError } from '@/store/authSlice';
import { Button } from '@/components/Form/Button';
import { Input } from '@/components/Form/Input';
import { Alert } from '@/components/Feedback/Alert';

// Validation schema
const registerSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Please enter a valid email'),
  phone: z.string().min(1, 'Phone number is required').regex(/^\+?[1-9]\d{9,14}$/, 'Please enter a valid phone number'),
  password: z.string().min(1, 'Password is required').min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const loading = useAppSelector(selectAuthLoading);
  const error = useAppSelector(selectAuthError);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      phone: '',
      password: '',
      confirm_password: '',
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      const { confirm_password, ...registerData } = data;
      await dispatch(register(registerData)).unwrap();
      navigate('/dashboard');
    } catch {
      // Error is handled by Redux
    }
  };

  React.useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Create Account</h1>
          <p className="text-gray-600 mt-2">Register to get started with VCK</p>
        </div>

        {error && (
          <Alert variant="error" className="mb-6" dismissible onDismiss={() => dispatch(clearError())}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Input
            label="Full Name"
            type="text"
            placeholder="Enter your full name"
            leftIcon={<User size={18} />}
            error={errors.email?.message}
            {...register('email')}
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="Enter your email"
            leftIcon={<Mail size={18} />}
            error={errors.email?.message}
            {...register('email')}
          />

          <Input
            label="Phone Number"
            type="tel"
            placeholder="Enter your phone number"
            leftIcon={<Phone size={18} />}
            error={errors.phone?.message}
            {...register('phone')}
          />

          <Input
            label="Password"
            type="password"
            placeholder="Create a password"
            leftIcon={<Lock size={18} />}
            error={errors.password?.message}
            {...register('password')}
          />

          <Input
            label="Confirm Password"
            type="password"
            placeholder="Confirm your password"
            leftIcon={<Lock size={18} />}
            error={errors.confirm_password?.message}
            {...register('confirm_password')}
          />

          <div className="flex items-start">
            <input
              type="checkbox"
              className="h-4 w-4 mt-0.5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              required
            />
            <span className="ml-2 text-sm text-gray-600">
              I agree to the{' '}
              <a href="#" className="text-primary-600 hover:text-primary-500">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="#" className="text-primary-600 hover:text-primary-500">
                Privacy Policy
              </a>
            </span>
          </div>

          <Button type="submit" fullWidth loading={loading === 'pending'}>
            Create Account
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default RegisterForm;
