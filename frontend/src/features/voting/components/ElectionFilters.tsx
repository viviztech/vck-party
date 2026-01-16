/**
 * Election Filters Component
 * Filter component for election list
 */

import React, { useState } from 'react';
import { Input } from '@/components/Form/Input';
import { Select } from '@/components/Form/Select';
import { Button } from '@/components/Form/Button';
import type { ElectionFilters, ElectionStatus } from '@/services/votingService';
import { Search, Filter, X, Calendar } from 'lucide-react';

interface ElectionFiltersProps {
  filters: ElectionFilters;
  onFilterChange: (filters: ElectionFilters) => void;
  onSearch: (search: string) => void;
}

export function ElectionFilters({
  filters,
  onFilterChange,
  onSearch,
}: ElectionFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [localSearch, setLocalSearch] = useState(filters.search || '');

  const handleSearchChange = (value: string) => {
    setLocalSearch(value);
    if (value.length === 0 || value.length >= 2) {
      onSearch(value);
    }
  };

  const handleClearFilters = () => {
    onFilterChange({});
    setLocalSearch('');
  };

  const handleFilterChange = (key: keyof ElectionFilters, value: unknown) => {
    const newFilters = { ...filters, [key]: value };
    if (value === '' || value === undefined || (Array.isArray(value) && value.length === 0)) {
      delete newFilters[key];
    }
    onFilterChange(newFilters);
  };

  const statusOptions = [
    { value: '', label: 'All Status' },
    { value: 'draft', label: 'Draft' },
    { value: 'published', label: 'Published' },
    { value: 'nominations_open', label: 'Nominations Open' },
    { value: 'nominations_closed', label: 'Nominations Closed' },
    { value: 'voting_open', label: 'Voting Open' },
    { value: 'voting_closed', label: 'Voting Closed' },
    { value: 'results_published', label: 'Results Published' },
    { value: 'cancelled', label: 'Cancelled' },
  ];

  const hasFilters = Object.keys(filters).length > 0 || localSearch.length > 0;

  return (
    <div className="p-4 border-b border-gray-200 space-y-4">
      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <Input
            placeholder="Search elections by title..."
            value={localSearch}
            onChange={(e) => handleSearchChange(e.target.value)}
            leftIcon={<Search size={16} />}
          />
        </div>
        
        <Select
          placeholder="Status"
          options={statusOptions}
          value={filters.status?.[0] || ''}
          onChange={(value) => handleFilterChange('status', value ? [value as ElectionStatus] : undefined)}
          className="w-48"
        />

        <Button
          variant={showAdvanced ? 'secondary' : 'outline'}
          onClick={() => setShowAdvanced(!showAdvanced)}
          leftIcon={<Filter size={16} />}
        >
          Filters
        </Button>

        {hasFilters && (
          <Button variant="ghost" onClick={handleClearFilters} leftIcon={<X size={16} />}>
            Clear
          </Button>
        )}
      </div>

      {showAdvanced && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-gray-100">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
            <Input
              type="date"
              value={filters.from_date || ''}
              onChange={(e) => handleFilterChange('from_date', e.target.value || undefined)}
              leftIcon={<Calendar size={14} />}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
            <Input
              type="date"
              value={filters.to_date || ''}
              onChange={(e) => handleFilterChange('to_date', e.target.value || undefined)}
              leftIcon={<Calendar size={14} />}
            />
          </div>
          <Input
            placeholder="Unit ID"
            value={filters.unit_id || ''}
            onChange={(e) => handleFilterChange('unit_id', e.target.value || undefined)}
          />
          <Select
            placeholder="Upcoming Only"
            options={[
              { value: '', label: 'All' },
              { value: 'true', label: 'Upcoming' },
            ]}
            value={filters.upcoming?.toString() || ''}
            onChange={(value) => handleFilterChange('upcoming', value ? value === 'true' : undefined)}
          />
        </div>
      )}
    </div>
  );
}

export default ElectionFilters;
