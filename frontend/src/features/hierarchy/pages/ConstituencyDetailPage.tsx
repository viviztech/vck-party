/**
 * Constituency Detail Page
 * View constituency details with wards
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card, CardContent, CardHeader } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { HierarchyBreadcrumb } from '../components/HierarchyBreadcrumb';
import { WardCard } from '../components/WardCard';
import { hierarchyService, type Constituency, type ConstituencyDetail, type District } from '@/services/hierarchyService';
import { Building2, Users, MapPin, Edit, Trash2, Plus } from 'lucide-react';

export function ConstituencyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [constituency, setConstituency] = useState<ConstituencyDetail | null>(null);
  const [district, setDistrict] = useState<District | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const data = await hierarchyService.getConstituencyDetail(id);
        setConstituency(data);
        setDistrict(data.district);
      } catch (err) {
        setError('Failed to load constituency');
        console.error('Failed to fetch constituency:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-2" />
          <div className="h-4 bg-gray-200 rounded w-1/4" />
        </div>
        <Card>
          <CardContent><div className="h-48 bg-gray-200 rounded animate-pulse" /></CardContent>
        </Card>
      </div>
    );
  }

  if (error || !constituency) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error || 'Constituency not found'}</p>
        <button
          onClick={() => navigate('/hierarchy/constituencies')}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          Back to Constituencies
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <HierarchyBreadcrumb district={district} constituency={constituency} />

      <PageHeader
        title={constituency.name}
        description={`Constituency code: ${constituency.code}`}
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Hierarchy', href: '/hierarchy' },
          { label: 'Constituencies', href: '/hierarchy/constituencies' },
          { label: constituency.name },
        ]}
        actions={
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate(`/hierarchy/constituencies/${constituency.id}/edit`)}
              className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Edit size={16} className="mr-2" />
              Edit
            </button>
            <button
              onClick={() => {
                if (window.confirm('Are you sure you want to delete this constituency?')) {
                  hierarchyService.deleteConstituency(constituency.id).then(() => {
                    navigate('/hierarchy/constituencies');
                  });
                }
              }}
              className="flex items-center px-3 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
            >
              <Trash2 size={16} className="mr-2" />
              Delete
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="flex items-center space-x-4">
            <div className="p-3 bg-indigo-100 rounded-full">
              <Building2 className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Type</p>
              <Badge variant="info" className="mt-1">
                {constituency.constituency_type}
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center space-x-4">
            <div className="p-3 bg-purple-100 rounded-full">
              <MapPin className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Wards</p>
              <p className="text-lg font-semibold text-gray-900">{constituency.wards_count}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center space-x-4">
            <div className="p-3 bg-emerald-100 rounded-full">
              <Users className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Electorate</p>
              <p className="text-lg font-semibold text-gray-900">
                {(constituency.electorate_count || 0).toLocaleString()}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center space-x-4">
            <div className="p-3 bg-gray-100 rounded-full">
              <MapPin className="w-6 h-6 text-gray-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">District</p>
              <p className="text-lg font-semibold text-gray-900">{district?.name}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {constituency.name_ta && (
        <Card>
          <CardHeader title="Local Name" />
          <CardContent>
            <p className="text-lg font-medium text-gray-900">{constituency.name_ta}</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader
          title="Wards"
          subtitle={`${constituency.wards?.length || 0} wards in this constituency`}
          action={
            <button
              onClick={() => navigate(`/hierarchy/wards/new?constituency_id=${constituency.id}`)}
              className="flex items-center text-sm text-blue-600 hover:text-blue-700"
            >
              <Plus size={16} className="mr-1" />
              Add Ward
            </button>
          }
        />
        <CardContent padding="none">
          {constituency.wards && constituency.wards.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
              {constituency.wards.map((ward) => (
                <WardCard key={ward.id} ward={ward} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No wards found</p>
              <button
                onClick={() => navigate(`/hierarchy/wards/new?constituency_id=${constituency.id}`)}
                className="mt-2 text-blue-600 hover:text-blue-700"
              >
                Add the first ward
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ConstituencyDetailPage;
