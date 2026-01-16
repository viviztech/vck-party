/**
 * Events Table Component
 * Displays events in a table format with sorting and selection
 */

import React from 'react';
import { Table, Pagination, Column } from '@/components/DataDisplay/Table';
import { Badge } from '@/components/DataDisplay/Badge';
import { Avatar } from '@/components/DataDisplay/Avatar';
import type { Event } from '@/services/eventsService';
import { formatDate } from '@/utils/helpers';
import { Calendar, MapPin, Users, Clock } from 'lucide-react';

interface EventsTableProps {
  events: Event[];
  loading: boolean;
  onRowClick: (event: Event) => void;
  page: number;
  limit: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function EventsTable({
  events,
  loading,
  onRowClick,
  page,
  limit,
  total,
  onPageChange,
}: EventsTableProps) {
  const totalPages = Math.ceil(total / limit);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      draft: { variant: 'default', label: 'Draft' },
      published: { variant: 'success', label: 'Published' },
      cancelled: { variant: 'error', label: 'Cancelled' },
      completed: { variant: 'info', label: 'Completed' },
      postponed: { variant: 'warning', label: 'Postponed' },
      in_progress: { variant: 'success', label: 'In Progress' },
    };
    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getTypeBadge = (type: string) => {
    const typeConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      meeting: { variant: 'info', label: 'Meeting' },
      rally: { variant: 'warning', label: 'Rally' },
      campaign: { variant: 'default', label: 'Campaign' },
      conference: { variant: 'info', label: 'Conference' },
      workshop: { variant: 'success', label: 'Workshop' },
      training: { variant: 'success', label: 'Training' },
      volunteer: { variant: 'info', label: 'Volunteer' },
      fundraiser: { variant: 'warning', label: 'Fundraiser' },
      awareness: { variant: 'info', label: 'Awareness' },
      visit: { variant: 'default', label: 'Visit' },
      inauguration: { variant: 'warning', label: 'Inauguration' },
      other: { variant: 'default', label: 'Other' },
    };
    const config = typeConfig[type] || { variant: 'default', label: type };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const columns: Column<Event>[] = [
    {
      key: 'event',
      header: 'Event',
      render: (row) => (
        <div className="flex items-center space-x-3">
          <Avatar
            src={row.image_url}
            name={row.title}
            size="md"
          />
          <div>
            <p className="font-medium text-gray-900">{row.title}</p>
            <p className="text-sm text-gray-500">{getTypeBadge(row.event_type)}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'date',
      header: 'Date & Time',
      render: (row) => (
        <div className="flex flex-col space-y-1">
          <div className="flex items-center text-sm text-gray-600">
            <Calendar size={14} className="mr-1" />
            {formatDate(row.start_date)}
          </div>
          {row.start_time && (
            <div className="flex items-center text-xs text-gray-500">
              <Clock size={12} className="mr-1" />
              {row.start_time} - {row.end_time || 'End'}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'venue',
      header: 'Venue',
      render: (row) => (
        <div className="flex items-center text-sm text-gray-600">
          <MapPin size={14} className="mr-1" />
          {row.venue || row.district || '-'}
        </div>
      ),
    },
    {
      key: 'attendees',
      header: 'Attendees',
      render: (row) => (
        <div className="flex items-center text-sm text-gray-600">
          <Users size={14} className="mr-1" />
          {row.actual_attendees || row.expected_attendees || 0}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => getStatusBadge(row.status),
    },
  ];

  return (
    <div>
      <Table
        columns={columns}
        data={events}
        keyExtractor={(row) => row.id}
        onRowClick={onRowClick}
        loading={loading}
        emptyMessage="No events found"
        className="border-t border-gray-200"
      />
      {totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
}

export default EventsTable;
