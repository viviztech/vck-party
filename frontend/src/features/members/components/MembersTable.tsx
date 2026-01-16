/**
 * Members Table Component
 * Displays members in a table format with sorting and selection
 */

import React from 'react';
import { Table, Pagination, Column } from '@/components/DataDisplay/Table';
import { Avatar } from '@/components/DataDisplay/Avatar';
import { Badge } from '@/components/DataDisplay/Badge';
import { Checkbox } from '@/components/Form/Checkbox';
import { Member } from '@/services/membersService';
import { formatDate } from '@/utils/helpers';
import { Phone, Mail } from 'lucide-react';

interface MembersTableProps {
  members: Member[];
  loading: boolean;
  onRowClick: (member: Member) => void;
  onSelectionChange: (ids: string[]) => void;
  page: number;
  limit: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function MembersTable({
  members,
  loading,
  onRowClick,
  onSelectionChange,
  page,
  limit,
  total,
  onPageChange,
}: MembersTableProps) {
  const totalPages = Math.ceil(total / limit);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      active: { variant: 'success', label: 'Active' },
      pending: { variant: 'warning', label: 'Pending' },
      suspended: { variant: 'error', label: 'Suspended' },
      inactive: { variant: 'info', label: 'Inactive' },
    };
    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const columns: Column<Member>[] = [
    {
      key: 'select',
      header: '',
      width: '40px',
      render: (row) => (
        <Checkbox
          checked={false}
          onChange={() => {}}
          onClick={(e) => e.stopPropagation()}
        />
      ),
    },
    {
      key: 'member',
      header: 'Member',
      sortable: true,
      render: (row) => (
        <div className="flex items-center space-x-3">
          <Avatar
            src={row.photo_url}
            name={`${row.first_name} ${row.last_name || ''}`}
            size="sm"
          />
          <div>
            <p className="font-medium">{row.first_name} {row.last_name || ''}</p>
            <p className="text-sm text-gray-500">{row.membership_number}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'phone',
      header: 'Phone',
      render: (row) => (
        <a href={`tel:${row.phone}`} className="flex items-center text-gray-600 hover:text-gray-900" onClick={(e) => e.stopPropagation()}>
          <Phone size={14} className="mr-1" />
          {row.phone}
        </a>
      ),
    },
    {
      key: 'email',
      header: 'Email',
      render: (row) => row.email ? (
        <a href={`mailto:${row.email}`} className="flex items-center text-gray-600 hover:text-gray-900" onClick={(e) => e.stopPropagation()}>
          <Mail size={14} className="mr-1" />
          {row.email}
        </a>
      ) : '-',
    },
    {
      key: 'district',
      header: 'District',
      render: (row) => row.district || '-',
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => getStatusBadge(row.status),
    },
    {
      key: 'joined_at',
      header: 'Joined',
      sortable: true,
      render: (row) => formatDate(row.joined_at),
    },
  ];

  return (
    <div>
      <Table
        columns={columns}
        data={members}
        keyExtractor={(row) => row.id}
        onRowClick={onRowClick}
        loading={loading}
        emptyMessage="No members found"
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

export default MembersTable;
