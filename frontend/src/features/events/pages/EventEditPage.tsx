/**
 * Event Edit Page
 * Edit an existing event
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/Form/Button';
import { EventForm } from '../components/EventForm';
import { eventsService, Event, EventUpdate } from '@/services/eventsService';
import { ArrowLeft } from 'lucide-react';

export function EventEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [event, setEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvent = async () => {
      if (!id) return;
      try {
        const eventData = await eventsService.getEvent(id);
        setEvent(eventData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch event');
      } finally {
        setLoading(false);
      }
    };
    fetchEvent();
  }, [id]);

  const handleSubmit = async (data: EventUpdate) => {
    if (!id) return;
    try {
      setError(null);
      await eventsService.updateEvent(id, data);
      navigate(`/events/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update event');
    }
  };

  const handleCancel = () => {
    if (id) {
      navigate(`/events/${id}`);
    } else {
      navigate('/events');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error && !event) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/events')}>
          Back to Events
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Edit Event</h1>
          <p className="text-gray-500">Update event details</p>
        </div>
        <Button variant="outline" onClick={() => navigate('/events')}>
          <ArrowLeft size={16} className="mr-1" />
          Back to Events
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {event && (
        <EventForm event={event} onSubmit={handleSubmit} onCancel={handleCancel} />
      )}
    </div>
  );
}

export default EventEditPage;
