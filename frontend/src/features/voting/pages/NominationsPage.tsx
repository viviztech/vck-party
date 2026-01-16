/**
 * Nominations Page
 * Manage nominations for an election
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/Form/Button';
import { Card, CardContent, CardHeader } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { Avatar } from '@/components/DataDisplay/Avatar';
import { Tabs } from '@/components/DataDisplay/Tabs';
import { votingService, Nomination, ElectionPosition } from '@/services/votingService';
import { formatDate } from '@/utils/helpers';
import { CheckCircle, XCircle, Clock, User } from 'lucide-react';

export function NominationsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [nominations, setNominations] = useState<Nomination[]>([]);
  const [positions, setPositions] = useState<ElectionPosition[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pending');

  const fetchData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [nominationsData, positionsData] = await Promise.all([
        votingService.getNominations(id),
        votingService.getElectionPositions(id),
      ]);
      setNominations(nominationsData.nominations);
      setPositions(positionsData);
    } catch (error) {
      console.error('Failed to fetch nominations:', error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleApprove = async (nominationId: string) => {
    if (!id) return;
    try {
      await votingService.processNomination(id, nominationId, { approved: true });
      fetchData();
    } catch (error) {
      console.error('Failed to approve nomination:', error);
    }
  };

  const handleReject = async (nominationId: string) => {
    if (!id) return;
    const reason = window.prompt('Please provide a reason for rejection:');
    if (reason === null) return;
    try {
      await votingService.processNomination(id, nominationId, { approved: false, rejection_reason: reason });
      fetchData();
    } catch (error) {
      console.error('Failed to reject nomination:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      pending: { variant: 'warning', label: 'Pending' },
      approved: { variant: 'success', label: 'Approved' },
      rejected: { variant: 'error', label: 'Rejected' },
      withdrawn: { variant: 'default', label: 'Withdrawn' },
    };
    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const pendingNominations = nominations.filter((n) => n.status === 'pending');
  const approvedNominations = nominations.filter((n) => n.status === 'approved');
  const rejectedNominations = nominations.filter((n) => n.status === 'rejected');

  const tabs = [
    { key: 'pending', label: `Pending (${pendingNominations.length})` },
    { key: 'approved', label: `Approved (${approvedNominations.length})` },
    { key: 'rejected', label: `Rejected (${rejectedNominations.length})` },
  ];

  const displayedNominations = activeTab === 'pending' 
    ? pendingNominations 
    : activeTab === 'approved' 
    ? approvedNominations 
    : rejectedNominations;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Nominations</h1>
          <p className="text-gray-500">Review and manage nomination applications</p>
        </div>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} variant="underline" />

      <div className="space-y-4">
        {displayedNominations.map((nomination) => (
          <Card key={nomination.id}>
            <CardContent>
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <Avatar
                    src={nomination.member_photo_url}
                    name={nomination.member_name || 'Member'}
                    size="lg"
                  />
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold text-gray-900">{nomination.member_name}</h3>
                      {getStatusBadge(nomination.status)}
                    </div>
                    <p className="text-sm text-gray-500">{nomination.position_name}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Nominated on {formatDate(nomination.nominated_at)}
                    </p>
                    {nomination.manifesto && (
                      <p className="text-sm text-gray-600 mt-2">{nomination.manifesto}</p>
                    )}
                    {nomination.rejection_reason && (
                      <p className="text-sm text-red-500 mt-2">
                        Rejection reason: {nomination.rejection_reason}
                      </p>
                    )}
                  </div>
                </div>
                {activeTab === 'pending' && (
                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleReject(nomination.id)}
                      leftIcon={<XCircle size={14} />}
                    >
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleApprove(nomination.id)}
                      leftIcon={<CheckCircle size={14} />}
                    >
                      Approve
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}

        {displayedNominations.length === 0 && (
          <Card>
            <CardContent className="text-center py-12">
              <User size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">No {activeTab} nominations</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default NominationsPage;
