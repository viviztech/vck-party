/**
 * Forums List Component
 * Reusable component to display forums list
 */

import { Forum } from '../../../services/communicationsService';
import { Badge } from '../../../components/DataDisplay';
import { format } from 'date-fns';

interface ForumsListProps {
  forums: Forum[];
  onForumClick: (forum: Forum) => void;
}

export default function ForumsList({ forums, onForumClick }: ForumsListProps) {
  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM d, yyyy');
  };

  if (forums.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No forums found
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-200">
      {forums.map((forum) => (
        <div
          key={forum.id}
          className="p-4 hover:bg-gray-50 cursor-pointer"
          onClick={() => onForumClick(forum)}
        >
          <div className="flex justify-between items-start">
            <div>
              <h3 className="font-medium text-gray-900">{forum.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{forum.description}</p>
              <div className="flex items-center gap-4 mt-2">
                <Badge variant="primary">{forum.category}</Badge>
                {forum.is_moderated && <Badge variant="warning">Moderated</Badge>}
                <span className="text-sm text-gray-500">
                  {forum.thread_count} threads • {forum.post_count} posts
                </span>
                <span className="text-sm text-gray-500">
                  by {forum.created_by_name}
                </span>
                {forum.last_activity_at && (
                  <span className="text-sm text-gray-500">
                    Active: {formatDate(forum.last_activity_at)}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
