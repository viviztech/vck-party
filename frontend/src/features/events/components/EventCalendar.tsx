/**
 * Event Calendar Component
 * Calendar view for displaying events
 */

import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardContent } from '@/components/DataDisplay/Card';
import { Button } from '@/components/Form/Button';
import type { Event } from '@/services/eventsService';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';

interface EventCalendarProps {
  events: Event[];
  onEventClick?: (event: Event) => void;
  onDateClick?: (date: Date) => void;
}

export function EventCalendar({ events, onEventClick, onDateClick }: EventCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const eventsByDate = useMemo(() => {
    const map = new Map<string, Event[]>();
    events.forEach((event) => {
      const dateKey = event.start_date.split('T')[0];
      const existing = map.get(dateKey) || [];
      map.set(dateKey, [...existing, event]);
    });
    return map;
  }, [events]);

  const daysInMonth = useMemo(() => {
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days: (Date | null)[] = [];

    // Add empty slots for days before the first day of the month
    for (let i = 0; i < firstDay.getDay(); i++) {
      days.push(null);
    }

    // Add all days of the month
    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(new Date(year, month, i));
    }

    return days;
  }, [year, month]);

  const getEventColor = (eventType: string): string => {
    const colors: Record<string, string> = {
      meeting: 'bg-blue-100 text-blue-800 border-blue-200',
      rally: 'bg-red-100 text-red-800 border-red-200',
      campaign: 'bg-purple-100 text-purple-800 border-purple-200',
      conference: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      workshop: 'bg-green-100 text-green-800 border-green-200',
      training: 'bg-teal-100 text-teal-800 border-teal-200',
      volunteer: 'bg-orange-100 text-orange-800 border-orange-200',
      fundraiser: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      awareness: 'bg-cyan-100 text-cyan-800 border-cyan-200',
      visit: 'bg-gray-100 text-gray-800 border-gray-200',
      inauguration: 'bg-pink-100 text-pink-800 border-pink-200',
      other: 'bg-gray-100 text-gray-800 border-gray-200',
    };
    return colors[eventType] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatDateKey = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev);
      if (direction === 'prev') {
        newDate.setMonth(newDate.getMonth() - 1);
      } else {
        newDate.setMonth(newDate.getMonth() + 1);
      }
      return newDate;
    });
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <Card>
      <div className="flex flex-row items-center justify-between p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center">
          <CalendarIcon size={20} className="mr-2" />
          {monthNames[month]} {year}
        </h2>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={goToToday}>Today</Button>
          <Button variant="ghost" size="sm" onClick={() => navigateMonth('prev')}>
            <ChevronLeft size={18} />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => navigateMonth('next')}>
            <ChevronRight size={18} />
          </Button>
        </div>
      </div>
      <CardContent>
        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {dayNames.map((day) => (
            <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 gap-1">
          {daysInMonth.map((day, index) => {
            if (!day) {
              return <div key={`empty-${index}`} className="h-24 bg-gray-50" />;
            }

            const dateKey = formatDateKey(day);
            const dayEvents = eventsByDate.get(dateKey) || [];
            const isToday = formatDateKey(new Date()) === dateKey;

            return (
              <div
                key={dateKey}
                className={`h-24 p-1 border rounded-lg cursor-pointer transition-colors ${
                  isToday
                    ? 'bg-blue-50 border-blue-300'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => onDateClick?.(day)}
              >
                <div className={`text-xs font-medium mb-1 ${
                  isToday ? 'text-blue-600' : 'text-gray-500'
                }`}>
                  {day.getDate()}
                </div>
                <div className="space-y-1 overflow-y-auto max-h-16">
                  {dayEvents.slice(0, 3).map((event) => (
                    <div
                      key={event.id}
                      className={`text-xs px-1 py-0.5 rounded border truncate cursor-pointer ${getEventColor(event.event_type)}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onEventClick?.(event);
                      }}
                    >
                      {event.title}
                    </div>
                  ))}
                  {dayEvents.length > 3 && (
                    <div className="text-xs text-gray-500 pl-1">
                      +{dayEvents.length - 3} more
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Event type legend */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex flex-wrap gap-2">
            {['meeting', 'rally', 'campaign', 'workshop', 'training', 'volunteer'].map((type) => (
              <div key={type} className="flex items-center space-x-1">
                <div className={`w-3 h-3 rounded ${getEventColor(type).split(' ')[0]}`} />
                <span className="text-xs text-gray-600 capitalize">{type}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default EventCalendar;
