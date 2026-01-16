/**
 * Announcements List Component
 * Reusable component to display announcements list
 */

import { Announcement } from '../../../services/communicationsService';
import { Badge } from '../../../components/DataDisplay';
import { Avatar } from '../../../components/DataDisplay';
import { format } from 'date-fns';

interface AnnouncementsListProps {
  announcements: Announcement[];
  onAnnouncementClick: (announcement: Announcement) => void;
}

export default function AnnouncementsList({ announcements, onAnnouncementClick }: AnnouncementsListProps) {
  const getPriorityBadge = (priority: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'> = {
      low: 'default',
      medium: 'info',
      high: 'warning',
      urgent: 'error',
    };
    return <Badge variant={colors[priority] || 'default'}>{priority}</Badge>;
  };

  const getCategoryBadge = (category: string) => {
    return <Badge variant="primary">{category}</Badge>;
  };

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM d, yyyy');
  };

  if (announcements.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No announcements found
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-200">
      {announcements.map((announcement) => (
        <div
          key={announcement.id}
          className="p-4 hover:bg-gray-50 cursor-pointer"
          onClick={() => onAnnouncementClick(announcement)}
        >
          <div className="flex items-start gap-4">
            {announcement.is_pinned && (
              <span className="text-yellow-500 text-xl" title="Pinned">
                📌
              </span>
            )}
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-medium text-gray-900">{announcement.title}</h3>
                {getCategoryBadge(announcement.category)}
                {getPriorityBadge(announcement.priority)}
              </div>
              <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                {announcement.content}
              </p>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <Avatar name={announcement.author_name} size="sm" />
                  <span>{announcement.author_name}</span>
                </div>
                <span>{formatDate(announcement.created_at)}</span>
                <span>{announcement.views_count} views</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
