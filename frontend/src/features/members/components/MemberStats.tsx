/**
 * Member Stats Component
 * Statistics widget for member dashboard
 */

import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/DataDisplay/Card';
import { membersService, type MemberStats } from '@/services/membersService';
import { Users, UserCheck, UserX, UserMinus, TrendingUp, TrendingDown } from 'lucide-react';

export function MemberStats() {
  const [stats, setStats] = useState<MemberStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const statsData = await membersService.getMemberStats();
        setStats(statsData);
      } catch (error) {
        console.error('Failed to fetch member stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="py-4">
              <div className="animate-pulse flex items-center space-x-4">
                <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                  <div className="h-6 bg-gray-200 rounded w-16"></div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const statCards = [
    { title: 'Total Members', value: stats.total_members, icon: Users, color: 'text-primary-600', bgColor: 'bg-primary-100' },
    { title: 'Active', value: stats.active_members, icon: UserCheck, color: 'text-success-600', bgColor: 'bg-success-100' },
    { title: 'Pending', value: stats.pending_members, icon: UserMinus, color: 'text-warning-600', bgColor: 'bg-warning-100' },
    { title: 'Suspended', value: stats.suspended_members, icon: UserX, color: 'text-error-600', bgColor: 'bg-error-100' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {statCards.map((stat) => (
        <Card key={stat.title}>
          <CardContent className="py-4">
            <div className="flex items-center space-x-4">
              <div className={`p-3 rounded-full ${stat.bgColor}`}>
                <stat.icon size={24} className={stat.color} />
              </div>
              <div>
                <p className="text-sm text-gray-500">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">New This Month</p>
              <p className="text-2xl font-bold text-gray-900">{stats.new_this_month}</p>
            </div>
            <div className={`p-2 rounded-full ${stats.growth_percentage_month >= 0 ? 'bg-success-100' : 'bg-error-100'}`}>
              {stats.growth_percentage_month >= 0 ? <TrendingUp size={20} className="text-success-600" /> : <TrendingDown size={20} className="text-error-600" />}
            </div>
          </div>
          <p className={`text-sm mt-1 ${stats.growth_percentage_month >= 0 ? 'text-success-600' : 'text-error-600'}`}>
            {stats.growth_percentage_month >= 0 ? '+' : ''}{stats.growth_percentage_month}% from last month
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">New This Year</p>
              <p className="text-2xl font-bold text-gray-900">{stats.new_this_year}</p>
            </div>
            <div className={`p-2 rounded-full ${stats.growth_percentage_year >= 0 ? 'bg-success-100' : 'bg-error-100'}`}>
              {stats.growth_percentage_year >= 0 ? <TrendingUp size={20} className="text-success-600" /> : <TrendingDown size={20} className="text-error-600" />}
            </div>
          </div>
          <p className={`text-sm mt-1 ${stats.growth_percentage_year >= 0 ? 'text-success-600' : 'text-error-600'}`}>
            {stats.growth_percentage_year >= 0 ? '+' : ''}{stats.growth_percentage_year}% from last year
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default MemberStats;
