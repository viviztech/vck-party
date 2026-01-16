/**
 * Event Card Component
 * Card view for displaying event information
 */

import React from 'react';
import { Card, CardContent } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import type { Event } from '@/services/eventsService';
import { Calendar, MapPin, Clock, Users } from 'lucide-react';
import { formatDate } from '@/utils/helpers';

interface EventCardProps {
  event: Event;
  onClick?: () => void;
}

export function EventCard({ event, onClick }: EventCardProps) {
  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      draft: { variant: 'default', label: 'Draft' },
      published: { variant: 'success', label: 'Published' },
      cancelled: { variant: 'error', label: 'Cancelled' },
      completed: { variant: 'info', label: 'Completed' },
      postponed: { variant: 'warning', label: 'Postponed' },
      in_progress: { variant: 'success', label: 'In Progress' },
    };
    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getTypeBadge = (type: string) => {
    const typeConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
      meeting: { variant: 'info', label: 'Meeting' },
      rally: { variant: 'warning', label: 'Rally' },
      campaign: { variant: 'default', label: 'Campaign' },
      conference: { variant: 'info', label: 'Conference' },
      workshop: { variant: 'success', label: 'Workshop' },
      training: { variant: 'success', label: 'Training' },
      volunteer: { variant: 'info', label: 'Volunteer' },
      fundraiser: { variant: 'warning', label: 'Fundraiser' },
      awareness: { variant: 'info', label: 'Awareness' },
      visit: { variant: 'default', label: 'Visit' },
      inauguration: { variant: 'warning', label: 'Inauguration' },
      other: { variant: 'default', label: 'Other' },
    };
    const config = typeConfig[type] || { variant: 'default', label: type };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  return (
    <div onClick={onClick} className={onClick ? 'cursor-pointer' : ''}>
      <Card hover={!!onClick}>
        <CardContent className="space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="font-semibold text-gray-900">{event.title}</h3>
                {getTypeBadge(event.event_type)}
              </div>
              {getStatusBadge(event.status)}
            </div>
          </div>

          {event.description && (
            <p className="text-sm text-gray-600 line-clamp-2">{event.description}</p>
          )}

          <div className="space-y-2">
            <div className="flex items-center text-sm text-gray-600">
              <Calendar size={14} className="mr-2" />
              {formatDate(event.start_date)}
              {event.start_date !== event.end_date && ` - ${formatDate(event.end_date)}`}
            </div>
            
            {event.start_time && (
              <div className="flex items-center text-sm text-gray-600">
                <Clock size={14} className="mr-2" />
                {event.start_time} - {event.end_time || 'End'}
              </div>
            )}
            
            <div className="flex items-center text-sm text-gray-600">
              <MapPin size={14} className="mr-2" />
              {event.venue || event.district || 'Location not specified'}
            </div>
            
            <div className="flex items-center text-sm text-gray-600">
              <Users size={14} className="mr-2" />
              Expected: {event.expected_attendees || 0}
              {event.actual_attendees && ` | Actual: ${event.actual_attendees}`}
            </div>
          </div>

          {event.tags && event.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {event.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="default" size="sm">{tag}</Badge>
              ))}
              {event.tags.length > 3 && (
                <Badge variant="default" size="sm">+{event.tags.length - 3}</Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default EventCard;
