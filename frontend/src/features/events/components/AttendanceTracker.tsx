/**
 * Attendance Tracker Component
 * Track and manage event attendance
 */

import React, { useState } from 'react';
import { Table, Column } from '@/components/DataDisplay/Table';
import { Badge } from '@/components/DataDisplay/Badge';
import { Button } from '@/components/Form/Button';
import { Input } from '@/components/Form/Input';
import { Card, CardHeader, CardContent } from '@/components/DataDisplay/Card';
import type { EventAttendance } from '@/services/eventsService';
import { Search, Download } from 'lucide-react';

interface AttendanceTrackerProps {
  attendance: EventAttendance[];
  total: number;
  loading: boolean;
  onCheckIn: (attendanceId: string) => Promise<void>;
  onCheckOut: (attendanceId: string) => Promise<void>;
  onSearch: (query: string) => void;
  onExport: () => void;
}

export function AttendanceTracker({
  attendance,
  total,
  loading,
  onCheckIn,
  onCheckOut,
  onSearch,
  onExport,
}: AttendanceTrackerProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    onSearch(value);
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      registered: { variant: 'info', label: 'Registered' },
      confirmed: { variant: 'success', label: 'Confirmed' },
      checked_in: { variant: 'success', label: 'Checked In' },
      checked_out: { variant: 'default', label: 'Checked Out' },
      no_show: { variant: 'warning', label: 'No Show' },
      cancelled: { variant: 'error', label: 'Cancelled' },
    };
    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const columns: Column<EventAttendance>[] = [
    {
      key: 'attendee',
      header: 'Attendee',
      render: (row) => (
        <div>
          <p className="font-medium">
            {row.member ? `${row.member.first_name} ${row.member.last_name || ''}` : (row.non_member_name || 'Guest')}
          </p>
          <p className="text-sm text-gray-500">{row.member?.phone || row.non_member_phone}</p>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => getStatusBadge(row.status),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center space-x-2">
          {(row.status === 'registered' || row.status === 'confirmed') && (
            <Button variant="primary" size="sm" onClick={() => onCheckIn(row.id)}>
              Check In
            </Button>
          )}
          {row.status === 'checked_in' && (
            <Button variant="secondary" size="sm" onClick={() => onCheckOut(row.id)}>
              Check Out
            </Button>
          )}
        </div>
      ),
    },
  ];

  const checkedInCount = attendance.filter((a) => a.status === 'checked_in').length;

  return (
    <Card>
      <div className="flex flex-row items-center justify-between p-4 border-b border-gray-200">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Attendance Tracking</h3>
          <p className="text-sm text-gray-500">Checked In: {checkedInCount} | Total: {total}</p>
        </div>
        <Button variant="outline" onClick={onExport} leftIcon={<Download size={16} />}>
          Export
        </Button>
      </div>
      <CardContent>
        <div className="mb-4">
          <Input
            placeholder="Search attendees..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            leftIcon={<Search size={16} />}
          />
        </div>
        <Table
          columns={columns}
          data={attendance}
          keyExtractor={(row) => row.id}
          loading={loading}
          emptyMessage="No attendance records found"
        />
      </CardContent>
    </Card>
  );
}

export default AttendanceTracker;
