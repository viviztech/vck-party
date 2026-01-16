/**
 * Event Form Component
 * Form for creating and editing events
 */

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Input } from '@/components/Form/Input';
import { Select } from '@/components/Form/Select';
import { Textarea } from '@/components/Form/Textarea';
import { Button } from '@/components/Form/Button';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/DataDisplay/Card';
import type { Event, EventType } from '@/services/eventsService';

interface EventFormProps {
  event?: Event;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
}

export function EventForm({ event, onSubmit, onCancel }: EventFormProps) {
  const isEditing = !!event;
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm();

  useEffect(() => {
    if (event) {
      reset({
        title: event.title,
        event_type: event.event_type,
        start_date: event.start_date,
        end_date: event.end_date,
        start_time: event.start_time || '',
        end_time: event.end_time || '',
        venue: event.venue || '',
        district: event.district || '',
        expected_attendees: event.expected_attendees || '',
      });
    }
  }, [event, reset]);

  const onFormSubmit = async (data: Record<string, unknown>) => {
    const submitData = {
      ...data,
      event_type: data.event_type as EventType,
      expected_attendees: data.expected_attendees ? Number(data.expected_attendees) : undefined,
    };
    if (isEditing && event) {
      (submitData as Record<string, unknown>).id = event.id;
    }
    await onSubmit(submitData);
  };

  const eventTypeOptions = [
    { value: 'meeting', label: 'Meeting' },
    { value: 'rally', label: 'Rally' },
    { value: 'campaign', label: 'Campaign' },
    { value: 'conference', label: 'Conference' },
    { value: 'workshop', label: 'Workshop' },
    { value: 'training', label: 'Training' },
    { value: 'volunteer', label: 'Volunteer' },
    { value: 'fundraiser', label: 'Fundraiser' },
    { value: 'awareness', label: 'Awareness' },
    { value: 'visit', label: 'Visit' },
    { value: 'inauguration', label: 'Inauguration' },
    { value: 'other', label: 'Other' },
  ];

  return (
    <form onSubmit={handleSubmit(onFormSubmit)}>
      <Card>
        <CardHeader title={isEditing ? 'Edit Event' : 'New Event'} />
        <CardContent>
          <div className="space-y-4">
            <Input
              label="Title *"
              {...register('title', { required: 'Title is required' })}
              error={errors.title?.message as string}
            />
            <Select
              label="Event Type *"
              options={eventTypeOptions}
              value={event?.event_type || 'meeting'}
              onChange={(value) => {}}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Start Date *"
                type="date"
                {...register('start_date', { required: true })}
                error={errors.start_date?.message as string}
              />
              <Input
                label="End Date *"
                type="date"
                {...register('end_date', { required: true })}
                error={errors.end_date?.message as string}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Start Time"
                type="time"
                {...register('start_time')}
              />
              <Input
                label="End Time"
                type="time"
                {...register('end_time')}
              />
            </div>
            <Input
              label="Venue"
              {...register('venue')}
            />
            <Input
              label="District"
              {...register('district')}
            />
            <Input
              label="Expected Attendees"
              type="number"
              {...register('expected_attendees')}
            />
            <Textarea
              label="Description"
              {...register('description')}
              rows={4}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-end space-x-3">
          <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
          <Button type="submit" loading={isSubmitting}>
            {isEditing ? 'Update Event' : 'Create Event'}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}

export default EventForm;
