/**
 * Dashboard Page
 * Main dashboard showing overview of the application
 */

import React from 'react';
import { Card } from '@/components/DataDisplay/Card';
import { PageHeader } from '@/components/Layout/PageHeader';
import { MemberStats } from '@/features/members/components/MemberStats';
import { HierarchyStats } from '@/features/hierarchy/components/HierarchyStats';
import { EventStats } from '@/features/events/components/EventStats';

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Welcome to the VCK Admin Dashboard"
      />

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-primary-500 to-primary-600 text-white">
          <div className="p-6">
            <h3 className="text-lg font-medium opacity-90">Total Members</h3>
            <p className="text-4xl font-bold mt-2">1,234</p>
            <p className="text-sm mt-2 opacity-75">+12% from last month</p>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <div className="p-6">
            <h3 className="text-lg font-medium opacity-90">Active Voters</h3>
            <p className="text-4xl font-bold mt-2">987</p>
            <p className="text-sm mt-2 opacity-75">+5% from last month</p>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <div className="p-6">
            <h3 className="text-lg font-medium opacity-90">Upcoming Events</h3>
            <p className="text-4xl font-bold mt-2">8</p>
            <p className="text-sm mt-2 opacity-75">This week</p>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <div className="p-6">
            <h3 className="text-lg font-medium opacity-90">Announcements</h3>
            <p className="text-4xl font-bold mt-2">15</p>
            <p className="text-sm mt-2 opacity-75">Active posts</p>
          </div>
        </Card>
      </div>

      {/* Feature Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MemberStats />
        <HierarchyStats />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EventStats />
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <p className="text-sm text-gray-600">New member registered: John Doe</p>
                <span className="text-xs text-gray-400 ml-auto">2 min ago</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <p className="text-sm text-gray-600">Event updated: Annual Meeting</p>
                <span className="text-xs text-gray-400 ml-auto">15 min ago</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                <p className="text-sm text-gray-600">Announcement published</p>
                <span className="text-xs text-gray-400 ml-auto">1 hour ago</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <p className="text-sm text-gray-600">New election created</p>
                <span className="text-xs text-gray-400 ml-auto">2 hours ago</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="flex flex-wrap gap-3">
            <a
              href="/members/new"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Add New Member
            </a>
            <a
              href="/events/new"
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Create Event
            </a>
            <a
              href="/communications/announcements/new"
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              Post Announcement
            </a>
            <a
              href="/voting/new"
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Create Election
            </a>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default DashboardPage;
