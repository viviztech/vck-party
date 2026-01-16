/**
 * Event Filters Component
 * Filter component for event list
 */

import React, { useState } from 'react';
import { Input } from '@/components/Form/Input';
import { Select } from '@/components/Form/Select';
import { Button } from '@/components/Form/Button';
import type { EventFilters, EventType, EventStatus } from '@/services/eventsService';
import { Search, Filter, X, Calendar, MapPin } from 'lucide-react';

interface EventFiltersProps {
  filters: EventFilters;
  onFilterChange: (filters: EventFilters) => void;
  onSearch: (search: string) => void;
}

export function EventFilters({
  filters,
  onFilterChange,
  onSearch,
}: EventFiltersProps) {
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

  const handleFilterChange = (key: keyof EventFilters, value: unknown) => {
    const newFilters = { ...filters, [key]: value };
    if (value === '' || value === undefined || (Array.isArray(value) && value.length === 0)) {
      delete newFilters[key];
    }
    onFilterChange(newFilters);
  };

  const eventTypeOptions = [
    { value: '', label: 'All Types' },
    { value: 'meeting', label: 'Meeting' },
    { value: 'rally', label: 'Rally' },
    { value: 'campaign', label: 'Campaign' },
    { value: 'conference', label: 'Conference' },
    { value: 'workshop', label: 'Workshop' },
    { value: 'training', label: 'Training' },
    { value: 'volunteer', label: 'Volunteer' },
    { value: 'fundraiser', label: 'Fundraiser' },
    { value: 'awareness', label: 'Awareness' },
    { value: 'visit', label: 'Visit' },
    { value: 'inauguration', label: 'Inauguration' },
    { value: 'other', label: 'Other' },
  ];

  const statusOptions = [
    { value: '', label: 'All Status' },
    { value: 'draft', label: 'Draft' },
    { value: 'published', label: 'Published' },
    { value: 'cancelled', label: 'Cancelled' },
    { value: 'completed', label: 'Completed' },
    { value: 'postponed', label: 'Postponed' },
    { value: 'in_progress', label: 'In Progress' },
  ];

  const hasFilters = Object.keys(filters).length > 0 || localSearch.length > 0;

  return (
    <div className="p-4 border-b border-gray-200 space-y-4">
      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <Input
            placeholder="Search events by title, description..."
            value={localSearch}
            onChange={(e) => handleSearchChange(e.target.value)}
            leftIcon={<Search size={16} />}
          />
        </div>
        
        <Select
          placeholder="Event Type"
          options={eventTypeOptions}
          value={filters.event_type?.[0] || ''}
          onChange={(value) => handleFilterChange('event_type', value ? [value as EventType] : undefined)}
          className="w-40"
        />

        <Select
          placeholder="Status"
          options={statusOptions}
          value={filters.status?.[0] || ''}
          onChange={(value) => handleFilterChange('status', value ? [value as EventStatus] : undefined)}
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
            placeholder="District"
            value={filters.district || ''}
            onChange={(e) => handleFilterChange('district', e.target.value || undefined)}
            leftIcon={<MapPin size={14} />}
          />
          <Input
            placeholder="Constituency"
            value={filters.constituency || ''}
            onChange={(e) => handleFilterChange('constituency', e.target.value || undefined)}
          />
        </div>
      )}
    </div>
  );
}

export default EventFilters;
