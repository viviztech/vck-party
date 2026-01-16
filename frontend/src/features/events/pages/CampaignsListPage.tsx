/**
 * Campaigns List Page
 * Lists all campaigns
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/Form/Button';
import { Card, CardContent } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { Input } from '@/components/Form/Input';
import { eventsService, Campaign } from '@/services/eventsService';
import { formatDate } from '@/utils/helpers';
import { Plus, Search } from 'lucide-react';

export function CampaignsListPage() {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchCampaigns = useCallback(async () => {
    setLoading(true);
    try {
      const response = await eventsService.getCampaigns({ search: search || undefined });
      setCampaigns(response.campaigns);
    } catch (error) {
      console.error('Failed to fetch campaigns:', error);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      planning: { variant: 'default', label: 'Planning' },
      active: { variant: 'success', label: 'Active' },
      paused: { variant: 'warning', label: 'Paused' },
      completed: { variant: 'info', label: 'Completed' },
    };
    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
          <p className="text-gray-500">Manage campaigns and initiatives</p>
        </div>
        <Button onClick={() => navigate('/campaigns/new')} leftIcon={<Plus size={16} />}>
          New Campaign
        </Button>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <Input
            placeholder="Search campaigns..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search size={16} />}
          />
        </div>
      </div>

      {campaigns.length === 0 && !loading ? (
        <div className="text-center py-12 text-gray-500">
          <p>No campaigns found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {campaigns.map((campaign) => (
            <Card
              key={campaign.id}
              hover
              onClick={() => navigate(`/campaigns/${campaign.id}`)}
              className="cursor-pointer"
            >
              <CardContent className="space-y-4">
                <div className="flex items-start justify-between">
                  <h3 className="font-semibold text-gray-900">{campaign.name}</h3>
                  {getStatusBadge(campaign.status)}
                </div>
                <p className="text-sm text-gray-600 line-clamp-2">{campaign.description}</p>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>{formatDate(campaign.start_date)} - {formatDate(campaign.end_date)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>{campaign.events_count || 0} events</span>
                  <span>{campaign.total_attendees || 0} attendees</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default CampaignsListPage;
