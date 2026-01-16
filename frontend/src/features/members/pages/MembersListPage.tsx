/**
 * Members List Page
 * Displays a list of members with filtering, search, and pagination
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card } from '@/components/DataDisplay/Card';
import { MembersTable } from '../components/MembersTable';
import { MemberFilters } from '../components/MemberFilters';
import { MemberStats } from '../components/MemberStats';
import { membersService, Member, MemberFilters as MemberFiltersType } from '@/services/membersService';
import { Button } from '@/components/Form/Button';
import { Plus, Download, Upload } from 'lucide-react';

export function MembersListPage() {
  const navigate = useNavigate();
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [filters, setFilters] = useState<MemberFiltersType>({});
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const fetchMembers = useCallback(async () => {
    setLoading(true);
    try {
      const response = await membersService.getMembers({
        ...filters,
        page,
        limit,
      });
      setMembers(response.members);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to fetch members:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, page, limit]);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  const handleFilterChange = (newFilters: MemberFiltersType) => {
    setFilters(newFilters);
    setPage(1);
  };

  const handleSearch = (search: string) => {
    handleFilterChange({ ...filters, search });
  };

  const handleRowClick = (member: Member) => {
    navigate(`/members/${member.id}`);
  };

  const handleSelectionChange = (ids: string[]) => {
    setSelectedIds(ids);
  };

  const handleBulkExport = async () => {
    try {
      const response = await membersService.exportMembers(filters);
      window.open(response.file_url, '_blank');
    } catch (error) {
      console.error('Failed to export members:', error);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    if (window.confirm(`Are you sure you want to delete ${selectedIds.length} members?`)) {
      try {
        await Promise.all(selectedIds.map(id => membersService.deleteMember(id)));
        fetchMembers();
        setSelectedIds([]);
      } catch (error) {
        console.error('Failed to delete members:', error);
      }
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Members"
        description={`Manage and view all members (${total} total)`}
        actions={
          <div className="flex items-center space-x-3">
            <Button variant="outline" leftIcon={<Upload size={16} />} onClick={() => navigate('/members/import')}>
              Import
            </Button>
            <Button variant="outline" leftIcon={<Download size={16} />} onClick={handleBulkExport}>
              Export
            </Button>
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/members/new')}>
              Add Member
            </Button>
          </div>
        }
      />

      <MemberStats />

      <Card padding="none">
        <MemberFilters
          filters={filters}
          onFilterChange={handleFilterChange}
          onSearch={handleSearch}
          selectedCount={selectedIds.length}
          onBulkDelete={handleBulkDelete}
        />
        <MembersTable
          members={members}
          loading={loading}
          onRowClick={handleRowClick}
          onSelectionChange={handleSelectionChange}
          page={page}
          limit={limit}
          total={total}
          onPageChange={setPage}
        />
      </Card>
    </div>
  );
}

export default MembersListPage;
