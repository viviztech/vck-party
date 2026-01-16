/**
 * Election Detail Page
 * View detailed election information
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/Form/Button';
import { Tabs } from '@/components/DataDisplay/Tabs';
import { Card, CardContent, CardHeader } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { votingService, ElectionDetail, ElectionResults } from '@/services/votingService';
import { formatDate } from '@/utils/helpers';
import {
  ArrowLeft, Calendar, Edit, Trash2, BarChart2, UserPlus, Vote, CheckCircle, XCircle
} from 'lucide-react';
import { ElectionResults as ElectionResultsComponent } from '../components/ElectionResults';

export function ElectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [election, setElection] = useState<ElectionDetail | null>(null);
  const [results, setResults] = useState<ElectionResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchElection = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const electionData = await votingService.getElection(id);
      setElection(electionData);

      if (electionData.status === 'results_published' || electionData.status === 'results_calculated') {
        try {
          const resultsData = await votingService.getElectionResults(id);
          setResults(resultsData);
        } catch {
          // Results not yet available
        }
      }
    } catch (error) {
      console.error('Failed to fetch election:', error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchElection();
  }, [fetchElection]);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      draft: { variant: 'default', label: 'Draft' },
      published: { variant: 'info', label: 'Published' },
      nominations_open: { variant: 'success', label: 'Nominations Open' },
      nominations_closed: { variant: 'warning', label: 'Nominations Closed' },
      voting_open: { variant: 'success', label: 'Voting Open' },
      voting_closed: { variant: 'warning', label: 'Voting Closed' },
      results_calculated: { variant: 'info', label: 'Results Calculated' },
      results_published: { variant: 'success', label: 'Results Published' },
      cancelled: { variant: 'error', label: 'Cancelled' },
    };
    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const handlePublish = async () => {
    if (!id) return;
    try {
      await votingService.publishElection(id);
      fetchElection();
    } catch (error) {
      console.error('Failed to publish election:', error);
    }
  };

  const handleOpenNominations = async () => {
    if (!id) return;
    try {
      await votingService.openNominations(id);
      fetchElection();
    } catch (error) {
      console.error('Failed to open nominations:', error);
    }
  };

  const handleStartVoting = async () => {
    if (!id) return;
    try {
      await votingService.startVoting(id);
      fetchElection();
    } catch (error) {
      console.error('Failed to start voting:', error);
    }
  };

  const handleEndVoting = async () => {
    if (!id) return;
    try {
      await votingService.endVoting(id);
      fetchElection();
    } catch (error) {
      console.error('Failed to end voting:', error);
    }
  };

  const handlePublishResults = async () => {
    if (!id) return;
    try {
      await votingService.publishResults(id);
      fetchElection();
    } catch (error) {
      console.error('Failed to publish results:', error);
    }
  };

  const handleDelete = async () => {
    if (!id || !window.confirm('Are you sure you want to delete this election?')) return;
    try {
      await votingService.deleteElection(id);
      navigate('/elections');
    } catch (error) {
      console.error('Failed to delete election:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!election) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Election not found</p>
        <Button variant="outline" onClick={() => navigate('/elections')} className="mt-4">
          Back to Elections
        </Button>
      </div>
    );
  }

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'candidates', label: 'Candidates' },
    { key: 'voters', label: 'Voters' },
    { key: 'results', label: 'Results' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/elections')}>
          <ArrowLeft size={16} />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{election.title}</h1>
          <p className="text-gray-500">{election.description}</p>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusBadge(election.status)}
          <Button variant="outline" onClick={() => navigate(`/elections/${election.id}/edit`)}>
            <Edit size={16} />
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            <Trash2 size={16} />
          </Button>
        </div>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} variant="underline" />

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader title="Timeline" />
            <CardContent className="space-y-4">
              <div className="flex items-center text-sm">
                <Calendar size={14} className="mr-2 text-gray-500" />
                <span className="text-gray-500 mr-2">Nominations:</span>
                <span>
                  {election.nominations_start && formatDate(election.nominations_start)}
                  {election.nominations_end && ` - ${formatDate(election.nominations_end)}`}
                </span>
              </div>
              <div className="flex items-center text-sm">
                <Vote size={14} className="mr-2 text-gray-500" />
                <span className="text-gray-500 mr-2">Voting:</span>
                <span>
                  {formatDate(election.voting_start)} - {formatDate(election.voting_end)}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader title="Statistics" />
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Positions</span>
                <span className="font-medium">{election.positions_count}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Candidates</span>
                <span className="font-medium">{election.candidates_count}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Nominations</span>
                <span className="font-medium">{election.nominations_count}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Total Votes</span>
                <span className="font-medium">{election.total_votes}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader title="Settings" />
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Secret Voting</span>
                {election.is_secret_voting ? (
                  <CheckCircle size={16} className="text-green-500" />
                ) : (
                  <XCircle size={16} className="text-gray-400" />
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Verified Voter ID</span>
                {election.require_verified_voter_id ? (
                  <CheckCircle size={16} className="text-green-500" />
                ) : (
                  <XCircle size={16} className="text-gray-400" />
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'overview' && election.status === 'draft' && (
        <div className="flex justify-end space-x-3">
          <Button onClick={handlePublish}>Publish Election</Button>
        </div>
      )}

      {activeTab === 'overview' && election.status === 'published' && (
        <div className="flex justify-end space-x-3">
          <Button onClick={handleOpenNominations} leftIcon={<UserPlus size={16} />}>
            Open Nominations
          </Button>
        </div>
      )}

      {activeTab === 'overview' && election.status === 'nominations_closed' && (
        <div className="flex justify-end space-x-3">
          <Button onClick={handleStartVoting} leftIcon={<Vote size={16} />}>
            Start Voting
          </Button>
        </div>
      )}

      {activeTab === 'overview' && election.status === 'voting_closed' && (
        <div className="flex justify-end space-x-3">
          <Button onClick={handlePublishResults} leftIcon={<BarChart2 size={16} />}>
            Publish Results
          </Button>
        </div>
      )}

      {activeTab === 'candidates' && (
        <Card>
          <CardHeader title="Candidates" action={<Button size="sm">Add Candidate</Button>} />
          <CardContent>
            <p className="text-gray-500 text-center py-8">Candidates will be listed here after nominations close</p>
          </CardContent>
        </Card>
      )}

      {activeTab === 'voters' && (
        <Card>
          <CardHeader title="Voters" />
          <CardContent>
            <p className="text-gray-500 text-center py-8">Voters list will be available during voting period</p>
          </CardContent>
        </Card>
      )}

      {activeTab === 'results' && (
        <div>
          {results ? (
            <ElectionResultsComponent results={results} />
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <BarChart2 size={48} className="mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">Results not yet available</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

export default ElectionDetailPage;
