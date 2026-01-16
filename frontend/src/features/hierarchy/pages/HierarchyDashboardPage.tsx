/**
 * Hierarchy Dashboard Page
 * Overview of hierarchy with statistics and quick navigation
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card, CardContent, CardHeader } from '@/components/DataDisplay/Card';
import { HierarchyStats } from '../components/HierarchyStats';
import { HierarchyTree } from '../components/HierarchyTree';
import { MapPin, Building2, LayoutGrid, Users, TreePine, BarChart3 } from 'lucide-react';
import { cn } from '@/utils/helpers';

export function HierarchyDashboardPage() {
  const navigate = useNavigate();

  const quickLinks = [
    {
      title: 'Districts',
      description: 'View all districts',
      icon: <MapPin className="w-6 h-6" />,
      href: '/hierarchy/districts',
      color: 'bg-blue-500',
    },
    {
      title: 'Constituencies',
      description: 'View all constituencies',
      icon: <Building2 className="w-6 h-6" />,
      href: '/hierarchy/constituencies',
      color: 'bg-indigo-500',
    },
    {
      title: 'Wards',
      description: 'View all wards',
      icon: <LayoutGrid className="w-6 h-6" />,
      href: '/hierarchy/wards',
      color: 'bg-purple-500',
    },
    {
      title: 'Booths',
      description: 'View all booths',
      icon: <Users className="w-6 h-6" />,
      href: '/hierarchy/booths',
      color: 'bg-emerald-500',
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Hierarchy Dashboard"
        description="View and manage the organizational hierarchy structure"
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Hierarchy' },
        ]}
        actions={
          <button
            onClick={() => navigate('/hierarchy/tree')}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <TreePine size={16} className="mr-2" />
            View Tree
          </button>
        }
      />

      <HierarchyStats />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {quickLinks.map((link) => (
          <Card
            key={link.title}
            hover
            className="cursor-pointer transition-all hover:shadow-lg hover:-translate-y-1"
            onClick={() => navigate(link.href)}
          >
            <CardContent className="flex items-center space-x-4">
              <div className={cn('p-3 rounded-full text-white', link.color)}>
                {link.icon}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{link.title}</h3>
                <p className="text-sm text-gray-500">{link.description}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader
            title="Hierarchy Overview"
            subtitle="Quick summary of organizational structure"
            action={
              <button
                onClick={() => navigate('/hierarchy/tree')}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                View Full Tree
              </button>
            }
          />
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <MapPin className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-gray-900">Districts</span>
                </div>
                <span className="text-2xl font-bold text-blue-600">38</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Building2 className="w-5 h-5 text-indigo-600" />
                  <span className="font-medium text-gray-900">Constituencies</span>
                </div>
                <span className="text-2xl font-bold text-indigo-600">234</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <LayoutGrid className="w-5 h-5 text-purple-600" />
                  <span className="font-medium text-gray-900">Wards</span>
                </div>
                <span className="text-2xl font-bold text-purple-600">1,856</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-emerald-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Users className="w-5 h-5 text-emerald-600" />
                  <span className="font-medium text-gray-900">Booths</span>
                </div>
                <span className="text-2xl font-bold text-emerald-600">12,450</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="Interactive Tree"
            subtitle="Expand to explore hierarchy"
          />
          <CardContent>
            <HierarchyTree className="max-h-96 overflow-y-auto" />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Analytics"
          subtitle="Quick statistics and insights"
          action={
            <button
              onClick={() => navigate('/hierarchy/stats')}
              className="flex items-center text-sm text-blue-600 hover:text-blue-700"
            >
              <BarChart3 size={16} className="mr-1" />
              Detailed Analytics
            </button>
          }
        />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Coverage by District</p>
              <p className="text-xl font-bold text-gray-900 mt-1">100%</p>
              <div className="mt-2 h-2 bg-gray-200 rounded-full">
                <div className="h-2 bg-blue-500 rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Members with Location</p>
              <p className="text-xl font-bold text-gray-900 mt-1">87%</p>
              <div className="mt-2 h-2 bg-gray-200 rounded-full">
                <div className="h-2 bg-emerald-500 rounded-full" style={{ width: '87%' }} />
              </div>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Booth Mapping Complete</p>
              <p className="text-xl font-bold text-gray-900 mt-1">92%</p>
              <div className="mt-2 h-2 bg-gray-200 rounded-full">
                <div className="h-2 bg-purple-500 rounded-full" style={{ width: '92%' }} />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default HierarchyDashboardPage;
