/**
 * Election Form Component
 * Form for creating and editing elections
 */

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Input } from '@/components/Form/Input';
import { Textarea } from '@/components/Form/Textarea';
import { Checkbox } from '@/components/Form/Checkbox';
import { Button } from '@/components/Form/Button';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/DataDisplay/Card';
import type { Election } from '@/services/votingService';

interface ElectionFormProps {
  election?: Election;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
}

export function ElectionForm({ election, onSubmit, onCancel }: ElectionFormProps) {
  const isEditing = !!election;
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm();

  useEffect(() => {
    if (election) {
      reset({
        title: election.title,
        description: election.description || '',
        voting_start: election.voting_start.split('T')[0],
        voting_end: election.voting_end.split('T')[0],
        nominations_start: election.nominations_start?.split('T')[0] || '',
        nominations_end: election.nominations_end?.split('T')[0] || '',
        is_secret_voting: election.is_secret_voting,
        require_verified_voter_id: election.require_verified_voter_id,
      });
    }
  }, [election, reset]);

  const onFormSubmit = async (data: Record<string, unknown>) => {
    const submitData = {
      ...data,
      voting_start: new Date(data.voting_start as string).toISOString(),
      voting_end: new Date(data.voting_end as string).toISOString(),
      nominations_start: data.nominations_start 
        ? new Date(data.nominations_start as string).toISOString() 
        : undefined,
      nominations_end: data.nominations_end 
        ? new Date(data.nominations_end as string).toISOString() 
        : undefined,
      is_secret_voting: data.is_secret_voting === true,
      require_verified_voter_id: data.require_verified_voter_id === true,
    };
    if (isEditing && election) {
      (submitData as Record<string, unknown>).id = election.id;
    }
    await onSubmit(submitData);
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)}>
      <Card>
        <CardHeader title={isEditing ? 'Edit Election' : 'New Election'} />
        <CardContent>
          <div className="space-y-4">
            <Input
              label="Title *"
              {...register('title', { required: 'Title is required' })}
              error={errors.title?.message as string}
            />
            <Textarea
              label="Description"
              {...register('description')}
              rows={4}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Nominations Start Date"
                type="date"
                {...register('nominations_start')}
              />
              <Input
                label="Nominations End Date"
                type="date"
                {...register('nominations_end')}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Voting Start Date *"
                type="date"
                {...register('voting_start', { required: 'Voting start date is required' })}
                error={errors.voting_start?.message as string}
              />
              <Input
                label="Voting End Date *"
                type="date"
                {...register('voting_end', { required: 'Voting end date is required' })}
                error={errors.voting_end?.message as string}
              />
            </div>
            <div className="space-y-3">
              <Checkbox
                label="Secret Voting"
                {...register('is_secret_voting')}
                defaultChecked
              />
              <Checkbox
                label="Require Verified Voter ID"
                {...register('require_verified_voter_id')}
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end space-x-3">
          <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
          <Button type="submit" loading={isSubmitting}>
            {isEditing ? 'Update Election' : 'Create Election'}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}

export default ElectionForm;
