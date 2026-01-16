/**
 * Forum Post Component
 * Displays a forum post with optional reply functionality
 */

import type { ForumPost } from '../../../services/communicationsService';
import { Badge } from '../../../components/DataDisplay';
import { Avatar } from '../../../components/DataDisplay';
import { Button } from '../../../components/Form';
import { format } from 'date-fns';

interface ForumPostProps {
  post: ForumPost;
  onLike?: () => void;
  onReply?: () => void;
  onClick?: () => void;
  showFullContent?: boolean;
}

export default function ForumPost({ 
  post, 
  onLike, 
  onReply, 
  onClick,
  showFullContent = false 
}: ForumPostProps) {
  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM d, yyyy h:mm a');
  };

  return (
    <div 
      className={`p-4 border border-gray-200 rounded-lg ${onClick ? 'cursor-pointer hover:bg-gray-50' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <Avatar name={post.author_name} size="md" />
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium">{post.author_name}</span>
            <span className="text-sm text-gray-500">{formatDate(post.created_at)}</span>
            {post.is_pinned && <Badge variant="warning" size="sm">Pinned</Badge>}
            {post.is_locked && <Badge variant="error" size="sm">Locked</Badge>}
            {post.is_anonymous && <Badge variant="default" size="sm">Anonymous</Badge>}
          </div>
          
          {post.title && (
            <h4 className="font-medium text-gray-900 mt-2">{post.title}</h4>
          )}
          
          <p className={`text-gray-700 mt-1 ${!showFullContent ? 'line-clamp-3' : ''}`}>
            {post.content}
          </p>

          {post.tags && post.tags.length > 0 && (
            <div className="mt-2 flex gap-1 flex-wrap">
              {post.tags.map((tag, index) => (
                <Badge key={index} variant="default" size="sm">{tag}</Badge>
              ))}
            </div>
          )}

          <div className="flex items-center gap-4 mt-3">
            <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onLike?.(); }}>
              👍 {post.likes_count}
            </Button>
            <span className="text-sm text-gray-600">{post.replies_count} replies</span>
            <span className="text-sm text-gray-600">{post.views_count} views</span>
            {onReply && (
              <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onReply?.(); }}>
                Reply
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
