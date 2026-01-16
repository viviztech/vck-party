/**
 * Post Detail Page
 * Displays post with comments
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { communicationsService, ForumPost, Comment } from '../../../services/communicationsService';
import { Button } from '../../../components/Form';
import { Card } from '../../../components/DataDisplay';
import { Badge } from '../../../components/DataDisplay';
import { Avatar } from '../../../components/DataDisplay';
import { Spinner } from '../../../components/Feedback';
import { CommentForm } from '../components';
import { format } from 'date-fns';

export default function PostDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [post, setPost] = useState<ForumPost | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPost = useCallback(async () => {
    if (!id) return;
    
    setLoading(true);
    try {
      const response = await communicationsService.getPost(id);
      setPost(response.post);
      setComments(response.comments);
    } catch (error) {
      console.error('Failed to load post:', error);
      navigate('/communications/forums');
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    fetchPost();
  }, [fetchPost]);

  const handleDelete = async () => {
    if (!id || !post) return;
    
    if (!window.confirm('Are you sure you want to delete this post?')) {
      return;
    }

    try {
      await communicationsService.deletePost(id);
      navigate(`/communications/forums/${post.forum_id}`);
    } catch (error) {
      console.error('Failed to delete post:', error);
    }
  };

  const handleLike = async () => {
    if (!id) return;
    
    try {
      const updatedPost = await communicationsService.likePost(id);
      setPost(updatedPost);
    } catch (error) {
      console.error('Failed to like post:', error);
    }
  };

  const handleCommentAdded = (comment: Comment) => {
    setComments([comment, ...comments]);
    if (post) {
      setPost({ ...post, replies_count: post.replies_count + 1 });
    }
  };

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM d, yyyy h:mm a');
  };

  const renderComment = (comment: Comment, depth = 0) => (
    <div key={comment.id} className={`${depth > 0 ? 'ml-8 mt-4' : 'mt-4'}`}>
      <div className="flex items-start gap-3">
        <Avatar name={comment.author_name} size="sm" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium">{comment.author_name}</span>
            <span className="text-sm text-gray-500">{formatDate(comment.created_at)}</span>
          </div>
          <p className="text-gray-700 mt-1">{comment.content}</p>
        </div>
      </div>
      {comment.replies?.map((reply) => renderComment(reply, depth + 1))}
    </div>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!post) {
    return (
      <div className="text-center py-8 text-gray-500">
        Post not found
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate(`/communications/forums/${post.forum_id}`)}>
          ← Back to Forum
        </Button>
      </div>

      <Card>
        <div className="p-6">
          <div className="flex items-start gap-4">
            <Avatar name={post.author_name} size="lg" />
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl font-bold text-gray-900">{post.title || 'Untitled'}</h1>
                {post.is_pinned && <Badge variant="warning">Pinned</Badge>}
                {post.is_locked && <Badge variant="error">Locked</Badge>}
                {post.is_anonymous && <Badge variant="default">Anonymous</Badge>}
              </div>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                <span>{post.author_name}</span>
                <span>{formatDate(post.created_at)}</span>
                <span>{post.views_count} views</span>
              </div>
          </div>

          </div>
            <div className="mt-6 prose max-w-none">
            <div className="whitespace-pre-wrap">{post.content}</div>
          </div>

          {post.tags && post.tags.length > 0 && (
            <div className="mt-4 flex gap-2 flex-wrap">
              {post.tags.map((tag, index) => (
                <Badge key={index} variant="default" size="sm">{tag}</Badge>
              ))}
            </div>
          )}

          <div className="mt-6 flex items-center gap-4 pt-4 border-t border-gray-200">
            <Button variant="outline" size="sm" onClick={handleLike}>
              👍 Like ({post.likes_count})
            </Button>
            <span className="text-sm text-gray-600">{post.replies_count} replies</span>
            <div className="flex-1"></div>
            <Button variant="outline" size="sm" onClick={handleDelete}>
              Delete
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-medium">Comments ({comments.length})</h2>
        </div>
        <div className="p-4">
          <CommentForm
            postId={post.id}
            onCommentAdded={handleCommentAdded}
          />
        </div>
        <div className="p-4 pt-0">
          {comments.length === 0 ? (
            <p className="text-center text-gray-500 py-4">No comments yet</p>
          ) : (
            <div className="space-y-4">
              {comments.map((comment) => renderComment(comment))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
