/**
 * Hierarchy Stats Component
 * Displays statistics about the organizational hierarchy
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/DataDisplay/Card';
import { hierarchyService, type HierarchyStats } from '@/services/hierarchyService';
import { Users, MapPin, Building2, LayoutGrid, TrendingUp } from 'lucide-react';
import { cn } from '@/utils/helpers';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  suffix?: string;
  className?: string;
}

function StatCard({ title, value, icon, color, suffix, className }: StatCardProps) {
  return (
    <Card className={cn('relative overflow-hidden', className)}>
      <CardContent className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            {value}
            {suffix && <span className="text-lg font-normal text-gray-500 ml-1">{suffix}</span>}
          </p>
        </div>
        <div className={cn('p-3 rounded-full', color)}>
          {icon}
        </div>
      </CardContent>
      <div className={cn('absolute bottom-0 left-0 right-0 h-1', color.replace('bg-', 'bg-'))} />
    </Card>
  );
}

export function HierarchyStats() {
  const [stats, setStats] = useState<HierarchyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await hierarchyService.getHierarchyStats();
        setStats(data);
      } catch (err) {
        setError('Failed to load hierarchy statistics');
        console.error('Failed to fetch hierarchy stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="flex items-center justify-between h-24">
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded w-24" />
                <div className="h-6 bg-gray-200 rounded w-16" />
              </div>
              <div className="h-12 w-12 bg-gray-200 rounded-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return (
      <Card className="bg-red-50 border-red-200">
        <CardContent className="py-4 text-center text-red-600">
          {error || 'Unable to load statistics'}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Districts"
        value={stats.total_districts}
        icon={<MapPin className="w-6 h-6 text-white" />}
        color="bg-blue-500"
        className="hover:shadow-lg transition-shadow"
      />
      <StatCard
        title="Total Constituencies"
        value={stats.total_constituencies}
        icon={<Building2 className="w-6 h-6 text-white" />}
        color="bg-indigo-500"
        className="hover:shadow-lg transition-shadow"
      />
      <StatCard
        title="Total Wards"
        value={stats.total_wards}
        icon={<LayoutGrid className="w-6 h-6 text-white" />}
        color="bg-purple-500"
        className="hover:shadow-lg transition-shadow"
      />
      <StatCard
        title="Total Voters"
        value={stats.total_voters.toLocaleString()}
        icon={<Users className="w-6 h-6 text-white" />}
        color="bg-emerald-500"
        className="hover:shadow-lg transition-shadow"
      />
    </div>
  );
}

export default HierarchyStats;
