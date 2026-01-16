/**
 * Forum Card Component
 * Card to display a single forum
 */

import { Forum } from '../../../services/communicationsService';
import { Badge } from '../../../components/DataDisplay';
import { format } from 'date-fns';

interface ForumCardProps {
  forum: Forum;
  onClick: () => void;
}

export default function ForumCard({ forum, onClick }: ForumCardProps) {
  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM d, yyyy');
  };

  return (
    <div
      className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md cursor-pointer transition-all"
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-medium text-gray-900">{forum.title}</h3>
            <Badge variant="primary" size="sm">{forum.category}</Badge>
            {forum.is_moderated && <Badge variant="warning" size="sm">Moderated</Badge>}
          </div>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{forum.description}</p>
          <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
            <span>{forum.thread_count} threads</span>
            <span>{forum.post_count} posts</span>
            <span>by {forum.created_by_name}</span>
            {forum.last_activity_at && (
              <span>Active: {formatDate(forum.last_activity_at)}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
