/**
 * Districts List Page
 * Displays a list of all districts with search and filtering
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card, CardContent } from '@/components/DataDisplay/Card';
import { Input } from '@/components/Form/Input';
import { Button } from '@/components/Form/Button';
import { Pagination } from '@/components/Navigation/Pagination';
import { DistrictCard } from '../components/DistrictCard';
import { hierarchyService, type District, type PaginatedDistrictResponse } from '@/services/hierarchyService';
import { Search, Filter, Download, Plus } from 'lucide-react';

export function DistrictsListPage() {
  const navigate = useNavigate();
  const [districts, setDistricts] = useState<District[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('');

  const fetchDistricts = useCallback(async () => {
    setLoading(true);
    try {
      const response: PaginatedDistrictResponse = await hierarchyService.getDistricts({
        search: search || undefined,
        district_id: stateFilter || undefined,
        page,
        limit,
      });
      setDistricts(response.districts);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to fetch districts:', error);
    } finally {
      setLoading(false);
    }
  }, [search, stateFilter, page, limit]);

  useEffect(() => {
    fetchDistricts();
  }, [fetchDistricts]);

  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  const handleStateFilter = (value: string) => {
    setStateFilter(value);
    setPage(1);
  };

  const handleExport = async () => {
    try {
      const response = await hierarchyService.exportHierarchy('district', 'csv');
      window.open(response.file_url, '_blank');
    } catch (error) {
      console.error('Failed to export districts:', error);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Districts"
        description={`Manage and view all districts (${total} total)`}
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Hierarchy', href: '/hierarchy' },
          { label: 'Districts' },
        ]}
        actions={
          <div className="flex items-center space-x-3">
            <Button variant="outline" leftIcon={<Download size={16} />} onClick={handleExport}>
              Export
            </Button>
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/hierarchy/districts/new')}>
              Add District
            </Button>
          </div>
        }
      />

      <Card padding="sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex-1 max-w-md">
            <Input
              placeholder="Search districts..."
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              leftIcon={<Search size={16} />}
            />
          </div>
          <div className="flex items-center space-x-3">
            <Input
              placeholder="Filter by state..."
              value={stateFilter}
              onChange={(e) => handleStateFilter(e.target.value)}
              className="w-48"
            />
            <Button variant="outline" leftIcon={<Filter size={16} />}>
              More Filters
            </Button>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          Array.from({ length: 6 }).map((_, index) => (
            <Card key={index} className="animate-pulse">
              <CardContent className="h-32">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
                <div className="h-3 bg-gray-200 rounded w-1/3 mb-4" />
                <div className="h-3 bg-gray-200 rounded w-2/3" />
              </CardContent>
            </Card>
          ))
        ) : districts.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <p className="text-gray-500">No districts found</p>
            <Button
              variant="link"
              onClick={() => navigate('/hierarchy/districts/new')}
              className="mt-2"
            >
              Add your first district
            </Button>
          </div>
        ) : (
          districts.map((district) => (
            <DistrictCard key={district.id} district={district} />
          ))
        )}
      </div>

      {total > limit && (
        <Pagination
          currentPage={page}
          totalPages={Math.ceil(total / limit)}
          onPageChange={setPage}
          showingText={`Showing ${((page - 1) * limit) + 1} to ${Math.min(page * limit, total)} of ${total} districts`}
        />
      )}
    </div>
  );
}

export default DistrictsListPage;
