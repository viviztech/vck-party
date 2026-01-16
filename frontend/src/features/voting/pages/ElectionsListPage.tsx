/**
 * Elections List Page
 * Lists all elections with filtering and search
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/Form/Button';
import { Tabs } from '@/components/DataDisplay/Tabs';
import { votingService, Election, ElectionFilters } from '@/services/votingService';
import { Plus, Vote, Grid, List } from 'lucide-react';
import { ElectionsTable } from '../components/ElectionsTable';
import { ElectionFilters as ElectionFiltersComponent } from '../components/ElectionFilters';
import { ElectionCard } from '../components/ElectionCard';

export function ElectionsListPage() {
  const navigate = useNavigate();
  const [elections, setElections] = useState<Election[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<ElectionFilters>({});
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [view, setView] = useState<'list' | 'grid'>('list');

  const limit = 10;

  const fetchElections = useCallback(async () => {
    setLoading(true);
    try {
      const response = await votingService.getElections({
        ...filters,
        page,
        limit,
      });
      setElections(response.elections);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to fetch elections:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    fetchElections();
  }, [fetchElections]);

  const handleSearch = (search: string) => {
    setFilters((prev) => ({ ...prev, search: search || undefined }));
    setPage(1);
  };

  const handleFilterChange = (newFilters: ElectionFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  const handleRowClick = (election: Election) => {
    navigate(`/elections/${election.id}`);
  };

  const tabs = [
    { key: 'all', label: 'All Elections' },
    { key: 'active', label: 'Active' },
    { key: 'upcoming', label: 'Upcoming' },
    { key: 'completed', label: 'Completed' },
  ];

  const [activeTab, setActiveTab] = useState('all');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Elections</h1>
          <p className="text-gray-500">Manage party elections and voting</p>
        </div>
        <Button onClick={() => navigate('/elections/new')} leftIcon={<Plus size={16} />}>
          New Election
        </Button>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} variant="underline" />

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <ElectionFiltersComponent
            filters={filters}
            onFilterChange={handleFilterChange}
            onSearch={handleSearch}
          />
          <div className="flex items-center space-x-2">
            <Button
              variant={view === 'list' ? 'secondary' : 'outline'}
              size="sm"
              onClick={() => setView('list')}
            >
              <List size={16} />
            </Button>
            <Button
              variant={view === 'grid' ? 'secondary' : 'outline'}
              size="sm"
              onClick={() => setView('grid')}
            >
              <Grid size={16} />
            </Button>
          </div>
        </div>

        {view === 'list' ? (
          <ElectionsTable
            elections={elections}
            loading={loading}
            onRowClick={handleRowClick}
            page={page}
            limit={limit}
            total={total}
            onPageChange={setPage}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {elections.map((election) => (
              <ElectionCard
                key={election.id}
                election={election}
                onClick={() => handleRowClick(election)}
              />
            ))}
            {elections.length === 0 && !loading && (
              <div className="col-span-full text-center py-12 text-gray-500">
                <Vote size={48} className="mx-auto mb-4 text-gray-300" />
                <p>No elections found</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => navigate('/elections/new')}
                >
                  Create your first election
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ElectionsListPage;
