/**
 * Events List Page
 * Lists all events with filtering and search
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/Form/Button';
import { Tabs } from '@/components/DataDisplay/Tabs';
import { eventsService, Event, EventFilters as EventFiltersType } from '@/services/eventsService';
import { Plus, Calendar, Grid, List } from 'lucide-react';
import { EventsTable } from '../components/EventsTable';
import { EventFilters } from '../components/EventFilters';
import { EventCard } from '../components/EventCard';

export function EventsListPage() {
  const navigate = useNavigate();
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<EventFiltersType>({});
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [view, setView] = useState<'list' | 'grid'>('list');

  const limit = 10;

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const response = await eventsService.getEvents({
        ...filters,
        page,
        limit,
      });
      setEvents(response.events);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handleSearch = (search: string) => {
    setFilters((prev) => ({ ...prev, search: search || undefined }));
    setPage(1);
  };

  const handleFilterChange = (newFilters: EventFiltersType) => {
    setFilters(newFilters);
    setPage(1);
  };

  const handleRowClick = (event: Event) => {
    navigate(`/events/${event.id}`);
  };

  const tabs = [
    { key: 'all', label: 'All Events' },
    { key: 'upcoming', label: 'Upcoming' },
    { key: 'past', label: 'Past' },
  ];

  const [activeTab, setActiveTab] = useState('all');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Events</h1>
          <p className="text-gray-500">Manage events, campaigns, and activities</p>
        </div>
        <Button onClick={() => navigate('/events/new')} leftIcon={<Plus size={16} />}>
          New Event
        </Button>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} variant="underline" />

      <div className="space-y-4">
          <div className="flex items-center justify-between">
            <EventFilters
              filters={filters}
              onFilterChange={handleFilterChange}
              onSearch={handleSearch}
            />
            <div className="flex items-center space-x-2">
              <Button
                variant={view === 'list' ? 'secondary' : 'outline'}
                size="sm"
                onClick={() => setView('list')}
              >
                <List size={16} />
              </Button>
              <Button
                variant={view === 'grid' ? 'secondary' : 'outline'}
                size="sm"
                onClick={() => setView('grid')}
              >
                <Grid size={16} />
              </Button>
            </div>
          </div>

          {view === 'list' ? (
            <EventsTable
              events={events}
              loading={loading}
              onRowClick={handleRowClick}
              page={page}
              limit={limit}
              total={total}
              onPageChange={setPage}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {events.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  onClick={() => handleRowClick(event)}
                />
              ))}
              {events.length === 0 && !loading && (
                <div className="col-span-full text-center py-12 text-gray-500">
                  <Calendar size={48} className="mx-auto mb-4 text-gray-300" />
                  <p>No events found</p>
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => navigate('/events/new')}
                  >
                    Create your first event
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
    </div>
  );
}

export default EventsListPage;
