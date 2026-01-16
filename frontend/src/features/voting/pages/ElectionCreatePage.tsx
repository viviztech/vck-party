/**
 * Election Create Page
 * Create a new election
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ElectionForm } from '../components/ElectionForm';
import { votingService, Election } from '@/services/votingService';

export function ElectionCreatePage() {
  const navigate = useNavigate();

  const handleSubmit = async (data: Record<string, unknown>) => {
    try {
      const election = await votingService.createElection(data as Partial<Election>);
      navigate(`/elections/${election.id}`);
    } catch (error) {
      console.error('Failed to create election:', error);
      throw error;
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <ElectionForm onSubmit={handleSubmit} onCancel={() => navigate('/elections')} />
    </div>
  );
}

export default ElectionCreatePage;
