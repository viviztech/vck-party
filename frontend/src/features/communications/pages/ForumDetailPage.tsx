/**
 * Forum Detail Page
 * Displays forum details with posts
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { communicationsService, Forum, ForumPost } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Card } from '../../../components/DataDisplay';
import { Badge } from '../../../components/DataDisplay';
import { Avatar } from '../../../components/DataDisplay';
import { Spinner } from '../../../components/Feedback';
import { format } from 'date-fns';

export default function ForumDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [forum, setForum] = useState<Forum | null>(null);
  const [posts, setPosts] = useState<ForumPost[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchForum = useCallback(async () => {
    if (!id) return;
    
    setLoading(true);
    try {
      const response = await communicationsService.getForum(id);
      setForum(response.forum);
      setPosts(response.recent_posts);
    } catch (error) {
      console.error('Failed to load forum:', error);
      navigate('/communications/forums');
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    fetchForum();
  }, [fetchForum]);

  const handleCreatePost = () => {
    navigate(`/communications/forums/${id}/posts/create`);
  };

  const handleViewPost = (post: ForumPost) => {
    navigate(`/communications/posts/${post.id}`);
  };

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM d, yyyy h:mm a');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!forum) {
    return (
      <div className="text-center py-8 text-gray-500">
        Forum not found
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/communications/forums')}>
          ← Back to Forums
        </Button>
      </div>

      <Card>
        <div className="p-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{forum.title}</h1>
              <p className="text-gray-600 mt-2">{forum.description}</p>
              <div className="flex items-center gap-4 mt-4">
                <Badge variant="primary">{forum.category}</Badge>
                {forum.is_moderated && <Badge variant="warning">Moderated</Badge>}
                <span className="text-sm text-gray-500">
                  Created by {forum.created_by_name} on {formatDate(forum.created_at)}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="primary" onClick={handleCreatePost}>
                New Post
              </Button>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-3 gap-4 border-t border-gray-200 pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{forum.thread_count}</div>
              <div className="text-sm text-gray-600">Threads</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{forum.post_count}</div>
              <div className="text-sm text-gray-600">Posts</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {forum.moderators?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Moderators</div>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-medium">Recent Posts</h2>
        </div>
        {posts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No posts yet. Be the first to post!
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {posts.map((post) => (
              <div
                key={post.id}
                className="p-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => handleViewPost(post)}
              >
                <div className="flex items-start gap-3">
                  <Avatar name={post.author_name} size="sm" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{post.title || 'Untitled'}</span>
                      {post.is_pinned && <Badge variant="warning" size="sm">Pinned</Badge>}
                      {post.is_locked && <Badge variant="error" size="sm">Locked</Badge>}
                    </div>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                      {post.content}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span>{post.author_name}</span>
                      <span>{formatDate(post.created_at)}</span>
                      <span>{post.replies_count} replies</span>
                      <span>{post.likes_count} likes</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
