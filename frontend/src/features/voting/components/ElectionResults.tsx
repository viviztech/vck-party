/**
 * Election Results Component
 * Displays election results with visualizations
 */

import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/DataDisplay/Card';
import { Progress } from '@/components/DataDisplay/Progress';
import { Avatar } from '@/components/DataDisplay/Avatar';
import { Badge } from '@/components/DataDisplay/Badge';
import type { ElectionResults, ElectionResultPosition } from '@/services/votingService';
import { Trophy } from 'lucide-react';

interface ElectionResultsProps {
  results: ElectionResults;
}

export function ElectionResults({ results }: ElectionResultsProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="text-center py-6">
            <p className="text-3xl font-bold text-gray-900">{results.total_voters}</p>
            <p className="text-sm text-gray-500">Total Voters</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="text-center py-6">
            <p className="text-3xl font-bold text-gray-900">{results.total_votes_cast}</p>
            <p className="text-sm text-gray-500">Votes Cast</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="text-center py-6">
            <p className="text-3xl font-bold text-gray-900">{results.turnout_percentage.toFixed(1)}%</p>
            <p className="text-sm text-gray-500">Turnout</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="text-center py-6">
            <p className="text-3xl font-bold text-gray-900">{results.positions.length}</p>
            <p className="text-sm text-gray-500">Positions</p>
          </CardContent>
        </Card>
      </div>

      {results.positions.map((position) => (
        <PositionResults key={position.position_id} position={position} />
      ))}

      {results.results_published_at && (
        <p className="text-sm text-gray-500 text-center">
          Results published on {new Date(results.results_published_at).toLocaleString()}
        </p>
      )}
    </div>
  );
}

interface PositionResultsProps {
  position: ElectionResultPosition;
}

function PositionResults({ position }: PositionResultsProps) {
  const maxVotes = Math.max(...position.candidates.map((c) => c.votes_received), 1);

  const getWinnerBadge = (isWinner: boolean) => {
    if (!isWinner) return null;
    return (
      <Badge variant="success" size="sm">
        <Trophy size={12} className="mr-1" />
        Winner
      </Badge>
    );
  };

  const getMethodLabel = (method: string) => {
    const labels: Record<string, string> = {
      fptp: 'First Past The Post',
      ranked: 'Ranked Choice',
      approval: 'Approval Voting',
      preferential: 'Preferential Voting',
    };
    return labels[method] || method;
  };

  return (
    <Card>
      <CardHeader
        title={position.position_name}
        subtitle={`${getMethodLabel(position.voting_method)} • ${position.seats_available} seat(s) available`}
      />
      <CardContent>
        <div className="space-y-4">
          {position.candidates
            .sort((a, b) => a.rank - b.rank)
            .map((candidate) => (
              <div key={candidate.candidate_id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Avatar
                      src={candidate.member_photo_url}
                      name={candidate.member_name}
                      size="md"
                    />
                    <div>
                      <div className="flex items-center space-x-2">
                        <p className="font-medium text-gray-900">{candidate.member_name}</p>
                        {getWinnerBadge(candidate.is_winner)}
                      </div>
                      <p className="text-sm text-gray-500">
                        Rank {candidate.rank} • {candidate.votes_received} votes
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">{candidate.percentage.toFixed(1)}%</p>
                  </div>
                </div>
                <Progress
                  value={(candidate.votes_received / maxVotes) * 100}
                  variant={candidate.is_winner ? 'success' : 'default'}
                />
              </div>
            ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default ElectionResults;
