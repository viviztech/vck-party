/**
 * Member Filters Component
 * Filter component for member list
 */

import React, { useState } from 'react';
import { Input } from '@/components/Form/Input';
import { Select } from '@/components/Form/Select';
import { Button } from '@/components/Form/Button';
import type { MemberFilters } from '@/services/membersService';
import { Search, Filter, X, Trash2 } from 'lucide-react';

interface MemberFiltersProps {
  filters: MemberFilters;
  onFilterChange: (filters: MemberFilters) => void;
  onSearch: (search: string) => void;
  selectedCount: number;
  onBulkDelete: () => void;
}

export function MemberFilters({
  filters,
  onFilterChange,
  onSearch,
  selectedCount,
  onBulkDelete,
}: MemberFiltersProps) {
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

  const handleFilterChange = (key: keyof MemberFilters, value: unknown) => {
    const newFilters = { ...filters, [key]: value };
    if (value === '') {
      delete newFilters[key];
    }
    onFilterChange(newFilters);
  };

  const statusOptions = [
    { value: '', label: 'All Status' },
    { value: 'active', label: 'Active' },
    { value: 'pending', label: 'Pending' },
    { value: 'suspended', label: 'Suspended' },
    { value: 'inactive', label: 'Inactive' },
  ];

  const genderOptions = [
    { value: '', label: 'All Genders' },
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'other', label: 'Other' },
  ];

  const membershipTypeOptions = [
    { value: '', label: 'All Types' },
    { value: 'regular', label: 'Regular' },
    { value: 'life', label: 'Life Member' },
    { value: 'honorary', label: 'Honorary' },
    { value: 'founder', label: 'Founder' },
  ];

  const hasFilters = Object.keys(filters).length > 0 || localSearch.length > 0;

  return (
    <div className="p-4 border-b border-gray-200 space-y-4">
      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <Input
            placeholder="Search by name, phone, email, or voter ID..."
            value={localSearch}
            onChange={(e) => handleSearchChange(e.target.value)}
            leftIcon={<Search size={16} />}
          />
        </div>
        
        <Select
          placeholder="Status"
          options={statusOptions}
          value={filters.status?.[0] || ''}
          onChange={(value) => handleFilterChange('status', value ? [value] : undefined)}
          className="w-40"
        />

        <Select
          placeholder="Gender"
          options={genderOptions}
          value={filters.gender || ''}
          onChange={(value) => handleFilterChange('gender', value || undefined)}
          className="w-40"
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

        {selectedCount > 0 && (
          <Button variant="danger" onClick={onBulkDelete} leftIcon={<Trash2 size={16} />}>
            Delete ({selectedCount})
          </Button>
        )}
      </div>

      {showAdvanced && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-gray-100">
          <Input
            placeholder="District"
            value={filters.district || ''}
            onChange={(e) => handleFilterChange('district', e.target.value || undefined)}
          />
          <Input
            placeholder="Constituency"
            value={filters.constituency || ''}
            onChange={(e) => handleFilterChange('constituency', e.target.value || undefined)}
          />
          <Input
            placeholder="Ward"
            value={filters.ward || ''}
            onChange={(e) => handleFilterChange('ward', e.target.value || undefined)}
          />
          <Select
            placeholder="Membership Type"
            options={membershipTypeOptions}
            value={filters.membership_type?.[0] || ''}
            onChange={(value) => handleFilterChange('membership_type', value ? [value] : undefined)}
          />
        </div>
      )}
    </div>
  );
}

export default MemberFilters;
