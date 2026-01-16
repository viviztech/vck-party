/**
 * Voting Ballot Component
 * Ballot component for casting votes
 */

import React, { useState } from 'react';
import { RadioGroup } from '@/components/Form/Radio';
import { Button } from '@/components/Form/Button';
import { Card, CardContent, CardHeader } from '@/components/DataDisplay/Card';
import { Avatar } from '@/components/DataDisplay/Avatar';
import { Alert } from '@/components/Feedback/Alert';
import type { VoteCast } from '@/services/votingService';
import { CheckCircle, Lock } from 'lucide-react';

interface VotingBallotProps {
  positions: Array<{
    position_id: string;
    position_name: string;
    has_voted: boolean;
    candidates: Array<{
      candidate_id: string;
      member_name: string;
      photo_url?: string;
    }>;
  }>;
  onSubmit: (votes: VoteCast[]) => void;
  loading: boolean;
}

interface PositionVote {
  positionId: string;
  candidateId: string | null;
}

export function VotingBallot({ positions, onSubmit, loading }: VotingBallotProps) {
  const [votes, setVotes] = useState<Record<string, string>>({});
  const [showConfirm, setShowConfirm] = useState(false);

  const handleVoteChange = (positionId: string, value: string) => {
    setVotes((prev) => ({ ...prev, [positionId]: value }));
  };

  const allPositionsVoted = positions.every((p) => votes[p.position_id]);

  const handleSubmit = () => {
    const validVotes: VoteCast[] = Object.entries(votes)
      .filter(([_, candidateId]) => candidateId)
      .map(([positionId, candidateId]) => ({ candidate_id: candidateId }));
    onSubmit(validVotes);
  };

  return (
    <div className="space-y-6">
      <Alert variant="info" title="Secure Voting">
        <div className="flex items-center">
          <Lock size={16} className="mr-2" />
          Your vote is anonymous and secure. Once submitted, it cannot be changed.
        </div>
      </Alert>

      {positions.map((position) => {
        const candidateOptions = position.candidates.map((c) => ({
          value: c.candidate_id,
          label: c.member_name,
        }));

        const selectedCandidate = position.candidates.find(
          (c) => c.candidate_id === votes[position.position_id]
        );

        return (
          <Card key={position.position_id}>
            <CardHeader
              title={position.position_name}
              subtitle={position.has_voted ? 'Vote cast' : 'Select one candidate'}
            />
            <CardContent>
              <RadioGroup
                name={`position-${position.position_id}`}
                options={candidateOptions}
                value={votes[position.position_id] || ''}
                onChange={(value) => handleVoteChange(position.position_id, String(value))}
                orientation="vertical"
              />
              {selectedCandidate && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg flex items-center space-x-3">
                  <Avatar src={selectedCandidate.photo_url} name={selectedCandidate.member_name} size="md" />
                  <span className="font-medium">{selectedCandidate.member_name}</span>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}

      {positions.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <p className="text-gray-500">No positions available for voting</p>
          </CardContent>
        </Card>
      )}

      {showConfirm && (
        <Alert variant="warning" title="Confirm Your Vote">
          <p className="mb-4">Are you sure you want to cast this vote? This action cannot be undone.</p>
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowConfirm(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} loading={loading}>
              <CheckCircle size={16} className="mr-2" />
              Confirm Vote
            </Button>
          </div>
        </Alert>
      )}

      {!showConfirm && (
        <div className="flex justify-end">
          <Button
            onClick={() => setShowConfirm(true)}
            disabled={!allPositionsVoted || loading}
            loading={loading}
          >
            Submit Vote
          </Button>
        </div>
      )}
    </div>
  );
}

export default VotingBallot;
