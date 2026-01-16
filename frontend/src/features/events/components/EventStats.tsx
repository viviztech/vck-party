/**
 * Event Stats Component
 * Statistics widget for events
 */

import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/DataDisplay/Card';
import { Progress } from '@/components/DataDisplay/Progress';
import type { EventStats } from '@/services/eventsService';
import { Calendar, Users, TrendingUp, Clock, CheckCircle, AlertCircle } from 'lucide-react';

interface EventStatsProps {
  stats: EventStats;
}

export function EventStats({ stats }: EventStatsProps) {
  const statCards = [
    {
      label: 'Total Events',
      value: stats.total_events,
      icon: Calendar,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      label: 'Upcoming Events',
      value: stats.upcoming_events,
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
    {
      label: 'Completed Events',
      value: stats.completed_events,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      label: 'Active Campaigns',
      value: stats.active_campaigns,
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="flex items-center space-x-4">
              <div className={`p-3 rounded-full ${stat.bgColor}`}>
                <stat.icon size={24} className={stat.color} />
              </div>
              <div>
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Attendance Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader title="Total Attendance" />
          <CardContent>
            <div className="flex items-center space-x-4">
              <Users size={32} className="text-blue-600" />
              <div className="flex-1">
                <p className="text-3xl font-bold text-gray-900">{stats.total_attendance.toLocaleString()}</p>
                <p className="text-sm text-gray-500">Total attendees across all events</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Average Attendance" />
          <CardContent>
            <div className="flex items-center space-x-4">
              <TrendingUp size={32} className="text-green-600" />
              <div className="flex-1">
                <p className="text-3xl font-bold text-gray-900">{stats.avg_attendance.toFixed(1)}</p>
                <p className="text-sm text-gray-500">Average per event</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Events by Type */}
      <Card>
        <CardHeader title="Events by Type" />
        <CardContent className="space-y-4">
          {Object.entries(stats.by_type).map(([type, count]) => {
            const percentage = stats.total_events > 0 ? (count / stats.total_events) * 100 : 0;
            return (
              <div key={type}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700 capitalize">{type.replace('_', ' ')}</span>
                  <span className="text-sm text-gray-500">{count} ({percentage.toFixed(1)}%)</span>
                </div>
                <Progress value={percentage} />
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Events by Status */}
      <Card>
        <CardHeader title="Events by Status" />
        <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(stats.by_status).map(([status, count]) => (
            <div key={status} className="flex items-center space-x-2">
              {status === 'completed' ? (
                <CheckCircle size={16} className="text-green-500" />
              ) : status === 'cancelled' ? (
                <AlertCircle size={16} className="text-red-500" />
              ) : status === 'published' ? (
                <Calendar size={16} className="text-blue-500" />
              ) : (
                <Clock size={16} className="text-gray-500" />
              )}
              <span className="text-sm text-gray-700 capitalize">{status.replace('_', ' ')}</span>
              <span className="text-sm font-medium text-gray-900">{count}</span>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Monthly Trend */}
      {stats.by_month && stats.by_month.length > 0 && (
        <Card>
          <CardHeader title="Monthly Trend" />
          <CardContent>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
              {stats.by_month.slice(-6).map((month) => (
                <div key={month.month} className="text-center">
                  <p className="text-xs text-gray-500 mb-1">{month.month}</p>
                  <p className="text-lg font-semibold text-gray-900">{month.count}</p>
                  <p className="text-xs text-gray-400">{month.attendance} attendees</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default EventStats;
