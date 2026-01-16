/**
 * App Routes Configuration
 * Defines all application routes with lazy loading and route guards
 */

import React, { lazy } from 'react';
import { Navigate } from 'react-router-dom';
import type { RouteObject } from 'react-router-dom';

// Redux hooks and selectors
import { useAppSelector } from '@/store/hooks';
import { selectIsAuthenticated, selectAuthLoading } from '@/store/authSlice';

// Layouts
import { Layout } from '@/components/Layout/Layout';
import { AuthLayout } from '@/features/auth/components/AuthLayout';

// Auth Pages (lazy loaded)
const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage').then(module => ({ default: module.LoginPage })));
const RegisterPage = lazy(() => import('@/features/auth/pages/RegisterPage').then(module => ({ default: module.RegisterPage })));
const ForgotPasswordPage = lazy(() => import('@/features/auth/pages/ForgotPasswordPage').then(module => ({ default: module.ForgotPasswordPage })));
const ResetPasswordPage = lazy(() => import('@/features/auth/pages/ResetPasswordPage').then(module => ({ default: module.ResetPasswordPage })));
const VerifyOTPPage = lazy(() => import('@/features/auth/pages/VerifyOTPPage').then(module => ({ default: module.VerifyOTPPage })));

// Feature Pages (lazy loaded)
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then(module => ({ default: module.DashboardPage })));
const MembersListPage = lazy(() => import('@/features/members/pages/MembersListPage').then(module => ({ default: module.MembersListPage })));
const MemberDetailPage = lazy(() => import('@/features/members/pages/MemberDetailPage').then(module => ({ default: module.MemberDetailPage })));
const MemberCreatePage = lazy(() => import('@/features/members/pages/MemberCreatePage').then(module => ({ default: module.MemberCreatePage })));
const MemberEditPage = lazy(() => import('@/features/members/pages/MemberEditPage').then(module => ({ default: module.MemberEditPage })));
const MemberImportPage = lazy(() => import('@/features/members/pages/MemberImportPage').then(module => ({ default: module.MemberImportPage })));
const MemberProfilePage = lazy(() => import('@/features/members/pages/MemberProfilePage').then(module => ({ default: module.MemberProfilePage })));
const MemberFamilyPage = lazy(() => import('@/features/members/pages/MemberFamilyPage').then(module => ({ default: module.MemberFamilyPage })));
const MemberDocumentsPage = lazy(() => import('@/features/members/pages/MemberDocumentsPage').then(module => ({ default: module.MemberDocumentsPage })));

// Hierarchy Pages
const HierarchyDashboardPage = lazy(() => import('@/features/hierarchy/pages/HierarchyDashboardPage').then(module => ({ default: module.default || module.HierarchyDashboardPage })));
const DistrictsListPage = lazy(() => import('@/features/hierarchy/pages/DistrictsListPage').then(module => ({ default: module.default || module.DistrictsListPage })));
const DistrictDetailPage = lazy(() => import('@/features/hierarchy/pages/DistrictDetailPage').then(module => ({ default: module.default || module.DistrictDetailPage })));
const ConstituencyDetailPage = lazy(() => import('@/features/hierarchy/pages/ConstituencyDetailPage').then(module => ({ default: module.default || module.ConstituencyDetailPage })));

// Events Pages
const EventsListPage = lazy(() => import('@/features/events/pages/EventsListPage').then(module => ({ default: module.default || module.EventsListPage })));
const EventCalendarPage = lazy(() => import('@/features/events/pages/EventCalendarPage').then(module => ({ default: module.default || module.EventCalendarPage })));
const EventEditPage = lazy(() => import('@/features/events/pages/EventEditPage').then(module => ({ default: module.default || module.EventEditPage })));
const CampaignsListPage = lazy(() => import('@/features/events/pages/CampaignsListPage').then(module => ({ default: module.default || module.CampaignsListPage })));

// Communications Pages
const AnnouncementsListPage = lazy(() => import('@/features/communications/pages/AnnouncementsListPage').then(module => ({ default: module.default })));
const AnnouncementDetailPage = lazy(() => import('@/features/communications/pages/AnnouncementDetailPage').then(module => ({ default: module.default })));
const AnnouncementCreatePage = lazy(() => import('@/features/communications/pages/AnnouncementCreatePage').then(module => ({ default: module.default })));
const ForumsListPage = lazy(() => import('@/features/communications/pages/ForumsListPage').then(module => ({ default: module.default })));
const ForumDetailPage = lazy(() => import('@/features/communications/pages/ForumDetailPage').then(module => ({ default: module.default })));
const ForumCreatePage = lazy(() => import('@/features/communications/pages/ForumCreatePage').then(module => ({ default: module.default })));
const PostDetailPage = lazy(() => import('@/features/communications/pages/PostDetailPage').then(module => ({ default: module.default })));

// Voting Pages
const ElectionsListPage = lazy(() => import('@/features/voting/pages/ElectionsListPage').then(module => ({ default: module.ElectionsListPage })));
const ElectionDetailPage = lazy(() => import('@/features/voting/pages/ElectionDetailPage').then(module => ({ default: module.ElectionDetailPage })));
const ElectionCreatePage = lazy(() => import('@/features/voting/pages/ElectionCreatePage').then(module => ({ default: module.ElectionCreatePage })));
const NominationsPage = lazy(() => import('@/features/voting/pages/NominationsPage').then(module => ({ default: module.NominationsPage })));

// Error Pages
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage').then(module => ({ default: module.NotFoundPage })));
const ForbiddenPage = lazy(() => import('@/pages/ForbiddenPage').then(module => ({ default: module.ForbiddenPage })));

// =============================================================================
// Route Guard Components
// =============================================================================

/**
 * Protected Route Wrapper
 * Redirects to login if user is not authenticated
 */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const loading = useAppSelector(selectAuthLoading);

  if (loading === 'pending') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: window.location.pathname }} />;
  }

  return <>{children}</>;
};

/**
 * Guest Route Wrapper
 * Redirects to dashboard if user is already authenticated
 */
const GuestRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const loading = useAppSelector(selectAuthLoading);

  if (loading === 'pending') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// =============================================================================
// Route Definitions
// =============================================================================

export const routes: RouteObject[] = [
  // Public Routes (Guest only - redirect to dashboard if authenticated)
  {
    element: <GuestRoute><AuthLayout /></GuestRoute>,
    children: [
      {
        path: '/login',
        element: <LoginPage />,
      },
      {
        path: '/register',
        element: <RegisterPage />,
      },
      {
        path: '/forgot-password',
        element: <ForgotPasswordPage />,
      },
      {
        path: '/reset-password',
        element: <ResetPasswordPage />,
      },
      {
        path: '/verify-otp',
        element: <VerifyOTPPage />,
      },
    ],
  },

  // Protected Routes (Require authentication)
  {
    element: <ProtectedRoute><Layout /></ProtectedRoute>,
    children: [
      // Dashboard
      {
        path: '/dashboard',
        element: <DashboardPage />,
      },
      {
        path: '/',
        element: <Navigate to="/dashboard" replace />,
      },

      // Members
      {
        path: '/members',
        children: [
          {
            index: true,
            element: <MembersListPage />,
          },
          {
            path: 'new',
            element: <MemberCreatePage />,
          },
          {
            path: 'import',
            element: <MemberImportPage />,
          },
          {
            path: ':id',
            children: [
              {
                index: true,
                element: <MemberDetailPage />,
              },
              {
                path: 'edit',
                element: <MemberEditPage />,
              },
              {
                path: 'profile',
                element: <MemberProfilePage />,
              },
              {
                path: 'family',
                element: <MemberFamilyPage />,
              },
              {
                path: 'documents',
                element: <MemberDocumentsPage />,
              },
            ],
          },
        ],
      },

      // Hierarchy
      {
        path: '/hierarchy',
        children: [
          {
            index: true,
            element: <HierarchyDashboardPage />,
          },
          {
            path: 'districts',
            children: [
              {
                index: true,
                element: <DistrictsListPage />,
              },
              {
                path: ':districtId',
                children: [
                  {
                    index: true,
                    element: <DistrictDetailPage />,
                  },
                  {
                    path: 'constituencies/:constituencyId',
                    element: <ConstituencyDetailPage />,
                  },
                ],
              },
            ],
          },
        ],
      },

      // Events
      {
        path: '/events',
        children: [
          {
            index: true,
            element: <EventsListPage />,
          },
          {
            path: 'calendar',
            element: <EventCalendarPage />,
          },
          {
            path: 'campaigns',
            element: <CampaignsListPage />,
          },
          {
            path: ':eventId/edit',
            element: <EventEditPage />,
          },
        ],
      },

      // Communications
      {
        path: '/communications',
        children: [
          {
            path: 'announcements',
            children: [
              {
                index: true,
                element: <AnnouncementsListPage />,
              },
              {
                path: 'new',
                element: <AnnouncementCreatePage />,
              },
              {
                path: ':id',
                element: <AnnouncementDetailPage />,
              },
            ],
          },
          {
            path: 'forums',
            children: [
              {
                index: true,
                element: <ForumsListPage />,
              },
              {
                path: 'new',
                element: <ForumCreatePage />,
              },
              {
                path: ':id',
                children: [
                  {
                    index: true,
                    element: <ForumDetailPage />,
                  },
                  {
                    path: 'posts/:postId',
                    element: <PostDetailPage />,
                  },
                ],
              },
            ],
          },
        ],
      },

      // Voting
      {
        path: '/voting',
        children: [
          {
            index: true,
            element: <ElectionsListPage />,
          },
          {
            path: 'new',
            element: <ElectionCreatePage />,
          },
          {
            path: 'nominations',
            element: <NominationsPage />,
          },
          {
            path: ':electionId',
            children: [
              {
                index: true,
                element: <ElectionDetailPage />,
              },
            ],
          },
        ],
      },

      // Settings (placeholder for future)
      {
        path: '/settings',
        element: <Navigate to="/dashboard" replace />,
      },
    ],
  },

  // Error Routes
  {
    path: '/404',
    element: <NotFoundPage />,
  },
  {
    path: '/403',
    element: <ForbiddenPage />,
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
];

export default routes;
