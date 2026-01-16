/**
 * Elections Table Component
 * Displays elections in a table format with sorting and selection
 */

import React from 'react';
import { Table, Pagination, Column } from '@/components/DataDisplay/Table';
import { Badge } from '@/components/DataDisplay/Badge';
import { Avatar } from '@/components/DataDisplay/Avatar';
import type { Election } from '@/services/votingService';
import { formatDate } from '@/utils/helpers';
import { Calendar, Vote } from 'lucide-react';

interface ElectionsTableProps {
  elections: Election[];
  loading: boolean;
  onRowClick: (election: Election) => void;
  page: number;
  limit: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function ElectionsTable({
  elections,
  loading,
  onRowClick,
  page,
  limit,
  total,
  onPageChange,
}: ElectionsTableProps) {
  const totalPages = Math.ceil(total / limit);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      draft: { variant: 'default', label: 'Draft' },
      published: { variant: 'info', label: 'Published' },
      nominations_open: { variant: 'success', label: 'Nominations Open' },
      nominations_closed: { variant: 'warning', label: 'Nominations Closed' },
      voting_open: { variant: 'success', label: 'Voting Open' },
      voting_closed: { variant: 'warning', label: 'Voting Closed' },
      results_calculated: { variant: 'info', label: 'Results Calculated' },
      results_published: { variant: 'success', label: 'Results Published' },
      cancelled: { variant: 'error', label: 'Cancelled' },
    };
    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const columns: Column<Election>[] = [
    {
      key: 'election',
      header: 'Election',
      render: (row) => (
        <div className="flex items-center space-x-3">
          <Avatar
            src={undefined}
            name={row.title}
            size="md"
          />
          <div>
            <p className="font-medium text-gray-900">{row.title}</p>
            {row.description && (
              <p className="text-sm text-gray-500 line-clamp-1">{row.description}</p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'voting_period',
      header: 'Voting Period',
      render: (row) => (
        <div className="flex flex-col space-y-1">
          <div className="flex items-center text-sm text-gray-600">
            <Calendar size={14} className="mr-1" />
            Start: {formatDate(row.voting_start)}
          </div>
          <div className="flex items-center text-xs text-gray-500">
            End: {formatDate(row.voting_end)}
          </div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => getStatusBadge(row.status),
    },
    {
      key: 'type',
      header: 'Type',
      render: (row) => (
        <div className="flex items-center text-sm text-gray-600">
          <Vote size={14} className="mr-1" />
          {row.is_secret_voting ? 'Secret' : 'Open'}
        </div>
      ),
    },
  ];

  return (
    <div>
      <Table
        columns={columns}
        data={elections}
        keyExtractor={(row) => row.id}
        onRowClick={onRowClick}
        loading={loading}
        emptyMessage="No elections found"
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

export default ElectionsTable;
