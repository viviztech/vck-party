/**
 * District Detail Page
 * View district details with constituencies
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card, CardContent, CardHeader } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { HierarchyBreadcrumb } from '../components/HierarchyBreadcrumb';
import { ConstituencyCard } from '../components/ConstituencyCard';
import { hierarchyService, type District, type DistrictDetail } from '@/services/hierarchyService';
import { MapPin, Building2, Users, Edit, Trash2, Plus } from 'lucide-react';

export function DistrictDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [district, setDistrict] = useState<DistrictDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDistrict = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const data = await hierarchyService.getDistrictDetail(id);
        setDistrict(data);
      } catch (err) {
        setError('Failed to load district');
        console.error('Failed to fetch district:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDistrict();
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-2" />
          <div className="h-4 bg-gray-200 rounded w-1/4" />
        </div>
        <Card>
          <CardContent className="h-48 animate-pulse" />
        </Card>
      </div>
    );
  }

  if (error || !district) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error || 'District not found'}</p>
        <button
          onClick={() => navigate('/hierarchy/districts')}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          Back to Districts
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <HierarchyBreadcrumb district={district} />

      <PageHeader
        title={district.name}
        description={`District code: ${district.code}`}
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Hierarchy', href: '/hierarchy' },
          { label: 'Districts', href: '/hierarchy/districts' },
          { label: district.name },
        ]}
        actions={
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate(`/hierarchy/districts/${district.id}/edit`)}
              className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Edit size={16} className="mr-2" />
              Edit
            </button>
            <button
              onClick={() => {
                if (window.confirm('Are you sure you want to delete this district?')) {
                  hierarchyService.deleteDistrict(district.id).then(() => {
                    navigate('/hierarchy/districts');
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="flex items-center space-x-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <MapPin className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">State</p>
              <p className="text-lg font-semibold text-gray-900">{district.state}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center space-x-4">
            <div className="p-3 bg-indigo-100 rounded-full">
              <Building2 className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Constituencies</p>
              <p className="text-lg font-semibold text-gray-900">{district.constituencies_count}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center space-x-4">
            <div className="p-3 bg-emerald-100 rounded-full">
              <Users className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <Badge variant={district.is_active ? 'success' : 'default'}>
                {district.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {district.name_ta && (
        <Card>
          <CardHeader title="Local Name" />
          <CardContent>
            <p className="text-lg font-medium text-gray-900">{district.name_ta}</p>
          </CardContent>
        </Card>
      )}

      {(district.latitude || district.longitude) && (
        <Card>
          <CardHeader title="Location" />
          <CardContent>
            <p className="text-sm text-gray-500">
              Lat: {district.latitude}, Lng: {district.longitude}
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader
          title="Constituencies"
          subtitle={`${district.constituencies?.length || 0} constituencies in this district`}
          action={
            <button
              onClick={() => navigate(`/hierarchy/constituencies/new?district_id=${district.id}`)}
              className="flex items-center text-sm text-blue-600 hover:text-blue-700"
            >
              <Plus size={16} className="mr-1" />
              Add Constituency
            </button>
          }
        />
        <CardContent padding="none">
          {district.constituencies && district.constituencies.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
              {district.constituencies.map((constituency) => (
                <ConstituencyCard key={constituency.id} constituency={constituency} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No constituencies found</p>
              <button
                onClick={() => navigate(`/hierarchy/constituencies/new?district_id=${district.id}`)}
                className="mt-2 text-blue-600 hover:text-blue-700"
              >
                Add the first constituency
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default DistrictDetailPage;
